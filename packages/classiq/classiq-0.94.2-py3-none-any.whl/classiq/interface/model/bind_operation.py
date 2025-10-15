from collections.abc import Mapping, Sequence
from typing import Literal

from classiq.interface.model.handle_binding import ConcreteHandleBinding, HandleBinding
from classiq.interface.model.quantum_statement import HandleMetadata, QuantumOperation

BIND_INPUT_NAME = "bind_input"
BIND_OUTPUT_NAME = "bind_output"


class BindOperation(QuantumOperation):
    kind: Literal["BindOperation"]

    in_handles: list[ConcreteHandleBinding]
    out_handles: list[ConcreteHandleBinding]

    @property
    def wiring_inputs(self) -> Mapping[str, HandleBinding]:
        return {
            f"{BIND_INPUT_NAME}_{i}": handle for i, handle in enumerate(self.in_handles)
        }

    @property
    def readable_inputs(self) -> Sequence[HandleMetadata]:
        return [
            HandleMetadata(
                handle=handle,
                readable_location="on the left-hand side of a bind statement",
            )
            for handle in self.in_handles
        ]

    @property
    def wiring_outputs(self) -> Mapping[str, HandleBinding]:
        return {
            f"{BIND_OUTPUT_NAME}_{i}": handle
            for i, handle in enumerate(self.out_handles)
        }

    @property
    def readable_outputs(self) -> Sequence[HandleMetadata]:
        return [
            HandleMetadata(
                handle=handle,
                readable_location="on the right-hand side of a bind statement",
            )
            for handle in self.out_handles
        ]
