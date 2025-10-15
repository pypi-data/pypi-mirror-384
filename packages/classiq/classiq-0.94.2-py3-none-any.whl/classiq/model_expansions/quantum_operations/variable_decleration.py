from typing import TYPE_CHECKING, cast

from classiq.interface.exceptions import ClassiqExpansionError
from classiq.interface.generator.functions.classical_type import ClassicalType
from classiq.interface.generator.functions.concrete_types import ConcreteType
from classiq.interface.helpers.text_utils import readable_list, s
from classiq.interface.model.handle_binding import HandleBinding
from classiq.interface.model.quantum_type import QuantumType
from classiq.interface.model.variable_declaration_statement import (
    VariableDeclarationStatement,
)

from classiq.evaluators.parameter_types import (
    evaluate_type_in_classical_symbol,
    evaluate_type_in_quantum_symbol,
)
from classiq.evaluators.qmod_annotated_expression import QmodAnnotatedExpression
from classiq.model_expansions.quantum_operations.emitter import Emitter
from classiq.model_expansions.scope import ClassicalSymbol, Evaluated, QuantumSymbol

if TYPE_CHECKING:
    from classiq.model_expansions.interpreters.base_interpreter import BaseInterpreter


class VariableDeclarationStatementEmitter(Emitter[VariableDeclarationStatement]):
    def __init__(
        self, interpreter: "BaseInterpreter", allow_symbolic_vars: bool = False
    ) -> None:
        super().__init__(interpreter)
        self._allow_symbolic_vars = allow_symbolic_vars

    def emit(self, variable_declaration: VariableDeclarationStatement, /) -> bool:
        var_decl = variable_declaration.model_copy(
            update=dict(back_ref=variable_declaration.uuid)
        )
        var_decl.qmod_type = variable_declaration.qmod_type.model_copy()
        if variable_declaration.name in self._current_scope:
            raise ClassiqExpansionError(
                f"Variable {variable_declaration.name!r} is already defined"
            )
        var_value: QuantumSymbol | ClassicalSymbol
        if variable_declaration.is_quantum:
            var_value = self._get_quantum_var(var_decl)
        else:
            var_value = self._get_classical_var(var_decl)
        self._current_scope[variable_declaration.name] = Evaluated(
            value=var_value, defining_function=self._builder.current_function
        )
        self.emit_statement(var_decl)
        return True

    def _get_quantum_var(self, var_decl: VariableDeclarationStatement) -> QuantumSymbol:
        updated_quantum_type = evaluate_type_in_quantum_symbol(
            cast(QuantumType, var_decl.qmod_type),
            self._current_scope,
            var_decl.name,
        )
        if not self._allow_symbolic_vars:
            symbolic_variables = list(
                dict.fromkeys(
                    classical_var.name
                    for expr in updated_quantum_type.expressions
                    if isinstance(expr_val := expr.value.value, QmodAnnotatedExpression)
                    for classical_var in expr_val.get_classical_vars().values()
                )
            )
            if len(symbolic_variables) > 0:
                raise ClassiqExpansionError(
                    f"Variable type is instantiated with non-compile-time "
                    f"variable{s(symbolic_variables)} "
                    f"{readable_list(symbolic_variables, quote=True)}"
                )
        var_decl.qmod_type = updated_quantum_type
        var_value = QuantumSymbol(
            handle=HandleBinding(name=var_decl.name),
            quantum_type=updated_quantum_type,
        )
        self._builder.current_block.captured_vars.init_var(
            var_decl.name, self._builder.current_function
        )
        return var_value

    def _get_classical_var(
        self, var_decl: VariableDeclarationStatement
    ) -> ClassicalSymbol:
        updated_classical_type = evaluate_type_in_classical_symbol(
            cast(ClassicalType, var_decl.qmod_type),
            self._current_scope,
            var_decl.name,
        )
        var_decl.qmod_type = cast(ConcreteType, updated_classical_type)
        var_value = ClassicalSymbol(
            handle=HandleBinding(name=var_decl.name),
            classical_type=updated_classical_type,
        )
        return var_value
