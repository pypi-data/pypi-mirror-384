from pydantic import BaseModel

from classiq.interface.analyzer.result import QasmCode
from classiq.interface.enum_utils import StrEnum


class QmodFormat(StrEnum):
    """
    Qmod code format.
    """

    NATIVE = "native"
    """
    Native Qmod (`.qmod`).
    """

    PYTHON = "python"
    """
    Python Qmod (`.py`).
    """


class QasmToQmodParams(BaseModel):
    qasm: QasmCode
    qmod_format: QmodFormat
