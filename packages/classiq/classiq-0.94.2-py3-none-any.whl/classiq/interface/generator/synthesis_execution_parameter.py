from typing import TypeAlias, Union

from classiq.interface.backend.pydantic_backend import PydanticExecutionParameter

PydanticIntSynthesisExecutionParameter = Union[PydanticExecutionParameter, int]
PydanticPowerType: TypeAlias = PydanticIntSynthesisExecutionParameter
ClassicalArg = Union[float, str]
