from datetime import time, date
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel, field_validator

from planqk.quantum.sdk.client.dto_utils import init_with_defined_params
from planqk.quantum.sdk.client.model_enums import Provider, BackendType, HardwareProvider, PlanqkBackendStatus, JobInputFormat


class DocumentationDto(BaseModel):
    description: Optional[str] = None
    url: Optional[str] = None
    # status_url: Optional[str] = None
    location: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class QubitDto(BaseModel):
    id: str

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)


class GateDto(BaseModel):
    name: str
    native_gate: bool

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class ConnectivityDto(BaseModel):
    fully_connected: bool
    graph: Optional[Dict[str, List[str]]] = None

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class ShotsRangeDto(BaseModel):
    min: int
    max: int

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class ConfigurationDto(BaseModel):
    gates: List[GateDto]
    instructions: List[str]
    qubits: Optional[List[QubitDto]] = None
    qubit_count: int
    connectivity: Optional[ConnectivityDto] = None
    supported_input_formats: List[JobInputFormat]
    shots_range: ShotsRangeDto
    memory_result_supported: Optional[bool] = False
    options: Optional[Dict] = None

    @field_validator('supported_input_formats', mode='before')
    def _validate_supported_input_formats(cls, v):
        if v is None:
            return []
        return [JobInputFormat.from_str(format_str) for format_str in v]

    def __post_init__(self):
        self.gates = [GateDto.from_dict(gate) for gate in self.gates]
        self.qubits = [QubitDto.from_dict(qubit) for qubit in self.qubits]
        self.connectivity = ConnectivityDto.from_dict(self.connectivity)
        self.shots_range = ShotsRangeDto.from_dict(self.shots_range)

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class AvailabilityTimesDto(BaseModel):
    granularity: str
    start: time
    end: time

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class CostDto(BaseModel):
    granularity: str
    currency: str
    value: float

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class BackendStateInfosDto(BaseModel):
    status: PlanqkBackendStatus
    queue_avg_time: Optional[int] = None
    queue_size: Optional[int] = None
    provider_token_valid: Optional[bool] = None

    def __post_init__(self):
        self.status = PlanqkBackendStatus(self.status) if self.status else None

    @classmethod
    def from_dict(cls, data: Dict):
        return init_with_defined_params(cls, data)


class BackendDto(BaseModel):
    id: str
    provider: Provider

    @field_validator('provider', mode='before')
    def _validate_provider(cls, v):
        return Provider.from_str(v)

    internal_id: Optional[str] = None
    hardware_provider: Optional[HardwareProvider] = None

    @field_validator('hardware_provider', mode='before')
    def _validate_hardware_provider(cls, v):
        return HardwareProvider.from_str(v)

    name: Optional[str] = None
    documentation: Optional[DocumentationDto] = None
    configuration: Optional[ConfigurationDto] = None
    type: Optional[BackendType] = None
    status: Optional[PlanqkBackendStatus] = None
    availability: Optional[List[AvailabilityTimesDto]] = None
    costs: Optional[List[CostDto]] = None
    updated_at: Optional[date] = None
    avg_queue_time: Optional[int] = None
