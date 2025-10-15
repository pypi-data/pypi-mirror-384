from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from classiq.interface.chemistry.operator import PauliOperator
from classiq.interface.executor.quantum_code import Arguments
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.helpers.custom_encoders import CUSTOM_ENCODERS


class EstimateInput(BaseModel, json_encoders=CUSTOM_ENCODERS):
    hamiltonian: PauliOperator
    parameters: list[Arguments]


class MinimizeCostInput(BaseModel, json_encoders=CUSTOM_ENCODERS):
    initial_params: Arguments
    max_iteration: int
    quantile: float
    tolerance: float | None


class MinimizeClassicalCostInput(MinimizeCostInput):
    cost_function: Expression
    kind: Literal["MinimizeClassicalCostInput"] = Field(
        default="MinimizeClassicalCostInput"
    )


class MinimizeQuantumCostInput(MinimizeCostInput):
    cost_function: PauliOperator
    kind: Literal["MinimizeQuantumCostInput"] = Field(
        default="MinimizeQuantumCostInput"
    )


ConcreteMinimizeCostInput = Annotated[
    Union[MinimizeQuantumCostInput, MinimizeClassicalCostInput],
    Field(discriminator="kind"),
]


class PrimitivesInput(BaseModel, json_encoders=CUSTOM_ENCODERS):
    sample: list[Arguments] | None = Field(default=None)
    estimate: EstimateInput | None = Field(default=None)
    minimize: ConcreteMinimizeCostInput | None = Field(default=None)
    random_seed: int | None = Field(default=None)
