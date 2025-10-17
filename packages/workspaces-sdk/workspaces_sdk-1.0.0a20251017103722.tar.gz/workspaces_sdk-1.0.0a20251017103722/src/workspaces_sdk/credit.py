"""
Credit Client for Workspaces SDK.

Provides access to credit transaction management functionality including credit
spending, transaction tracking, and credit cost calculations.
"""

from typing import Any, List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Credit system
class AddOnInputPayment(TypedDict):
    id: str
    quantity: Optional[int]


class SpendCreditsInput(TypedDict):
    billingAccountId: str
    planId: Optional[str]
    storeItemId: Optional[str]
    addOnIds: Optional[List[AddOnInputPayment]]
    isAnnual: Optional[bool]


class CreditTransaction(TypedDict):
    id: str
    status: str  # "pending", "success", "failed", "refund"
    type: str  # "purchase", "usage", "adjustment"
    amount: float
    billingAccountId: str
    billingAccount: Any  # BillingAccount object
    transactionId: Optional[str]
    transaction: Optional[Any]  # Transaction object
    productId: str
    entityId: Optional[str]
    entityType: Optional[str]
    createdAt: str
    updatedAt: str


class CreditRate(TypedDict):
    id: str
    rateUSD: float
    effectiveFrom: str
    createdAt: str
    updatedAt: str


class CreditCost(TypedDict):
    amount: float


class SpendCreditResponse(TypedDict):
    creditTransactionID: str


class PaginatedCreditTransactions(TypedDict):
    creditTransactions: List[CreditTransaction]
    totalCount: int
    hasMore: bool
    page: int
    pageSize: int


class CreditClient:
    """
    Client for managing credits in the Workspaces platform.

    Provides methods to spend credits, retrieve credit transactions, and calculate  # noqa: E501
    credit costs with proper authentication and error handling.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Credit client with a GraphQL endpoint.

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

    # Credit Query Operations
    async def get_billing_account_credit_transactions(
        self,
        billing_account_id: str,
        days: int,
        token: str,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> PaginatedCreditTransactions:
        """
        Retrieves credit transactions for a billing account within a specified time period.  # noqa: E501

        Args:
            billing_account_id (str): ID of the billing account
            days (int): Number of days to look back for transactions
            token (str): Authentication token
            page (int, optional): Page number for pagination
            page_size (int, optional): Number of items per page

        Returns:
            PaginatedCreditTransactions: Paginated credit transactions result
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetBillingAccountCreditTransactions(
                    $billingAccountID: ID!
                    $days: Int!
                    $page: Int
                    $pageSize: Int
                ) {
                    getBillingAccountCreditTransactions(
                        billingAccountID: $billingAccountID
                        days: $days
                        page: $page
                        pageSize: $pageSize
                    ) {
                        creditTransactions {
                            id
                            status
                            type
                            amount
                            billingAccountId
                            billingAccount {
                                id
                                accountName
                            }
                            transactionId
                            transaction {
                                id
                                amount
                                status
                            }
                            productId
                            entityId
                            entityType
                            createdAt
                            updatedAt
                        }
                        totalCount
                        hasMore
                        page
                        pageSize
                    }
                }
            """
            )

            variables = {"billingAccountID": billing_account_id, "days": days}

            if page is not None:
                variables["page"] = page
            if page_size is not None:
                variables["pageSize"] = page_size

            result = client.execute(query, variable_values=variables)
            return result.get(
                "getBillingAccountCreditTransactions",
                {
                    "creditTransactions": [],
                    "totalCount": 0,
                    "hasMore": False,
                    "page": 1,
                    "pageSize": 10,
                },
            )
        except Exception as e:
            print(f"Get billing account credit transactions failed: {str(e)}")
            return {
                "creditTransactions": [],
                "totalCount": 0,
                "hasMore": False,
                "page": 1,
                "pageSize": 10,
            }

    async def get_credit_transaction_details(
        self, credit_transaction_id: str, token: str
    ) -> Optional[CreditTransaction]:
        """
        Retrieves detailed information for a specific credit transaction.

        Args:
            credit_transaction_id (str): ID of the credit transaction
            token (str): Authentication token

        Returns:
            Optional[CreditTransaction]: Credit transaction details or None if not found  # noqa: E501
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetCreditTransactionDetails($creditTransactionID: ID!) {
                    getCreditTransactionDetails(creditTransactionID: $creditTransactionID) {  # noqa: E501
                        id
                        status
                        type
                        amount
                        billingAccountId
                        billingAccount {
                            id
                            accountName
                            creditAmount
                        }
                        transactionId
                        transaction {
                            id
                            amount
                            status
                            type
                        }
                        productId
                        entityId
                        entityType
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"creditTransactionID": credit_transaction_id}
            result = client.execute(query, variable_values=variables)
            return result.get("getCreditTransactionDetails")
        except Exception as e:
            print(f"Get credit transaction details failed: {str(e)}")
            return None

    async def get_cost_of_credits(
        self, credit_amount: float, currency: str, token: str
    ) -> Optional[CreditCost]:
        """
        Calculates the cost of a specific amount of credits in the given currency.

        Args:
            credit_amount (float): Amount of credits to calculate cost for
            currency (str): Currency code (e.g., "USD", "EUR")
            token (str): Authentication token

        Returns:
            Optional[CreditCost]: Credit cost information or None if calculation fails  # noqa: E501
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetCostOfCredits($creditAmount: Float!, $currency: String!) {  # noqa: E501
                    getCostOfCredits(creditAmount: $creditAmount, currency: $currency) {
                        amount
                    }
                }
            """
            )

            variables = {"creditAmount": credit_amount, "currency": currency}

            result = client.execute(query, variable_values=variables)
            return result.get("getCostOfCredits")
        except Exception as e:
            print(f"Get cost of credits failed: {str(e)}")
            return None

    # Credit Mutation Operations
    async def spend_credits(
        self,
        billing_account_id: str,
        token: str,
        plan_id: Optional[str] = None,
        store_item_id: Optional[str] = None,
        addon_ids: Optional[List[AddOnInputPayment]] = None,
        is_annual: Optional[bool] = None,
    ) -> Optional[SpendCreditResponse]:
        """
        Spend credits from a billing account for various services or purchases.

        Args:
            billing_account_id (str): ID of the billing account to spend credits from
            token (str): Authentication token
            plan_id (str, optional): ID of the plan being purchased
            store_item_id (str, optional): ID of the store item being purchased
            addon_ids (List[AddOnInputPayment], optional): List of add-ons being purchased  # noqa: E501
            is_annual (bool, optional): Whether the purchase is for annual subscription

        Returns:
            Optional[SpendCreditResponse]: Response with credit transaction ID or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation SpendCredits($input: SpendCreditsInput!) {
                    spendCredits(input: $input) {
                        creditTransactionID
                    }
                }
            """
            )

            input_data = {"billingAccountId": billing_account_id}

            if plan_id is not None:
                input_data["planId"] = plan_id
            if store_item_id is not None:
                input_data["storeItemId"] = store_item_id
            if addon_ids is not None:
                input_data["addOnIds"] = addon_ids
            if is_annual is not None:
                input_data["isAnnual"] = is_annual

            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get("spendCredits")
        except Exception as e:
            print(f"Spend credits failed: {str(e)}")
            return None

    # Helper method for creating addon payment input
    def create_addon_payment_input(
        self, addon_id: str, quantity: Optional[int] = None
    ) -> AddOnInputPayment:
        """
        Helper method to create an AddOnInputPayment object.

        Args:
            addon_id (str): ID of the addon
            quantity (int, optional): Quantity of the addon

        Returns:
            AddOnInputPayment: Formatted addon payment input
        """
        addon_input = {"id": addon_id}
        if quantity is not None:
            addon_input["quantity"] = quantity
        return addon_input


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Credit client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = CreditClient(graphql_endpoint)


def get_client() -> CreditClient:
    """Get the default Credit client."""
    if _default_client is None:
        raise RuntimeError("Credit client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def get_billing_account_credit_transactions(*args, **kwargs):
    return await get_client().get_billing_account_credit_transactions(*args, **kwargs)


async def get_credit_transaction_details(*args, **kwargs):
    return await get_client().get_credit_transaction_details(*args, **kwargs)


async def get_cost_of_credits(*args, **kwargs):
    return await get_client().get_cost_of_credits(*args, **kwargs)


async def spend_credits(*args, **kwargs):
    return await get_client().spend_credits(*args, **kwargs)


def create_addon_payment_input(*args, **kwargs):
    if _default_client is None:
        raise RuntimeError("Credit client not initialized. Call initialize() first.")
    return _default_client.create_addon_payment_input(*args, **kwargs)
