"""
Notification Client for Workspaces SDK.

Provides access to notification management functionality including creating,
updating, and managing notifications for users.
"""

from typing import List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Notification system
class CreateNotificationInput(TypedDict):
    title: str
    message: str
    type: Optional[str]  # "info", "warning", "success", "error", "system", "user"
    redirectUrl: Optional[str]
    appName: Optional[str]
    email: Optional[bool]
    sms: Optional[bool]
    whatsapp: Optional[bool]
    userIds: Optional[List[str]]


class UpdateNotificationInput(TypedDict):
    id: str
    title: Optional[str]
    message: Optional[str]
    type: Optional[str]
    status: Optional[str]  # "unread", "read", "archived"
    redirectUrl: Optional[str]
    appName: Optional[str]
    email: Optional[bool]
    sms: Optional[bool]
    whatsapp: Optional[bool]


class NotificationFilterInput(TypedDict):
    status: Optional[str]  # "unread", "read", "archived"
    type: Optional[str]  # "info", "warning", "success", "error", "system", "user"
    appName: Optional[str]
    limit: Optional[int]
    offset: Optional[int]


class User(TypedDict):
    id: str
    name: str


class Notification(TypedDict):
    id: str
    title: str
    message: str
    type: str
    status: str
    redirectUrl: Optional[str]
    appName: Optional[str]
    email: bool
    sms: bool
    whatsapp: bool
    userId: str
    createdAt: str
    updatedAt: str
    readAt: Optional[str]
    user: Optional[User]


class NotificationResponse(TypedDict):
    notifications: List[Notification]
    totalCount: int
    unreadCount: int
    hasMore: bool


class NotificationBulkResponse(TypedDict):
    notifications: List[Notification]
    successCount: int
    failureCount: int
    errors: List[str]


class AppNotificationCount(TypedDict):
    appName: str
    totalCount: int
    unreadCount: int
    readCount: int


class NotificationCountsResponse(TypedDict):
    appCounts: List[AppNotificationCount]
    totalNotifications: int
    totalUnread: int
    totalRead: int


class NotificationClient:
    """
    Client for managing notifications in the Workspaces platform.

    Provides methods to create, update, retrieve, and manage notifications
    with proper authentication and error handling.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Notification client with a GraphQL endpoint.

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

    # Notification Query Operations
    async def get_notifications(
        self,
        token: str,
        filter_input: Optional[NotificationFilterInput] = None,
    ) -> NotificationResponse:
        """
        Retrieves all notifications for a user with pagination and filtering.

        Args:
            token (str): Authentication token
            filter_input (NotificationFilterInput, optional): Filter criteria

        Returns:
            NotificationResponse: Notifications with metadata
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetNotifications($filter: NotificationFilterInput) {
                    getNotifications(filter: $filter) {
                        notifications {
                            id
                            title
                            message
                            type
                            status
                            redirectUrl
                            appName
                            email
                            sms
                            whatsapp
                            userId
                            createdAt
                            updatedAt
                            readAt
                            user {
                                id
                                name
                            }
                        }
                        totalCount
                        unreadCount
                        hasMore
                    }
                }
            """
            )

            variables = {"filter": filter_input} if filter_input else {}
            result = client.execute(query, variable_values=variables)
            return result.get(
                "getNotifications",
                {
                    "notifications": [],
                    "totalCount": 0,
                    "unreadCount": 0,
                    "hasMore": False,
                },
            )
        except Exception as e:
            print(f"Get notifications failed: {str(e)}")
            return {
                "notifications": [],
                "totalCount": 0,
                "unreadCount": 0,
                "hasMore": False,
            }

    async def get_notification(
        self, notification_id: str, token: str
    ) -> Optional[Notification]:
        """
        Retrieves a single notification by ID.

        Args:
            notification_id (str): ID of the notification
            token (str): Authentication token

        Returns:
            Optional[Notification]: Notification details or None if not found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetNotification($id: ID!) {
                    getNotification(id: $id) {
                        id
                        title
                        message
                        type
                        status
                        redirectUrl
                        appName
                        email
                        sms
                        whatsapp
                        userId
                        createdAt
                        updatedAt
                        readAt
                        user {
                            id
                            name
                        }
                    }
                }
            """
            )

            variables = {"id": notification_id}
            result = client.execute(query, variable_values=variables)
            return result.get("getNotification")
        except Exception as e:
            print(f"Get notification failed: {str(e)}")
            return None

    async def get_unread_notifications(
        self,
        token: str,
        filter_input: Optional[NotificationFilterInput] = None,
    ) -> NotificationResponse:
        """
        Retrieves unread notifications for a user.

        Args:
            token (str): Authentication token
            filter_input (NotificationFilterInput, optional): Filter criteria

        Returns:
            NotificationResponse: Unread notifications with metadata
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetUnreadNotification($filter: NotificationFilterInput) {
                    getUnreadNotification(filter: $filter) {
                        notifications {
                            id
                            title
                            message
                            type
                            status
                            redirectUrl
                            appName
                            email
                            sms
                            whatsapp
                            userId
                            createdAt
                            updatedAt
                            readAt
                            user {
                                id
                                name
                            }
                        }
                        totalCount
                        unreadCount
                        hasMore
                    }
                }
            """
            )

            variables = {"filter": filter_input} if filter_input else {}
            result = client.execute(query, variable_values=variables)
            return result.get(
                "getUnreadNotification",
                {
                    "notifications": [],
                    "totalCount": 0,
                    "unreadCount": 0,
                    "hasMore": False,
                },
            )
        except Exception as e:
            print(f"Get unread notifications failed: {str(e)}")
            return {
                "notifications": [],
                "totalCount": 0,
                "unreadCount": 0,
                "hasMore": False,
            }

    # Notification Mutation Operations
    async def create_notification(
        self,
        title: str,
        message: str,
        token: str,
        type: str = "info",
        redirect_url: str = "",
        app_name: Optional[str] = None,
        email: bool = False,
        sms: bool = False,
        whatsapp: bool = False,
        user_ids: Optional[List[str]] = None,
    ) -> NotificationBulkResponse:
        """
        Creates a new notification (single or bulk).

        Args:
            title (str): Notification title
            message (str): Notification message
            token (str): Authentication token
            type (str): Notification type ("info", "warning", "success", "error", "system", "user")
            redirect_url (str): URL to redirect to when notification is clicked
            app_name (str, optional): Name of the application
            email (bool): Whether to send email notification
            sms (bool): Whether to send SMS notification
            whatsapp (bool): Whether to send WhatsApp notification
            user_ids (List[str], optional): List of user IDs to send notification to  # noqa: E501

        Returns:
            NotificationBulkResponse: Result of notification creation
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateNotification($input: CreateNotificationInput!) {
                    createNotification(input: $input) {
                        notifications {
                            id
                            title
                            message
                            type
                            status
                            redirectUrl
                            appName
                            email
                            sms
                            whatsapp
                            userId
                            createdAt
                            updatedAt
                            readAt
                        }
                        successCount
                        failureCount
                        errors
                    }
                }
            """
            )

            input_data = {
                "title": title,
                "message": message,
                "type": type,
                "redirectUrl": redirect_url,
                "email": email,
                "sms": sms,
                "whatsapp": whatsapp,
            }

            if app_name:
                input_data["appName"] = app_name
            if user_ids:
                input_data["userIds"] = user_ids

            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get(
                "createNotification",
                {
                    "notifications": [],
                    "successCount": 0,
                    "failureCount": 0,
                    "errors": [],
                },
            )
        except Exception as e:
            print(f"Create notification failed: {str(e)}")
            return {
                "notifications": [],
                "successCount": 0,
                "failureCount": 1,
                "errors": [str(e)],
            }

    async def update_notification(
        self,
        notification_id: str,
        token: str,
        title: Optional[str] = None,
        message: Optional[str] = None,
        type: Optional[str] = None,
        status: Optional[str] = None,
        redirect_url: Optional[str] = None,
        app_name: Optional[str] = None,
        email: Optional[bool] = None,
        sms: Optional[bool] = None,
        whatsapp: Optional[bool] = None,
    ) -> Optional[Notification]:
        """
        Updates an existing notification.

        Args:
            notification_id (str): ID of the notification to update
            token (str): Authentication token
            title (str, optional): New notification title
            message (str, optional): New notification message
            type (str, optional): New notification type
            status (str, optional): New notification status
            redirect_url (str, optional): New redirect URL
            app_name (str, optional): New app name
            email (bool, optional): New email setting
            sms (bool, optional): New SMS setting
            whatsapp (bool, optional): New WhatsApp setting

        Returns:
            Optional[Notification]: Updated notification or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateNotification($input: UpdateNotificationInput!) {
                    updateNotification(input: $input) {
                        id
                        title
                        message
                        type
                        status
                        redirectUrl
                        appName
                        email
                        sms
                        whatsapp
                        userId
                        createdAt
                        updatedAt
                        readAt
                    }
                }
            """
            )

            update_input = {"id": notification_id}

            if title is not None:
                update_input["title"] = title
            if message is not None:
                update_input["message"] = message
            if type is not None:
                update_input["type"] = type
            if status is not None:
                update_input["status"] = status
            if redirect_url is not None:
                update_input["redirectUrl"] = redirect_url
            if app_name is not None:
                update_input["appName"] = app_name
            if email is not None:
                update_input["email"] = email
            if sms is not None:
                update_input["sms"] = sms
            if whatsapp is not None:
                update_input["whatsapp"] = whatsapp

            variables = {"input": update_input}

            result = client.execute(mutation, variable_values=variables)
            return result.get("updateNotification")
        except Exception as e:
            print(f"Update notification failed: {str(e)}")
            return None

    async def mark_notification_as_read(
        self, notification_id: str, token: str
    ) -> Optional[Notification]:
        """
        Marks a notification as read.

        Args:
            notification_id (str): ID of the notification
            token (str): Authentication token

        Returns:
            Optional[Notification]: Updated notification or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation MarkNotificationAsRead($id: ID!) {
                    markNotificationAsRead(id: $id) {
                        id
                        title
                        message
                        type
                        status
                        redirectUrl
                        appName
                        email
                        sms
                        whatsapp
                        userId
                        createdAt
                        updatedAt
                        readAt
                    }
                }
            """
            )

            variables = {"id": notification_id}
            result = client.execute(mutation, variable_values=variables)
            return result.get("markNotificationAsRead")
        except Exception as e:
            print(f"Mark notification as read failed: {str(e)}")
            return None

    async def mark_notifications_as_read(
        self, notification_ids: List[str], token: str
    ) -> List[Notification]:
        """
        Marks multiple notifications as read.

        Args:
            notification_ids (List[str]): List of notification IDs
            token (str): Authentication token

        Returns:
            List[Notification]: List of updated notifications
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation MarkNotificationsAsRead($ids: [ID!]!) {
                    markNotificationsAsRead(ids: $ids) {
                        id
                        title
                        message
                        type
                        status
                        redirectUrl
                        appName
                        email
                        sms
                        whatsapp
                        userId
                        createdAt
                        updatedAt
                        readAt
                    }
                }
            """
            )

            variables = {"ids": notification_ids}
            result = client.execute(mutation, variable_values=variables)
            return result.get("markNotificationsAsRead", [])
        except Exception as e:
            print(f"Mark notifications as read failed: {str(e)}")
            return []

    async def mark_all_notifications_as_read(self, token: str) -> bool:
        """
        Marks all notifications as read for a specific user.

        Args:
            token (str): Authentication token

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation MarkAllNotificationsAsRead {
                    markAllNotificationsAsRead
                }
            """
            )

            result = client.execute(mutation)
            return result.get("markAllNotificationsAsRead", False)
        except Exception as e:
            print(f"Mark all notifications as read failed: {str(e)}")
            return False

    async def archive_notification(
        self, notification_id: str, token: str
    ) -> Optional[Notification]:
        """
        Archives a notification.

        Args:
            notification_id (str): ID of the notification
            token (str): Authentication token

        Returns:
            Optional[Notification]: Archived notification or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ArchiveNotification($id: ID!) {
                    archiveNotification(id: $id) {
                        id
                        title
                        message
                        type
                        status
                        redirectUrl
                        appName
                        email
                        sms
                        whatsapp
                        userId
                        createdAt
                        updatedAt
                        readAt
                    }
                }
            """
            )

            variables = {"id": notification_id}
            result = client.execute(mutation, variable_values=variables)
            return result.get("archiveNotification")
        except Exception as e:
            print(f"Archive notification failed: {str(e)}")
            return None

    async def delete_notification(self, notification_id: str, token: str) -> bool:
        """
        Deletes a notification.

        Args:
            notification_id (str): ID of the notification
            token (str): Authentication token

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DeleteNotification($id: ID!) {
                    deleteNotification(id: $id)
                }
            """
            )

            variables = {"id": notification_id}
            result = client.execute(mutation, variable_values=variables)
            return result.get("deleteNotification", False)
        except Exception as e:
            print(f"Delete notification failed: {str(e)}")
            return False

    async def delete_notifications(
        self, notification_ids: List[str], token: str
    ) -> bool:
        """
        Deletes multiple notifications.

        Args:
            notification_ids (List[str]): List of notification IDs
            token (str): Authentication token

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DeleteNotifications($ids: [ID!]!) {
                    deleteNotifications(ids: $ids)
                }
            """
            )

            variables = {"ids": notification_ids}
            result = client.execute(mutation, variable_values=variables)
            return result.get("deleteNotifications", False)
        except Exception as e:
            print(f"Delete notifications failed: {str(e)}")
            return False

    async def delete_all_read_notifications(self, token: str) -> bool:
        """
        Deletes all read notifications for a specific user.

        Args:
            token (str): Authentication token

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DeleteAllReadNotifications {
                    deleteAllReadNotifications
                }
            """
            )

            result = client.execute(mutation)
            return result.get("deleteAllReadNotifications", False)
        except Exception as e:
            print(f"Delete all read notifications failed: {str(e)}")
            return False

    async def get_notification_counts_by_app(
        self, token: str
    ) -> Optional[NotificationCountsResponse]:
        """
        Gets notification counts grouped by application for the authenticated user.  # noqa: E501

        Args:
            token (str): Authentication token

        Returns:
            NotificationCountsResponse: Notification counts grouped by app, or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetNotificationCountsByApp {
                    getNotificationCountsByApp {
                        appCounts {
                            appName
                            totalCount
                            unreadCount
                            readCount
                        }
                        totalNotifications
                        totalUnread
                        totalRead
                    }
                }
            """
            )

            result = client.execute(query)
            return result.get("getNotificationCountsByApp", None)
        except Exception as e:
            print(f"Get notification counts by app failed: {str(e)}")
            return None


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Notification client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = NotificationClient(graphql_endpoint)


def get_client() -> NotificationClient:
    """Get the default Notification client."""
    if _default_client is None:
        raise RuntimeError(
            "Notification client not initialized. Call initialize() first."
        )
    return _default_client


# Convenience functions that use the default client
async def get_notifications(*args, **kwargs):
    return await get_client().get_notifications(*args, **kwargs)


async def get_notification(*args, **kwargs):
    return await get_client().get_notification(*args, **kwargs)


async def get_unread_notifications(*args, **kwargs):
    return await get_client().get_unread_notifications(*args, **kwargs)


async def create_notification(*args, **kwargs):
    return await get_client().create_notification(*args, **kwargs)


async def update_notification(*args, **kwargs):
    return await get_client().update_notification(*args, **kwargs)


async def mark_notification_as_read(*args, **kwargs):
    return await get_client().mark_notification_as_read(*args, **kwargs)


async def mark_notifications_as_read(*args, **kwargs):
    return await get_client().mark_notifications_as_read(*args, **kwargs)


async def mark_all_notifications_as_read(*args, **kwargs):
    return await get_client().mark_all_notifications_as_read(*args, **kwargs)


async def archive_notification(*args, **kwargs):
    return await get_client().archive_notification(*args, **kwargs)


async def delete_notification(*args, **kwargs):
    return await get_client().delete_notification(*args, **kwargs)


async def delete_notifications(*args, **kwargs):
    return await get_client().delete_notifications(*args, **kwargs)


async def delete_all_read_notifications(*args, **kwargs):
    return await get_client().delete_all_read_notifications(*args, **kwargs)


async def get_notification_counts_by_app(*args, **kwargs):
    return await get_client().get_notification_counts_by_app(*args, **kwargs)
