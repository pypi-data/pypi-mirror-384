from enum import IntEnum
from typing import TYPE_CHECKING

from classiq.interface.generator.types.enum_declaration import EnumDeclaration

if TYPE_CHECKING:
    from classiq.qmod.builtins.structs import SparsePauliOp


class Optimizer(IntEnum):
    COBYLA = 1
    SPSA = 2
    L_BFGS_B = 3
    NELDER_MEAD = 4
    ADAM = 5
    SLSQP = 6


class Pauli(IntEnum):
    """
    Enumeration for the Pauli matrices used in quantum computing.

    Represents the four Pauli matrices used in quantum mechanics: Identity (I), X, Y, and Z operators.
    The Pauli matrices are defined as:

    $$
    I = \\begin{pmatrix} 1 & 0 \\\\ 0 & 1 \\end{pmatrix}
    $$

    $$
    X = \\begin{pmatrix} 0 & 1 \\\\ 1 & 0 \\end{pmatrix}
    $$

    $$
    Y = \\begin{pmatrix} 0 & -i \\\\ i & 0 \\end{pmatrix}
    $$

    $$
    Z = \\begin{pmatrix} 1 & 0 \\\\ 0 & -1 \\end{pmatrix}
    $$

    Attributes:
        I (int): The identity operator (value 0).
        X (int): The Pauli-X operator (value 1).
        Y (int): The Pauli-Y operator (value 2).
        Z (int): The Pauli-Z operator (value 3).
    """

    I = 0  # noqa: E741

    X = 1

    Y = 2

    Z = 3

    def __call__(self, index: int) -> "SparsePauliOp":
        from classiq.qmod.builtins.structs import (
            IndexedPauli,
            SparsePauliOp,
            SparsePauliTerm,
        )

        return SparsePauliOp(
            terms=[
                SparsePauliTerm(
                    paulis=[  # type:ignore[arg-type]
                        IndexedPauli(pauli=self, index=index)  # type:ignore[arg-type]
                    ],
                    coefficient=1.0,  # type:ignore[arg-type]
                )
            ],
            num_qubits=index + 1,
        )


class QSVMFeatureMapEntanglement(IntEnum):
    FULL = 0
    LINEAR = 1
    CIRCULAR = 2
    SCA = 3
    PAIRWISE = 4


BUILTIN_ENUM_DECLARATIONS = {
    enum_def.__name__: EnumDeclaration(
        name=enum_def.__name__,
        members={enum_val.name: enum_val.value for enum_val in enum_def},
    )
    for enum_def in vars().values()
    if (
        isinstance(enum_def, type)
        and issubclass(enum_def, IntEnum)
        and enum_def is not IntEnum
    )
}

__all__ = [
    "Optimizer",
    "Pauli",
    "QSVMFeatureMapEntanglement",
]
