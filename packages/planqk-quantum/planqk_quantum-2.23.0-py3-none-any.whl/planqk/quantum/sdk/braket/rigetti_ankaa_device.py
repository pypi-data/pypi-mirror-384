import json

from braket.device_schema.rigetti.rigetti_device_capabilities_v2 import RigettiDeviceCapabilities

from planqk.quantum.sdk.braket.braket_provider import PlanqkBraketProvider
from planqk.quantum.sdk.braket.gate_based_device import PlanqkAwsGateBasedDevice


@PlanqkBraketProvider.register_device("aws.rigetti.ankaa")
class PlanqkAwsRigettiAnkaaDevice(PlanqkAwsGateBasedDevice):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        return "Ankaa-3"

    @property
    def provider_name(self) -> str:
        return "Rigetti"

    @property
    def properties(self) -> RigettiDeviceCapabilities:
        """RigettiDeviceCapabilities: Return the device properties"""
        config = self._get_backend_config()
        return RigettiDeviceCapabilities.parse_raw(json.dumps(config))
