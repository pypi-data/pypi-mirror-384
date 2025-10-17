"""
Billing Client for Workspaces SDK.

Provides access to billing account management functionality including creating,
updating, and managing billing accounts and their associated data.
"""

from typing import Any, List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Billing system
class CreateBillingAccountInput(TypedDict):
    billingFrequency: str  # "daily", "weekly", "monthly", "quarterly", "yearly"
    accountName: str
    billingAddress: str
    city: str
    state: str
    country: str
    postalCode: str
    contactEmail: str
    contactPhoneNumber: Optional[str]


class UpdateBillingAccountInput(TypedDict):
    id: str
    billingFrequency: Optional[str]
    accountName: Optional[str]
    billingAddress: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    postalCode: Optional[str]
    contactEmail: Optional[str]
    contactPhoneNumber: Optional[str]


class CreditTransaction(TypedDict):
    id: str
    status: str
    type: str
    amount: float
    billingAccountId: str
    transactionId: Optional[str]
    productId: str
    entityId: Optional[str]
    entityType: Optional[str]
    createdAt: str
    updatedAt: str


class Workspace(TypedDict):
    id: str
    name: str


class Subscription(TypedDict):
    id: str
    status: str
    startDate: str
    endDate: str


class PaymentMethod(TypedDict):
    id: str
    type: str
    details: Any


class Transaction(TypedDict):
    id: str
    amount: float
    status: str
    type: str
    createdAt: str


class Invoice(TypedDict):
    id: str
    totalAmount: float
    status: str
    taxAmount: float
    periodStart: str
    periodEnd: str
    createdAt: str


class BillingAccount(TypedDict):
    id: str
    accountName: str
    billingAddress: str
    creditTransactions: List[CreditTransaction]
    creditAmount: float
    city: str
    state: str
    country: str
    postalCode: str
    contactEmail: str
    contactPhoneNumber: Optional[str]
    workspace: Workspace
    workspaceId: str
    subscriptions: List[Subscription]
    paymentMethods: List[PaymentMethod]
    transactions: List[Transaction]
    invoices: List[Invoice]
    billingFrequency: str
    nextBillingDate: Optional[str]
    billingStartDate: Optional[str]
    createdAt: str
    updatedAt: str


class BillingClient:
    """
    Client for managing billing accounts in the Workspaces platform.

    Provides methods to create, update, retrieve, and manage billing accounts
    with proper authentication and error handling.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Billing client with a GraphQL endpoint.

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

    # Billing Query Operations
    async def get_workspace_billing_accounts(self, token: str) -> List[BillingAccount]:
        """
        Retrieves all billing accounts for the current workspace.

        Args:
            token (str): Authentication token

        Returns:
            List[BillingAccount]: List of billing accounts for the workspace
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetWorkspaceBillingAccounts {
                    getWorkspaceBillingAccounts {
                        id
                        accountName
                        billingAddress
                        creditTransactions {
                            id
                            status
                            type
                            amount
                            billingAccountId
                            transactionId
                            productId
                            entityId
                            entityType
                            createdAt
                            updatedAt
                        }
                        creditAmount
                        city
                        state
                        country
                        postalCode
                        contactEmail
                        contactPhoneNumber
                        workspace {
                            id
                            name
                        }
                        workspaceId
                        subscriptions {
                            id
                            status
                            startDate
                            endDate
                        }
                        paymentMethods {
                            id
                            type
                            details
                        }
                        transactions {
                            id
                            amount
                            status
                            type
                            createdAt
                        }
                        invoices {
                            id
                            totalAmount
                            status
                            taxAmount
                            periodStart
                            periodEnd
                            createdAt
                        }
                        billingFrequency
                        nextBillingDate
                        billingStartDate
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(query)
            return result.get("getWorkspaceBillingAccounts", [])
        except Exception as e:
            print(f"Get workspace billing accounts failed: {str(e)}")
            return []

    async def get_billing_account_details(
        self, account_id: str, token: str
    ) -> Optional[BillingAccount]:
        """
        Retrieves detailed information for a specific billing account.

        Args:
            account_id (str): ID of the billing account
            token (str): Authentication token

        Returns:
            Optional[BillingAccount]: Billing account details or None if not found  # noqa: E501
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetBillingAccountDetails($id: ID!) {
                    getBillingAccountDetails(id: $id) {
                        id
                        accountName
                        billingAddress
                        creditTransactions {
                            id
                            status
                            type
                            amount
                            billingAccountId
                            transactionId
                            productId
                            entityId
                            entityType
                            createdAt
                            updatedAt
                        }
                        creditAmount
                        city
                        state
                        country
                        postalCode
                        contactEmail
                        contactPhoneNumber
                        workspace {
                            id
                            name
                        }
                        workspaceId
                        subscriptions {
                            id
                            status
                            startDate
                            endDate
                        }
                        paymentMethods {
                            id
                            type
                            details
                        }
                        transactions {
                            id
                            amount
                            status
                            type
                            createdAt
                        }
                        invoices {
                            id
                            totalAmount
                            status
                            taxAmount
                            periodStart
                            periodEnd
                            createdAt
                        }
                        billingFrequency
                        nextBillingDate
                        billingStartDate
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"id": account_id}
            result = client.execute(query, variable_values=variables)
            return result.get("getBillingAccountDetails")
        except Exception as e:
            print(f"Get billing account details failed: {str(e)}")
            return None

    async def get_filtered_billing_accounts(self, token: str) -> List[BillingAccount]:
        """
        Retrieves filtered billing accounts based on specific criteria.

        Args:
            token (str): Authentication token

        Returns:
            List[BillingAccount]: List of filtered billing accounts
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetFilteredBillingAccount {
                    getFilteredBillingAccount {
                        id
                        accountName
                        billingAddress
                        creditTransactions {
                            id
                            status
                            type
                            amount
                            billingAccountId
                            transactionId
                            productId
                            entityId
                            entityType
                            createdAt
                            updatedAt
                        }
                        creditAmount
                        city
                        state
                        country
                        postalCode
                        contactEmail
                        contactPhoneNumber
                        workspace {
                            id
                            name
                        }
                        workspaceId
                        billingFrequency
                        nextBillingDate
                        billingStartDate
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(query)
            return result.get("getFilteredBillingAccount", [])
        except Exception as e:
            print(f"Get filtered billing accounts failed: {str(e)}")
            return []

    # Billing Mutation Operations
    async def create_billing_account(
        self,
        billing_frequency: str,
        account_name: str,
        billing_address: str,
        city: str,
        state: str,
        country: str,
        postal_code: str,
        contact_email: str,
        token: str,
        contact_phone_number: Optional[str] = None,
    ) -> bool:
        """
        Creates a new billing account.

        Args:
            billing_frequency (str): Billing frequency ("daily", "weekly", "monthly", "quarterly", "yearly")  # noqa: E501
            account_name (str): Name of the billing account
            billing_address (str): Billing address
            city (str): City
            state (str): State or province
            country (str): Country
            postal_code (str): Postal or ZIP code
            contact_email (str): Contact email address
            token (str): Authentication token
            contact_phone_number (str, optional): Contact phone number

        Returns:
            bool: True if billing account creation succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateBillingAccount($input: CreateBillingAccountInput!) {  # noqa: E501
                    createBillingAccount(input: $input)
                }
            """
            )

            input_data = {
                "billingFrequency": billing_frequency,
                "accountName": account_name,
                "billingAddress": billing_address,
                "city": city,
                "state": state,
                "country": country,
                "postalCode": postal_code,
                "contactEmail": contact_email,
            }

            if contact_phone_number:
                input_data["contactPhoneNumber"] = contact_phone_number

            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get("createBillingAccount", False)
        except Exception as e:
            print(f"Create billing account failed: {str(e)}")
            return False

    async def update_billing_account(
        self,
        account_id: str,
        token: str,
        billing_frequency: Optional[str] = None,
        account_name: Optional[str] = None,
        billing_address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone_number: Optional[str] = None,
    ) -> bool:
        """
        Updates an existing billing account.

        Args:
            account_id (str): ID of the billing account to update
            token (str): Authentication token
            billing_frequency (str, optional): New billing frequency
            account_name (str, optional): New account name
            billing_address (str, optional): New billing address
            city (str, optional): New city
            state (str, optional): New state
            country (str, optional): New country
            postal_code (str, optional): New postal code
            contact_email (str, optional): New contact email
            contact_phone_number (str, optional): New contact phone number

        Returns:
            bool: True if billing account update succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateBillingAccount($input: UpdateBillingAccountInput!) {  # noqa: E501
                    updateBillingAccount(input: $input)
                }
            """
            )

            update_input = {"id": account_id}

            if billing_frequency is not None:
                update_input["billingFrequency"] = billing_frequency
            if account_name is not None:
                update_input["accountName"] = account_name
            if billing_address is not None:
                update_input["billingAddress"] = billing_address
            if city is not None:
                update_input["city"] = city
            if state is not None:
                update_input["state"] = state
            if country is not None:
                update_input["country"] = country
            if postal_code is not None:
                update_input["postalCode"] = postal_code
            if contact_email is not None:
                update_input["contactEmail"] = contact_email
            if contact_phone_number is not None:
                update_input["contactPhoneNumber"] = contact_phone_number

            variables = {"input": update_input}

            result = client.execute(mutation, variable_values=variables)
            return result.get("updateBillingAccount", False)
        except Exception as e:
            print(f"Update billing account failed: {str(e)}")
            return False


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Billing client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = BillingClient(graphql_endpoint)


def get_client() -> BillingClient:
    """Get the default Billing client."""
    if _default_client is None:
        raise RuntimeError("Billing client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def get_workspace_billing_accounts(*args, **kwargs):
    return await get_client().get_workspace_billing_accounts(*args, **kwargs)


async def get_billing_account_details(*args, **kwargs):
    return await get_client().get_billing_account_details(*args, **kwargs)


async def get_filtered_billing_accounts(*args, **kwargs):
    return await get_client().get_filtered_billing_accounts(*args, **kwargs)


async def create_billing_account(*args, **kwargs):
    return await get_client().create_billing_account(*args, **kwargs)


async def update_billing_account(*args, **kwargs):
    return await get_client().update_billing_account(*args, **kwargs)
