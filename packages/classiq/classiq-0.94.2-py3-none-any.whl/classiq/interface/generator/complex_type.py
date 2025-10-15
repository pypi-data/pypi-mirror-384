from typing import Annotated

from pydantic import PlainSerializer, PlainValidator
from pydantic.json_schema import WithJsonSchema


def validate_complex(v: complex | str) -> complex:
    if isinstance(v, str):
        v = "".join(v.split())
    return complex(v)


Complex = Annotated[
    complex,
    PlainValidator(validate_complex),
    PlainSerializer(lambda x: str(x)),
    WithJsonSchema({"type": "string", "pattern": r"[+-]?\d+\.?\d* *[+-] *\d+\.?\d*j"}),
]
