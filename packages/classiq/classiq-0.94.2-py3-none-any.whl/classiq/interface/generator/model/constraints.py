import warnings
from collections import defaultdict
from typing import TypeVar, Union

import pydantic
from pydantic import BaseModel, ConfigDict

from classiq.interface.enum_utils import StrEnum
from classiq.interface.exceptions import ClassiqDeprecationWarning, ClassiqValueError
from classiq.interface.generator.transpiler_basis_gates import TranspilerBasisGates

UNCONSTRAINED = -1


class OptimizationParameter(StrEnum):
    WIDTH = "width"
    DEPTH = "depth"
    NO_OPTIMIZATION = "no_opt"


OptimizationParameterType = Union[OptimizationParameter, TranspilerBasisGates]

T = TypeVar("T")


def optimization_parameter_type_from_string(param: str) -> OptimizationParameterType:
    for enum_ in (OptimizationParameter, TranspilerBasisGates):
        try:
            return enum_(param)  # type: ignore[return-value]
        except ValueError:
            pass
    raise ClassiqValueError(f"Invalid OptimizationParameterType {param}")


class Constraints(BaseModel):
    """
    Constraints for the quantum circuit synthesis engine.

    This class is used to specify constraints such as maximum width, depth,
    gate count, and optimization parameters for the synthesis engine,
    guiding the generation of quantum circuits that satisfy these constraints.

    Attributes:
        max_width (int):
            Maximum number of qubits allowed in the generated quantum circuit.
            Defaults to `None`.
        max_depth (int):
            Maximum depth of the generated quantum circuit. Defaults to `None`.
        max_gate_count (Dict[TranspilerBasisGates, int]):
            A dictionary specifying the maximum allowed count for each type of gate
            in the quantum circuit. Defaults to an empty dictionary.
        optimization_parameter (OptimizationParameterType):
            Determines if and how the synthesis engine should optimize
            the solution. Defaults to `NO_OPTIMIZATION`. See `OptimizationParameterType`
    """

    model_config = ConfigDict(extra="forbid")

    max_width: pydantic.PositiveInt | None = pydantic.Field(
        default=None,
        description="Maximum number of qubits in generated quantum circuit",
    )
    max_depth: pydantic.PositiveInt | None = pydantic.Field(
        default=None,
    )

    max_gate_count: dict[TranspilerBasisGates, pydantic.NonNegativeInt] = (
        pydantic.Field(
            default_factory=lambda: defaultdict(int),
        )
    )

    optimization_parameter: OptimizationParameterType = pydantic.Field(
        default=OptimizationParameter.NO_OPTIMIZATION,
        description="If set, the synthesis engine optimizes the solution"
        " according to that chosen parameter",
    )

    @pydantic.field_validator("max_depth", mode="before")
    @classmethod
    def deprecate_max_depth(cls, value: T) -> T:
        if value is not None:
            warnings.warn(
                "max_depth is deprecated and will no longer be supported starting on 2025-10-27 at the earliest.",
                ClassiqDeprecationWarning,
                stacklevel=1,
            )
        return value

    @pydantic.field_validator("max_gate_count", mode="before")
    @classmethod
    def deprecate_max_gate_count(cls, value: T) -> T:
        if value:
            warnings.warn(
                "max_gate_count is deprecated and will no longer be supported starting on 2025-10-27 at the earliest.",
                ClassiqDeprecationWarning,
                stacklevel=1,
            )
        return value
