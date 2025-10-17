"""
Organization Client for Workspaces SDK.

Provides access to organization management functionality including creating,
updating, and managing organizations.
"""

from typing import List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Organization system
class CreateOrganizationInput(TypedDict):
    name: str
    domain: Optional[str]
    contactEmail: Optional[str]
    website: Optional[str]
    address: Optional[str]
    tenantID: Optional[str]


class UpdateOrganizationInput(TypedDict):
    id: str
    name: Optional[str]


class User(TypedDict):
    id: str
    name: Optional[str]
    email: str


class Workspace(TypedDict):
    id: str
    name: str
    type: str
    status: str


class Organization(TypedDict):
    id: str
    name: str
    type: str
    status: str
    ownerId: Optional[str]
    workspaces: List[Workspace]
    createdAt: str
    updatedAt: Optional[str]
    createdBy: User


class OrganizationClient:
    """
    Client for managing organizations in the Workspaces platform.

    Provides methods to create, update, retrieve, and delete organizations
    with proper authentication and error handling.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Organization client with a GraphQL endpoint.

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

    # Organization Query Operations
    async def get_organizations(
        self,
        token: str,
        organization_id: Optional[str] = None,
        name: Optional[str] = None,
        product_id: Optional[str] = None,
    ) -> List[Organization]:
        """
        Retrieves organizations based on filters.

        Args:
            token (str): Authentication token
            organization_id (str, optional): Organization ID to filter
            name (str, optional): Organization name to filter
            product_id (str, optional): Product ID to filter

        Returns:
            List[Organization]: List of organizations matching the filters
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetOrganization($id: ID, $name: String, $productID: String) {  # noqa: E501
                    organization(id: $id, name: $name, productID: $productID) {
                        id
                        name
                        type
                        status
                        ownerId
                        workspaces {
                            id
                            name
                            type
                            status
                        }
                        createdAt
                        updatedAt
                        createdBy {
                            id
                            name
                            email
                        }
                    }
                }
            """
            )

            variables = {
                "id": organization_id,
                "name": name,
                "productID": product_id,
            }

            result = client.execute(query, variable_values=variables)
            return result.get("organization", [])
        except Exception as e:
            print(f"Get organizations failed: {str(e)}")
            return []

    # Organization Mutation Operations
    async def create_organization(
        self,
        name: str,
        token: str,
        domain: Optional[str] = None,
        contact_email: Optional[str] = None,
        website: Optional[str] = None,
        address: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Optional[Organization]:
        """
        Creates a new organization.

        Args:
            name (str): Organization name
            token (str): Authentication token
            domain (str, optional): Organization domain
            contact_email (str, optional): Contact email
            website (str, optional): Organization website
            address (str, optional): Organization address
            tenant_id (str, optional): Tenant ID

        Returns:
            Optional[Organization]: The created organization or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateOrganization($details: CreateOrganizationInput!) {  # noqa: E501
                    createOrganization(details: $details) {
                        id
                        name
                        type
                        status
                        ownerId
                        workspaces {
                            id
                            name
                            type
                            status
                        }
                        createdAt
                        updatedAt
                        createdBy {
                            id
                            name
                            email
                        }
                    }
                }
            """
            )

            input_data = {"name": name}

            if domain:
                input_data["domain"] = domain
            if contact_email:
                input_data["contactEmail"] = contact_email
            if website:
                input_data["website"] = website
            if address:
                input_data["address"] = address
            if tenant_id:
                input_data["tenantID"] = tenant_id

            variables = {"details": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get("createOrganization")
        except Exception as e:
            print(f"Create organization failed: {str(e)}")
            return None

    async def update_organization(
        self, organization_id: str, name: str, token: str
    ) -> Optional[Organization]:
        """
        Updates an existing organization.

        Args:
            organization_id (str): ID of the organization to update
            name (str): New organization name
            token (str): Authentication token

        Returns:
            Optional[Organization]: The updated organization or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateOrganization($details: UpdateOrganizationInput!) {  # noqa: E501
                    updateOrganization(details: $details) {
                        id
                        name
                        type
                        status
                        ownerId
                        workspaces {
                            id
                            name
                            type
                            status
                        }
                        createdAt
                        updatedAt
                        createdBy {
                            id
                            name
                            email
                        }
                    }
                }
            """
            )

            update_input = {"id": organization_id, "name": name}

            variables = {"details": update_input}

            result = client.execute(mutation, variable_values=variables)
            return result.get("updateOrganization")
        except Exception as e:
            print(f"Update organization failed: {str(e)}")
            return None

    async def delete_organizations(
        self, organization_ids: List[str], token: str
    ) -> List[Organization]:
        """
        Deletes multiple organizations.

        Args:
            organization_ids (List[str]): List of organization IDs to delete
            token (str): Authentication token

        Returns:
            List[Organization]: List of deleted organizations
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DeleteOrganizations($idList: [ID!]!) {
                    deleteOrganizations(idList: $idList) {
                        id
                        name
                        type
                        status
                        ownerId
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"idList": organization_ids}

            result = client.execute(mutation, variable_values=variables)
            return result.get("deleteOrganizations", [])
        except Exception as e:
            print(f"Delete organizations failed: {str(e)}")
            return []


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Organization client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = OrganizationClient(graphql_endpoint)


def get_client() -> OrganizationClient:
    """Get the default Organization client."""
    if _default_client is None:
        raise RuntimeError(
            "Organization client not initialized. Call initialize() first."
        )
    return _default_client


# Convenience functions that use the default client
async def get_organizations(*args, **kwargs):
    return await get_client().get_organizations(*args, **kwargs)


async def create_organization(*args, **kwargs):
    return await get_client().create_organization(*args, **kwargs)


async def update_organization(*args, **kwargs):
    return await get_client().update_organization(*args, **kwargs)


async def delete_organizations(*args, **kwargs):
    return await get_client().delete_organizations(*args, **kwargs)
