import re
import struct
import threading
import time
import warnings
from collections.abc import Sequence
from typing import Any, Literal, Optional, Union

import numpy
import tidy3d

from . import typing as pft
from .cache import _mode_overlap_cache, cache_s_matrix
from .extension import (
    Component,
    GaussianPort,
    Model,
    Port,
    Reference,
    SMatrix,
    _connect_s_matrices,
    _content_repr,
    frequency_classification,
    register_model_class,
)
from .tidy3d_model import _align_and_overlap, _ModeSolverRunner


def _gather_status(*runners: Any) -> dict[str, Any]:
    """Create an overall status based on a collection of Tidy3D runners."""
    num_tasks = 0
    progress = 0
    message = "success"
    tasks = {}
    for task in runners:
        task_status = task.status
        inner_tasks = task_status.get("tasks", {})
        tasks.update(inner_tasks)
        task_weight = max(1, len(inner_tasks))
        num_tasks += task_weight
        if message != "error":
            if task_status["message"] == "error":
                message = "error"
            elif task_status["message"] == "running":
                message = "running"
                progress += task_weight * task_status["progress"]
            elif task_status["message"] == "success":
                progress += task_weight * 100
    if message == "running":
        progress /= num_tasks
    else:
        progress = 100
    return {"progress": progress, "message": message, "tasks": tasks}


class _CircuitModelRunner:
    def __init__(
        self,
        runners: dict[Any, Any],
        frequencies: Sequence[float],
        component_name: str,
        ports: dict[str, Port],
        port_connections: dict[str, tuple[int, str, int]],
        connections: Sequence[tuple[tuple[int, str, int], tuple[int, str, int]]],
        instance_port_data: Sequence[tuple[Any, Any]],
        cost_estimation: bool,
    ) -> None:
        self.runners = runners
        self.frequencies = frequencies
        self.component_name = component_name
        self.ports = ports
        self.port_connections = port_connections
        self.connections = connections
        self.instance_port_data = instance_port_data
        self.cost_estimation = cost_estimation

        self.lock = threading.Lock()
        self._s_matrix = None
        self._status = {"progress": 0, "message": "running", "tasks": {}}

        self.thread = threading.Thread(daemon=True, target=self._run_and_monitor_task)
        self.thread.start()

    def _run_and_monitor_task(self):
        task_status = _gather_status(*self.runners.values())
        w_tasks = 3 * len(task_status["tasks"])
        n_ports = len(self.instance_port_data)
        n_connections = len(self.connections)
        denominator = w_tasks + n_ports + n_connections

        with self.lock:
            self._status = task_status
            self._status["progress"] *= w_tasks / denominator

        while task_status["message"] == "running":
            time.sleep(0.1)
            task_status = _gather_status(*self.runners.values())
            with self.lock:
                self._status = task_status
                self._status["progress"] *= w_tasks / denominator

        if task_status["message"] == "error":
            with self.lock:
                self._status = task_status
                self._status["message"] = "error"
                self._status["progress"] = 100
            return

        with self.lock:
            self._status = task_status
            if self.cost_estimation:
                return
            self._status["message"] = "running"
            self._status["progress"] *= w_tasks / denominator

        s_dict = {}
        for index, (instance_ports, instance_keys) in enumerate(self.instance_port_data):
            # Check if reference is needed
            if instance_ports is None:
                continue

            s_matrix = self.runners[index].s_matrix
            if s_matrix is None:
                with self.lock:
                    self._status["message"] = "error"
                    self._status["progress"] = 100
                return

            # Fix port phases if a rotation is applied
            mode_factor = {
                f"{port_name}@{mode}": 1.0
                for port_name, port in instance_ports
                for mode in range(port.num_modes)
            }

            if instance_keys is not None:
                for port_name, port in instance_ports:
                    key = instance_keys.get(port_name)
                    if key is None:
                        continue

                    # Port mode
                    overlap = _mode_overlap_cache[key]
                    if overlap is None:
                        overlap = _align_and_overlap(
                            self.runners[(index, port_name, 0)].data,
                            self.runners[(index, port_name, 1)].data,
                        )[0]
                        _mode_overlap_cache[key] = overlap

                    for mode in range(port.num_modes):
                        mode_factor[f"{port_name}@{mode}"] = overlap[mode]

            for (i, j), s_ji in s_matrix.elements.items():
                s_dict[(index, i), (index, j)] = s_ji * mode_factor[i] / mode_factor[j]

            with self.lock:
                self._status["progress"] = 100 * (w_tasks + index + 1) / denominator

        s_dict = _connect_s_matrices(s_dict, self.connections, len(self.instance_port_data))

        # Build S matrix with desired ports
        ports = {
            (index, f"{ref_name}@{n}"): f"{port_name}@{n}"
            for (index, ref_name, modes), port_name in self.port_connections.items()
            for n in range(modes)
        }

        elements = {
            (ports[i], ports[j]): s_ji
            for (i, j), s_ji in s_dict.items()
            if i in ports and j in ports
        }

        with self.lock:
            self._s_matrix = SMatrix(self.frequencies, elements, self.ports)
            self._status["progress"] = 100
            self._status["message"] = "success"

    @property
    def status(self) -> dict[str, Any]:
        with self.lock:
            return self._status

    @property
    def s_matrix(self) -> SMatrix:
        with self.lock:
            return self._s_matrix


def _compare_angles(a: float, b: float) -> bool:
    r = (a - b) % 360
    return r <= 1e-12 or 360 - r <= 1e-12


# Return a flattening key (for caching) if flattening is required, and
# a bool indicating whether phase correction is required
def _analyze_transform(
    reference: Reference,
    classification: Literal["optical", "electrical"],
    frequencies: Sequence[float],
) -> tuple[Union[tuple[Union[tuple[float, float], None], float, bool], None], bool]:
    technology = reference.component.technology

    background_medium = technology.get_background_medium(classification)
    extrusion_media = [e.get_medium(classification) for e in technology.extrusion_specs]

    uniform = background_medium.is_spatially_uniform and all(
        medium.is_spatially_uniform for medium in extrusion_media
    )

    translated = not numpy.allclose(reference.origin, (0, 0), atol=1e-12)
    rotated = not _compare_angles(reference.rotation, 0)

    if not uniform and (translated or rotated):
        return (tuple(reference.origin.tolist()), reference.rotation, reference.x_reflection), None

    if reference.x_reflection:
        return (None, reference.rotation, reference.x_reflection), None

    # _align_and_overlap only works for rotations that are a multiple of 90°
    rotation_fraction = reference.rotation % 90
    is_multiple_of_90 = rotation_fraction < 1e-12 or (90 - rotation_fraction < 1e-12)
    if not is_multiple_of_90:
        return (None, reference.rotation, reference.x_reflection), None

    # _align_and_overlap does not support angled ports either
    ports = reference.component.select_ports(classification)
    for port in ports.values():
        if isinstance(port, GaussianPort):
            _, _, _, theta, _ = port._axis_aligned_properties(frequencies)
        else:
            _, _, _, theta, _ = port._axis_aligned_properties()
        if theta != 0.0:
            return (None, reference.rotation, reference.x_reflection), None

    translated_mask = any(e.mask_spec.uses_translation() for e in technology.extrusion_specs)
    if translated_mask and rotated:
        return (None, reference.rotation, reference.x_reflection), None

    fully_anisotropic = background_medium.is_fully_anisotropic or any(
        medium.is_fully_anisotropic for medium in extrusion_media
    )
    in_plane_isotropic = (
        not fully_anisotropic
        and (
            not isinstance(background_medium, tidy3d.AnisotropicMedium)
            or background_medium.xx == background_medium.yy
        )
        and all(
            (not isinstance(medium, tidy3d.AnisotropicMedium) or medium.xx == medium.yy)
            for medium in extrusion_media
        )
    )

    if (fully_anisotropic and rotated) or (
        not in_plane_isotropic and rotated and not _compare_angles(reference.rotation, 180)
    ):
        return (None, reference.rotation, reference.x_reflection), None

    return None, rotated


def _validate_update_dict(
    updates: dict[Union[str, re.Pattern, int, tuple[re.Pattern, int], None], Any],
) -> list[tuple[Union[str, re.Pattern, int, tuple[re.Pattern, int], None], Any]]:
    """Validate keys in updates dictionary and puth them in canonical form."""
    valid_updates = []
    for key, value in updates.items():
        if len(key) == 0:
            raise KeyError("Empty key in 'updates' is not allowed.")
        valid_key = []
        expect_int = False
        for i, k in enumerate(key):
            if k is None:
                if len(valid_key) == 0 or valid_key[-1] is not None:
                    valid_key.append(None)
                expect_int = False
            elif isinstance(k, str):
                valid_key.append((re.compile(k), -1))
                expect_int = True
            elif isinstance(k, re.Pattern):
                valid_key.append((re.compile(k), -1))
                expect_int = True
            elif isinstance(k, int) and expect_int:
                valid_key[-1] = (valid_key[-1][0], k)
                expect_int = False
            elif (
                isinstance(k, tuple)
                and len(k) == 2
                and isinstance(k[0], re.Pattern)
                and isinstance(k[1], int)
            ):
                valid_key.append(k)
            else:
                raise RuntimeError(
                    f"Invalid value in position {i} in key {tuple(key)}: {k}. Expected a "
                    "string, a compiled regular expression pattern, "
                    + ("an integer, " if expect_int else "")
                    + "or 'None'."
                )
        valid_updates.append((tuple(valid_key), value))
    return valid_updates


class CircuitModel(Model):
    """Model based on circuit-level S-parameter calculation.

    The component is expected to be composed of interconnected references.
    Scattering parameters are computed based on the S matrices from all
    references and their interconnections.

    The S matrix of each reference is calculated based on the active model
    of the reference's component. Each calculation is preceded by an update
    to the componoent's technology, the component itself, and its active
    model by calling :attr:`Reference.update`. They are reset to their
    original state after the :func:`CircuitModel.start` function is called.
    Keyword arguents in :attr:`Reference.s_matrix_kwargs` will be passed on
    to :func:`CircuitModel.start`.

    If a reference includes repetitions, it is flattened so that each
    instance is called separatelly.

    Args:
        mesh_refinement: Minimal number of mesh elements per wavelength used
          for mode solving.
        verbose: Flag setting the verbosity of mode solver runs.

    See also:
        `Circuit Model guide <../guides/Circuit_Model.ipynb>`__
    """

    def __init__(
        self,
        mesh_refinement: Optional[pft.PositiveFloat] = None,
        verbose: bool = True,
    ):
        super().__init__(mesh_refinement=mesh_refinement, verbose=verbose)
        self.mesh_refinement = mesh_refinement
        self.verbose = verbose

    def __copy__(self) -> "CircuitModel":
        return CircuitModel(self.mesh_refinement, self.verbose)

    def __deepcopy__(self, memo: Optional[dict] = None) -> "CircuitModel":
        return CircuitModel(self.mesh_refinement, self.verbose)

    def __str__(self) -> str:
        return "CircuitModel"

    def __repr__(self) -> str:
        return "CircuitModel()"

    @cache_s_matrix
    def start(
        self,
        component: Component,
        frequencies: Sequence[float],
        updates: dict[Sequence[Union[str, int, None]], dict[str, dict[str, Any]]] = {},
        chain_technology_updates: bool = True,
        verbose: Optional[bool] = None,
        cost_estimation: bool = False,
        **kwargs: Any,
    ) -> _CircuitModelRunner:
        """Start computing the S matrix response from a component.

        Args:
            component: Component from which to compute the S matrix.
            frequencies: Sequence of frequencies at which to perform the
              computation.
            updates: Dictionary of parameter updates to be applied to
              components, technologies, and models for references within the
              main component. See below for further information.
            chain_technology_updates: if set, a technology update will trigger
              an update for all components using that technology.
            verbose: If set, overrides the model's ``verbose`` attribute and
              is passed to reference models.
            cost_estimation: If set, Tidy3D simulations are uploaded, but not
              executed. S matrix will *not* be computed.
            **kwargs: Keyword arguments passed to reference models.

        Returns:
            Result object with attributes ``status`` and ``s_matrix``.

        The ``'updates'`` dictionary contains keyword arguments for the
        :func:`Reference.update` function for the references in the component
        dependency tree, such that, when the S parameter of a specific reference
        are computed, that reference can be updated without affecting others
        using the same component.

        Each key in the dictionary is used as a reference specification. It must
        be a tuple with any number of the following:

        - ``name: str | re.Pattern``: selects any reference whose component name
          matches the given regex.

        - ``i: int``, directly following ``name``: limits the selection to
          ``reference[i]`` from the list of references matching the name. A
          negative value will match all list items. Note that each repetiton in
          a reference array counts as a single element in the list.

        - ``None``: matches any reference at any depth.

        Examples:
            >>> updates = {
            ...     # Apply component updates to the first "ARM" reference in
            ...     # the main component
            ...     ("ARM", 0): {"component_updates": {"radius": 10}}
            ...     # Apply model updates to the second "BEND" reference under
            ...     # any "SUB" references in the main component
            ...     ("SUB", "BEND", 1): {"model_updates": {"verbose": False}}
            ...     # Apply technology updates to references with component name
            ...     # starting with "COMP_" prefix, at any subcomponent depth
            ...     (None, "COMP.*"): {"technology_updates": {"thickness": 0.3}}
            ... }
            >>> s_matrix = component.s_matrix(
            ...     frequencies, model_kwargs={"updates": updates}
            ... )

        See also:
            - `Circuit Model guide <../guides/Circuit_Model.ipynb>`__
            - `Cascaded Rings Filter example
              <../examples/Cascaded_Rings_Filter.ipynb>`__
        """
        if verbose is None:
            verbose = self.verbose
            s_matrix_kwargs = {}
        else:
            s_matrix_kwargs = {"verbose": verbose}
        if cost_estimation:
            s_matrix_kwargs["cost_estimation"] = cost_estimation
        frequencies = numpy.array(frequencies, dtype=float, ndmin=1)
        classification = frequency_classification(frequencies)
        netlist = component.get_netlist()

        # 'inputs' is not supported in CircuitModel
        kwargs = dict(kwargs)
        if "inputs" in kwargs:
            del kwargs["inputs"]

        valid_updates = _validate_update_dict(updates)
        reference_index = {}

        # Store copies of instance ports and their reference for phase correction
        instance_port_data = [(None, None)] * len(netlist["instances"])

        runners = {}
        flattened_component_cache = {}

        for index, reference in enumerate(netlist["instances"]):
            ref_component = reference.component
            current_reference_index = reference_index.get(ref_component.name, -1) + 1
            reference_index[ref_component.name] = current_reference_index

            if ref_component.select_active_model(classification) is None:
                # Check if the model is really needed
                if any(
                    index0 == index or index1 == index
                    for (index0, _, _), (index1, _, _) in netlist["connections"]
                ) or any(i == index for i, _, _ in netlist["ports"]):
                    raise RuntimeError(f"Component '{ref_component.name}' has no active model.")
                continue

            ports = ref_component.select_ports(classification)
            instance_port_data[index] = (
                tuple((port_name, port.copy(True)) for port_name, port in ports.items()),
                None,
            )

            # Match updates with current reference
            reference_updates = {}
            technology_updates = {}
            component_updates = {}
            model_updates = {}
            for key, value in valid_updates:
                if key[0] is None:
                    reference_updates[key] = value
                    key = key[1:]
                if len(key) == 0:
                    technology_updates.update(value.get("technology_updates", {}))
                    component_updates.update(value.get("component_updates", {}))
                    model_updates.update(value.get("model_updates", {}))
                elif key[0][0].match(ref_component.name):
                    if key[0][1] < 0 or key[0][1] == current_reference_index:
                        if len(key) == 1:
                            technology_updates.update(value.get("technology_updates", {}))
                            component_updates.update(value.get("component_updates", {}))
                            model_updates.update(value.get("model_updates", {}))
                        else:
                            reference_updates[key[1:]] = value

            # Apply required updates
            reset_list = reference.update(
                technology_updates=technology_updates,
                component_updates=component_updates,
                model_updates=model_updates,
                chain_technology_updates=chain_technology_updates,
                classification=classification,
            )

            # Account for reference transformations
            inner_component = ref_component
            flattening_key, requires_phase_correction = _analyze_transform(
                reference, classification, frequencies
            )
            if flattening_key is not None:
                flattening_key = _content_repr(ref_component, *flattening_key, include_config=False)
                inner_component = flattened_component_cache.get(flattening_key)
                if inner_component is None:
                    inner_component = reference.transformed_component(
                        ref_component.name + "-flattened"
                    )
                    flattened_component_cache[flattening_key] = inner_component
            elif requires_phase_correction:
                # S matrix correction factor depends on the mode solver for transformed ports
                port_keys = {}
                for port_name, port in ports.items():
                    # No mode solver runs for 1D ports
                    if isinstance(port, Port) and port.spec.limits[1] != port.spec.limits[0]:
                        runners[(index, port_name, 0)] = _ModeSolverRunner(
                            port,
                            frequencies[:1],
                            self.mesh_refinement,
                            ref_component.technology,
                            cost_estimation=cost_estimation,
                            verbose=verbose,
                        )
                        runners[(index, port_name, 1)] = _ModeSolverRunner(
                            reference[port_name],
                            frequencies[:1],
                            self.mesh_refinement,
                            ref_component.technology,
                            cost_estimation=cost_estimation,
                            verbose=verbose,
                        )
                        port_keys[port_name] = _content_repr(
                            ref_component.technology,
                            port.spec,
                            port.input_direction % 360,
                            port.inverted,
                            reference.rotation % 360,
                            include_config=False,
                        )

                instance_port_data[index] = (instance_port_data[index][0], port_keys)

            s_matrix_kwargs["updates"] = {}
            s_matrix_kwargs["chain_technology_updates"] = chain_technology_updates
            s_matrix_kwargs.update(kwargs)
            s_matrix_kwargs.update(reference_updates.pop("s_matrix_kwargs", {}))
            if reference.s_matrix_kwargs is not None:
                s_matrix_kwargs.update(reference.s_matrix_kwargs)
            s_matrix_kwargs["updates"].update(reference_updates)

            runners[index] = reference.component.select_active_model(classification).start(
                inner_component, frequencies, **s_matrix_kwargs
            )

            # Reset all updates
            for item, kwds in reset_list:
                item.parametric_kwargs = kwds
                item.update()

        if len(runners) == 0:
            warnings.warn(
                f"No subcomponets found in the circuit model for component '{component.name}'.",
                stacklevel=2,
            )

        component_ports = {
            name: port.copy(True) for name, port in component.select_ports(classification).items()
        }
        port_connections = netlist["ports"]
        # In the circuit model, virtual connections behave like real connections
        connections = netlist["connections"] + netlist["virtual connections"]

        return _CircuitModelRunner(
            runners,
            frequencies,
            component.name,
            component_ports,
            port_connections,
            connections,
            instance_port_data,
            cost_estimation,
        )

    # Deprecated: kept for backwards compatibility
    @classmethod
    def from_bytes(cls, byte_repr: bytes) -> "CircuitModel":
        """De-serialize this model."""
        (version, verbose, mesh_refinement) = struct.unpack("<B?d", byte_repr)
        if version != 0:
            raise RuntimeError("Unsuported CircuitModel version.")

        if mesh_refinement <= 0:
            mesh_refinement = None
        return cls(mesh_refinement, verbose)


register_model_class(CircuitModel)
