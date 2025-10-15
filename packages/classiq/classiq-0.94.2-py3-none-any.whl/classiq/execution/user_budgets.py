from classiq.interface.backend.quantum_backend_providers import ProviderVendor
from classiq.interface.executor.user_budget import UserBudgets

from classiq._internals import async_utils
from classiq._internals.api_wrapper import ApiWrapper

PROVIDER_MAPPER = {
    ProviderVendor.IONQ: "IONQ",
    ProviderVendor.IBM_QUANTUM: "IBM_CLOUD",
    ProviderVendor.AZURE_QUANTUM: "AZURE",
    ProviderVendor.AMAZON_BRAKET: "AMAZON",
    ProviderVendor.GOOGLE: "GOOGLE",
    ProviderVendor.ALICE_AND_BOB: "ALICE_AND_BOB",
    ProviderVendor.OQC: "OQC",
    ProviderVendor.INTEL: "INTEL",
    ProviderVendor.AQT: "AQT",
    ProviderVendor.IQCC: "IQCC",
    ProviderVendor.CLASSIQ: "CLASSIQ",
}


async def get_budget_async(
    provider_vendor: ProviderVendor | None = None,
) -> UserBudgets:

    budgets_list = await ApiWrapper().call_get_all_budgets()
    if provider_vendor:
        provider = PROVIDER_MAPPER.get(provider_vendor, None)
        budgets_list = [
            budget for budget in budgets_list if budget.provider == provider
        ]

    return UserBudgets(budgets=budgets_list)


def get_budget(
    provider_vendor: ProviderVendor | None = None,
) -> UserBudgets:
    """
    Retrieve the user's budget information for quantum computing resources.

    Args:
        provider_vendor:
            (Optional) The quantum backend provider to filter budgets by.
            If not provided, budgets for all providers will be returned.

    Returns:
        UserBudgets: An object containing the user's budget information.
    """
    return async_utils.run(get_budget_async(provider_vendor))


async def set_budget_limit_async(
    provider_vendor: ProviderVendor,
    limit: float,
) -> UserBudgets:
    provider = PROVIDER_MAPPER.get(provider_vendor, None)
    if not provider:
        raise ValueError(f"Unsupported provider: {provider_vendor}")

    budget = get_budget(provider_vendor)
    if budget is None:
        raise ValueError(f"No budget found for provider: {provider_vendor}")

    if limit <= 0:
        raise ValueError("Budget limit must be greater than zero.")

    if limit > budget.budgets[0].available_budget:
        print(  # noqa: T201
            f"Budget limit {limit} exceeds available budget {budget.budgets[0].available_budget} for provider {provider_vendor}.\n"
            "Setting budget limit to the maximum available budget."
        )
    budgets_list = await ApiWrapper().call_set_budget_limit(provider, limit)
    return UserBudgets(budgets=[budgets_list])


def set_budget_limit(
    provider_vendor: ProviderVendor,
    limit: float,
) -> UserBudgets:
    """
    Set a budget limit for a specific quantum backend provider.

    Args:
        provider_vendor:
            The quantum backend provider for which to set the budget limit.
        limit:
            The budget limit to set. Must be greater than zero and not exceed the available budget.

    Returns:
        UserBudgets: An object containing the updated budget information.

    Raises:
        ValueError: If the provider is unsupported, no budget is found, or the limit is invalid.
    """
    return async_utils.run(set_budget_limit_async(provider_vendor, limit))


async def clear_budget_limit_async(provider_vendor: ProviderVendor) -> UserBudgets:
    provider = PROVIDER_MAPPER.get(provider_vendor, None)
    if not provider:
        raise ValueError(f"Unsupported provider: {provider_vendor}")

    budgets_list = await ApiWrapper().call_clear_budget_limit(provider)
    return UserBudgets(budgets=[budgets_list])


def clear_budget_limit(provider_vendor: ProviderVendor) -> UserBudgets:
    """
    Clear the budget limit for a specific quantum backend provider.

    Args:
        provider_vendor:
            The quantum backend provider for which to clear the budget limit.

    Returns:
        UserBudgets: An object containing the updated budget information.

    Raises:
        ValueError: If the provider is unsupported.
    """
    return async_utils.run(clear_budget_limit_async(provider_vendor))
