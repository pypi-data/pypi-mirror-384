from typing import Literal

from classiq.interface.generator.expressions.expression import Expression
from classiq.interface.model.handle_binding import ConcreteHandleBinding
from classiq.interface.model.quantum_statement import QuantumOperation


class SetBoundsStatement(QuantumOperation):
    kind: Literal["SetBoundsStatement"]

    target: ConcreteHandleBinding
    lower_bound: Expression | None
    upper_bound: Expression | None

    @property
    def expressions(self) -> list[Expression]:
        exprs = []
        if self.lower_bound is not None:
            exprs.append(self.lower_bound)
        if self.upper_bound is not None:
            exprs.append(self.upper_bound)
        return exprs
