import dataclasses
import inspect
from enum import EnumMeta
from typing import (
    Any,
    ForwardRef,
    Literal,
    get_args,
    get_origin,
)

from classiq.interface.exceptions import ClassiqValueError
from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.generator.functions.classical_type import (
    Bool,
    ClassicalArray,
    ClassicalTuple,
    Integer,
    Real,
)
from classiq.interface.generator.functions.concrete_types import ConcreteClassicalType
from classiq.interface.generator.functions.type_name import Enum, Struct, TypeName

from classiq.qmod.cparam import CArray, CBool, CInt, CReal
from classiq.qmod.utilities import type_to_str, version_portable_get_args

CARRAY_ERROR_MESSAGE = (
    "CArray accepts one or two generic parameters in the form "
    "`CArray[<element-type>]` or `CArray[<element-type>, <size>]`"
)


def _has_struct_or_enum(classical_type: ConcreteClassicalType) -> bool:
    if isinstance(classical_type, TypeName):
        return True
    if isinstance(classical_type, ClassicalArray):
        return _has_struct_or_enum(classical_type.element_type)
    if isinstance(classical_type, ClassicalTuple):
        return any(
            _has_struct_or_enum(element_type)
            for element_type in classical_type.element_types
        )
    return False


class PythonClassicalType:
    def convert(
        self, py_type: type, nested: bool = False
    ) -> ConcreteClassicalType | None:
        if py_type is int:
            return Integer().set_generative()
        elif py_type is CInt:
            return Integer()
        elif py_type in (float, complex):
            return Real().set_generative()
        elif py_type is CReal:
            return Real()
        elif py_type is bool:
            return Bool().set_generative()
        elif py_type is CBool:
            return Bool()
        elif get_origin(py_type) is list:
            element_py_type = get_args(py_type)[0]
            element_type = self.convert(element_py_type, nested=True)
            if element_type is None:
                return None
            if not element_type.is_generative and not _has_struct_or_enum(element_type):
                raise ClassiqValueError(
                    f"Invalid type annotation: 'list' is generative but "
                    f"{type_to_str(element_py_type)!r} is declarative"
                )
            return ClassicalArray(element_type=element_type).set_generative()
        elif get_origin(py_type) is CArray:
            array_args = version_portable_get_args(py_type)
            if len(array_args) == 1:
                length = None
            elif len(array_args) == 2:
                length = Expression(expr=get_type_hint_expr(array_args[1]))
            else:
                raise ClassiqValueError(CARRAY_ERROR_MESSAGE)
            element_type = self.convert(array_args[0], nested=True)
            if element_type is None:
                return None
            if element_type.is_generative and not _has_struct_or_enum(element_type):
                raise ClassiqValueError(
                    f"Invalid type annotation: 'CArray' is declarative but "
                    f"{type_to_str(array_args[0])!r} is generative"
                )
            return ClassicalArray(
                element_type=self.convert(array_args[0], nested=True), length=length
            )
        elif inspect.isclass(py_type) and dataclasses.is_dataclass(py_type):
            return self.register_struct(py_type)
        elif inspect.isclass(py_type) and isinstance(py_type, EnumMeta):
            self.register_enum(py_type)
            enum_type = Enum(name=py_type.__name__)
            if not nested:
                enum_type.set_generative()
            return enum_type
        elif py_type in (CArray, list):
            raise ClassiqValueError(CARRAY_ERROR_MESSAGE)
        return None

    def register_struct(self, py_type: type) -> TypeName:
        return Struct(name=py_type.__name__)

    def register_enum(self, py_type: EnumMeta) -> None:
        pass


def get_type_hint_expr(type_hint: Any) -> str:
    if isinstance(type_hint, ForwardRef):  # expression in string literal
        return str(type_hint.__forward_arg__)
    if get_origin(type_hint) == Literal:  # explicit numeric literal
        return str(get_args(type_hint)[0])
    else:
        return str(type_hint)  # implicit numeric literal
