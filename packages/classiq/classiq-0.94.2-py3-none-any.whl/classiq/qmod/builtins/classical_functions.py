# This file was generated automatically - do not edit manually


from classiq.qmod.qmod_parameter import CInt, CReal
from classiq.qmod.symbolic import symbolic_function

from .structs import *


def qft_const_adder_phase(
    bit_index: CInt,
    value: CInt,
    reg_len: CInt,
) -> CReal:
    return symbolic_function(
        bit_index, value, reg_len, return_type=CReal  # type:ignore[type-abstract]
    )


__all__ = [
    "qft_const_adder_phase",
]
