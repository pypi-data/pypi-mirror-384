"""
Payment Client for Workspaces SDK.

Provides access to payment processing functionality including transactions,
invoices, payment methods, and order creation for Razorpay and Stripe.
"""

from typing import Any, List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Payment system
class AddOnInputPayment(TypedDict):
    id: str
    quantity: Optional[int]


class CreateTransactionInput(TypedDict):
    billingAccountId: str
    paymentMethodId: str
    description: Optional[str]
    type: str  # "payment", "refund", "adjustment"
    discountId: Optional[str]


class CreateRazorpayOrderInput(TypedDict):
    billingAccountId: str
    planId: Optional[str]
    storeItemId: Optional[str]
    creditAmount: Optional[int]
    currencySelected: str
    addOnIds: Optional[List[AddOnInputPayment]]
    recurrence: Optional[bool]


class CreateStripeOrderInput(TypedDict):
    billingAccountId: str
    planId: Optional[str]
    storeItemId: Optional[str]
    creditAmount: Optional[int]
    currencySelected: str
    addOnIds: Optional[List[AddOnInputPayment]]
    recurrence: Optional[bool]


class CreateRazorpayOrderResponse(TypedDict):
    amount: str
    currency: str
    orderID: str
    key: str
    transactionID: str


class CreateStripeOrderResponse(TypedDict):
    clientSecret: str
    transactionID: str
    key: str
    amount: str


class PollingStatus(TypedDict):
    status: str


class PDF(TypedDict):
    pdf: str


class PaymentMethod(TypedDict):
    id: str
    billingAccountId: str
    type: str  # "credit_card", "debit_card", "payment_gateway", etc.
    details: Any
    transactions: List[Any]  # List of Transaction objects
    createdAt: str
    updatedAt: str


class InvoiceTransaction(TypedDict):
    id: str
    invoiceId: str
    transactionId: str


class CreditRate(TypedDict):
    id: str
    rateUSD: float
    effectiveFrom: str
    createdAt: str
    updatedAt: str


class Transaction(TypedDict):
    id: str
    billingAccountId: str
    paymentMethodId: str
    creditRateId: Optional[str]
    creditTransactionId: Optional[CreditRate]
    amount: float
    currency: str
    description: Optional[str]
    status: str  # "pending", "success", "failed"
    type: str  # "payment", "refund", "adjustment"
    invoiceLink: List[InvoiceTransaction]
    discountId: Optional[str]
    metadata: Any
    createdAt: str
    updatedAt: str


class Invoice(TypedDict):
    id: str
    billingAccountId: str
    transactionsLink: List[InvoiceTransaction]
    totalAmount: float
    currency: str
    periodStart: str
    periodEnd: str
    status: str  # "draft", "issued", "paid", "void"
    taxAmount: float
    taxDetails: Any
    createdAt: str
    updatedAt: str


class PaginatedTransactions(TypedDict):
    transactions: List[Transaction]
    totalCount: int
    hasMore: bool
    page: int
    pageSize: int


class PaginatedInvoices(TypedDict):
    invoices: List[Invoice]
    totalCount: int
    hasMore: bool
    page: int
    pageSize: int


class PaymentClient:
    """
    Client for managing payments in the Workspaces platform.

    Provides methods to create transactions, manage invoices, process payments
    through Razorpay and Stripe, and handle payment-related operations.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Payment client with a GraphQL endpoint.

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

    # Payment Query Operations
    async def get_billing_account_transactions(
        self,
        billing_account_id: str,
        days: int,
        token: str,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> PaginatedTransactions:
        """
        Retrieves transactions for a billing account within a specified time period.  # noqa: E501

        Args:
            billing_account_id (str): ID of the billing account
            days (int): Number of days to look back for transactions
            token (str): Authentication token
            page (int, optional): Page number for pagination
            page_size (int, optional): Number of items per page

        Returns:
            PaginatedTransactions: Paginated transactions result
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetBillingAccountTransactions(
                    $billingAccountID: ID!
                    $days: Int!
                    $page: Int
                    $pageSize: Int
                ) {
                    getBillingAccountTransactions(
                        billingAccountID: $billingAccountID
                        days: $days
                        page: $page
                        pageSize: $pageSize
                    ) {
                        transactions {
                            id
                            billingAccountId
                            paymentMethodId
                            creditRateId
                            creditTransactionId {
                                id
                                rateUSD
                                effectiveFrom
                                createdAt
                                updatedAt
                            }
                            amount
                            currency
                            description
                            status
                            type
                            invoiceLink {
                                id
                                invoiceId
                                transactionId
                            }
                            discountId
                            metadata
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
                "getBillingAccountTransactions",
                {
                    "transactions": [],
                    "totalCount": 0,
                    "hasMore": False,
                    "page": 1,
                    "pageSize": 10,
                },
            )
        except Exception as e:
            print(f"Get billing account transactions failed: {str(e)}")
            return {
                "transactions": [],
                "totalCount": 0,
                "hasMore": False,
                "page": 1,
                "pageSize": 10,
            }

    async def get_billing_account_invoices(
        self,
        billing_account_id: str,
        token: str,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> PaginatedInvoices:
        """
        Retrieves invoices for a billing account.

        Args:
            billing_account_id (str): ID of the billing account
            token (str): Authentication token
            page (int, optional): Page number for pagination
            page_size (int, optional): Number of items per page

        Returns:
            PaginatedInvoices: Paginated invoices result
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetBillingAccountInvoices(
                    $billingAccountID: ID!
                    $page: Int
                    $pageSize: Int
                ) {
                    getBillingAccountInvoices(
                        billingAccountID: $billingAccountID
                        page: $page
                        pageSize: $pageSize
                    ) {
                        invoices {
                            id
                            billingAccountId
                            transactionsLink {
                                id
                                invoiceId
                                transactionId
                            }
                            totalAmount
                            currency
                            periodStart
                            periodEnd
                            status
                            taxAmount
                            taxDetails
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

            variables = {"billingAccountID": billing_account_id}

            if page is not None:
                variables["page"] = page
            if page_size is not None:
                variables["pageSize"] = page_size

            result = client.execute(query, variable_values=variables)
            return result.get(
                "getBillingAccountInvoices",
                {
                    "invoices": [],
                    "totalCount": 0,
                    "hasMore": False,
                    "page": 1,
                    "pageSize": 10,
                },
            )
        except Exception as e:
            print(f"Get billing account invoices failed: {str(e)}")
            return {
                "invoices": [],
                "totalCount": 0,
                "hasMore": False,
                "page": 1,
                "pageSize": 10,
            }

    async def get_transaction_details(
        self, transaction_id: str, token: str
    ) -> Optional[Transaction]:
        """
        Retrieves detailed information for a specific transaction.

        Args:
            transaction_id (str): ID of the transaction
            token (str): Authentication token

        Returns:
            Optional[Transaction]: Transaction details or None if not found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetTransactionDetails($transactionID: ID!) {
                    getTransactionDetails(transactionID: $transactionID) {
                        id
                        billingAccountId
                        paymentMethodId
                        creditRateId
                        creditTransactionId
                        amount
                        currency
                        description
                        status
                        type
                        invoiceLink {
                            id
                            invoiceId
                            transactionId
                        }
                        discountId
                        metadata
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"transactionID": transaction_id}
            result = client.execute(query, variable_values=variables)
            return result.get("getTransactionDetails")
        except Exception as e:
            print(f"Get transaction details failed: {str(e)}")
            return None

    async def get_invoice(self, invoice_id: str, token: str) -> Optional[Invoice]:
        """
        Retrieves detailed information for a specific invoice.

        Args:
            invoice_id (str): ID of the invoice
            token (str): Authentication token

        Returns:
            Optional[Invoice]: Invoice details or None if not found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetInvoice($invoiceID: ID!) {
                    getInvoice(invoiceID: $invoiceID) {
                        id
                        billingAccountId
                        transactionsLink {
                            id
                            invoiceId
                            transactionId
                        }
                        totalAmount
                        currency
                        periodStart
                        periodEnd
                        status
                        taxAmount
                        taxDetails
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"invoiceID": invoice_id}
            result = client.execute(query, variable_values=variables)
            return result.get("getInvoice")
        except Exception as e:
            print(f"Get invoice failed: {str(e)}")
            return None

    async def get_polling_status(
        self, transaction_id: str, token: str
    ) -> Optional[PollingStatus]:
        """
        Gets the polling status for a transaction.

        Args:
            transaction_id (str): ID of the transaction
            token (str): Authentication token

        Returns:
            Optional[PollingStatus]: Polling status or None if failed
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query PollingStatus($transactionID: String!) {
                    pollingStatus(transactionID: $transactionID) {
                        status
                    }
                }
            """
            )

            variables = {"transactionID": transaction_id}
            result = client.execute(query, variable_values=variables)
            return result.get("pollingStatus")
        except Exception as e:
            print(f"Get polling status failed: {str(e)}")
            return None

    async def get_invoice_pdf(self, invoice_id: str, token: str) -> Optional[PDF]:
        """
        Generates and retrieves a PDF for a specific invoice.

        Args:
            invoice_id (str): ID of the invoice
            token (str): Authentication token

        Returns:
            Optional[PDF]: PDF data or None if generation fails
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetInvoicePdf($invoiceID: ID!) {
                    getInvoicePdf(invoiceID: $invoiceID) {
                        pdf
                    }
                }
            """
            )

            variables = {"invoiceID": invoice_id}
            result = client.execute(query, variable_values=variables)
            return result.get("getInvoicePdf")
        except Exception as e:
            print(f"Get invoice PDF failed: {str(e)}")
            return None

    # Payment Mutation Operations
    async def generate_invoice_for_billing_account(
        self,
        billing_account_id: str,
        start_date: str,
        end_date: str,
        token: str,
    ) -> Optional[Invoice]:
        """
        Generates an invoice for a billing account within a date range.

        Args:
            billing_account_id (str): ID of the billing account
            start_date (str): Start date for invoice period (ISO format)
            end_date (str): End date for invoice period (ISO format)
            token (str): Authentication token

        Returns:
            Optional[Invoice]: Generated invoice or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation GenerateInvoiceForBillingAccount(
                    $billingAccountID: ID!
                    $startDate: DateTime!
                    $endDate: DateTime!
                ) {
                    generateInvoiceForBillingAccount(
                        billingAccountID: $billingAccountID
                        startDate: $startDate
                        endDate: $endDate
                    ) {
                        id
                        billingAccountId
                        totalAmount
                        currency
                        periodStart
                        periodEnd
                        status
                        taxAmount
                        taxDetails
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {
                "billingAccountID": billing_account_id,
                "startDate": start_date,
                "endDate": end_date,
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("generateInvoiceForBillingAccount")
        except Exception as e:
            print(f"Generate invoice for billing account failed: {str(e)}")
            return None

    async def generate_invoice_for_transaction(
        self, transaction_id: str, token: str
    ) -> Optional[Invoice]:
        """
        Generates an invoice for a specific transaction.

        Args:
            transaction_id (str): ID of the transaction
            token (str): Authentication token

        Returns:
            Optional[Invoice]: Generated invoice or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation GenerateInvoiceForTransaction($transactionID: ID!) {
                    generateInvoiceForTransaction(transactionID: $transactionID) {  # noqa: E501
                        id
                        billingAccountId
                        totalAmount
                        currency
                        periodStart
                        periodEnd
                        status
                        taxAmount
                        taxDetails
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"transactionID": transaction_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("generateInvoiceForTransaction")
        except Exception as e:
            print(f"Generate invoice for transaction failed: {str(e)}")
            return None

    async def create_razorpay_order(
        self,
        billing_account_id: str,
        currency_selected: str,
        token: str,
        plan_id: Optional[str] = None,
        store_item_id: Optional[str] = None,
        credit_amount: Optional[int] = None,
        addon_ids: Optional[List[AddOnInputPayment]] = None,
        recurrence: Optional[bool] = None,
    ) -> Optional[CreateRazorpayOrderResponse]:
        """
        Creates a Razorpay payment order.

        Args:
            billing_account_id (str): ID of the billing account
            currency_selected (str): Currency for the payment
            token (str): Authentication token
            plan_id (str, optional): ID of the plan being purchased
            store_item_id (str, optional): ID of the store item being purchased
            credit_amount (int, optional): Amount of credits being purchased
            addon_ids (List[AddOnInputPayment], optional): List of add-ons being purchased  # noqa: E501
            recurrence (bool, optional): Whether this is a recurring payment

        Returns:
            Optional[CreateRazorpayOrderResponse]: Razorpay order details or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateRazorpayOrder($input: createRazorpayOrderInput!) {  # noqa: E501
                    createRazorpayOrder(input: $input) {
                        amount
                        currency
                        orderID
                        key
                        transactionID
                    }
                }
            """
            )

            input_data = {
                "billingAccountId": billing_account_id,
                "currencySelected": currency_selected,
            }

            if plan_id is not None:
                input_data["planId"] = plan_id
            if store_item_id is not None:
                input_data["storeItemId"] = store_item_id
            if credit_amount is not None:
                input_data["creditAmount"] = credit_amount
            if addon_ids is not None:
                input_data["addOnIds"] = addon_ids
            if recurrence is not None:
                input_data["recurrence"] = recurrence

            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get("createRazorpayOrder")
        except Exception as e:
            print(f"Create Razorpay order failed: {str(e)}")
            return None

    async def create_stripe_order(
        self,
        billing_account_id: str,
        currency_selected: str,
        token: str,
        plan_id: Optional[str] = None,
        store_item_id: Optional[str] = None,
        credit_amount: Optional[int] = None,
        addon_ids: Optional[List[AddOnInputPayment]] = None,
        recurrence: Optional[bool] = None,
    ) -> Optional[CreateStripeOrderResponse]:
        """
        Creates a Stripe payment order.

        Args:
            billing_account_id (str): ID of the billing account
            currency_selected (str): Currency for the payment
            token (str): Authentication token
            plan_id (str, optional): ID of the plan being purchased
            store_item_id (str, optional): ID of the store item being purchased
            credit_amount (int, optional): Amount of credits being purchased
            addon_ids (List[AddOnInputPayment], optional): List of add-ons being purchased  # noqa: E501
            recurrence (bool, optional): Whether this is a recurring payment

        Returns:
            Optional[CreateStripeOrderResponse]: Stripe order details or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateStripeOrder($input: createStripeOrderInput!) {
                    createStripeOrder(input: $input) {
                        clientSecret
                        transactionID
                        key
                        amount
                    }
                }
            """
            )

            input_data = {
                "billingAccountId": billing_account_id,
                "currencySelected": currency_selected,
            }

            if plan_id is not None:
                input_data["planId"] = plan_id
            if store_item_id is not None:
                input_data["storeItemId"] = store_item_id
            if credit_amount is not None:
                input_data["creditAmount"] = credit_amount
            if addon_ids is not None:
                input_data["addOnIds"] = addon_ids
            if recurrence is not None:
                input_data["recurrence"] = recurrence

            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get("createStripeOrder")
        except Exception as e:
            print(f"Create Stripe order failed: {str(e)}")
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
    Initialize the default Payment client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = PaymentClient(graphql_endpoint)


def get_client() -> PaymentClient:
    """Get the default Payment client."""
    if _default_client is None:
        raise RuntimeError("Payment client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def get_billing_account_transactions(*args, **kwargs):
    return await get_client().get_billing_account_transactions(*args, **kwargs)


async def get_billing_account_invoices(*args, **kwargs):
    return await get_client().get_billing_account_invoices(*args, **kwargs)


async def get_transaction_details(*args, **kwargs):
    return await get_client().get_transaction_details(*args, **kwargs)


async def get_invoice(*args, **kwargs):
    return await get_client().get_invoice(*args, **kwargs)


async def get_polling_status(*args, **kwargs):
    return await get_client().get_polling_status(*args, **kwargs)


async def get_invoice_pdf(*args, **kwargs):
    return await get_client().get_invoice_pdf(*args, **kwargs)


async def generate_invoice_for_billing_account(*args, **kwargs):
    return await get_client().generate_invoice_for_billing_account(*args, **kwargs)


async def generate_invoice_for_transaction(*args, **kwargs):
    return await get_client().generate_invoice_for_transaction(*args, **kwargs)


async def create_razorpay_order(*args, **kwargs):
    return await get_client().create_razorpay_order(*args, **kwargs)


async def create_stripe_order(*args, **kwargs):
    return await get_client().create_stripe_order(*args, **kwargs)


def create_addon_payment_input(*args, **kwargs):
    if _default_client is None:
        raise RuntimeError("Payment client not initialized. Call initialize() first.")
    return _default_client.create_addon_payment_input(*args, **kwargs)
