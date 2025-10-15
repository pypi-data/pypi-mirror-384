from classiq.interface.ast_node import ASTNode
from classiq.interface.exceptions import ClassiqError


class Parameter(ASTNode):
    name: str | None

    def get_name(self) -> str:
        if self.name is None:
            raise ClassiqError("Cannot resolve parameter name")
        return self.name
