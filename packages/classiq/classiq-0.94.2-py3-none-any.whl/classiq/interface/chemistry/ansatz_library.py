from pydantic import BaseModel


class HardwareEfficientConstraints(BaseModel):
    num_qubits: int
    num_two_qubit_gates: int | None = None
    num_one_qubit_gates: int | None = None
    max_depth: int | None = None


class HardwareEfficient(BaseModel):
    structure: str
    constraints: HardwareEfficientConstraints
