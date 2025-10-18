from typing import Optional as _Optional

import numpy as _np
import tidy3d as _td

import photonforge as _pf
import photonforge.typing as _pft

_ThermoOpticCoeff = _pft.annotate(float, label="dn/dT", units="1/K")
_LossTemperatureCoeff = _pft.annotate(float, label="dL/dT", units="dB/μm/K")


@_pf.parametric_component
def straight_waveguide(
    *,
    length: _pft.Dimension = 10,
    n_eff: complex = 2.4,
    n_group: _Optional[float] = None,
    reference_frequency: _pft.Frequency = _pf.C_0 / 1.55,
    propagation_loss: _pft.PropagationLoss = 0.0,
    dispersion: _pft.Dispersion = 0.0,
    dispersion_slope: _pft.DispersionSlope = 0.0,
    dn_dT: _ThermoOpticCoeff = 0.0,
    dL_dT: _LossTemperatureCoeff = 0.0,
    temperature: _pft.Temperature = 293.0,
    reference_temperature: _pft.Temperature = 293.0,
):
    model = _pf.AnalyticWaveguideModel(
        n_eff=n_eff,
        length=length,
        propagation_loss=propagation_loss,
        n_group=n_group,
        dispersion=dispersion,
        dispersion_slope=dispersion_slope,
        reference_frequency=reference_frequency,
        dn_dT=dn_dT,
        dL_dT=dL_dT,
        temperature=temperature,
        reference_temperature=reference_temperature,
    )

    comp = model.black_box_component(_pf.virtual_port_spec(), name="WG")
    return comp


@_pf.parametric_component
def bend_waveguide(
    *,
    radius: _pft.Dimension = 10.0,
    angle: _pft.Angle = 90.0,
    n_eff: complex = 2.4,
    reference_frequency: _pft.Frequency = _pf.C_0 / 1.55,
    propagation_loss: _pft.PropagationLoss = 0.0,
    extra_loss: _pft.Loss = 0.0,
    n_group: _Optional[float] = None,
    dispersion: _pft.Dispersion = 0.0,
    dispersion_slope: _pft.DispersionSlope = 0.0,
    dn_dT: _ThermoOpticCoeff = 0.0,
    dL_dT: _LossTemperatureCoeff = 0.0,
    temperature: _pft.Temperature = 293.0,
    reference_temperature: _pft.Temperature = 293.0,
):
    """
    Bend waveguide (two-port, single-mode, lumped phase/ loss).

    Notes
    -----
    • Uses `AnalyticWaveguideModel` with arc length L = |radius| * |angle| (in radians).
    • `propagation_loss` is per-length; `extra_loss` is a lumped dB penalty (e.g., mode mismatch or
    bend loss).
    • Geometry shown is symbolic (90° preview); model uses the exact `angle` you pass.
    """
    # Arc length in the model
    model = _pf.AnalyticWaveguideModel(
        n_eff=n_eff,
        reference_frequency=reference_frequency,
        length=float(abs(angle / 180.0 * _np.pi * radius)),
        propagation_loss=propagation_loss,
        extra_loss=extra_loss,
        n_group=n_group,
        dispersion=dispersion,
        dispersion_slope=dispersion_slope,
        dn_dT=dn_dT,
        dL_dT=dL_dT,
        temperature=temperature,
        reference_temperature=reference_temperature,
    )
    comp = model.black_box_component(_pf.virtual_port_spec())
    comp.name = "WG Bend"
    comp.ports["P1"].center = (abs(radius), abs(radius))
    comp.ports["P1"].input_direction = -90
    comp.properties.__thumbnail__ = "bend"
    return comp


@_pf.parametric_component
def y_splitter(
    *,
    insertion_loss: _pft.Loss = 0.01,  # dB, total non-returned power (scattering/absorption)
    return_loss0: _pft.Loss = 40.0,  # dB, reflection seen from input port p0
    return_loss1: _pft.Loss = 40.0,  # dB, reflection seen from either output port (p1/p2)
    isolation: _pft.Fraction = 0.0,  # amplitude leakage between the two output arms
):
    """
    Lumped 3-port optical Y-splitter using an analytic model (no geometry, no phase/dispersion).

    Model: photonforge.PowerSplitterModel(t, i, r0, r1, ports=None)

    Ports:
      • p0 (input) at (-0.5, 0), facing → (0°), spec: 1 optical mode
      • p1 (output-top) at (0.5, +0.5), facing ← (180°), spec: 1 optical mode
      • p2 (output-bottom) at (0.5, −0.5), facing ← (180°), spec: 1 optical mode

    Parameters:
      insertion_loss : Loss (dB)
          Total non-returned power. Transmission amplitude scale a = 10^(−IL/20).
      return_loss0 : Loss (dB)
          Reflection magnitude seen from input port p0: |r0| = 10^(−RL0/20).
      return_loss1 : Loss (dB)
          Reflection magnitude seen from either output port p1/p2: |r1| = 10^(−RL1/20).
      isolation : Fraction
          Output-to-output leakage amplitude (|i|). Default 0.

    Coefficient mapping (single-mode, symmetric):
      t  = a / sqrt(2)
      i  = isolation
      r0 = 10^(−return_loss0/20)
      r1 = 10^(−return_loss1/20)

    Power sanity checks (warnings if exceeded by > 1e−9):
      • Excite p0:  2|t|² + |r0|² ≤ 1
      • Excite p1:  |t|² + |i|² + |r1|² ≤ 1
      • Excite p2:  |t|² + |i|² + |r1|² ≤ 1
    """
    # Map dB → amplitudes
    a = 10.0 ** (-insertion_loss / 20.0)
    r0 = 10.0 ** (-return_loss0 / 20.0)
    r1 = 10.0 ** (-return_loss1 / 20.0)
    i = float(isolation)

    # Symmetric per-branch transmission amplitude
    t = a / _np.sqrt(2.0)

    # # Power checks (warn if > 1)
    # total_p_p0 = 2.0 * (abs(t) ** 2) + (abs(r0) ** 2)
    # if total_p_p0 > 1.0 + 1e-9:
    #     _warn(f"Y_Splitter power imbalance (p0): total={total_p_p0:.6f} > 1.0", stacklevel=2)

    # total_p_p1 = (abs(t) ** 2) + (abs(i) ** 2) + (abs(r1) ** 2)
    # if total_p_p1 > 1.0 + 1e-9:
    #     _warn(f"Y_Splitter power imbalance (p1): total={total_p_p1:.6f} > 1.0", stacklevel=2)

    # Attach analytic model
    model = _pf.PowerSplitterModel(t=t, i=i, r0=r0, r1=r1, ports=None)

    comp = model.black_box_component(_pf.virtual_port_spec(), name="Y Splitter")
    return comp


@_pf.parametric_component
def taper(
    *,
    insertion_loss: _pft.Loss = 0.01,  # dB, includes all non-returned power
    return_loss0: _pft.Loss = 40.0,  # dB, reflection seen from port 0
    return_loss1: _pft.Loss = 40.0,  # dB, reflection seen from port 1
):
    """
    Taper (two-port, single-mode, lumped).

    Parameters
    ----------
    insertion_loss : _pft.Loss
        Total one-pass insertion loss in dB.
    return_loss0 : _pft.Loss
        Return loss in dB as seen from port 0 (→ |r0| = 10^(−RL0/20)).
    return_loss1 : _pft.Loss
        Return loss in dB as seen from port 1 (→ |r1| = 10^(−RL1/20)).

    Amplitude Mapping
    -----------------
        |t|  = 10^(−insertion_loss/20)
        |r0| = 10^(−return_loss0/20)
        |r1| = 10^(−return_loss1/20)

    Notes
    -----
    • This is a constant-phase, lumped model (no additional phase/dispersion).
    • Power checks (single mode):
        excite port 0: |t|² + |r0|² ≤ 1
        excite port 1: |t|² + |r1|² ≤ 1
      A warning is issued if either exceeds 1 (tolerance = 1e−9).
    """
    # Amplitudes (constant phase assumed)
    t = 10 ** (-insertion_loss / 20.0)
    r0 = 10 ** (-return_loss0 / 20.0)
    r1 = 10 ** (-return_loss1 / 20.0)

    # # Power sanity (single-mode)
    # if (t**2 + r0**2) > 1.0 + 1e-9 or (t**2 + r1**2) > 1.0 + 1e-9:
    #     _warn(
    #         f"Taper power imbalance: "
    #         f"(|t|^2+|r0|^2={(t**2 + r0**2):.6f}, |t|^2+|r1|^2={(t**2 + r1**2):.6f}) exceeds 1. "
    #         "Check insertion_loss vs return losses.",
    #         stacklevel=2,
    #     )

    model = _pf.TwoPortModel(t=t, r0=r0, r1=r1)
    comp = model.black_box_component(_pf.virtual_port_spec(), name="WG Taper")
    comp.properties.__thumbnail__ = "taper"
    return comp


@_pf.parametric_component
def waveguide_transition(
    *,
    insertion_loss: _pft.Loss = 0.01,  # dB, includes all non-returned power
    return_loss0: _pft.Loss = 40.0,  # dB, reflection seen from port 0
    return_loss1: _pft.Loss = 40.0,  # dB, reflection seen from port 1
):
    """
    Waveguide transition (two-port, single-mode, lumped).

    Mapping:
        |t| = 10^(−insertion_loss/20)
        |r0| = 10^(−return_loss0/20)
        |r1| = 10^(−return_loss1/20)

    Notes:
        • Power checks: |t|² + |r0|² ≤ 1 (excite port 0), |t|² + |r1|² ≤ 1 (excite port 1).
          A warning is issued if either exceeds unity (tolerance = 1e−9).
    """
    # Amplitudes (constant phase assumed)
    t = 10 ** (-insertion_loss / 20.0)
    r0 = 10 ** (-return_loss0 / 20.0)
    r1 = 10 ** (-return_loss1 / 20.0)

    # # Power sanity (single-mode)
    # if (t**2 + r0**2) > 1.0 + 1e-9 or (t**2 + r1**2) > 1.0 + 1e-9:
    #     _warn(
    #         f"WaveguideTransition power imbalance: "
    #         f"(|t|^2+|r0|^2={(t**2 + r0**2):.6f}, |t|^2+|r1|^2={(t**2 + r1**2):.6f}) exceeds 1. "
    #         "Check insertion_loss vs return losses.",
    #         stacklevel=2,
    #     )

    model = _pf.TwoPortModel(t=t, r0=r0, r1=r1)
    comp = model.black_box_component(_pf.virtual_port_spec(), name="WG Transition")
    comp.properties.__thumbnail__ = "transition"
    return comp


@_pf.parametric_component
def grating_coupler(
    *,
    insertion_loss: _pft.Loss = 1.5,  # dB, total non-returned power
    return_loss_fiber: _pft.Loss = 40.0,  # dB, reflection seen from fiber side (port 0)
    return_loss_wg: _pft.Loss = 35.0,  # dB, reflection seen from waveguide side (port 1)
):
    """
    Grating Coupler (two-port, single-mode, lumped).

    Mapping:
        |t|  = 10^(−insertion_loss / 20)
        |r0| = 10^(−return_loss_fiber / 20)
        |r1| = 10^(−return_loss_wg    / 20)

    Assumptions:
        • Linear, passive, no phase/dispersion.
        • All non-returned power is radiated (loss).
        • Asymmetric reflections allowed.

    Power checks:
        |t|² + |r0|² ≤ 1   (excite fiber side)
        |t|² + |r1|² ≤ 1   (excite waveguide side)
    """
    # Amplitudes (constant phase assumed)
    t = 10 ** (-insertion_loss / 20.0)
    r0 = 10 ** (-return_loss_fiber / 20.0)
    r1 = 10 ** (-return_loss_wg / 20.0)

    # # Power sanity
    # if (t**2 + r0**2) > 1.0 + 1e-9 or (t**2 + r1**2) > 1.0 + 1e-9:
    #     _warn(
    #         f"GratingCoupler power imbalance: "
    #         f"(|t|^2+|r0|^2={(t**2 + r0**2):.6f}, |t|^2+|r1|^2={(t**2 + r1**2):.6f}) exceeds 1.",
    #         stacklevel=2,
    #     )

    model = _pf.TwoPortModel(t=t, r0=r0, r1=r1)
    comp = model.black_box_component(_pf.virtual_port_spec(), name="Grating Coupler")
    comp.properties.__thumbnail__ = "grating_coupler"
    return comp


@_pf.parametric_component
def edge_coupler(
    *,
    insertion_loss: _pft.Loss = 0.5,  # dB total non-returned power (fiber<->chip)
    return_loss_fiber: _pft.Loss = 40.0,  # dB reflection seen from fiber side (port 0)
    return_loss_wg: _pft.Loss = 40.0,  # dB reflection seen from chip side (port 1)
):
    """
    Edge Coupler (two-port, single-mode, lumped).

    This models a generic edge coupler as a scalar two-port:
        |t|  = 10^(−insertion_loss / 20)
        |r0| = 10^(−return_loss_fiber / 20)
        |r1| = 10^(−return_loss_wg / 20)

    Assumptions:
        • No phase/dispersion; constant amplitudes over the band of interest.
        • insertion_loss already includes scattering and other non-returned power.
        • Asymmetric reflections allowed (fiber vs chip side).

    Power checks (single-mode):
        |t|² + |r0|² ≤ 1   (excite fiber side, port 0)
        |t|² + |r1|² ≤ 1   (excite chip side,  port 1)

    Use when:
        • You only need IL and RL, not polarization/bandwidth/alignment effects.
    """
    # Amplitudes (constant phase assumed)
    t = 10 ** (-insertion_loss / 20.0)
    r0 = 10 ** (-return_loss_fiber / 20.0)
    r1 = 10 ** (-return_loss_wg / 20.0)

    # # Power sanity
    # if (t**2 + r0**2) > 1.0 + 1e-9 or (t**2 + r1**2) > 1.0 + 1e-9:
    #     _warn(
    #         f"EdgeCoupler power imbalance: "
    #         f"(|t|^2+|r0|^2={(t**2 + r0**2):.6f}, |t|^2+|r1|^2={(t**2 + r1**2):.6f}) exceeds 1. "
    #         "Check insertion_loss vs return losses.",
    #         stacklevel=2,
    #     )

    model = _pf.TwoPortModel(t=t, r0=r0, r1=r1, ports=None)
    comp = model.black_box_component(_pf.virtual_port_spec(), name="Edge Coupler")
    comp.properties.__thumbnail__ = "edge_coupler"
    return comp


@_pf.parametric_component
def directional_coupler(
    *,
    coupling_ratio: _pft.Fraction = 0.5,
    propagation_length: _pft.Dimension = 0.0,
    cross_phase: _pft.Angle = -90.0,
    insertion_loss: _pft.Loss = 0.0,
    isolation: complex = 0.0,
    reflection: complex = 0.0,
    n_eff: complex = 2.4,
    n_group: _Optional[float] = None,
    reference_frequency: _pft.Frequency = _pf.C_0 / 1.55,
):
    """
    Directional coupler (single-mode).

    Implements an analytic 4-port directional coupler with insertion loss,
    coupling ratio, cross-port phase, isolation, and reflection.

    Power budgeting:
        a = 10^(-IL/20)
        t = a * sqrt(1 - coupling_ratio)
        c = a * sqrt(coupling_ratio) * exp(j * cross_phase)

    so that |t|^2 + |c|^2 = 10^(-IL/10).
    Note: The provided insertion_loss should already include contributions
    from reflection and isolation; these are not subtracted again.

    Parameters
    ----------
    coupling_ratio : Fraction
        Fraction of input power coupled to cross port [0–1].
    propagation_length : Dimension, optional
        Extra physical length contributing to phase delay (μm).
    cross_phase : Angle
        Relative phase on cross port (°).
    insertion_loss : Loss
        Total excess loss in dB, including reflection/isolation.
    isolation : complex
        Complex leakage amplitude to isolated port.
    reflection : complex
        Complex reflection amplitude back into inputs.
    n_eff : complex
        Effective index used for phase accumulation.
    n_group : float, optional
        Group index for dispersion modeling.
    reference_frequency : Frequency
        Reference frequency (Hz).
    """
    a = 10 ** (-insertion_loss / 20)
    t = a * _np.sqrt(1 - coupling_ratio)
    c = a * _np.sqrt(coupling_ratio) * _np.exp(1j * (cross_phase / 180 * _np.pi))

    # p_total = (
    #     _np.abs(t) ** 2 + _np.abs(c) ** 2 + _np.abs(isolation) ** 2 + _np.abs(reflection) ** 2
    # )
    # if p_total > 1.0 + 1e-9:
    #     _warn(
    #         f"DirectionalCoupler power imbalance: total={p_total:.3f} exceeds 1.0. "
    #         "Check insertion_loss vs isolation/reflection settings.",
    #         stacklevel=2,
    #     )

    model = _pf.DirectionalCouplerModel(
        t=t,
        c=c,
        i=isolation,
        r=reflection,
        propagation_length=propagation_length,
        n_eff=n_eff,
        n_group=n_group,
        reference_frequency=reference_frequency,
    )
    comp = model.black_box_component(_pf.virtual_port_spec(), name="Directional Coupler")
    return comp


@_pf.parametric_component
def waveguide_crossing(
    *,
    t: complex = 1.0,
    x: complex = 0.0,
    r: complex = 0.0,
    propagation_length: _pft.Dimension = 0.0,
    n_eff: complex = 2.4,
    n_group: _Optional[float] = None,
    reference_frequency: _pft.Frequency = _pf.C_0 / 1.55,
):
    """
    Waveguide crossing (single-mode, 4-port).

    Ports
    -----
    p1: left  (→, 0°), p2: bottom (↑, 90°), p3: right (←, 180°), p4: top (↓, −90°).

    Model
    -----
    t, x, r are complex amplitudes for straight-through, cross, and reflection.
    If these include insertion loss, energy obeys |t|² + 2|x|² + |r|² ≤ 1.
    Global phase is accumulated via `propagation_length` with `n_eff` at `reference_frequency`
    (when provided). `n_group` enables group-delay effects.

    Parameters
    ----------
    t, x, r : complex
        Amplitudes (including any excess loss); phases carried in the complex angle.
    propagation_length : Dimension
        Extra optical length (μm) used for phase accumulation.
    n_eff : complex
        Effective index for phase. Complex part may encode attenuation.
    n_group : float, optional
        Group index for first-order dispersion/time-delay.
    reference_frequency : Frequency, optional
        Reference frequency (Hz). If None, the model treats phase as length-independent.

    Notes
    -----
    A warning is issued if total power |t|² + 2|x|² + |r|² exceeds 1 (numerical tol).
    """

    # # compute per-mode total power and warn if any mode exceeds 1
    # p_total = _np.abs(t) ** 2 + 2 * _np.abs(x) ** 2 + _np.abs(r) ** 2
    # if _np.any(p_total > 1.0 + 1e-9):
    #     _warn(
    #         f"Crossing power imbalance: total = {p_total}. "
    #         "Power exceeds unity (|t|² + 2|x|² + |r|² > 1).",
    #         stacklevel=2,
    #     )

    model = _pf.CrossingModel(
        t=t,
        x=x,
        r=r,
        propagation_length=propagation_length,
        n_eff=n_eff,
        n_group=n_group,
        reference_frequency=reference_frequency,
    )
    comp = model.black_box_component(_pf.virtual_port_spec(), name="WG Crossing")
    return comp


@_pf.parametric_component
def electrical_termination(
    *,
    return_loss: _pft.Loss = 60.0,
):
    """
    Electrical one-port termination specified by Return Loss (RL, in dB).

    Notes
    -----
    - Return loss (dB) is related to the (magnitude of the) reflection coefficient |r| via:
          |r| = 10^(-RL / 20)
      We assume a constant (irrelevant) phase and only set the magnitude.
    - Larger RL implies a better match (smaller reflection). For example:
          RL = 20 dB  -> |r| ≈ 0.10
          RL = 40 dB  -> |r| ≈ 0.01
          RL = 60 dB  -> |r| ≈ 0.001

    Parameters
    ----------
    return_loss : _pft.Loss
        Desired return loss at the reference condition (in dB). Must be ≥ 0.
        Default 60 dB corresponds to |r| ≈ 1e-3.

    Models
    ------
    TerminationModel(r)
        Underlying analytic termination model using reflection magnitude r = 10^(-RL/20).
    """
    # RL (dB) -> reflection magnitude
    r_mag = 10.0 ** (-return_loss / 20.0)
    r_mag = float(_np.clip(r_mag, 0.0, 1.0))  # safety clamp

    # attach the model
    model = _pf.TerminationModel(r=r_mag)
    comp = model.black_box_component(
        _pf.virtual_port_spec(classification="electrical"), name="Electrical Termination"
    )
    comp.properties.__thumbnail__ = "electrical_termination"
    return comp


@_pf.parametric_component
def optical_termination(
    *,
    return_loss: _pft.Loss = 60.0,
):
    """
    optical one-port termination specified by Return Loss (RL, in dB).

    Notes
    -----
    - Return loss (dB) is related to the (magnitude of the) reflection coefficient |r| via:
          |r| = 10^(-RL / 20)
      We assume a constant (irrelevant) phase and only set the magnitude.
    - Larger RL implies a better match (smaller reflection). For example:
          RL = 20 dB  -> |r| ≈ 0.10
          RL = 40 dB  -> |r| ≈ 0.01
          RL = 60 dB  -> |r| ≈ 0.001

    Parameters
    ----------
    return_loss : _pft.Loss
        Desired return loss at the reference condition (in dB). Must be ≥ 0.
        Default 60 dB corresponds to |r| ≈ 1e-3.

    Models
    ------
    TerminationModel(r)
        Underlying analytic termination model using reflection magnitude r = 10^(-RL/20).
    """
    # RL (dB) -> reflection magnitude
    r_mag = 10.0 ** (-return_loss / 20.0)
    r_mag = float(_np.clip(r_mag, 0.0, 1.0))  # safety clamp

    model = _pf.TerminationModel(r=r_mag)
    comp = model.black_box_component(_pf.virtual_port_spec(), name="WG Termination")
    return comp


@_pf.parametric_component
def polarization_splitter_rotator(
    *,
    t_0: complex = 1.0 + 0.0j,  # P0@0 → P1@(0 or pol_out)
    t_1: complex = 1.0 + 0.0j,  # P0@1 → P2@(0 or pol_out)
    x_0_to_p2: complex = 0.0 + 0.0j,  # P0@0 → P2@(0 or pol_out) (crosstalk)
    x_1_to_p1: complex = 0.0 + 0.0j,  # P0@1 → P1@(0 or pol_out) (crosstalk)
    leak_p1_p2: complex = 0.0 + 0.0j,  # P1@(0 or pol_out) ↔ P2@(0 or pol_out) leakage
    r_00: complex = 0.0 + 0.0j,  # reflection @ P0 mode 0
    r_01: complex = 0.0 + 0.0j,  # reflection @ P0 mode 1
    r_10: complex = 0.0 + 0.0j,  # reflection @ P1 mode 0
    r_11: complex = 0.0 + 0.0j,  # reflection @ P1 mode 1  (unused in Layout A)
    r_20: complex = 0.0 + 0.0j,  # reflection @ P2 mode 0
    r_21: complex = 0.0 + 0.0j,  # reflection @ P2 mode 1  (unused in Layout A)
    all_multimode: bool = False,  # False → Layout A (4×4). True → Layout B (6×6).
    pol_out: int = 0,  # Only used when all_multimode=True; selects {0,1}
):
    """
    Polarization Splitter Rotator (frequency-independent).

    This component wraps `PolarizationSplitterRotatorModel` with constant (frequency-independent)
    complex S-parameters.

    Parameters
    ----------
    t_0 : complex
        Functional transmission for P0@0 → P1@0 (Layout A) or P0@0 → P1@pol_out (Layout B).
    t_1 : complex
        Functional transmission for P0@1 → P2@0 (Layout A) or P0@1 → P2@pol_out (Layout B).
    x_0_to_p2 : complex
        Crosstalk from P0@0 → P2@0 (Layout A) or P0@0 → P2@pol_out (Layout B).
    x_1_to_p1 : complex
        Crosstalk from P0@1 → P1@0 (Layout A) or P0@1 → P1@pol_out (Layout B).
    leak_p1_p2 : complex
        Leakage between outputs at the functional mode:
        P1@0 ↔ P2@0 (Layout A) or P1@pol_out ↔ P2@pol_out (Layout B).
    r_00, r_01, r_10, r_11, r_20, r_21 : complex
        Per-channel reflections. Layout A uses r_00, r_01, r_10, r_20; r_11 and r_21 are ignored.
    all_multimode : bool
        If False, P0 is 2-mode and P1/P2 are single-mode (4×4 reduced matrix).
        If True, all ports are 2-mode (6×6 full matrix).
    pol_out : {0,1}
        Only for all_multimode=True. Selects which output mode at P1/P2 carries t_0, t_1,
        crosstalk terms, and leakage.

    Notes
    -----
    • All S-parameters set here are constants (no frequency dependence).
    • Unspecified S-parameters are set to 0.
    """
    if not all_multimode:
        # === Layout A: 4-port effective topology ===
        specs = (_pf.virtual_port_spec(2), _pf.virtual_port_spec())
        model = _pf.PolarizationSplitterRotatorModel(
            # Input reflections (P0@m0,m1); no inter-mode reflection parameterized
            s00=r_00,
            s01=0.0 + 0.0j,
            s11=r_01,
            # Functional & crosstalk paths to P1@m0
            s02=t_0,  # P0@0 → P1@0
            s12=x_1_to_p1,  # P0@1 → P1@0 (crosstalk)
            # Functional & crosstalk paths to P2@m0
            s04=x_0_to_p2,  # P0@0 → P2@0 (crosstalk)
            s14=t_1,  # P0@1 → P2@0
            # Output reflections (kept mode 0 at outputs)
            s22=r_10,  # P1@0 reflection
            s44=r_20,  # P2@0 reflection
            # Output↔output leakage (kept mode)
            s24=leak_p1_p2,
            # Zero everything else explicitly touched by signature
            s23=0.0 + 0.0j,
            s25=0.0 + 0.0j,
            s33=0.0 + 0.0j,
            s34=0.0 + 0.0j,
            s35=0.0 + 0.0j,
            s45=0.0 + 0.0j,
            s55=0.0 + 0.0j,
            # Reduce to 4-port view on output mode 0
            output_mode=0,
            ports=None,
        )

    else:
        # === Layout B: 6-port full topology ===
        specs = (_pf.virtual_port_spec(2), _pf.virtual_port_spec(2))

        pol = int(pol_out)
        if pol not in (0, 1):
            raise ValueError("pol_out must be 0 or 1 when all_multimode=True.")

        kwargs = {
            # Input reflections (P0)
            "s00": r_00,
            "s01": 0.0 + 0.0j,
            "s11": r_01,
            # Output reflections (P1 m0/m1, P2 m0/m1)
            "s22": r_10,
            "s33": r_11,
            "s44": r_20,
            "s55": r_21,
            # Initialize all possibly used couplings to 0
            "s02": 0.0 + 0.0j,
            "s03": 0.0 + 0.0j,  # P0@0 → P1@m0/m1
            "s04": 0.0 + 0.0j,
            "s05": 0.0 + 0.0j,  # P0@0 → P2@m0/m1
            "s12": 0.0 + 0.0j,
            "s13": 0.0 + 0.0j,  # P0@1 → P1@m0/m1
            "s14": 0.0 + 0.0j,
            "s15": 0.0 + 0.0j,  # P0@1 → P2@m0/m1
            "s24": 0.0 + 0.0j,
            "s35": 0.0 + 0.0j,  # leakage (mode-diagonal)
            "s23": 0.0 + 0.0j,
            "s25": 0.0 + 0.0j,
            "s34": 0.0 + 0.0j,
            "s45": 0.0 + 0.0j,
        }

        if pol == 0:
            kwargs.update(
                s02=t_0,  # P0@0 → P1@0
                s14=t_1,  # P0@1 → P2@0
                s04=x_0_to_p2,  # P0@0 → P2@0
                s12=x_1_to_p1,  # P0@1 → P1@0
                s24=leak_p1_p2,  # P1@0 ↔ P2@0
            )
        else:  # pol == 1
            kwargs.update(
                s03=t_0,  # P0@0 → P1@1
                s15=t_1,  # P0@1 → P2@1
                s05=x_0_to_p2,  # P0@0 → P2@1
                s13=x_1_to_p1,  # P0@1 → P1@1
                s35=leak_p1_p2,  # P1@1 ↔ P2@1
            )

        model = _pf.PolarizationSplitterRotatorModel(
            **kwargs,
            output_mode=pol,
            ports=None,
        )

    comp = model.black_box_component(*specs, name="PSR")
    return comp


@_pf.parametric_component
def polarization_beam_splitter(
    *,
    t_0: complex = 1.0 + 0.0j,  # mode 0: P0 ↔ preferred output
    x_0: complex = 0.0 + 0.0j,  # mode 0: P0 ↔ other output (crosstalk)
    t_1: complex = 1.0 + 0.0j,  # mode 1: P0 ↔ preferred output
    x_1: complex = 0.0 + 0.0j,  # mode 1: P0 ↔ other output (crosstalk)
    r_00: complex = 0.0 + 0.0j,  # reflections at P0 (mode 0)
    r_10: complex = 0.0 + 0.0j,  # reflections at P1 (mode 0)
    r_20: complex = 0.0 + 0.0j,  # reflections at P2 (mode 0)
    r_01: complex = 0.0 + 0.0j,  # reflections at P0 (mode 1)
    r_11: complex = 0.0 + 0.0j,  # reflections at P1 (mode 1)
    r_21: complex = 0.0 + 0.0j,  # reflections at P2 (mode 1)
    mode_routing: dict[int, int] = {0: 1, 1: 2},  # mode → preferred output port in {1,2}
):
    """
    Polarization Beam Splitter (PBS), three ports, two modes, no mode mixing.

    Ports
    -----
    • P0: common input (supports 2 modes)
    • P1: output 1 (supports 2 modes)
    • P2: output 2 (supports 2 modes)

    Parameters
    ----------
    t_0, x_0 : complex
        Mode-0 transmission amplitudes from P0 to the preferred and other output, respectively.
    t_1, x_1 : complex
        Mode-1 transmission amplitudes from P0 to the preferred and other output, respectively.
    r_00, r_10, r_20 : complex
        Reflection amplitudes at P0, P1, P2 for mode 0.
    r_01, r_11, r_21 : complex
        Reflection amplitudes at P0, P1, P2 for mode 1.
    mode_routing : dict[int, int]
        Maps mode index → preferred output port index in {1,2}. Default {0:1, 1:2}.
        The “other” port is the remaining one in {1,2}.

    Notes
    -----
    • No polarization (mode) conversion: mixed-mode S-entries are zero.
    • Leakage between outputs (P1↔P2) is set to zero by default (i = 0 for both modes).
    • For each mode m, the pair (t_m, x_m) is assigned to (t1[m], t2[m]) according to
      `mode_routing`. If mode m prefers P1, then t1[m]=t_m and t2[m]=x_m; if it prefers P2, then
      t1[m]=x_m and t2[m]=t_m.
    """
    # Build per-mode transmission arrays to P1 (t1) and P2 (t2) based on routing
    tm = [t_0, t_1]
    xm = [x_0, x_1]
    t1 = [0.0 + 0.0j, 0.0 + 0.0j]
    t2 = [0.0 + 0.0j, 0.0 + 0.0j]
    for m in (0, 1):
        pref = mode_routing.get(m, 1)  # default to port 1 if missing
        if pref == 1:
            t1[m] = tm[m]
            t2[m] = xm[m]
        else:  # pref == 2
            t1[m] = xm[m]
            t2[m] = tm[m]

    # Reflections per port, per mode
    r0 = [r_00, r_01]
    r1 = [r_10, r_11]
    r2 = [r_20, r_21]

    # No explicit output-to-output leakage term provided; set i=0 per mode
    i_leak = [0.0 + 0.0j, 0.0 + 0.0j]

    # Attach analytic model (assumed available in the notebook)
    model = _pf.PolarizationBeamSplitterModel(
        t1=t1,
        t2=t2,
        i=i_leak,
        r0=r0,
        r1=r1,
        r2=r2,
    )
    comp = model.black_box_component(_pf.virtual_port_spec(2), name="PBS")
    comp.properties.__thumbnail__ = "psr"
    return comp


@_pf.parametric_component
def polarization_splitter_grating_coupler(
    *,
    t_0: complex = 1.0 + 0.0j,  # mode 0: P0 ↔ preferred output (waveguide)
    x_0: complex = 0.0 + 0.0j,  # mode 0: P0 ↔ other output (crosstalk)
    t_1: complex = 1.0 + 0.0j,  # mode 1: P0 ↔ preferred output (waveguide)
    x_1: complex = 0.0 + 0.0j,  # mode 1: P0 ↔ other output (crosstalk)
    r_00: complex = 0.0 + 0.0j,  # reflections at P0 (mode 0)
    r_10: complex = 0.0 + 0.0j,  # reflections at P1 (mode 0)
    r_20: complex = 0.0 + 0.0j,  # reflections at P2 (mode 0)
    r_01: complex = 0.0 + 0.0j,  # reflections at P0 (mode 1)
    r_11: complex = 0.0 + 0.0j,  # reflections at P1 (mode 1)
    r_21: complex = 0.0 + 0.0j,  # reflections at P2 (mode 1)
    mode_routing: dict[int, int] = {0: 1, 1: 2},  # mode → preferred output port in {1,2}
):
    """
    Polarization Splitter Grating Coupler (PSGC), three ports, two modes, no mode mixing.

    Concept
    -------
    • P0 represents the *fiber/coupler* side that supports two orthogonal modes (e.g., TE/TM in
      fiber basis).
    • P1 and P2 are on-chip single-direction waveguides (each supports two modes, but no mode mixing
      is modeled).
    • Different physics than a PBS device, but *identical S-matrix mapping*: each mode at P0 routes
      primarily to one of {P1, P2} with (t_m) while leaking to the other output with (x_m);
      reflections r_km per port/mode.

    Parameters
    ----------
    t_0, x_0 : complex
        Mode-0 complex amplitudes. `t_0` goes to the preferred output, `x_0` to the other output.
    t_1, x_1 : complex
        Mode-1 complex amplitudes. `t_1` goes to the preferred output, `x_1` to the other output.
    r_00, r_10, r_20 : complex
        Reflection amplitudes at ports P0, P1, P2 for mode 0.
    r_01, r_11, r_21 : complex
        Reflection amplitudes at ports P0, P1, P2 for mode 1.
    mode_routing : dict[int, int]
        Maps mode index → preferred output port index in {1,2}. Default {0:1, 1:2}.
        The “other” port is the remaining one.

    Notes
    -----
    • No polarization (mode) conversion: mixed-mode entries are zero.
    • Output-to-output direct leakage term is set to zero (i_m = 0) unless you extend it later.
    """
    # Route per-mode (t,x) to (t1,t2) based on preferred output
    tm = [t_0, t_1]
    xm = [x_0, x_1]
    t1 = [0.0 + 0.0j, 0.0 + 0.0j]
    t2 = [0.0 + 0.0j, 0.0 + 0.0j]
    for m in (0, 1):
        pref = mode_routing.get(m, 1)
        if pref == 1:
            t1[m] = tm[m]
            t2[m] = xm[m]
        else:
            t1[m] = xm[m]
            t2[m] = tm[m]

    # Reflections per port and mode
    r0 = [r_00, r_01]
    r1 = [r_10, r_11]
    r2 = [r_20, r_21]

    # No explicit output-to-output coupling (isolation term) by default
    i_leak = [0.0 + 0.0j, 0.0 + 0.0j]

    # Attach the analytic S-matrix model (assumed available)
    model = _pf.PolarizationBeamSplitterModel(
        t1=t1,
        t2=t2,
        i=i_leak,
        r0=r0,
        r1=r1,
        r2=r2,
    )
    comp = model.black_box_component(_pf.virtual_port_spec(2), name="PSGC")
    comp.properties.__thumbnail__ = "psgc"
    return comp


if __name__ == "__main__":
    d = dict(locals())

    import json
    import pathlib

    from photonforge._backend.component import component_to_node

    path = pathlib.Path(__file__).parent / "../../example_schemas/default_library"
    path.mkdir(exist_ok=True, parents=True)
    for file in path.glob("*.json"):
        file.unlink()

    _pf.config.default_technology = _pf.Technology("Empty", "0", {}, [], {}, _td.Medium())
    for name, fn in d.items():
        if name.startswith("_"):
            continue
        print(f"Exporting netlist from '{name}'…", flush=True)
        component = fn()
        node = component_to_node(component)
        json_data = node.model_dump(mode="json")
        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
        (path / f"{name}.json").write_text(json_str)
