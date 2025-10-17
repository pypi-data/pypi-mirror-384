"""
WorkspaceClient - Main client for Workspaces SDK

Provides a unified interface to all Workspaces platform functionality including
the Enhanced Actor-based RBAC system.
"""

from typing import Optional

from gql import Client
from gql.transport.requests import RequestsHTTPTransport

from .addon import AddonClient
from .analytics import AnalyticsClient
from .billing import BillingClient
from .config import get_default_headers
from .configuration import ConfigClient
from .credit import CreditClient
from .data_export import DataExportClient
from .newsletter import NewsletterClient
from .notification import NotificationClient
from .payment import PaymentClient
from .plan import PlanClient
from .quota import QuotaClient
from .rbac import RBACClient
from .settings import SettingsClient
from .store import StoreClient
from .usage import UsageClient


class WorkspaceClient:
    """
    Main client for interacting with the Workspaces platform.

    Provides access to all platform functionality including:
    - RBAC (Role-Based Access Control) - self.rbac
    - Addon Management - self.addon
    - Billing Account Management - self.billing
    - Credit Transactions - self.credit
    - Payment Processing - self.payment
    - Subscription Plan Management - self.plan
    - Configuration Management - self.configuration
    - Quota Management - self.quota
    - Usage Tracking and Analytics - self.usage
    - Store Management - self.store
    - Notification Management - self.notification
    - Newsletter Management - self.newsletter
    - Data Export Operations - self.data_export
    - Settings and Configuration Management - self.settings
    - Analytics and Insights - self.analytics
    """

    def __init__(
        self,
        endpoint: str,
        token: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        Initialize the Workspaces client.

        Args:
            endpoint (str): GraphQL endpoint URL
            token (str, optional): JWT authentication token
            api_key (str, optional): API key for authentication
        """
        self.endpoint = endpoint
        self.token = token
        self.api_key = api_key

        # Initialize all module clients
        self.rbac = RBACClient(endpoint)
        self.addon = AddonClient(endpoint)
        self.billing = BillingClient(endpoint)
        self.credit = CreditClient(endpoint)
        self.payment = PaymentClient(endpoint)
        self.plan = PlanClient(endpoint)
        self.configuration = ConfigClient(endpoint)
        self.quota = QuotaClient(endpoint)
        self.usage = UsageClient(endpoint)
        self.store = StoreClient(endpoint)
        self.notification = NotificationClient(endpoint)
        self.newsletter = NewsletterClient(endpoint)
        self.data_export = DataExportClient(endpoint)
        self.settings = SettingsClient(endpoint)
        self.analytics = AnalyticsClient(endpoint)

        # Set up transport headers with default headers (including product ID)
        self._headers = get_default_headers()
        if token:
            self._headers["Authorization"] = f"Bearer {token}"
        elif api_key:
            self._headers["X-API-Key"] = api_key

    def get_client(self, token: Optional[str] = None) -> Client:
        """
        Create and return a GraphQL client with authentication headers.

        Args:
            token (str, optional): Override token for this request

        Returns:
            Client: Configured GraphQL client
        """
        headers = self._headers.copy()
        if token:
            headers["Authorization"] = f"Bearer {token}"

        transport = RequestsHTTPTransport(url=self.endpoint, headers=headers)
        return Client(transport=transport, fetch_schema_from_transport=True)

    def set_token(self, token: str) -> None:
        """
        Update the authentication token for this client.

        Args:
            token (str): New JWT authentication token
        """
        self.token = token
        self._headers["Authorization"] = f"Bearer {token}"
