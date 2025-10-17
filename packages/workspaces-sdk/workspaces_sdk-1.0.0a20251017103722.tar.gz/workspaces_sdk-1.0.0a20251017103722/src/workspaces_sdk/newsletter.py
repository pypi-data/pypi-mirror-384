"""
Newsletter Module for Workspaces SDK - Python

Provides comprehensive newsletter functionality including:
- Newsletter CRUD operations
- Subscription management with topic filtering
- Delivery and scheduling operations
- Analytics and tracking
- Bulk operations
- RBAC integration
"""

from typing import Any, Dict, List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type Definitions
class Newsletter(TypedDict):
    """Newsletter data structure"""

    id: str
    title: str
    content: str
    subject: str
    productId: Optional[str]
    topics: List[str]
    isGeneral: bool
    scheduleType: str  # 'INSTANT' | 'SCHEDULED'
    scheduledAt: Optional[str]
    cronPattern: Optional[str]
    status: str  # 'DRAFT' | 'SCHEDULED' | 'SENDING' | 'SENT' | 'FAILED'
    recipientCount: int
    createdAt: str
    updatedAt: str
    createdBy: Dict[str, str]
    brandingConfig: Optional[Dict[str, Any]]


class NewsletterSubscription(TypedDict):
    """Newsletter subscription data structure"""

    id: str
    userId: str
    newsletterId: Optional[str]
    status: str  # 'ACTIVE' | 'PAUSED' | 'UNSUBSCRIBED'
    topics: List[str]
    productId: Optional[str]
    subscribedAt: str
    unsubscribedAt: Optional[str]
    metadata: Optional[Dict[str, Any]]
    user: Optional[Dict[str, str]]
    newsletter: Optional[Dict[str, str]]


class NewsletterDelivery(TypedDict):
    """Newsletter delivery tracking data structure"""

    id: str
    newsletterId: str
    recipientId: str
    status: str
    sentAt: Optional[str]
    failureReason: Optional[str]
    messageId: Optional[str]
    opened: bool
    openedAt: Optional[str]
    clicked: bool
    clickedAt: Optional[str]


class NewsletterStats(TypedDict):
    """Newsletter analytics data structure"""

    total: int
    sent: int
    pending: int
    failed: int
    opened: int
    clicked: int
    sentRate: float
    openRate: float
    clickRate: float
    clickToOpenRate: float


class CreateNewsletterInput(TypedDict):
    """Input for creating a newsletter"""

    title: str
    content: str
    subject: str
    productId: Optional[str]
    topics: Optional[List[str]]
    isGeneral: Optional[bool]
    scheduleType: Optional[str]
    scheduledAt: Optional[str]
    cronPattern: Optional[str]
    brandingConfig: Optional[Dict[str, Any]]


class UpdateNewsletterInput(TypedDict):
    """Input for updating a newsletter"""

    title: Optional[str]
    content: Optional[str]
    subject: Optional[str]
    topics: Optional[List[str]]
    isGeneral: Optional[bool]
    scheduleType: Optional[str]
    scheduledAt: Optional[str]
    cronPattern: Optional[str]
    brandingConfig: Optional[Dict[str, Any]]


class NewsletterSubscriptionInput(TypedDict):
    """Input for newsletter subscription operations"""

    newsletterId: Optional[str]
    topics: List[str]
    productId: Optional[str]
    metadata: Optional[Dict[str, Any]]


class NewsletterFilterInput(TypedDict):
    """Input for filtering newsletters"""

    status: Optional[str]
    productId: Optional[str]
    topics: Optional[List[str]]
    isGeneral: Optional[bool]
    createdAfter: Optional[str]
    createdBefore: Optional[str]


class PaginationInfo(TypedDict):
    """Pagination metadata structure"""

    currentPage: int
    pageSize: int
    totalPages: int
    totalCount: int
    hasNextPage: bool
    hasPreviousPage: bool


class PaginatedNewsletters(TypedDict):
    """Paginated newsletters response structure"""

    newsletters: List[Newsletter]
    pagination: PaginationInfo


class NewsletterPreferencesInput(TypedDict):
    """Input for updating newsletter preferences"""

    emailNotifications: Optional[bool]
    frequency: Optional[str]  # 'IMMEDIATE' | 'DAILY' | 'WEEKLY' | 'MONTHLY'
    topicPreferences: Optional[List[str]]
    productPreferences: Optional[List[str]]
    unsubscribeAll: Optional[bool]


class UserNewsletterPreferences(TypedDict):
    """User newsletter preferences data structure"""

    id: str
    userId: str
    emailNotifications: bool
    frequency: str
    topicPreferences: List[str]
    productPreferences: List[str]
    unsubscribeAll: bool
    createdAt: str
    updatedAt: str


class ShareNewsletterInput(TypedDict):
    """Input for sharing a newsletter"""

    newsletterId: str
    recipientEmails: List[str]
    message: Optional[str]
    allowForwarding: Optional[bool]


class NewsletterSharingResult(TypedDict):
    """Result of newsletter sharing operation"""

    success: bool
    sharedWith: List[str]
    failedRecipients: List[str]
    message: Optional[str]


class AssignNewsletterPermissionInput(TypedDict):
    """Input for assigning newsletter permission"""

    newsletterId: str
    userId: str
    permission: str  # 'VIEW' | 'EDIT' | 'ADMIN'
    expiresAt: Optional[str]


class RevokeNewsletterPermissionInput(TypedDict):
    """Input for revoking newsletter permission"""

    newsletterId: str
    userId: str


class NewsletterPermissionResult(TypedDict):
    """Result of newsletter permission operation"""

    success: bool
    message: Optional[str]
    permission: Optional[Dict[str, Any]]


class NewsletterPermission(TypedDict):
    """Newsletter permission data structure"""

    id: str
    newsletterId: str
    userId: str
    permission: str
    grantedBy: Dict[str, str]
    grantedAt: str
    expiresAt: Optional[str]
    user: Dict[str, str]


class NewsletterClient:
    """
    Client for newsletter operations in the Workspaces platform.

    Provides comprehensive newsletter functionality including CRUD operations,
    subscription management, delivery operations, and analytics.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Newsletter client.

        Args:
            graphql_endpoint (str): GraphQL endpoint URL
        """
        self.graphql_endpoint = graphql_endpoint

    def get_client(self, token: str) -> Client:
        """
        Create and return a GraphQL client with authentication headers.

        Args:
            token (str): JWT authentication token

        Returns:
            Client: Configured GraphQL client
        """
        headers = get_default_headers()
        headers["Authorization"] = f"Bearer {token}"
        transport = RequestsHTTPTransport(url=self.graphql_endpoint, headers=headers)
        return Client(transport=transport, fetch_schema_from_transport=True)

    # Newsletter CRUD Operations
    async def create_newsletter(
        self, input_data: CreateNewsletterInput, token: str
    ) -> Optional[Newsletter]:
        """
        Create a new newsletter.

        Args:
            input_data (CreateNewsletterInput): Newsletter creation data
            token (str): Authentication token

        Returns:
            Optional[Newsletter]: Created newsletter or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateNewsletter($input: CreateNewsletterInput!) {
                    createNewsletter(input: $input) {
                        id
                        title
                        content
                        subject
                        productId
                        topics
                        isGeneral
                        scheduleType
                        scheduledAt
                        cronPattern
                        status
                        recipientCount
                        createdAt
                        updatedAt
                        createdBy {
                            id
                            name
                            email
                        }
                        brandingConfig
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("createNewsletter")
        except Exception as e:
            print(f"Create newsletter failed: {str(e)}")
            return None

    async def update_newsletter(
        self, newsletter_id: str, input_data: UpdateNewsletterInput, token: str
    ) -> Optional[Newsletter]:
        """
        Update an existing newsletter.

        Args:
            newsletter_id (str): Newsletter ID to update
            input_data (UpdateNewsletterInput): Newsletter update data
            token (str): Authentication token

        Returns:
            Optional[Newsletter]: Updated newsletter or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateNewsletter(
                    $id: ID!,
                    $input: UpdateNewsletterInput!
                ) {
                    updateNewsletter(id: $id, input: $input) {
                        id
                        title
                        content
                        subject
                        productId
                        topics
                        isGeneral
                        scheduleType
                        scheduledAt
                        cronPattern
                        status
                        recipientCount
                        createdAt
                        updatedAt
                        createdBy {
                            id
                            name
                            email
                        }
                        brandingConfig
                    }
                }
            """
            )

            result = client.execute(
                mutation,
                variable_values={"id": newsletter_id, "input": input_data},
            )
            return result.get("updateNewsletter")
        except Exception as e:
            print(f"Update newsletter failed: {str(e)}")
            return None

    async def get_newsletter(
        self, newsletter_id: str, token: str
    ) -> Optional[Newsletter]:
        """
        Retrieve a single newsletter by ID.

        Args:
            newsletter_id (str): Newsletter ID to retrieve
            token (str): Authentication token

        Returns:
            Optional[Newsletter]: Newsletter data or None if not found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetNewsletter($id: ID!) {
                    newsletter(id: $id) {
                        id
                        title
                        content
                        subject
                        productId
                        topics
                        isGeneral
                        scheduleType
                        scheduledAt
                        cronPattern
                        status
                        recipientCount
                        createdAt
                        updatedAt
                        createdBy {
                            id
                            name
                            email
                        }
                        brandingConfig
                    }
                }
            """
            )

            result = client.execute(query, variable_values={"id": newsletter_id})
            return result.get("newsletter")
        except Exception as e:
            print(f"Get newsletter failed: {str(e)}")
            return None

    async def get_newsletters(
        self,
        filter_input: Optional[NewsletterFilterInput] = None,
        token: str = None,
    ) -> List[Newsletter]:
        """
        Retrieve newsletters with optional filtering.

        Args:
            filter_input (Optional[NewsletterFilterInput]): Filter criteria
            token (str): Authentication token

        Returns:
            List[Newsletter]: List of newsletters matching criteria
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetNewsletters($filter: NewsletterFilterInput) {
                    newsletters(filter: $filter) {
                        id
                        title
                        content
                        subject
                        productId
                        topics
                        isGeneral
                        scheduleType
                        scheduledAt
                        cronPattern
                        status
                        recipientCount
                        createdAt
                        updatedAt
                        createdBy {
                            id
                            name
                            email
                        }
                        brandingConfig
                    }
                }
            """
            )

            result = client.execute(query, variable_values={"filter": filter_input})
            return result.get("newsletters", [])
        except Exception as e:
            print(f"Get newsletters failed: {str(e)}")
            return []

    async def get_newsletters_paginated(
        self,
        filter_input: Optional[NewsletterFilterInput] = None,
        page: int = 1,
        page_size: int = 10,
        token: str = None,
    ) -> Optional[PaginatedNewsletters]:
        """
        Retrieve newsletters with pagination support.

        Args:
            filter_input (Optional[NewsletterFilterInput]): Filter criteria
            page (int): Page number (default: 1)
            page_size (int): Number of items per page (default: 10)
            token (str): Authentication token

        Returns:
            Optional[PaginatedNewsletters]: Paginated
                newsletters with metadata or None
                if failed
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetNewslettersPaginated(
                    $filter: NewsletterFilterInput,
                    $page: Int!,
                    $pageSize: Int!
                ) {
                    newslettersPaginated(
                        filter: $filter,
                        page: $page,
                        pageSize: $pageSize
                    ) {
                        newsletters {
                            id
                            title
                            content
                            subject
                            productId
                            topics
                            isGeneral
                            scheduleType
                            scheduledAt
                            cronPattern
                            status
                            recipientCount
                            createdAt
                            updatedAt
                            createdBy {
                                id
                                name
                                email
                            }
                            brandingConfig
                        }
                        pagination {
                            currentPage
                            pageSize
                            totalPages
                            totalCount
                            hasNextPage
                            hasPreviousPage
                        }
                    }
                }
            """
            )

            result = client.execute(
                query,
                variable_values={
                    "filter": filter_input,
                    "page": page,
                    "pageSize": page_size,
                },
            )
            return result.get("newslettersPaginated")
        except Exception as e:
            print(f"Get newsletters paginated failed: {str(e)}")
            return None

    async def delete_newsletter(self, newsletter_id: str, token: str) -> bool:
        """
        Delete a newsletter.

        Args:
            newsletter_id (str): Newsletter ID to delete
            token (str): Authentication token

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DeleteNewsletter($id: ID!) {
                    deleteNewsletter(id: $id)
                }
            """
            )

            result = client.execute(mutation, variable_values={"id": newsletter_id})
            return result.get("deleteNewsletter", False)
        except Exception as e:
            print(f"Delete newsletter failed: {str(e)}")
            return False

    # Newsletter Delivery Operations
    async def send_newsletter(
        self, newsletter_id: str, token: str
    ) -> Optional[Newsletter]:
        """
        Send a newsletter immediately.

        Args:
            newsletter_id (str): Newsletter ID to send
            token (str): Authentication token

        Returns:
            Optional[Newsletter]: Updated newsletter with sending status
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation SendNewsletter($id: ID!) {
                    sendNewsletter(id: $id) {
                        id
                        title
                        status
                        recipientCount
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"id": newsletter_id})
            return result.get("sendNewsletter")
        except Exception as e:
            print(f"Send newsletter failed: {str(e)}")
            return None

    async def schedule_newsletter(
        self, newsletter_id: str, token: str
    ) -> Optional[Newsletter]:
        """
        Schedule a newsletter for delivery.

        Args:
            newsletter_id (str): Newsletter ID to schedule
            token (str): Authentication token

        Returns:
            Optional[Newsletter]: Newsletter with scheduled status
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ScheduleNewsletter($id: ID!) {
                    scheduleNewsletter(id: $id) {
                        id
                        status
                        scheduledAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"id": newsletter_id})
            return result.get("scheduleNewsletter")
        except Exception as e:
            print(f"Schedule newsletter failed: {str(e)}")
            return None

    async def cancel_newsletter_schedule(
        self, newsletter_id: str, token: str
    ) -> Optional[Newsletter]:
        """
        Cancel a scheduled newsletter.

        Args:
            newsletter_id (str): Newsletter ID to cancel schedule
            token (str): Authentication token

        Returns:
            Optional[Newsletter]: Newsletter with updated status
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CancelNewsletterSchedule($id: ID!) {
                    cancelNewsletterSchedule(id: $id) {
                        id
                        status
                        scheduledAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"id": newsletter_id})
            return result.get("cancelNewsletterSchedule")
        except Exception as e:
            print(f"Cancel newsletter schedule failed: {str(e)}")
            return None

    async def force_process_newsletter_delivery(
        self, newsletter_id: str, token: str
    ) -> Optional[Newsletter]:
        """
        Manually retry failed newsletter deliveries.

        Admin operation for manually triggering
        reprocessing of failed deliveries for a
        specific newsletter. This is useful for
        retrying deliveries that failed due to
        temporary issues.

        Args:
            newsletter_id (str): Newsletter ID to reprocess deliveries
            token (str): Authentication token

        Returns:
            Optional[Newsletter]: Newsletter with updated delivery status
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ForceProcessNewsletterDelivery($id: ID!) {
                    forceProcessNewsletterDelivery(id: $id) {
                        id
                        title
                        status
                        recipientCount
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"id": newsletter_id})
            return result.get("forceProcessNewsletterDelivery")
        except Exception as e:
            print(f"Force process newsletter delivery failed: {str(e)}")
            return None

    # Subscription Management
    async def subscribe_to_newsletter(
        self, input_data: NewsletterSubscriptionInput, token: str
    ) -> Optional[NewsletterSubscription]:
        """
        Subscribe to a newsletter or newsletter topics.

        Args:
            input_data (NewsletterSubscriptionInput): Subscription data
            token (str): Authentication token

        Returns:
            Optional[NewsletterSubscription]: Created subscription
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation SubscribeToNewsletter(
                    $input:
                        NewsletterSubscriptionInput!
                ) {
                    subscribeToNewsletter(input: $input) {
                        id
                        userId
                        newsletterId
                        status
                        topics
                        productId
                        subscribedAt
                        unsubscribedAt
                        metadata
                        user {
                            id
                            name
                            email
                        }
                        newsletter {
                            id
                            title
                        }
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("subscribeToNewsletter")
        except Exception as e:
            print(f"Subscribe to newsletter failed: {str(e)}")
            return None

    async def update_newsletter_subscription(
        self,
        subscription_id: str,
        input_data: NewsletterSubscriptionInput,
        token: str,
    ) -> Optional[NewsletterSubscription]:
        """
        Update newsletter subscription preferences.

        Args:
            subscription_id (str): Subscription ID to update
            input_data (NewsletterSubscriptionInput): Updated subscription data
            token (str): Authentication token

        Returns:
            Optional[NewsletterSubscription]: Updated subscription
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateNewsletterSubscription(
                    $id: ID!,
                    $input:
                        NewsletterSubscriptionInput!
                ) {
                    updateNewsletterSubscription(id: $id, input: $input) {
                        id
                        userId
                        newsletterId
                        status
                        topics
                        productId
                        subscribedAt
                        unsubscribedAt
                        metadata
                        user {
                            id
                            name
                            email
                        }
                        newsletter {
                            id
                            title
                        }
                    }
                }
            """
            )

            result = client.execute(
                mutation,
                variable_values={"id": subscription_id, "input": input_data},
            )
            return result.get("updateNewsletterSubscription")
        except Exception as e:
            print(f"Update newsletter subscription failed: {str(e)}")
            return None

    async def unsubscribe_from_newsletter(
        self, subscription_id: str, token: str
    ) -> bool:
        """
        Unsubscribe from a newsletter.

        Args:
            subscription_id (str): Subscription ID to unsubscribe
            token (str): Authentication token

        Returns:
            bool: True if unsubscribed successfully
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UnsubscribeFromNewsletter($subscriptionId: ID!) {
                    unsubscribeFromNewsletter(subscriptionId: $subscriptionId)
                }
            """
            )

            result = client.execute(
                mutation, variable_values={"subscriptionId": subscription_id}
            )
            return result.get("unsubscribeFromNewsletter", False)
        except Exception as e:
            print(f"Unsubscribe from newsletter failed: {str(e)}")
            return False

    async def get_my_newsletter_subscriptions(
        self, token: str
    ) -> List[NewsletterSubscription]:
        """
        Get current user's newsletter subscriptions.

        Args:
            token (str): Authentication token

        Returns:
            List[NewsletterSubscription]: User's subscriptions
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetMyNewsletterSubscriptions {
                    myNewsletterSubscriptions {
                        id
                        userId
                        newsletterId
                        status
                        topics
                        productId
                        subscribedAt
                        unsubscribedAt
                        metadata
                        user {
                            id
                            name
                            email
                        }
                        newsletter {
                            id
                            title
                        }
                    }
                }
            """
            )

            result = client.execute(query)
            return result.get("myNewsletterSubscriptions", [])
        except Exception as e:
            print(f"Get my newsletter subscriptions failed: {str(e)}")
            return []

    async def get_newsletter_subscription(
        self, subscription_id: str, token: str
    ) -> Optional[NewsletterSubscription]:
        """
        Retrieve a single newsletter subscription by ID.

        Args:
            subscription_id (str): Subscription ID to retrieve
            token (str): Authentication token

        Returns:
            Optional[NewsletterSubscription]:
                Subscription data or None if not
                found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetNewsletterSubscription($id: ID!) {
                    newsletterSubscription(id: $id) {
                        id
                        userId
                        newsletterId
                        status
                        topics
                        productId
                        subscribedAt
                        unsubscribedAt
                        metadata
                        user {
                            id
                            name
                            email
                        }
                        newsletter {
                            id
                            title
                        }
                    }
                }
            """
            )

            result = client.execute(query, variable_values={"id": subscription_id})
            return result.get("newsletterSubscription")
        except Exception as e:
            print(f"Get newsletter subscription failed: {str(e)}")
            return None

    async def update_newsletter_preferences(
        self, input_data: NewsletterPreferencesInput, token: str
    ) -> Optional[UserNewsletterPreferences]:
        """
        Update user's newsletter preferences.

        Args:
            input_data (NewsletterPreferencesInput): Newsletter
                preferences data
            token (str): Authentication token

        Returns:
            Optional[UserNewsletterPreferences]:
                Updated preferences or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateNewsletterPreferences(
                    $input:
                        NewsletterPreferencesInput!
                ) {
                    updateNewsletterPreferences(input: $input) {
                        id
                        userId
                        emailNotifications
                        frequency
                        topicPreferences
                        productPreferences
                        unsubscribeAll
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("updateNewsletterPreferences")
        except Exception as e:
            print(f"Update newsletter preferences failed: {str(e)}")
            return None

    async def get_newsletter_preferences(
        self, token: str
    ) -> Optional[UserNewsletterPreferences]:
        """
        Get current user's newsletter preferences.

        Args:
            token (str): Authentication token

        Returns:
            Optional[UserNewsletterPreferences]:
                User's preferences or None if not
                found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetUserNewsletterPreferences {
                    getUserNewsletterPreferences {
                        id
                        userId
                        emailNotifications
                        frequency
                        topicPreferences
                        productPreferences
                        unsubscribeAll
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(query)
            return result.get("getUserNewsletterPreferences")
        except Exception as e:
            print(f"Get newsletter preferences failed: {str(e)}")
            return None

    # Bulk Operations
    async def bulk_subscribe(
        self,
        user_ids: List[str],
        input_data: NewsletterSubscriptionInput,
        token: str,
    ) -> List[NewsletterSubscription]:
        """
        Subscribe multiple users to a newsletter.

        Args:
            user_ids (List[str]): List of user IDs to subscribe
            input_data (NewsletterSubscriptionInput): Subscription data
            token (str): Authentication token

        Returns:
            List[NewsletterSubscription]: Created subscriptions
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation BulkSubscribe(
                    $userIds: [ID!]!,
                    $input:
                        NewsletterSubscriptionInput!
                ) {
                    bulkSubscribe(userIds: $userIds, input: $input) {
                        id
                        userId
                        newsletterId
                        status
                        topics
                        productId
                        subscribedAt
                        user {
                            id
                            name
                            email
                        }
                    }
                }
            """
            )

            result = client.execute(
                mutation,
                variable_values={"userIds": user_ids, "input": input_data},
            )
            return result.get("bulkSubscribe", [])
        except Exception as e:
            print(f"Bulk subscribe failed: {str(e)}")
            return []

    # Analytics and Tracking
    async def get_newsletter_stats(
        self, newsletter_id: str, token: str
    ) -> Optional[NewsletterStats]:
        """
        Get analytics and statistics for a newsletter.

        Args:
            newsletter_id (str): Newsletter ID
            token (str): Authentication token

        Returns:
            Optional[NewsletterStats]: Newsletter statistics
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetNewsletterStats($id: ID!) {
                    newsletterStats(id: $id) {
                        total
                        sent
                        pending
                        failed
                        opened
                        clicked
                        sentRate
                        openRate
                        clickRate
                        clickToOpenRate
                    }
                }
            """
            )

            result = client.execute(query, variable_values={"id": newsletter_id})
            return result.get("newsletterStats")
        except Exception as e:
            print(f"Get newsletter stats failed: {str(e)}")
            return None

    async def get_newsletter_deliveries(
        self, newsletter_id: str, token: str
    ) -> List[NewsletterDelivery]:
        """
        Get delivery tracking data for a newsletter.

        Args:
            newsletter_id (str): Newsletter ID
            token (str): Authentication token

        Returns:
            List[NewsletterDelivery]: Delivery tracking data
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetNewsletterDeliveries($newsletterId: ID!) {
                    newsletterDeliveries(newsletterId: $newsletterId) {
                        id
                        newsletterId
                        recipientId
                        status
                        sentAt
                        failureReason
                        messageId
                        opened
                        openedAt
                        clicked
                        clickedAt
                    }
                }
            """
            )

            result = client.execute(
                query, variable_values={"newsletterId": newsletter_id}
            )
            return result.get("newsletterDeliveries", [])
        except Exception as e:
            print(f"Get newsletter deliveries failed: {str(e)}")
            return []

    # Utility Methods
    async def validate_cron_pattern(self, pattern: str, token: str) -> bool:
        """
        Validate a cron pattern for scheduling.

        Args:
            pattern (str): Cron pattern to validate
            token (str): Authentication token

        Returns:
            bool: True if pattern is valid
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query ValidateCronPattern($pattern: String!) {
                    validateCronPattern(pattern: $pattern)
                }
            """
            )

            result = client.execute(query, variable_values={"pattern": pattern})
            return result.get("validateCronPattern", False)
        except Exception as e:
            print(f"Validate cron pattern failed: {str(e)}")
            return False

    async def get_scheduler_status(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get newsletter scheduler status.

        Args:
            token (str): Authentication token

        Returns:
            Optional[Dict[str, Any]]: Scheduler status information
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetSchedulerStatus {
                    schedulerStatus {
                        isRunning
                        lastRun
                        nextRun
                    }
                }
            """
            )

            result = client.execute(query)
            return result.get("schedulerStatus")
        except Exception as e:
            print(f"Get scheduler status failed: {str(e)}")
            return None

    # Advanced RBAC Operations (Phase 3 - P2)
    async def share_newsletter(
        self, input_data: ShareNewsletterInput, token: str
    ) -> Optional[NewsletterSharingResult]:
        """
        Share a newsletter with specified recipients.

        Args:
            input_data (ShareNewsletterInput): Newsletter sharing data
            token (str): Authentication token

        Returns:
            Optional[NewsletterSharingResult]:
                Sharing result with success status
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ShareNewsletter($input: ShareNewsletterInput!) {
                    shareNewsletter(input: $input) {
                        success
                        sharedWith
                        failedRecipients
                        message
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("shareNewsletter")
        except Exception as e:
            print(f"Share newsletter failed: {str(e)}")
            return None

    async def assign_newsletter_permission(
        self, input_data: AssignNewsletterPermissionInput, token: str
    ) -> Optional[NewsletterPermissionResult]:
        """
        Assign permission to a user for a newsletter.

        Args:
            input_data (AssignNewsletterPermissionInput): Permission
                assignment data
            token (str): Authentication token

        Returns:
            Optional[NewsletterPermissionResult]: Permission assignment result
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation AssignNewsletterPermission(
                    $input:
                        AssignNewsletterPermissionInput!
                ) {
                    assignNewsletterPermission(input: $input) {
                        success
                        message
                        permission {
                            id
                            newsletterId
                            userId
                            permission
                            grantedBy {
                                id
                                name
                                email
                            }
                            grantedAt
                            expiresAt
                        }
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("assignNewsletterPermission")
        except Exception as e:
            print(f"Assign newsletter permission failed: {str(e)}")
            return None

    async def revoke_newsletter_permission(
        self, input_data: RevokeNewsletterPermissionInput, token: str
    ) -> Optional[NewsletterPermissionResult]:
        """
        Revoke a user's permission for a newsletter.

        Args:
            input_data (RevokeNewsletterPermissionInput): Permission
                revocation data
            token (str): Authentication token

        Returns:
            Optional[NewsletterPermissionResult]: Permission revocation result
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation RevokeNewsletterPermission(
                    $input:
                        RevokeNewsletterPermissionInput!
                ) {
                    revokeNewsletterPermission(input: $input) {
                        success
                        message
                        permission {
                            id
                            newsletterId
                            userId
                        }
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("revokeNewsletterPermission")
        except Exception as e:
            print(f"Revoke newsletter permission failed: {str(e)}")
            return None

    async def get_newsletter_permissions(
        self, newsletter_id: str, token: str
    ) -> List[NewsletterPermission]:
        """
        Get all permissions for a newsletter.

        Args:
            newsletter_id (str): Newsletter ID
            token (str): Authentication token

        Returns:
            List[NewsletterPermission]: List of newsletter permissions
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetNewsletterPermissions($newsletterId: ID!) {
                    newsletterPermissions(newsletterId: $newsletterId) {
                        id
                        newsletterId
                        userId
                        permission
                        grantedBy {
                            id
                            name
                            email
                        }
                        grantedAt
                        expiresAt
                        user {
                            id
                            name
                            email
                        }
                    }
                }
            """
            )

            result = client.execute(
                query, variable_values={"newsletterId": newsletter_id}
            )
            return result.get("newsletterPermissions", [])
        except Exception as e:
            print(f"Get newsletter permissions failed: {str(e)}")
            return []


# Convenience functions for direct usage
async def create_newsletter(
    endpoint: str, input_data: CreateNewsletterInput, token: str
) -> Optional[Newsletter]:
    """
    Convenience function to create a newsletter.

    Args:
        endpoint (str): GraphQL endpoint URL
        input_data (CreateNewsletterInput): Newsletter data
        token (str): Authentication token

    Returns:
        Optional[Newsletter]: Created newsletter
    """
    client = NewsletterClient(endpoint)
    return await client.create_newsletter(input_data, token)


async def get_newsletters(
    endpoint: str,
    filter_input: Optional[NewsletterFilterInput] = None,
    token: str = None,
) -> List[Newsletter]:
    """
    Convenience function to get newsletters.

    Args:
        endpoint (str): GraphQL endpoint URL
        filter_input (Optional[NewsletterFilterInput]): Filter criteria
        token (str): Authentication token

    Returns:
        List[Newsletter]: List of newsletters
    """
    client = NewsletterClient(endpoint)
    return await client.get_newsletters(filter_input, token)


async def send_newsletter(
    endpoint: str, newsletter_id: str, token: str
) -> Optional[Newsletter]:
    """
    Convenience function to send a newsletter.

    Args:
        endpoint (str): GraphQL endpoint URL
        newsletter_id (str): Newsletter ID to send
        token (str): Authentication token

    Returns:
        Optional[Newsletter]: Newsletter with updated status
    """
    client = NewsletterClient(endpoint)
    return await client.send_newsletter(newsletter_id, token)


async def subscribe_to_newsletter(
    endpoint: str, input_data: NewsletterSubscriptionInput, token: str
) -> Optional[NewsletterSubscription]:
    """
    Convenience function to subscribe to a newsletter.

    Args:
        endpoint (str): GraphQL endpoint URL
        input_data (NewsletterSubscriptionInput): Subscription data
        token (str): Authentication token

    Returns:
        Optional[NewsletterSubscription]: Created subscription
    """
    client = NewsletterClient(endpoint)
    return await client.subscribe_to_newsletter(input_data, token)
