from abc import abstractmethod, ABC
from typing import Optional, Union

from qiskit.circuit import Instruction as QiskitInstruction, Delay, Parameter, Reset
from qiskit.circuit import Measure
from qiskit.providers import BackendV2
from qiskit.providers.models import QasmBackendConfiguration, GateConfig
from qiskit.transpiler import Target

from planqk.quantum.sdk.backend import PlanqkBackend
from planqk.quantum.sdk.client.backend_dtos import ConfigurationDto, BackendDto, ConnectivityDto
from planqk.quantum.sdk.client.job_dtos import JobDto
from planqk.quantum.sdk.client.model_enums import BackendType, PlanqkSdkProvider
from .job import PlanqkQiskitJob
from .options import OptionsV2
from ..client.client import _PlanqkClient


class PlanqkQiskitBackend(PlanqkBackend, BackendV2, ABC):

    def __init__(  # pylint: disable=too-many-arguments
        self,
        planqk_client: _PlanqkClient,
        backend_info: BackendDto,
        backend_version: Optional[str] = None,
        **fields,
    ):
        """PlanqkBackend for executing Qiskit circuits against PLANQK devices.

        Example:
            provider = PlanqkQuantumProvider()
            actual = provider.get_backend("azure.ionq.simulator")
            transpiled_circuit = transpile(circuit, actual=actual)
            actual.run(transpiled_circuit, shots=10).result().get_counts()
            {"100": 10, "001": 10}

        Args:
            planqk_client: PLANQK client for API communication
            backend_info: PLANQK backend infos
            backend_version: Backend version string. Defaults to "2" if not provided.
            **fields: other arguments
        """

        PlanqkBackend.__init__(self, planqk_client=planqk_client, backend_info=backend_info)
        BackendV2.__init__(self,
                           provider=backend_info.provider.name,
                           name=backend_info.id,
                           description=f"PLANQK Backend: {backend_info.hardware_provider.name} {backend_info.id}.",
                           online_date=backend_info.updated_at,
                           backend_version=backend_version or "2",
                           **fields)

        self._normalize_qubit_indices()
        self._initialize_backend_components()
        self._instance = None

    def _initialize_backend_components(self):
        """Template method for initializing target and configuration.
        
        Subclasses can override this method to customize the initialization order.
        Default implementation follows target-first approach for instruction building.
        """
        self._target = self._planqk_backend_to_target()
        self._configuration = self._planqk_backend_dto_to_configuration()

    @abstractmethod
    def _to_gate(self, name: str):
        pass

    @abstractmethod
    def _get_single_qubit_gate_properties(self, instr_name: Optional[str]) -> dict:
        pass

    @abstractmethod
    def _get_multi_qubit_gate_properties(self):
        pass

    non_gate_instr_mapping = {
        "delay": Delay(Parameter("t")),
        "measure": Measure(),
        "reset": Reset(),
    }

    def _normalize_qubit_indices(self):
        # Override to handle non-contiguous zero starting qubit indices
        pass

    @property
    def is_simulator(self):
        return self.backend_info.type == BackendType.SIMULATOR

    def _to_non_gate_instruction(self, name: str) -> Optional[QiskitInstruction]:
        instr = self.non_gate_instr_mapping.get(name, None)
        if instr is not None:
            return instr
        return None

    class PlanqkQiskitTarget(Target):
        def __init__(self, configuration: ConfigurationDto, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._configuration = configuration

        @property
        def physical_qubits(self):
            return sorted(int(qubit.id) for qubit in self._configuration.qubits)

    def _planqk_backend_to_target(self) -> Target:
        """Converts properties of a PLANQK actual into Qiskit Target object.

        Returns:
            target for Qiskit actual
        """

        configuration: ConfigurationDto = self.backend_info.configuration

        self._update_connectivity_with_contiguous_qubit_indices(configuration.connectivity)

        qubit_count: int = self._num_qubits()
        target = self.PlanqkQiskitTarget(configuration=configuration, description=f"Target for PLANQK actual {self.name}", num_qubits=qubit_count)

        single_qubit_props = self._get_single_qubit_gate_properties()
        multi_qubit_props = self._get_multi_qubit_gate_properties()
        gates_names = {gate.name.lower() for gate in configuration.gates}

        for gate_name in gates_names:
            gate = self._to_gate(gate_name)

            if gate is None:
                continue

            if gate.num_qubits == 1:
                target.add_instruction(instruction=gate, properties=single_qubit_props)
            elif gate.num_qubits > 1:
                target.add_instruction(instruction=gate, properties=multi_qubit_props)
            elif gate.num_qubits == 0 and single_qubit_props == {None: None}:
                # For gates without qubit number qargs can not be determined
                target.add_instruction(instruction=gate, properties={None: None})

        measure_props = self._get_single_qubit_gate_properties("measure")
        target.add_instruction(Measure(), measure_props)

        non_gate_instructions = set(configuration.instructions).difference(gates_names).difference({'measure'})
        for non_gate_instruction_name in non_gate_instructions:
            instruction = self._to_non_gate_instruction(non_gate_instruction_name)
            if instruction is not None:
                instr_props = self._get_single_qubit_gate_properties(instruction.name)
                target.add_instruction(instruction, instr_props)

        return target

    def _planqk_backend_dto_to_configuration(self) -> QasmBackendConfiguration:
        basis_gates = [self._get_gate_config_from_target(basis_gate.name)
                       for basis_gate in self.backend_info.configuration.gates if basis_gate.native_gate
                       and self._get_gate_config_from_target(basis_gate.name) is not None]
        gates = [self._get_gate_config_from_target(gate.name)
                 for gate in self.backend_info.configuration.gates if not gate.native_gate
                 and self._get_gate_config_from_target(gate.name) is not None]

        return QasmBackendConfiguration(
            backend_name=self.name,
            backend_version=self.backend_version,
            n_qubits=self._num_qubits(),
            basis_gates=basis_gates,
            gates=gates,
            local=False,
            simulator=self.backend_info.type == BackendType.SIMULATOR,
            conditional=False,
            open_pulse=False,
            memory=self.backend_info.configuration.memory_result_supported,
            max_shots=self.backend_info.configuration.shots_range.max,
            coupling_map=self.coupling_map,
            supported_instructions=self._target.instructions,
            max_experiments=self.backend_info.configuration.shots_range.max,  # Only one circuit is supported per job
            description=self.backend_info.documentation.description,
            min_shots=self.backend_info.configuration.shots_range.min,
            online_date=self.backend_info.updated_at
        )

    @staticmethod
    def _update_connectivity_with_contiguous_qubit_indices(connectivity: ConnectivityDto) -> None:
        """Device qubit indices may be noncontiguous (label between x0 and x7, x being
        the number of the octagon) while the Qiskit transpiler creates and/or
        handles coupling maps with contiguous indices. This function converts the
        noncontiguous connectivity graph from Aspen to a contiguous one.

        Args:
            connectivity_graph (dict): connectivity graph from Aspen. For example
                4 qubit system, the connectivity graph will be:
                    {"0": ["1", "2", "7"], "1": ["0","2","7"], "2": ["0","1","7"],
                    "7": ["0","1","2"]}

        Returns:
            dict: Connectivity graph with contiguous indices. For example for an
            input connectivity graph with noncontiguous indices (qubit 0, 1, 2 and
            then qubit 7) as shown here:
                {"0": ["1", "2", "7"], "1": ["0","2","7"], "2": ["0","1","7"],
                "7": ["0","1","2"]}
            the qubit index 7 will be mapped to qubit index 3 for the qiskit
            transpilation step. Thereby the resultant contiguous qubit indices
            output will be:
                {"0": ["1", "2", "3"], "1": ["0","2","3"], "2": ["0","1","3"],
                "3": ["0","1","2"]}
        """

        if connectivity.fully_connected:
            return None

        connectivity_graph = connectivity.graph

        # Creates list of existing qubit indices which are noncontiguous.
        indices = sorted(
            int(i)
            for i in set.union(*[{k} | set(v) for k, v in connectivity_graph.items()])
        )
        # Creates a list of contiguous indices for number of qubits.
        map_list = list(range(len(indices)))
        # Creates a dictionary to remap the noncontiguous indices to contiguous.
        mapper = dict(zip(indices, map_list))
        # Performs the remapping from the noncontiguous to the contiguous indices.
        contiguous_connectivity_graph = {
            mapper[int(k)]: [mapper[int(v)] for v in val]
            for k, val in connectivity_graph.items()
        }
        connectivity.graph = contiguous_connectivity_graph

    def _num_qubits(self):
        return self.backend_info.configuration.qubit_count

    def _get_gate_config_from_target(self, name) -> GateConfig:
        operations = [operation for operation in self._target.operations
                      if isinstance(operation.name, str)  # Filters out the IBM conditional instructions having no name
                      and operation.name.casefold() == name.casefold()]
        if len(operations) == 1:
            operation = operations[0]
            return GateConfig(
                name=name,
                parameters=operation.params,
                qasm_def='',
            )

    @property
    def target(self):
        return self._target

    @property
    def max_circuits(self):
        return None

    @classmethod
    def _default_options(cls):
        return OptionsV2()

    def _run_job(self, job_request: JobDto) -> Union[PlanqkQiskitJob]:
        from planqk.quantum.sdk.qiskit.job_factory import PlanqkQiskitJobFactory

        job_request.sdk_provider = PlanqkSdkProvider.QISKIT
        return PlanqkQiskitJobFactory.create_job(backend=self, job_details=job_request, planqk_client=self._planqk_client)

    def retrieve_job(self, job_id: str) -> PlanqkQiskitJob:
        """Return a single job.

        Args:
            job_id: id of the job to retrieve.

        Returns:
            The job with the given id.
        """
        from planqk.quantum.sdk.qiskit.job_factory import PlanqkQiskitJobFactory
        return PlanqkQiskitJobFactory.create_job(backend=self, job_id=job_id, planqk_client=self._planqk_client)

    def configuration(self) -> QasmBackendConfiguration:
        """Return the actual configuration.

        Returns:
            QasmBackendConfiguration: the configuration for the actual.
        """
        return self._configuration
