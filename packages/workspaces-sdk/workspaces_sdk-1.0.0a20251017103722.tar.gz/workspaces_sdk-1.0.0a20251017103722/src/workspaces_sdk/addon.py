"""
Addon Client for Workspaces SDK.

Provides access to addon management functionality including creating, updating,
and managing addon subscriptions.
"""

from typing import List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Addon system
class AddonQuotaInput(TypedDict):
    quotaId: str
    quantity: int


class CreateAddOnsInput(TypedDict):
    name: str
    price: float
    currency: str
    duration: str  # "monthly" or "yearly"
    quotas: List[AddonQuotaInput]
    productId: str


class UpdateAddOnsInput(TypedDict):
    id: str
    name: Optional[str]
    price: Optional[float]
    currency: Optional[str]
    duration: Optional[str]
    quotas: List[AddonQuotaInput]
    isActive: Optional[bool]


class SubscriptionFeatures(TypedDict):
    id: str
    planId: Optional[str]
    addonId: Optional[str]
    quotaId: str


class AddonSubscription(TypedDict):
    id: str
    currentSubscriptionId: str
    addonId: str
    quantity: int
    startDate: str
    endDate: str
    createdAt: str
    updatedAt: str


class Addon(TypedDict):
    id: str
    name: str
    price: float
    productID: str
    currency: str
    duration: str
    isActive: bool
    features: List[SubscriptionFeatures]
    addonSubscriptions: List[AddonSubscription]
    createdAt: str
    updatedAt: str


class AddonClient:
    """
    Client for managing addons in the Workspaces platform.

    Provides methods to create, update, retrieve, and manage addon subscriptions  # noqa: E501
    with proper authentication and error handling.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Addon client with a GraphQL endpoint.

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

    # Addon Query Operations
    async def get_all_addons(self, token: str) -> List[Addon]:
        """
        Retrieves all available addons.

        Args:
            token (str): Authentication token

        Returns:
            List[Addon]: List of all available addons
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAllAddons {
                    getAllAddOns {
                        id
                        name
                        price
                        productID
                        currency
                        duration
                        isActive
                        features {
                            id
                            planId
                            addonId
                            quotaId
                        }
                        addonSubscriptions {
                            id
                            currentSubscriptionId
                            addonId
                            quantity
                            startDate
                            endDate
                            createdAt
                            updatedAt
                        }
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(query)
            return result.get("getAllAddOns", [])
        except Exception as e:
            print(f"Get all addons failed: {str(e)}")
            return []

    async def get_selected_addons(
        self, addon_ids: List[str], token: str
    ) -> List[Addon]:
        """
        Retrieves specific addons by their IDs.

        Args:
            addon_ids (List[str]): List of addon IDs to retrieve
            token (str): Authentication token

        Returns:
            List[Addon]: List of requested addons
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetSelectedAddons($addonIDs: [String!]!) {
                    getSelectedAddons(addonIDs: $addonIDs) {
                        id
                        name
                        price
                        productID
                        currency
                        duration
                        isActive
                        features {
                            id
                            planId
                            addonId
                            quotaId
                        }
                        addonSubscriptions {
                            id
                            currentSubscriptionId
                            addonId
                            quantity
                            startDate
                            endDate
                            createdAt
                            updatedAt
                        }
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"addonIDs": addon_ids}
            result = client.execute(query, variable_values=variables)
            return result.get("getSelectedAddons", [])
        except Exception as e:
            print(f"Get selected addons failed: {str(e)}")
            return []

    # Addon Mutation Operations
    async def create_addon(
        self,
        name: str,
        price: float,
        currency: str,
        duration: str,
        quotas: List[AddonQuotaInput],
        product_id: str,
        token: str,
    ) -> bool:
        """
        Creates a new addon.

        Args:
            name (str): Name of the addon
            price (float): Price of the addon
            currency (str): Currency for pricing
            duration (str): Duration ("monthly" or "yearly")
            quotas (List[AddonQuotaInput]): List of quota configurations
            product_id (str): Product ID the addon belongs to
            token (str): Authentication token

        Returns:
            bool: True if addon creation succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateAddOns($input: createAddOnsInput!) {
                    createAddOns(input: $input)
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
            return result.get("createAddOns", False)
        except Exception as e:
            print(f"Create addon failed: {str(e)}")
            return False

    async def update_addon(
        self,
        addon_id: str,
        quotas: List[AddonQuotaInput],
        token: str,
        name: Optional[str] = None,
        price: Optional[float] = None,
        currency: Optional[str] = None,
        duration: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> bool:
        """
        Updates an existing addon.

        Args:
            addon_id (str): ID of the addon to update
            quotas (List[AddonQuotaInput]): List of quota configurations
            token (str): Authentication token
            name (str, optional): New name for the addon
            price (float, optional): New price for the addon
            currency (str, optional): New currency for the addon
            duration (str, optional): New duration for the addon
            is_active (bool, optional): New active status for the addon

        Returns:
            bool: True if addon update succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateAddonDetails($input: updateAddOnsInput!) {
                    updateAddOnDetails(input: $input)
                }
            """
            )

            update_input = {"id": addon_id, "quotas": quotas}

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
            return result.get("updateAddOnDetails", False)
        except Exception as e:
            print(f"Update addon failed: {str(e)}")
            return False

    async def toggle_addon(self, addon_id: str, status: bool, token: str) -> bool:
        """
        Toggles the active status of an addon.

        Args:
            addon_id (str): ID of the addon to toggle
            status (bool): New active status (True for active, False for inactive)  # noqa: E501
            token (str): Authentication token

        Returns:
            bool: True if toggle operation succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ToggleAddon($id: ID!, $status: Boolean!) {
                    toggleAddOn(id: $id, status: $status)
                }
            """
            )

            variables = {"id": addon_id, "status": status}

            result = client.execute(mutation, variable_values=variables)
            return result.get("toggleAddOn", False)
        except Exception as e:
            print(f"Toggle addon failed: {str(e)}")
            return False


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Addon client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = AddonClient(graphql_endpoint)


def get_client() -> AddonClient:
    """Get the default Addon client."""
    if _default_client is None:
        raise RuntimeError("Addon client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def get_all_addons(*args, **kwargs):
    return await get_client().get_all_addons(*args, **kwargs)


async def get_selected_addons(*args, **kwargs):
    return await get_client().get_selected_addons(*args, **kwargs)


async def create_addon(*args, **kwargs):
    return await get_client().create_addon(*args, **kwargs)


async def update_addon(*args, **kwargs):
    return await get_client().update_addon(*args, **kwargs)


async def toggle_addon(*args, **kwargs):
    return await get_client().toggle_addon(*args, **kwargs)
