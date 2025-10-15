import warnings
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from typing import NamedTuple

from classiq.interface.ast_node import ASTNode
from classiq.interface.exceptions import (
    ClassiqDeprecationWarning,
    ClassiqInternalExpansionError,
)
from classiq.interface.generator.compiler_keywords import EXPANDED_KEYWORD
from classiq.interface.generator.functions.port_declaration import (
    PortDeclarationDirection,
)
from classiq.interface.generator.functions.type_modifier import TypeModifier
from classiq.interface.generator.visitor import NodeType
from classiq.interface.model.allocate import Allocate
from classiq.interface.model.bind_operation import BindOperation
from classiq.interface.model.block import Block
from classiq.interface.model.control import Control
from classiq.interface.model.invert import Invert
from classiq.interface.model.model_visitor import ModelVisitor
from classiq.interface.model.native_function_definition import NativeFunctionDefinition
from classiq.interface.model.power import Power
from classiq.interface.model.quantum_expressions.amplitude_loading_operation import (
    AmplitudeLoadingOperation,
)
from classiq.interface.model.quantum_expressions.arithmetic_operation import (
    ArithmeticOperation,
)
from classiq.interface.model.quantum_function_call import QuantumFunctionCall
from classiq.interface.model.skip_control import SkipControl
from classiq.interface.model.within_apply_operation import WithinApply
from classiq.interface.source_reference import SourceReference


class _BoundVars(NamedTuple):
    in_identifiers: list[str]
    out_identifiers: list[str]
    source_ref: SourceReference | None

    def reverse(self) -> "_BoundVars":
        return _BoundVars(
            in_identifiers=self.out_identifiers,
            out_identifiers=self.in_identifiers,
            source_ref=self.source_ref,
        )


class UncomputationSignatureInference(ModelVisitor):
    """
    Infers the uncomputation signature of a function (permutation/non-permutation for
    the function, and const/non-const for each parameter).

    A function is a permutation if and only if all its body operations are permutations
    (note that amplitude loading operation is not a permutation).

    A parameter is const if and only if it is used as a const argument in all the
    body operations (including when binding it to a different variable). An exception
    for this rule is that a const parameter can be used as a non-const argument to a
    permutation function inside a `within` block.

    This class assumes that dependent functions are already inferred, so it doesn't
    recursively inferring function calls.
    """

    def __init__(self) -> None:
        self._is_permutation: bool = True
        self._non_permutation_reasons: list[SourceReference | None] = []
        self._non_const_with_reasons: dict[str, list[SourceReference | None]] = (
            defaultdict(list)
        )

        self._in_conjugation: bool = False
        self._source_ref: SourceReference | None = None

        # remember bound vars inside `within` to invert their effect after the `apply`
        self._bound_vars_list: list[_BoundVars] = []

    def run(self, func_def: NativeFunctionDefinition) -> None:
        self._is_permutation = True
        self._non_permutation_reasons.clear()
        self._non_const_with_reasons.clear()
        self.visit(func_def.body)

    def is_permutation(self) -> bool:
        return self._is_permutation

    def non_permutation_reasons(self) -> list[SourceReference | None]:
        if self._is_permutation:
            raise ClassiqInternalExpansionError("Function is a permutation")
        return self._non_permutation_reasons

    def is_const(self, port: str) -> bool:
        return port not in self._non_const_with_reasons

    def non_const_reasons(self, port: str) -> list[SourceReference | None]:
        if port not in self._non_const_with_reasons:
            raise ClassiqInternalExpansionError("Parameter is constant")
        return self._non_const_with_reasons[port]

    def visit(self, node: NodeType) -> None:
        if isinstance(node, ASTNode):
            with self._source_reference_context(node.source_ref):
                super().visit(node)
        else:
            super().visit(node)

    def visit_QuantumFunctionCall(self, call: QuantumFunctionCall) -> None:
        if not call.func_decl.permutation:
            self._mark_as_non_permutation()

        in_identifiers: list[str] = []
        out_identifiers: list[str] = []

        for handle, port in call.handles_with_params:
            if port.type_modifier is not TypeModifier.Const:
                self._mark_as_non_const(handle.name, call.func_decl.permutation)

            if port.direction is PortDeclarationDirection.Input:
                in_identifiers.append(handle.name)
            elif port.direction is PortDeclarationDirection.Output:
                out_identifiers.append(handle.name)

        if in_identifiers or out_identifiers:
            bound_vars = _BoundVars(in_identifiers, out_identifiers, call.source_ref)
            self._mark_bind_outputs(bound_vars)
            self._bound_vars_list.append(bound_vars)

    def visit_Allocate(self, alloc: Allocate) -> None:
        self._mark_as_non_const(alloc.target.name, True)

    def visit_BindOperation(self, bind_op: BindOperation) -> None:
        in_identifiers = [handle.name for handle in bind_op.in_handles]
        out_identifiers = [handle.name for handle in bind_op.out_handles]
        bound_vars = _BoundVars(in_identifiers, out_identifiers, bind_op.source_ref)
        self._mark_bind_outputs(bound_vars)
        self._bound_vars_list.append(bound_vars)

    def visit_ArithmeticOperation(self, arith: ArithmeticOperation) -> None:
        self._mark_as_non_const(arith.result_var.name, True)

    def visit_AmplitudeLoadingOperation(
        self, amp_load: AmplitudeLoadingOperation
    ) -> None:
        self._mark_as_non_permutation()
        self._mark_as_non_const(amp_load.result_var.name, False)

    def visit_Control(self, control: Control) -> None:
        self.visit(control.body)
        if control.else_block is not None:
            self.visit(control.else_block)

    def visit_Invert(self, invert: Invert) -> None:
        self.visit(invert.body)

    def visit_Power(self, power: Power) -> None:
        self.visit(power.body)

    def visit_WithinApply(self, within_apply: WithinApply) -> None:
        with self._conjugation_context() as bound_vars_list:
            self.visit(within_apply.compute)
        self.visit(within_apply.action)

        for bound_vars in reversed(bound_vars_list):
            self._mark_bind_outputs(bound_vars.reverse())

    def visit_Block(self, block: Block) -> None:
        self.visit(block.statements)

    def visit_SkipControl(self, block: SkipControl) -> None:
        self.visit(block.body)

    def _mark_as_non_permutation(self) -> None:
        self._is_permutation = False
        self._non_permutation_reasons.append(self._source_ref)

    def _mark_as_non_const(
        self,
        identifier: str,
        permutation_op: bool,
        source_ref: SourceReference | None = None,
    ) -> None:
        if self._in_conjugation and permutation_op:
            return
        self._non_const_with_reasons[identifier].append(source_ref or self._source_ref)

    def _mark_bind_outputs(self, bound_vars: _BoundVars) -> None:
        if all(self.is_const(identifier) for identifier in bound_vars.in_identifiers):
            return
        for identifier in bound_vars.out_identifiers:
            self._mark_as_non_const(identifier, False, bound_vars.source_ref)

    @contextmanager
    def _conjugation_context(self) -> Iterator[list[_BoundVars]]:
        previous_bound_vars = self._bound_vars_list
        previous_context = self._in_conjugation
        self._bound_vars_list = []
        self._in_conjugation = True
        try:
            yield self._bound_vars_list
        finally:
            self._in_conjugation = previous_context
            self._bound_vars_list = previous_bound_vars

    @contextmanager
    def _source_reference_context(
        self, source_ref: SourceReference | None
    ) -> Iterator[None]:
        previous_source_ref = self._source_ref
        self._source_ref = source_ref
        try:
            yield
        finally:
            self._source_ref = previous_source_ref


def infer_and_validate_uncomputation_signature(
    func_def: NativeFunctionDefinition,
    disable_perm_check: bool = False,
    disable_const_checks: list[str] | bool = False,
    tighten_signature: bool = False,
) -> None:
    """
    Runs the uncomputation signature inference in order to validate the function signature
    and tighten it when requested (changing non-permutation to permutation and non-const
    to const).
    """
    for port in func_def.port_declarations:
        if port.type_modifier is TypeModifier.Const and port.direction in (
            PortDeclarationDirection.Input,
            PortDeclarationDirection.Output,
        ):
            warnings.warn(
                _input_output_const(port.name, port.direction, func_def.name),
                ClassiqDeprecationWarning,
                stacklevel=1,
            )

    if disable_perm_check and (disable_const_checks is True) and not tighten_signature:
        return

    visitor = UncomputationSignatureInference()
    visitor.run(func_def)

    if not disable_perm_check and func_def.permutation and not visitor.is_permutation():
        for source_ref in visitor.non_permutation_reasons():
            warnings.warn(
                _non_permutation_usage(func_def.name, source_ref),
                ClassiqDeprecationWarning,
                stacklevel=1,
            )

    if tighten_signature and not func_def.permutation and visitor.is_permutation():
        func_def.permutation = True

    unchecked = (
        set(disable_const_checks) if isinstance(disable_const_checks, list) else set()
    )
    for port in func_def.port_declarations:
        if (
            not ((disable_const_checks is True) or port.name in unchecked)
            and port.type_modifier is TypeModifier.Const
            and not visitor.is_const(port.name)
        ):
            for source_ref in visitor.non_const_reasons(port.name):
                warnings.warn(
                    _non_const_usage(port.name, source_ref),
                    ClassiqDeprecationWarning,
                    stacklevel=1,
                )

        if (
            tighten_signature
            and port.type_modifier is not TypeModifier.Const
            and visitor.is_const(port.name)
        ):
            port.type_modifier = TypeModifier.Const


def _input_output_const(
    port_name: str,
    direction: PortDeclarationDirection,
    function_name: str,
) -> str:
    return (
        f"{direction.capitalize()} parameters cannot be defined as constants"
        f" (parameter {port_name!r} in function {function_name.split('_' + EXPANDED_KEYWORD)[0]!r}).\n"
        "The deprecation warning will be elevated to an error starting 2025-10-30, at the earliest."
    )


def _non_const_usage(
    port_name: str,
    source_ref: SourceReference | None = None,
) -> str:
    source_ref_str = f"\n\tat {source_ref}" if source_ref else ""
    return (
        f"Non-constant usage of a constant parameter {port_name!r}.{source_ref_str}\n"
        "Tip: if the commulative use of the parameter in the function is constant, "
        "use the `disable_const_checks` flag to instruct the compiler to disregard individual operations.\n"
        "The deprecation warning will be elevated to an error starting 2025-10-30, at the earliest."
    )


def _non_permutation_usage(
    function_name: str,
    source_ref: SourceReference | None = None,
) -> str:
    source_ref_str = f"\n\tat {source_ref}" if source_ref else ""
    return (
        f"Non-permutation operation used in a permutation function {function_name.split('_' + EXPANDED_KEYWORD)[0]!r}.{source_ref_str}\n"
        "Tip: if the commulative effect of the function is a permutation, "
        "use the `disable_perm_check` flag to instruct the compiler to disregard individual operations.\n"
        "The deprecation warning will be elevated to an error starting 2025-10-30, at the earliest."
    )
