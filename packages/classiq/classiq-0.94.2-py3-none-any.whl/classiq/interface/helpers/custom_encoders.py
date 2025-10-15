from collections.abc import Callable
from typing import Any

CUSTOM_ENCODERS: dict[type, Callable[[Any], Any]] = {complex: str}
