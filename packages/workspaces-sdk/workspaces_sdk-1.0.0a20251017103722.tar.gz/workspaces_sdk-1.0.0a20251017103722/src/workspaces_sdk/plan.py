"""
Plan Client for Workspaces SDK.

Provides access to subscription plan management functionality including creating,  # noqa: E501
updating, and managing plans and subscriptions.
"""

from typing import Any, List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Plan system
class PlanQuotaInput(TypedDict):
    quotaId: str
    quantity: int


class CreatePlanInput(TypedDict):
    name: str
    price: float
    currency: Optional[str]  # Default USD
    duration: str  # "monthly" or "yearly"
    quotas: List[PlanQuotaInput]
    productId: str


class UpdatePlanInput(TypedDict):
    id: str
    name: Optional[str]
    price: Optional[float]
    currency: Optional[str]  # Default USD
    duration: Optional[str]
    quotas: List[PlanQuotaInput]
    isActive: Optional[bool]


class SubscriptionFeatures(TypedDict):
    id: str
    planId: Optional[str]
    addonId: Optional[str]
    quotaId: str


class SubscriptionEntitlement(TypedDict):
    id: str
    itemId: str
    planId: str
    accessType: str


class QuotaAssignment(TypedDict):
    id: str
    name: str
    limits: Any
    reusable: bool
    subscriptionId: str
    createdAt: str
    endtime: str


class AddonSubscription(TypedDict):
    id: str
    addonId: str
    quantity: int
    startDate: str
    endDate: str


class BillingAccount(TypedDict):
    id: str
    accountName: str


class Subscription(TypedDict):
    id: str
    billingAccountId: str
    billingAccount: BillingAccount
    planId: str
    addonSubscriptions: List[AddonSubscription]
    status: str  # "active", "canceled", "expired"
    startDate: str
    endDate: str
    creditsAwarded: float
    recurrence: bool
    duration: str  # "monthly" or "yearly"
    quotas: List[QuotaAssignment]
    createdAt: str
    updatedAt: str


class Plan(TypedDict):
    id: str
    name: str
    price: float
    currency: str
    duration: str  # "monthly" or "yearly"
    isActive: bool
    productID: str
    features: List[SubscriptionFeatures]
    subscriptions: List[Subscription]
    itemEntitlements: List[SubscriptionEntitlement]
    createdAt: str
    updatedAt: str


class PlanClient:
    """
    Client for managing subscription plans in the Workspaces platform.

    Provides methods to create, update, retrieve, and manage subscription plans
    with proper authentication and error handling.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Plan client with a GraphQL endpoint.

        Args:
            graphql_endpoint (str): The GraphQL endpoint URL
        """
        self.graphql_endpoint = graphql_endpoint

    def get_client(self, token: str) -> Client:
        """Create and return a GraphQL client with the given token."""
        headers = get_default_headers()
        headers["Authorization"] = f"Bearer {token}"

        transport = RequestsHTTPTransport(url=self.graphql_endpoint, headers=headers)
        return Client(transport=transport, fetch_schema_from_transport=True)

    # Plan Query Operations
    async def get_all_plans(self, token: str) -> List[Plan]:
        """
        Retrieves all available subscription plans.

        Args:
            token (str): Authentication token

        Returns:
            List[Plan]: List of all available plans
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAllPlans {
                    getAllPlans {
                        id
                        name
                        price
                        currency
                        duration
                        isActive
                        productID
                        features {
                            id
                            planId
                            addonId
                            quotaId
                        }
                        subscriptions {
                            id
                            billingAccountId
                            billingAccount {
                                id
                                accountName
                            }
                            planId
                            addonSubscriptions {
                                id
                                addonId
                                quantity
                                startDate
                                endDate
                            }
                            status
                            startDate
                            endDate
                            creditsAwarded
                            recurrence
                            duration
                            quotas {
                                id
                                name
                                limits
                                reusable
                                subscriptionId
                                createdAt
                                endtime
                            }
                            createdAt
                            updatedAt
                        }
                        itemEntitlements {
                            id
                            itemId
                            planId
                            accessType
                        }
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(query)
            return result.get("getAllPlans", [])
        except Exception as e:
            print(f"Get all plans failed: {str(e)}")
            return []

    async def get_plan(self, plan_id: str, token: str) -> Optional[Plan]:
        """
        Retrieves detailed information for a specific plan.

        Args:
            plan_id (str): ID of the plan
            token (str): Authentication token

        Returns:
            Optional[Plan]: Plan details or None if not found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetPlan($id: ID!) {
                    getPlan(id: $id) {
                        id
                        name
                        price
                        currency
                        duration
                        isActive
                        productID
                        features {
                            id
                            planId
                            addonId
                            quotaId
                        }
                        subscriptions {
                            id
                            billingAccountId
                            billingAccount {
                                id
                                accountName
                            }
                            planId
                            addonSubscriptions {
                                id
                                addonId
                                quantity
                                startDate
                                endDate
                            }
                            status
                            startDate
                            endDate
                            creditsAwarded
                            recurrence
                            duration
                            quotas {
                                id
                                name
                                limits
                                reusable
                                subscriptionId
                                createdAt
                                endtime
                            }
                            createdAt
                            updatedAt
                        }
                        itemEntitlements {
                            id
                            itemId
                            planId
                            accessType
                        }
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"id": plan_id}
            result = client.execute(query, variable_values=variables)
            return result.get("getPlan")
        except Exception as e:
            print(f"Get plan failed: {str(e)}")
            return None

    # Plan Mutation Operations
    async def create_plan(
        self,
        name: str,
        price: float,
        duration: str,
        quotas: List[PlanQuotaInput],
        product_id: str,
        token: str,
        currency: Optional[str] = "USD",
    ) -> bool:
        """
        Creates a new subscription plan.

        Args:
            name (str): Name of the plan
            price (float): Price of the plan
            duration (str): Duration ("monthly" or "yearly")
            quotas (List[PlanQuotaInput]): List of quota configurations
            product_id (str): Product ID the plan belongs to
            token (str): Authentication token
            currency (str, optional): Currency for pricing (defaults to "USD")

        Returns:
            bool: True if plan creation succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreatePlan($input: createPlanInput!) {
                    createPlan(input: $input)
                }
            """
            )

            variables = {
                "input": {
                    "name": name,
                    "price": price,
                    "currency": currency,
                    "duration": duration,
                    "quotas": quotas,
                    "productId": product_id,
                }
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("createPlan", False)
        except Exception as e:
            print(f"Create plan failed: {str(e)}")
            return False

    async def update_plan(
        self,
        plan_id: str,
        quotas: List[PlanQuotaInput],
        token: str,
        name: Optional[str] = None,
        price: Optional[float] = None,
        currency: Optional[str] = None,
        duration: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> bool:
        """
        Updates an existing subscription plan.

        Args:
            plan_id (str): ID of the plan to update
            quotas (List[PlanQuotaInput]): List of quota configurations
            token (str): Authentication token
            name (str, optional): New name for the plan
            price (float, optional): New price for the plan
            currency (str, optional): New currency for the plan
            duration (str, optional): New duration for the plan
            is_active (bool, optional): New active status for the plan

        Returns:
            bool: True if plan update succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdatePlan($input: updatePlanInput!) {
                    updatePlan(input: $input)
                }
            """
            )

            update_input = {"id": plan_id, "quotas": quotas}

            if name is not None:
                update_input["name"] = name
            if price is not None:
                update_input["price"] = price
            if currency is not None:
                update_input["currency"] = currency
            if duration is not None:
                update_input["duration"] = duration
            if is_active is not None:
                update_input["isActive"] = is_active

            variables = {"input": update_input}

            result = client.execute(mutation, variable_values=variables)
            return result.get("updatePlan", False)
        except Exception as e:
            print(f"Update plan failed: {str(e)}")
            return False

    async def toggle_plan(self, plan_id: str, status: bool, token: str) -> bool:
        """
        Toggles the active status of a subscription plan.

        Args:
            plan_id (str): ID of the plan to toggle
            status (bool): New active status (True for active, False for inactive)  # noqa: E501
            token (str): Authentication token

        Returns:
            bool: True if toggle operation succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation TogglePlan($planID: ID!, $status: Boolean!) {
                    togglePlan(planID: $planID, status: $status)
                }
            """
            )

            variables = {"planID": plan_id, "status": status}

            result = client.execute(mutation, variable_values=variables)
            return result.get("togglePlan", False)
        except Exception as e:
            print(f"Toggle plan failed: {str(e)}")
            return False

    # Helper method for creating plan quota input
    def create_plan_quota_input(self, quota_id: str, quantity: int) -> PlanQuotaInput:
        """
        Helper method to create a PlanQuotaInput object.

        Args:
            quota_id (str): ID of the quota
            quantity (int): Quantity for the quota

        Returns:
            PlanQuotaInput: Formatted plan quota input
        """
        return {"quotaId": quota_id, "quantity": quantity}


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Plan client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = PlanClient(graphql_endpoint)


def get_client() -> PlanClient:
    """Get the default Plan client."""
    if _default_client is None:
        raise RuntimeError("Plan client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def get_all_plans(*args, **kwargs):
    return await get_client().get_all_plans(*args, **kwargs)


async def get_plan(*args, **kwargs):
    return await get_client().get_plan(*args, **kwargs)


async def create_plan(*args, **kwargs):
    return await get_client().create_plan(*args, **kwargs)


async def update_plan(*args, **kwargs):
    return await get_client().update_plan(*args, **kwargs)


async def toggle_plan(*args, **kwargs):
    return await get_client().toggle_plan(*args, **kwargs)


def create_plan_quota_input(*args, **kwargs):
    if _default_client is None:
        raise RuntimeError("Plan client not initialized. Call initialize() first.")
    return _default_client.create_plan_quota_input(*args, **kwargs)
