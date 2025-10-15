# This file was generated automatically - do not edit manually


from enum import IntEnum


class Optimizer(IntEnum):
    COBYLA = 1
    SPSA = 2
    L_BFGS_B = 3
    NELDER_MEAD = 4
    ADAM = 5
    SLSQP = 6


class Pauli(IntEnum):
    I = 0  # noqa: E741
    X = 1
    Y = 2
    Z = 3


class QSVMFeatureMapEntanglement(IntEnum):
    FULL = 0
    LINEAR = 1
    CIRCULAR = 2
    SCA = 3
    PAIRWISE = 4


__all__ = [
    "Optimizer",
    "Pauli",
    "QSVMFeatureMapEntanglement",
]
