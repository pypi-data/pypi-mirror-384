from classiq.interface.enum_utils import StrEnum


class TypeModifier(StrEnum):
    Const = "const"
    Permutable = "permutable"
    Mutable = "mutable"
    Inferred = "inferred"
