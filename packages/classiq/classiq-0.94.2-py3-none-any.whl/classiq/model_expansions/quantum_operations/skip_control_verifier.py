from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.model.skip_control import SkipControl

from classiq.model_expansions.function_builder import FunctionContext
from classiq.model_expansions.quantum_operations.emitter import Emitter


class SkipControlVerifier(Emitter[SkipControl]):
    def emit(self, skip_control: SkipControl, /) -> bool:
        for op, block in list(
            zip(self._builder._operations, self._builder._blocks, strict=True)
        )[::-1]:
            if isinstance(op, FunctionContext):
                break
            if block in ("action", "apply"):
                raise ClassiqExpansionError(
                    "skip_control cannot be used under within-apply's 'apply' block"
                )
        return False
