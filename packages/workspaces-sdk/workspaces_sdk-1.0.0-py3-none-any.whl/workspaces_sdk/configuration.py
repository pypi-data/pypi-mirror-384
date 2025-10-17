"""
Config Client for Workspaces SDK.

Provides access to configuration management functionality including product usage  # noqa: E501
configurations, operation parameters, and system settings.
"""

from typing import Any, List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers

# Note: This module is named 'configuration' to avoid circular import with the config module  # noqa: E501


# Type definitions for Config system
class Config(TypedDict):
    id: str
    key: str
    value: Any  # JSON value


class ProductUsageOperation(TypedDict):
    operationName: str
    quotaName: str
    value: int
    description: Optional[str]
    tags: Optional[Any]


class ProductUsageOperationInput(TypedDict):
    operationName: str
    quotaName: str
    value: int
    description: Optional[str]
    tags: Optional[Any]


class ProductUsageConfig(TypedDict):
    productId: str
    productName: Optional[str]
    operations: List[ProductUsageOperation]


class ProductUsageConfigFilter(TypedDict, total=False):
    productId: Optional[str]
    productName: Optional[str]
    searchTerm: Optional[str]
    operationName: Optional[str]
    quotaName: Optional[str]


class PaginationInput(TypedDict, total=False):
    limit: Optional[int]
    offset: Optional[int]
    sortBy: Optional[str]
    sortDirection: Optional[str]  # "ASC" or "DESC"


class ProductUsageConfigConnection(TypedDict):
    items: List[ProductUsageConfig]
    totalCount: int
    hasNextPage: bool
    hasPreviousPage: bool


class ConfigClient:
    """
    Client for managing configurations in the Workspaces platform.

    Provides methods to manage system configurations, product usage configurations,  # noqa: E501
    and operation parameters with proper authentication and error handling.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Config client with a GraphQL endpoint.

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

    # Config Query Operations
    async def get_config(self, token: str) -> List[Config]:
        """
        Retrieves all system configurations.

        Args:
            token (str): Authentication token

        Returns:
            List[Config]: List of all system configurations
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetConfig {
                    getConfig {
                        id
                        key
                        value
                    }
                }
            """
            )

            result = client.execute(query)
            return result.get("getConfig", [])
        except Exception as e:
            print(f"Get config failed: {str(e)}")
            return []

    async def get_product_usage_config(
        self, product_id: str, token: str
    ) -> Optional[ProductUsageConfig]:
        """
        Retrieves product usage configuration by product ID.

        Args:
            product_id (str): Product ID to retrieve configuration for
            token (str): Authentication token

        Returns:
            Optional[ProductUsageConfig]: Product usage configuration or None if not found  # noqa: E501
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetProductUsageConfig($productId: String!) {
                    getProductUsageConfig(productId: $productId) {
                        productId
                        productName
                        operations {
                            operationName
                            quotaName
                            value
                            description
                            tags
                        }
                    }
                }
            """
            )

            variables = {"productId": product_id}
            result = client.execute(query, variable_values=variables)
            return result.get("getProductUsageConfig")
        except Exception as e:
            print(f"Get product usage config failed: {str(e)}")
            return None

    async def get_operation_usage(
        self, product_id: str, operation_name: str, token: str
    ) -> Optional[ProductUsageOperation]:
        """
        Retrieves usage parameters for a specific operation.

        Args:
            product_id (str): Product ID
            operation_name (str): Name of the operation
            token (str): Authentication token

        Returns:
            Optional[ProductUsageOperation]: Operation usage configuration or None if not found  # noqa: E501
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetOperationUsage($productId: String!, $operationName: String!) {  # noqa: E501
                    getOperationUsage(productId: $productId, operationName: $operationName) {
                        operationName
                        quotaName
                        value
                        description
                        tags
                    }
                }
            """
            )

            variables = {
                "productId": product_id,
                "operationName": operation_name,
            }
            result = client.execute(query, variable_values=variables)
            return result.get("getOperationUsage")
        except Exception as e:
            print(f"Get operation usage failed: {str(e)}")
            return None

    async def get_all_product_usage_configs(
        self,
        token: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[ProductUsageConfig]:
        """
        Retrieves all product usage configurations with optional pagination.

        Args:
            token (str): Authentication token
            limit (int, optional): Number of items to return
            offset (int, optional): Number of items to skip

        Returns:
            List[ProductUsageConfig]: List of product usage configurations
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAllProductUsageConfigs($limit: Int, $offset: Int) {
                    getAllProductUsageConfigs(limit: $limit, offset: $offset) {
                        productId
                        productName
                        operations {
                            operationName
                            quotaName
                            value
                            description
                            tags
                        }
                    }
                }
            """
            )

            variables = {}
            if limit is not None:
                variables["limit"] = limit
            if offset is not None:
                variables["offset"] = offset

            result = client.execute(query, variable_values=variables)
            return result.get("getAllProductUsageConfigs", [])
        except Exception as e:
            print(f"Get all product usage configs failed: {str(e)}")
            return []

    async def search_product_usage_configs(
        self,
        token: str,
        filter_params: Optional[ProductUsageConfigFilter] = None,
        pagination: Optional[PaginationInput] = None,
    ) -> ProductUsageConfigConnection:
        """
        Searches product usage configurations with pagination and filtering.

        Args:
            token (str): Authentication token
            filter_params (ProductUsageConfigFilter, optional): Filter parameters  # noqa: E501
            pagination (PaginationInput, optional): Pagination parameters

        Returns:
            ProductUsageConfigConnection: Paginated search results
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query SearchProductUsageConfigs(
                    $filter: ProductUsageConfigFilter
                    $pagination: PaginationInput
                ) {
                    searchProductUsageConfigs(filter: $filter, pagination: $pagination) {  # noqa: E501
                        items {
                            productId
                            productName
                            operations {
                                operationName
                                quotaName
                                value
                                description
                                tags
                            }
                        }
                        totalCount
                        hasNextPage
                        hasPreviousPage
                    }
                }
            """
            )

            variables = {}
            if filter_params:
                variables["filter"] = filter_params
            if pagination:
                variables["pagination"] = pagination

            result = client.execute(query, variable_values=variables)
            return result.get(
                "searchProductUsageConfigs",
                {
                    "items": [],
                    "totalCount": 0,
                    "hasNextPage": False,
                    "hasPreviousPage": False,
                },
            )
        except Exception as e:
            print(f"Search product usage configs failed: {str(e)}")
            return {
                "items": [],
                "totalCount": 0,
                "hasNextPage": False,
                "hasPreviousPage": False,
            }

    # Config Mutation Operations
    async def create_config(self, key: str, value: Any, token: str) -> Optional[Config]:
        """
        Creates a new system configuration.

        Args:
            key (str): Configuration key
            value (Any): Configuration value (JSON serializable)
            token (str): Authentication token

        Returns:
            Optional[Config]: Created configuration or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateConfig($key: String!, $value: JSON!) {
                    createConfig(key: $key, value: $value) {
                        id
                        key
                        value
                    }
                }
            """
            )

            variables = {"key": key, "value": value}

            result = client.execute(mutation, variable_values=variables)
            return result.get("createConfig")
        except Exception as e:
            print(f"Create config failed: {str(e)}")
            return None

    async def update_config(self, key: str, value: Any, token: str) -> Optional[Config]:
        """
        Updates an existing system configuration.

        Args:
            key (str): Configuration key to update
            value (Any): New configuration value (JSON serializable)
            token (str): Authentication token

        Returns:
            Optional[Config]: Updated configuration or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateConfig($key: String!, $value: JSON!) {
                    updateConfig(key: $key, value: $value) {
                        id
                        key
                        value
                    }
                }
            """
            )

            variables = {"key": key, "value": value}

            result = client.execute(mutation, variable_values=variables)
            return result.get("updateConfig")
        except Exception as e:
            print(f"Update config failed: {str(e)}")
            return None

    async def delete_config(self, key: str, token: str) -> bool:
        """
        Deletes a system configuration.

        Args:
            key (str): Configuration key to delete
            token (str): Authentication token

        Returns:
            bool: True if deletion succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DeleteConfig($key: String!) {
                    deleteConfig(key: $key)
                }
            """
            )

            variables = {"key": key}

            result = client.execute(mutation, variable_values=variables)
            return result.get("deleteConfig", False)
        except Exception as e:
            print(f"Delete config failed: {str(e)}")
            return False

    async def set_product_usage_config(
        self,
        product_id: str,
        operations: List[ProductUsageOperationInput],
        token: str,
        product_name: Optional[str] = None,
    ) -> Optional[ProductUsageConfig]:
        """
        Creates or updates product usage configuration.

        Args:
            product_id (str): Product ID
            operations (List[ProductUsageOperationInput]): List of operation configurations  # noqa: E501
            token (str): Authentication token
            product_name (str, optional): Product name

        Returns:
            Optional[ProductUsageConfig]: Created/updated configuration or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation SetProductUsageConfig(
                    $productId: String!
                    $productName: String
                    $operations: [ProductUsageOperationInput!]!
                ) {
                    setProductUsageConfig(
                        productId: $productId
                        productName: $productName
                        operations: $operations
                    ) {
                        productId
                        productName
                        operations {
                            operationName
                            quotaName
                            value
                            description
                            tags
                        }
                    }
                }
            """
            )

            variables = {"productId": product_id, "operations": operations}
            if product_name:
                variables["productName"] = product_name

            result = client.execute(mutation, variable_values=variables)
            return result.get("setProductUsageConfig")
        except Exception as e:
            print(f"Set product usage config failed: {str(e)}")
            return None

    async def set_operation_usage(
        self,
        product_id: str,
        operation_name: str,
        quota_name: str,
        value: int,
        token: str,
        description: Optional[str] = None,
        tags: Optional[Any] = None,
    ) -> Optional[ProductUsageOperation]:
        """
        Adds or updates a single operation's usage configuration.

        Args:
            product_id (str): Product ID
            operation_name (str): Operation name
            quota_name (str): Quota name
            value (int): Usage value/cost
            token (str): Authentication token
            description (str, optional): Operation description
            tags (Any, optional): Additional tags

        Returns:
            Optional[ProductUsageOperation]: Created/updated operation configuration or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation SetOperationUsage(
                    $productId: String!
                    $operationName: String!
                    $quotaName: String!
                    $value: Int!
                    $description: String
                    $tags: JSON
                ) {
                    setOperationUsage(
                        productId: $productId
                        operationName: $operationName
                        quotaName: $quotaName
                        value: $value
                        description: $description
                        tags: $tags
                    ) {
                        operationName
                        quotaName
                        value
                        description
                        tags
                    }
                }
            """
            )

            variables = {
                "productId": product_id,
                "operationName": operation_name,
                "quotaName": quota_name,
                "value": value,
            }
            if description:
                variables["description"] = description
            if tags:
                variables["tags"] = tags

            result = client.execute(mutation, variable_values=variables)
            return result.get("setOperationUsage")
        except Exception as e:
            print(f"Set operation usage failed: {str(e)}")
            return None

    async def remove_operation_usage(
        self, product_id: str, operation_name: str, token: str
    ) -> bool:
        """
        Removes an operation from product usage configuration.

        Args:
            product_id (str): Product ID
            operation_name (str): Operation name to remove
            token (str): Authentication token

        Returns:
            bool: True if removal succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation RemoveOperationUsage($productId: String!, $operationName: String!) {  # noqa: E501
                    removeOperationUsage(productId: $productId, operationName: $operationName)
                }
            """
            )

            variables = {
                "productId": product_id,
                "operationName": operation_name,
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("removeOperationUsage", False)
        except Exception as e:
            print(f"Remove operation usage failed: {str(e)}")
            return False


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Config client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = ConfigClient(graphql_endpoint)


def get_client() -> ConfigClient:
    """Get the default Config client."""
    if _default_client is None:
        raise RuntimeError("Config client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def get_config(*args, **kwargs):
    return await get_client().get_config(*args, **kwargs)


async def get_product_usage_config(*args, **kwargs):
    return await get_client().get_product_usage_config(*args, **kwargs)


async def get_operation_usage(*args, **kwargs):
    return await get_client().get_operation_usage(*args, **kwargs)


async def get_all_product_usage_configs(*args, **kwargs):
    return await get_client().get_all_product_usage_configs(*args, **kwargs)


async def search_product_usage_configs(*args, **kwargs):
    return await get_client().search_product_usage_configs(*args, **kwargs)


async def create_config(*args, **kwargs):
    return await get_client().create_config(*args, **kwargs)


async def update_config(*args, **kwargs):
    return await get_client().update_config(*args, **kwargs)


async def delete_config(*args, **kwargs):
    return await get_client().delete_config(*args, **kwargs)


async def set_product_usage_config(*args, **kwargs):
    return await get_client().set_product_usage_config(*args, **kwargs)


async def set_operation_usage(*args, **kwargs):
    return await get_client().set_operation_usage(*args, **kwargs)


async def remove_operation_usage(*args, **kwargs):
    return await get_client().remove_operation_usage(*args, **kwargs)
