"""
Quota Client for Workspaces SDK.

Provides access to quota management functionality including quota creation,
management, and subscription feature assignments.
"""

from typing import Any, List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Quota system
class CreateQuotaInput(TypedDict):
    name: str
    limits: Any  # JSON object
    reusable: bool


class UpdateQuotaInput(TypedDict):
    id: str
    name: Optional[str]
    limits: Optional[Any]  # JSON object
    reusable: Optional[bool]
    isActive: bool


class SubscriptionFeatures(TypedDict):
    id: str
    planId: Optional[str]
    addonId: Optional[str]
    quotaId: str


class Quota(TypedDict):
    id: str
    name: str
    limits: Any  # JSON object defining limits
    isActive: bool
    reusable: bool
    subscriptions: List[SubscriptionFeatures]
    createdAt: str
    updatedAt: str


class QuotaClient:
    """
    Client for managing quotas in the Workspaces platform.

    Provides methods to create, update, and retrieve quota configurations
    with proper authentication and error handling.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Quota client with a GraphQL endpoint.

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

    # Quota Query Operations
    async def get_all_quotas_of_subscription(
        self, subscription_id: str, token: str
    ) -> List[Quota]:
        """
        Retrieves all quotas associated with a specific subscription.

        Args:
            subscription_id (str): ID of the subscription
            token (str): Authentication token

        Returns:
            List[Quota]: List of quotas for the subscription
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAllQuotasOfSub($subscriptionId: ID!) {
                    getAllQuotasOfSub(subscriptionId: $subscriptionId) {
                        id
                        name
                        limits
                        isActive
                        reusable
                        subscriptions {
                            id
                            planId
                            addonId
                            quotaId
                        }
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"subscriptionId": subscription_id}
            result = client.execute(query, variable_values=variables)
            return result.get("getAllQuotasOfSub", [])
        except Exception as e:
            print(f"Get all quotas of subscription failed: {str(e)}")
            return []

    async def get_all_quotas(self, token: str) -> List[Quota]:
        """
        Retrieves all available quotas in the system.

        Args:
            token (str): Authentication token

        Returns:
            List[Quota]: List of all quotas
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAllQuotas {
                    getAllQuotas {
                        id
                        name
                        limits
                        isActive
                        reusable
                        subscriptions {
                            id
                            planId
                            addonId
                            quotaId
                        }
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(query)
            return result.get("getAllQuotas", [])
        except Exception as e:
            print(f"Get all quotas failed: {str(e)}")
            return []

    # Quota Mutation Operations
    async def create_quota(
        self, name: str, limits: Any, reusable: bool, token: str
    ) -> bool:
        """
        Creates a new quota configuration.

        Args:
            name (str): Name of the quota
            limits (Any): JSON object defining the quota limits
            reusable (bool): Whether the quota is reusable (e.g., bot seats)
            token (str): Authentication token

        Returns:
            bool: True if quota creation succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateQuota($input: createQuotaInput!) {
                    createQuota(input: $input)
                }
            """
            )

            variables = {
                "input": {"name": name, "limits": limits, "reusable": reusable}
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("createQuota", False)
        except Exception as e:
            print(f"Create quota failed: {str(e)}")
            return False

    async def update_quota(
        self,
        quota_id: str,
        is_active: bool,
        token: str,
        name: Optional[str] = None,
        limits: Optional[Any] = None,
        reusable: Optional[bool] = None,
    ) -> bool:
        """
        Updates an existing quota configuration.

        Args:
            quota_id (str): ID of the quota to update
            is_active (bool): Whether the quota should be active
            token (str): Authentication token
            name (str, optional): New name for the quota
            limits (Any, optional): New limits configuration
            reusable (bool, optional): New reusable setting

        Returns:
            bool: True if quota update succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateQuota($input: updateQuotaInput!) {
                    updateQuota(input: $input)
                }
            """
            )

            update_input = {"id": quota_id, "isActive": is_active}

            if name is not None:
                update_input["name"] = name
            if limits is not None:
                update_input["limits"] = limits
            if reusable is not None:
                update_input["reusable"] = reusable

            variables = {"input": update_input}

            result = client.execute(mutation, variable_values=variables)
            return result.get("updateQuota", False)
        except Exception as e:
            print(f"Update quota failed: {str(e)}")
            return False

    # Helper methods
    def create_quota_limits(self, **limits_config: Any) -> dict:
        """
        Helper method to create quota limits configuration.

        Args:
            **limits_config: Key-value pairs for limit configuration

        Returns:
            dict: Formatted limits configuration

        Example:
            limits = client.create_quota_limits(
                message_limit=1000,
                bot_creation_limit=5,
                storage_limit_mb=1024
            )
        """
        return limits_config

    def create_create_quota_input(
        self, name: str, limits: Any, reusable: bool
    ) -> CreateQuotaInput:
        """
        Helper method to create a CreateQuotaInput object.

        Args:
            name (str): Quota name
            limits (Any): Quota limits configuration
            reusable (bool): Whether quota is reusable

        Returns:
            CreateQuotaInput: Formatted quota input
        """
        return {"name": name, "limits": limits, "reusable": reusable}

    def create_update_quota_input(
        self,
        quota_id: str,
        is_active: bool,
        name: Optional[str] = None,
        limits: Optional[Any] = None,
        reusable: Optional[bool] = None,
    ) -> UpdateQuotaInput:
        """
        Helper method to create an UpdateQuotaInput object.

        Args:
            quota_id (str): ID of quota to update
            is_active (bool): Active status
            name (str, optional): New name
            limits (Any, optional): New limits
            reusable (bool, optional): New reusable setting

        Returns:
            UpdateQuotaInput: Formatted update input
        """
        update_input = {"id": quota_id, "isActive": is_active}

        if name is not None:
            update_input["name"] = name
        if limits is not None:
            update_input["limits"] = limits
        if reusable is not None:
            update_input["reusable"] = reusable

        return update_input


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Quota client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = QuotaClient(graphql_endpoint)


def get_client() -> QuotaClient:
    """Get the default Quota client."""
    if _default_client is None:
        raise RuntimeError("Quota client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def get_all_quotas_of_subscription(*args, **kwargs):
    return await get_client().get_all_quotas_of_subscription(*args, **kwargs)


async def get_all_quotas(*args, **kwargs):
    return await get_client().get_all_quotas(*args, **kwargs)


async def create_quota(*args, **kwargs):
    return await get_client().create_quota(*args, **kwargs)


async def update_quota(*args, **kwargs):
    return await get_client().update_quota(*args, **kwargs)


def create_quota_limits(*args, **kwargs):
    if _default_client is None:
        raise RuntimeError("Quota client not initialized. Call initialize() first.")
    return _default_client.create_quota_limits(*args, **kwargs)


def create_create_quota_input(*args, **kwargs):
    if _default_client is None:
        raise RuntimeError("Quota client not initialized. Call initialize() first.")
    return _default_client.create_create_quota_input(*args, **kwargs)


def create_update_quota_input(*args, **kwargs):
    if _default_client is None:
        raise RuntimeError("Quota client not initialized. Call initialize() first.")
    return _default_client.create_update_quota_input(*args, **kwargs)
