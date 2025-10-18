from datetime import datetime
from typing import Any, Literal, NewType
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

ApplicationId = NewType("ApplicationId", UUID)
ProjectId = NewType("ProjectId", UUID)
ComponentId = NewType("ComponentId", UUID)
JobId = NewType("JobId", UUID)
PortId = NewType("PortId", UUID)
TerminalId = NewType("TerminalId", UUID)

ParametricSchema = dict[str, Any]


class PortCanvasProperties(BaseModel):
    side: Literal["top", "right", "bottom", "left"]
    offset: float = Field(ge=-0.5, le=0.5)


class Port(BaseModel):
    name: str
    baseType: Literal["Port", "FiberPort", "GaussianPort"]
    classificationType: Literal["optical", "electrical"]
    numModes: PositiveInt
    canvasProperties: PortCanvasProperties


class Terminal(BaseModel):
    name: str
    portName: str | None = None
    canvasProperties: PortCanvasProperties


class CanvasProperties(BaseModel):
    position: tuple[float, float] | None = None
    zOrder: float | None = None
    rotation: float | None = None


class ActiveModels(BaseModel):
    electrical: str | None = None
    optical: str | None = None


class Node(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: ComponentId
    componentId: ComponentId
    componentRef: list | None = None
    name: str | None = None
    parameters: ParametricSchema
    modelParameters: dict[str, ParametricSchema]
    activeModel: ActiveModels
    ports: list[Port]
    terminals: list[Terminal]
    thumbnail: str | None = None  # TODO: Where should thumbnails really reside?
    preview: str | None = None
    canvasProperties: CanvasProperties | None = None


class ConnectionPort(BaseModel):
    nodeId: ComponentId
    portName: str


class ExternalPort(BaseModel):
    nodeId: ComponentId
    portName: str
    externalName: str


class ExternalTerminal(BaseModel):
    nodeId: ComponentId
    portName: str | None = None
    terminalName: str
    externalName: str


class Connection(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID
    frm: ConnectionPort = Field(..., alias="from")
    to: ConnectionPort
    properties: dict[str, Any] | None = None


class Netlist(BaseModel):
    nodes: list[Node]
    virtualConnections: list[Connection]
    ports: list[ExternalPort]
    terminals: list[ExternalTerminal]


class SMatrixElement(BaseModel):
    input: str
    output: str
    values: list[tuple[float, float]]


class SMatrix(BaseModel):
    frequencies: list[float]
    wavelengths: list[float]
    elements: list[SMatrixElement]


class JobStatus(BaseModel):
    id: JobId
    projectId: ProjectId
    applicationId: ApplicationId
    createdAt: datetime
    startedAt: datetime | None = None
    completedAt: datetime | None = None
    state: Literal["queued", "running", "succeeded", "failed", "aborted"]
    progress: int = Field(0, ge=0, le=100)
    result: SMatrix | None = None
    error: str | None = None
    reason: str | None = None  # abort reason
    documentHeads: list[str] | None = None
