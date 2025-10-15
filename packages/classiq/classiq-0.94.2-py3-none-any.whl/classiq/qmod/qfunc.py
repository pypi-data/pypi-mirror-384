import warnings
from collections.abc import Callable
from typing import Literal, overload

from classiq.interface.exceptions import (
    ClassiqDeprecationWarning,
    ClassiqInternalError,
    ClassiqValueError,
)

from classiq.qmod.global_declarative_switch import get_global_declarative_switch
from classiq.qmod.quantum_callable import QCallable
from classiq.qmod.quantum_function import (
    BaseQFunc,
    ExternalQFunc,
    GenerativeQFunc,
    QFunc,
)


@overload
def qfunc(func: Callable) -> GenerativeQFunc: ...


@overload
def qfunc(
    *,
    external: Literal[True],
    synthesize_separately: Literal[False] = False,
    unchecked: list[str] | None = None,
    disable_perm_check: bool = False,
    disable_const_checks: list[str] | bool = False,
) -> Callable[[Callable], ExternalQFunc]: ...


@overload
def qfunc(
    *,
    generative: Literal[False],
    synthesize_separately: bool = False,
    unchecked: list[str] | None = None,
    disable_perm_check: bool = False,
    disable_const_checks: list[str] | bool = False,
) -> Callable[[Callable], QFunc]: ...


@overload
def qfunc(
    *,
    synthesize_separately: bool,
    unchecked: list[str] | None = None,
    disable_perm_check: bool = False,
    disable_const_checks: list[str] | bool = False,
) -> Callable[[Callable], GenerativeQFunc]: ...


@overload
def qfunc(
    *,
    synthesize_separately: bool = False,
    unchecked: list[str] | None = None,
    disable_perm_check: bool = False,
    disable_const_checks: list[str] | bool = False,
) -> Callable[[Callable], GenerativeQFunc]: ...


def qfunc(
    func: Callable | None = None,
    *,
    external: bool = False,
    generative: bool | None = None,
    synthesize_separately: bool = False,
    unchecked: list[str] | None = None,
    disable_perm_check: bool = False,
    disable_const_checks: list[str] | bool = False,
) -> Callable[[Callable], QCallable] | QCallable:
    return _qfunc_inner(
        func=func,
        external=external,
        generative=generative,
        synthesize_separately=synthesize_separately,
        unchecked=unchecked,
        permutation=False,
        disable_perm_check=disable_perm_check,
        disable_const_checks=disable_const_checks,
    )


@overload
def qperm(func: Callable) -> GenerativeQFunc: ...


@overload
def qperm(
    *,
    external: Literal[True],
    synthesize_separately: Literal[False] = False,
    unchecked: list[str] | None = None,
    disable_perm_check: bool = False,
    disable_const_checks: list[str] | bool = False,
) -> Callable[[Callable], ExternalQFunc]: ...


@overload
def qperm(
    *,
    generative: Literal[False],
    synthesize_separately: bool = False,
    unchecked: list[str] | None = None,
    disable_perm_check: bool = False,
    disable_const_checks: list[str] | bool = False,
) -> Callable[[Callable], QFunc]: ...


@overload
def qperm(
    *,
    synthesize_separately: bool,
    unchecked: list[str] | None = None,
    disable_perm_check: bool = False,
    disable_const_checks: list[str] | bool = False,
) -> Callable[[Callable], GenerativeQFunc]: ...


@overload
def qperm(
    *,
    synthesize_separately: bool = False,
    unchecked: list[str] | None = None,
    disable_perm_check: bool = False,
    disable_const_checks: list[str] | bool = False,
) -> Callable[[Callable], GenerativeQFunc]: ...


def qperm(
    func: Callable | None = None,
    *,
    external: bool = False,
    generative: bool | None = None,
    synthesize_separately: bool = False,
    unchecked: list[str] | None = None,
    disable_perm_check: bool = False,
    disable_const_checks: list[str] | bool = False,
) -> Callable[[Callable], QCallable] | QCallable:
    return _qfunc_inner(
        func=func,
        external=external,
        generative=generative,
        synthesize_separately=synthesize_separately,
        unchecked=unchecked,
        permutation=True,
        disable_perm_check=disable_perm_check,
        disable_const_checks=disable_const_checks,
    )


def _qfunc_inner(
    *,
    func: Callable | None = None,
    external: bool = False,
    generative: bool | None = None,
    synthesize_separately: bool = False,
    unchecked: list[str] | None = None,
    permutation: bool = False,
    disable_perm_check: bool = False,
    disable_const_checks: list[str] | bool = False,
) -> Callable[[Callable], QCallable] | QCallable:
    if generative is None:
        generative = True
    if get_global_declarative_switch():
        generative = False

    def wrapper(func: Callable) -> QCallable:
        qfunc: BaseQFunc

        if external:
            _validate_directives(synthesize_separately, unchecked)
            return ExternalQFunc(func, permutation=permutation)

        if generative:
            qfunc = GenerativeQFunc(func, permutation=permutation)
        else:
            qfunc = QFunc(func, permutation=permutation)
        if synthesize_separately:
            qfunc.update_compilation_metadata(should_synthesize_separately=True)
        if unchecked is not None and len(unchecked) > 0:
            nonlocal disable_const_checks
            if disable_const_checks:
                raise ClassiqValueError(
                    "The 'unchecked' parameter is deprecated, please use 'disable_const_checks' only."
                )
            warnings.warn(
                "The 'unchecked' parameter is deprecated and will no longer be supported starting on 2025-10-30 at the earliest. Please use the 'disable_const_checks' instead.",
                ClassiqDeprecationWarning,
                stacklevel=2,
            )
            disable_const_checks = unchecked
        if disable_perm_check:
            qfunc.update_compilation_metadata(disable_perm_check=disable_perm_check)
        if disable_const_checks:
            qfunc.update_compilation_metadata(disable_const_checks=disable_const_checks)
        return qfunc

    if func is not None:
        return wrapper(func)
    return wrapper


def _validate_directives(
    synthesize_separately: bool, unchecked: list[str] | None = None
) -> None:
    error_msg = ""
    if synthesize_separately:
        error_msg += "External functions can't be marked as synthesized separately. \n"
    if unchecked is not None and len(unchecked) > 0:
        error_msg += "External functions can't have unchecked modifiers."
    if error_msg:
        raise ClassiqInternalError(error_msg)
