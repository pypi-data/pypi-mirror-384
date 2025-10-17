from typing import Optional, Dict

from braket.circuits import Circuit, Instruction
from braket.circuits.circuit_helpers import validate_circuit_and_shots
from braket.circuits.compiler_directives import StartVerbatimBox
from braket.circuits.gates import PulseGate
from braket.circuits.serialization import QubitReferenceType, OpenQASMSerializationProperties, IRType
from braket.ir.openqasm import Program as OpenQASMProgram
from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from qiskit.providers import Options
from qiskit_braket_provider.providers.adapter import _GATE_NAME_TO_QISKIT_GATE, to_braket

from planqk.quantum.sdk.client.model_enums import JobInputFormat
from planqk.quantum.sdk.qiskit import PlanqkQiskitBackend
from planqk.quantum.sdk.qiskit.options import OptionsV2
from planqk.quantum.sdk.qiskit.provider import PlanqkQuantumProvider


@PlanqkQuantumProvider.register_backend("aws.ionq.aria")
@PlanqkQuantumProvider.register_backend("aws.ionq.aria-2")
@PlanqkQuantumProvider.register_backend("aws.ionq.forte")
@PlanqkQuantumProvider.register_backend("aws.sim.dm1")
@PlanqkQuantumProvider.register_backend("aws.sim.sv1")
class PlanqkAwsBackend(PlanqkQiskitBackend):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _default_options(cls):
        return OptionsV2()

    @property
    def num_qubits(self) -> int:
        """Return the number of qubits the backend has."""
        # For IQM Garnet backends the qubit size derived from the target is invalid (as they don't use zero-based qubit indices)
        return len(self.backend_info.configuration.qubits)

    def _to_gate(self, name: str) -> Optional[Gate]:
        name = name.lower()
        gate = _GATE_NAME_TO_QISKIT_GATE.get(name, None)
        # Braket quantum backends only support 1 and 2 qubit gates
        return gate if (gate and gate.num_qubits < 3) or self.is_simulator else None

    def _get_single_qubit_gate_properties(self, instr_name: Optional[str] = None) -> dict:
        if self.is_simulator:
            return {None: None}

        qubits = self.backend_info.configuration.qubits
        return {(i,): None for i in range(len(qubits))}

    def _get_multi_qubit_gate_properties(self) -> dict:
        qubits = self.backend_info.configuration.qubits
        connectivity = self.backend_info.configuration.connectivity
        if self.is_simulator:
            return {None: None}
        if connectivity.fully_connected:
            return {(int(qubit1.id), int(qubit2.id)): None for qubit1 in qubits for qubit2 in qubits
                    if qubit1.id != qubit2.id}
        else:
            return {(int(qubit), int(connected_qubit)): None
                    for qubit, connections in connectivity.graph.items()
                    for connected_qubit in connections}

    def _convert_to_job_input(self, job_input: QuantumCircuit, options: Options = None):
        shots = options.get("shots", 1)
        inputs = options.get("inputs", {})
        verbatim = options.get("verbatim", False)

        basis_gates = self.operation_names if not verbatim else None
        braket_circuit = to_braket(job_input, basis_gates, verbatim=verbatim)

        validate_circuit_and_shots(braket_circuit, shots)

        return self._transform_braket_to_qasm_3_program(braket_circuit, False, inputs)

    def _get_job_input_format(self) -> JobInputFormat:
        return JobInputFormat.BRAKET_OPEN_QASM_V3

    def _convert_to_job_params(self, job_input=None, options=None) -> dict:
        return {'disable_qubit_rewiring': False}

    def _transform_braket_to_qasm_3_program(self, braket_circuit: Circuit,
                                            disable_qubit_rewiring: bool,
                                            inputs: Dict[str, float]) -> str:
        """Transforms a Braket input to a QASM 3 program."""

        qubit_reference_type = QubitReferenceType.VIRTUAL

        if (
            disable_qubit_rewiring
            or Instruction(StartVerbatimBox()) in braket_circuit.instructions
            or any(isinstance(instruction.operator, PulseGate) for instruction in braket_circuit.instructions)
        ):
            qubit_reference_type = QubitReferenceType.PHYSICAL

        serialization_properties = OpenQASMSerializationProperties(
            qubit_reference_type=qubit_reference_type
        )

        openqasm_program = braket_circuit.to_ir(
            ir_type=IRType.OPENQASM, serialization_properties=serialization_properties
        )
        if inputs:
            inputs_copy = openqasm_program.inputs.copy() if openqasm_program.inputs is not None else {}
            inputs_copy.update(inputs)
            openqasm_program = OpenQASMProgram(
                source=openqasm_program.source,
                inputs=inputs_copy,
            )

        return openqasm_program.source
