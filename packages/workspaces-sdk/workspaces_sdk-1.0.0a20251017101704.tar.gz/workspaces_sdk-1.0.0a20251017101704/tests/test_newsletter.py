"""
Comprehensive test suite for NewsletterClient

Tests all newsletter functionality including:
- Newsletter CRUD operations (create, update, get, get_list,
  get_paginated, delete)
- Subscription management (subscribe, update_sub, unsubscribe,
  get_my_subs, get_sub_by_id, bulk_subscribe)
- Delivery operations (send, schedule, cancel, force_process)
- Analytics and tracking (get_stats, get_deliveries)
- User preferences (get_preferences, update_preferences)
- Utility methods (validate_cron, get_scheduler_status)
- RBAC operations (share, assign_permission, revoke_permission,
  get_permissions)

Total methods tested: 25
"""

import os
import sys

# Add src to path before other imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from typing import List  # noqa: E402
from unittest.mock import Mock, patch  # noqa: E402

import pytest  # noqa: E402

from workspaces_sdk.newsletter import (  # noqa: E402
    AssignNewsletterPermissionInput,
    CreateNewsletterInput,
    Newsletter,
    NewsletterClient,
    NewsletterDelivery,
    NewsletterFilterInput,
    NewsletterPermission,
    NewsletterPermissionResult,
    NewsletterPreferencesInput,
    NewsletterSharingResult,
    NewsletterStats,
    NewsletterSubscription,
    NewsletterSubscriptionInput,
    PaginatedNewsletters,
    RevokeNewsletterPermissionInput,
    ShareNewsletterInput,
    UpdateNewsletterInput,
    UserNewsletterPreferences,
)


# Module-level fixtures
# (must be at module level to work with nested test classes)
@pytest.fixture
def newsletter_client():
    """Create a NewsletterClient instance for testing"""
    return NewsletterClient("https://api.example.com/graphql")


@pytest.fixture
def mock_client():
    """Mock GraphQL client - gql Client.execute() is synchronous"""
    mock = Mock()
    # Not AsyncMock - execute() is synchronous in gql library
    mock.execute = Mock()
    return mock


@pytest.fixture
def sample_newsletter() -> Newsletter:
    """Sample newsletter data for testing"""
    return {
        "id": "newsletter-123",
        "title": "Test Newsletter",
        "content": "<h1>Welcome</h1><p>This is a test newsletter.</p>",
        "subject": "Welcome to our newsletter",
        "productId": "product-456",
        "topics": ["product-updates", "announcements"],
        "isGeneral": False,
        "scheduleType": "INSTANT",
        "scheduledAt": None,
        "cronPattern": None,
        "status": "DRAFT",
        "recipientCount": 0,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
        "createdBy": {
            "id": "user-789",
            "name": "John Doe",
            "email": "john@example.com",
        },
        "brandingConfig": {
            "primaryColor": "#007bff",
            "logoUrl": "https://example.com/logo.png",
        },
    }


@pytest.fixture
def sample_subscription() -> NewsletterSubscription:
    """Sample subscription data for testing"""
    return {
        "id": "subscription-789",
        "userId": "user-123",
        "newsletterId": "newsletter-123",
        "status": "ACTIVE",
        "topics": ["product-updates", "announcements"],
        "productId": "product-456",
        "subscribedAt": "2024-01-01T00:00:00Z",
        "unsubscribedAt": None,
        "metadata": {"source": "web", "referrer": "homepage"},
        "user": {
            "id": "user-123",
            "name": "Jane Doe",
            "email": "jane@example.com",
        },
        "newsletter": {"id": "newsletter-123", "title": "Test Newsletter"},
    }


@pytest.fixture
def test_token():
    """Test authentication token"""
    return "test-jwt-token-123-abc-xyz"


class TestNewsletterClient:
    """Test suite for NewsletterClient"""

    class TestNewsletterCRUD:
        """Test newsletter CRUD operations (6 methods)"""

        @pytest.mark.asyncio
        async def test_create_newsletter_success(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test successful newsletter creation"""
            input_data: CreateNewsletterInput = {
                "title": "Test Newsletter",
                "content": "<h1>Welcome</h1><p>This is a test newsletter.</p>",
                "subject": "Welcome to our newsletter",
                "productId": "product-456",
                "topics": ["product-updates", "announcements"],
                "isGeneral": False,
                "scheduleType": "INSTANT",
                "scheduledAt": None,
                "cronPattern": None,
                "brandingConfig": {
                    "primaryColor": "#007bff",
                    "logoUrl": "https://example.com/logo.png",
                },
            }

            mock_client.execute.return_value = {"createNewsletter": sample_newsletter}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.create_newsletter(
                    input_data, test_token
                )

            assert result == sample_newsletter
            assert result["title"] == "Test Newsletter"
            assert result["status"] == "DRAFT"
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_create_newsletter_with_scheduling(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test newsletter creation with scheduling"""
            input_data: CreateNewsletterInput = {
                "title": "Scheduled Newsletter",
                "content": "<h1>Coming Soon</h1>",
                "subject": "Upcoming announcement",
                "scheduleType": "SCHEDULED",
                "scheduledAt": "2024-01-02T10:00:00Z",
                "cronPattern": None,
            }

            scheduled_newsletter = sample_newsletter.copy()
            scheduled_newsletter["scheduleType"] = "SCHEDULED"
            scheduled_newsletter["scheduledAt"] = "2024-01-02T10:00:00Z"

            mock_client.execute.return_value = {
                "createNewsletter": scheduled_newsletter
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.create_newsletter(
                    input_data, test_token
                )

            assert result["scheduleType"] == "SCHEDULED"
            assert result["scheduledAt"] == "2024-01-02T10:00:00Z"

        @pytest.mark.asyncio
        async def test_create_newsletter_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter creation with error"""
            input_data: CreateNewsletterInput = {
                "title": "Test Newsletter",
                "content": "<h1>Welcome</h1>",
                "subject": "Welcome to our newsletter",
                "topics": ["product-updates"],
            }

            mock_client.execute.side_effect = Exception("GraphQL Error: Unauthorized")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.create_newsletter(
                    input_data, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_update_newsletter_success(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test successful newsletter update"""
            newsletter_id = "newsletter-123"
            input_data: UpdateNewsletterInput = {
                "title": "Updated Newsletter Title",
                "content": "<h1>Updated Welcome</h1>",
                "isGeneral": True,
                "topics": ["general-updates"],
            }

            updated_newsletter = sample_newsletter.copy()
            updated_newsletter["title"] = "Updated Newsletter Title"
            updated_newsletter["isGeneral"] = True
            updated_newsletter["topics"] = ["general-updates"]

            mock_client.execute.return_value = {"updateNewsletter": updated_newsletter}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.update_newsletter(
                    newsletter_id, input_data, test_token
                )

            assert result == updated_newsletter
            assert result["title"] == "Updated Newsletter Title"
            assert result["isGeneral"] is True
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_update_newsletter_partial(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test partial newsletter update"""
            newsletter_id = "newsletter-123"
            input_data: UpdateNewsletterInput = {"title": "Partial Update"}

            updated_newsletter = sample_newsletter.copy()
            updated_newsletter["title"] = "Partial Update"

            mock_client.execute.return_value = {"updateNewsletter": updated_newsletter}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.update_newsletter(
                    newsletter_id, input_data, test_token
                )

            assert result["title"] == "Partial Update"

        @pytest.mark.asyncio
        async def test_update_newsletter_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter update with error"""
            newsletter_id = "newsletter-123"
            input_data: UpdateNewsletterInput = {"title": "Updated Title"}

            mock_client.execute.side_effect = Exception("GraphQL Error: Not found")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.update_newsletter(
                    newsletter_id, input_data, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_get_newsletter_success(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test successful newsletter retrieval"""
            newsletter_id = "newsletter-123"

            mock_client.execute.return_value = {"newsletter": sample_newsletter}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter(
                    newsletter_id, test_token
                )

            assert result == sample_newsletter
            assert result["id"] == newsletter_id
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_get_newsletter_not_found(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter retrieval when not found"""
            newsletter_id = "nonexistent-123"

            mock_client.execute.return_value = {"newsletter": None}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter(
                    newsletter_id, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_get_newsletter_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter retrieval with error"""
            newsletter_id = "newsletter-123"

            mock_client.execute.side_effect = Exception("Network error")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter(
                    newsletter_id, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_get_newsletters_with_filter(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test newsletters retrieval with filter"""
            filter_data: NewsletterFilterInput = {
                "status": "SENT",
                "productId": "product-456",
                "isGeneral": False,
                "topics": ["product-updates"],
            }

            newsletters = [sample_newsletter, sample_newsletter.copy()]

            mock_client.execute.return_value = {"newsletters": newsletters}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletters(
                    filter_data, test_token
                )

            assert result == newsletters
            assert len(result) == 2
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_get_newsletters_without_filter(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test newsletters retrieval without filter"""
            mock_client.execute.return_value = {"newsletters": [sample_newsletter]}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletters(None, test_token)

            assert len(result) == 1
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_get_newsletters_empty_result(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletters retrieval with empty result"""
            mock_client.execute.return_value = {"newsletters": []}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletters(None, test_token)

            assert result == []

        @pytest.mark.asyncio
        async def test_get_newsletters_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletters retrieval with error"""
            mock_client.execute.side_effect = Exception("GraphQL Error")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletters(None, test_token)

            assert result == []

        @pytest.mark.asyncio
        async def test_get_newsletters_paginated_success(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test paginated newsletters retrieval"""
            filter_data: NewsletterFilterInput = {"status": "SENT"}

            paginated_response: PaginatedNewsletters = {
                "newsletters": [sample_newsletter, sample_newsletter.copy()],
                "pagination": {
                    "currentPage": 1,
                    "pageSize": 10,
                    "totalPages": 5,
                    "totalCount": 42,
                    "hasNextPage": True,
                    "hasPreviousPage": False,
                },
            }

            mock_client.execute.return_value = {
                "newslettersPaginated": paginated_response
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletters_paginated(
                    filter_data, 1, 10, test_token
                )

            assert result == paginated_response
            assert len(result["newsletters"]) == 2
            assert result["pagination"]["currentPage"] == 1
            assert result["pagination"]["totalCount"] == 42

        @pytest.mark.asyncio
        async def test_get_newsletters_paginated_custom_page_size(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test paginated newsletters with custom page size"""
            paginated_response: PaginatedNewsletters = {
                "newsletters": [sample_newsletter] * 25,
                "pagination": {
                    "currentPage": 2,
                    "pageSize": 25,
                    "totalPages": 3,
                    "totalCount": 75,
                    "hasNextPage": True,
                    "hasPreviousPage": True,
                },
            }

            mock_client.execute.return_value = {
                "newslettersPaginated": paginated_response
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletters_paginated(
                    None, 2, 25, test_token
                )

            assert len(result["newsletters"]) == 25
            assert result["pagination"]["pageSize"] == 25

        @pytest.mark.asyncio
        async def test_get_newsletters_paginated_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test paginated newsletters retrieval with error"""
            mock_client.execute.side_effect = Exception("Database error")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletters_paginated(
                    None, 1, 10, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_delete_newsletter_success(
            self, newsletter_client, mock_client, test_token
        ):
            """Test successful newsletter deletion"""
            newsletter_id = "newsletter-123"

            mock_client.execute.return_value = {"deleteNewsletter": True}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.delete_newsletter(
                    newsletter_id, test_token
                )

            assert result is True
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_delete_newsletter_not_found(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter deletion when not found"""
            newsletter_id = "nonexistent-123"

            mock_client.execute.return_value = {"deleteNewsletter": False}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.delete_newsletter(
                    newsletter_id, test_token
                )

            assert result is False

        @pytest.mark.asyncio
        async def test_delete_newsletter_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter deletion with error"""
            newsletter_id = "newsletter-123"

            mock_client.execute.side_effect = Exception("Permission denied")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.delete_newsletter(
                    newsletter_id, test_token
                )

            assert result is False

    class TestNewsletterDelivery:
        """Test newsletter delivery operations (4 methods)"""

        @pytest.mark.asyncio
        async def test_send_newsletter_success(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test successful newsletter sending"""
            newsletter_id = "newsletter-123"

            sent_newsletter = sample_newsletter.copy()
            sent_newsletter["status"] = "SENDING"
            sent_newsletter["recipientCount"] = 100

            mock_client.execute.return_value = {"sendNewsletter": sent_newsletter}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.send_newsletter(
                    newsletter_id, test_token
                )

            assert result == sent_newsletter
            assert result["status"] == "SENDING"
            assert result["recipientCount"] == 100
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_send_newsletter_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter sending with error"""
            newsletter_id = "newsletter-123"

            mock_client.execute.side_effect = Exception("SMTP error")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.send_newsletter(
                    newsletter_id, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_schedule_newsletter_success(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test successful newsletter scheduling"""
            newsletter_id = "newsletter-123"

            scheduled_newsletter = sample_newsletter.copy()
            scheduled_newsletter["status"] = "SCHEDULED"
            scheduled_newsletter["scheduledAt"] = "2024-01-02T00:00:00Z"

            mock_client.execute.return_value = {
                "scheduleNewsletter": scheduled_newsletter
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.schedule_newsletter(
                    newsletter_id, test_token
                )

            assert result == scheduled_newsletter
            assert result["status"] == "SCHEDULED"
            assert result["scheduledAt"] == "2024-01-02T00:00:00Z"
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_schedule_newsletter_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter scheduling with error"""
            newsletter_id = "newsletter-123"

            mock_client.execute.side_effect = Exception("Invalid schedule time")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.schedule_newsletter(
                    newsletter_id, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_cancel_newsletter_schedule_success(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test successful newsletter schedule cancellation"""
            newsletter_id = "newsletter-123"

            cancelled_newsletter = sample_newsletter.copy()
            cancelled_newsletter["status"] = "DRAFT"
            cancelled_newsletter["scheduledAt"] = None

            mock_client.execute.return_value = {
                "cancelNewsletterSchedule": cancelled_newsletter
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.cancel_newsletter_schedule(
                    newsletter_id, test_token
                )

            assert result == cancelled_newsletter
            assert result["status"] == "DRAFT"
            assert result["scheduledAt"] is None
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_cancel_newsletter_schedule_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter schedule cancellation with error"""
            newsletter_id = "newsletter-123"

            mock_client.execute.side_effect = Exception("Newsletter already sent")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.cancel_newsletter_schedule(
                    newsletter_id, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_force_process_newsletter_delivery_success(
            self, newsletter_client, mock_client, sample_newsletter, test_token
        ):
            """Test successful force process newsletter delivery"""
            newsletter_id = "newsletter-123"

            processed_newsletter = sample_newsletter.copy()
            processed_newsletter["status"] = "SENDING"
            processed_newsletter["recipientCount"] = 150

            mock_client.execute.return_value = {
                "forceProcessNewsletterDelivery": processed_newsletter
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.force_process_newsletter_delivery(
                    newsletter_id, test_token
                )

            assert result == processed_newsletter
            assert result["status"] == "SENDING"
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_force_process_newsletter_delivery_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test force process newsletter delivery with error"""
            newsletter_id = "newsletter-123"

            mock_client.execute.side_effect = Exception("Admin permission required")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.force_process_newsletter_delivery(
                    newsletter_id, test_token
                )

            assert result is None

    class TestSubscriptionManagement:
        """Test subscription management operations (6 methods)"""

        @pytest.mark.asyncio
        async def test_subscribe_to_newsletter_success(
            self,
            newsletter_client,
            mock_client,
            sample_subscription,
            test_token,
        ):
            """Test successful newsletter subscription"""
            input_data: NewsletterSubscriptionInput = {
                "newsletterId": "newsletter-123",
                "topics": ["product-updates", "announcements"],
                "productId": "product-456",
                "metadata": {"source": "web"},
            }

            mock_client.execute.return_value = {
                "subscribeToNewsletter": sample_subscription
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.subscribe_to_newsletter(
                    input_data, test_token
                )

            assert result == sample_subscription
            assert result["status"] == "ACTIVE"
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_subscribe_to_newsletter_topic_only(
            self,
            newsletter_client,
            mock_client,
            sample_subscription,
            test_token,
        ):
            """Test newsletter subscription to topics only"""
            input_data: NewsletterSubscriptionInput = {
                "topics": ["general-updates"],
                "productId": "product-456",
            }

            topic_subscription = sample_subscription.copy()
            topic_subscription["newsletterId"] = None
            topic_subscription["topics"] = ["general-updates"]

            mock_client.execute.return_value = {
                "subscribeToNewsletter": topic_subscription
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.subscribe_to_newsletter(
                    input_data, test_token
                )

            assert result["newsletterId"] is None
            assert "general-updates" in result["topics"]

        @pytest.mark.asyncio
        async def test_subscribe_to_newsletter_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter subscription with error"""
            input_data: NewsletterSubscriptionInput = {
                "newsletterId": "newsletter-123",
                "topics": ["product-updates"],
            }

            mock_client.execute.side_effect = Exception("Already subscribed")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.subscribe_to_newsletter(
                    input_data, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_update_newsletter_subscription_success(
            self,
            newsletter_client,
            mock_client,
            sample_subscription,
            test_token,
        ):
            """Test successful subscription update"""
            subscription_id = "subscription-789"
            input_data: NewsletterSubscriptionInput = {
                "topics": ["product-updates"],
                "productId": "product-456",
            }

            updated_subscription = sample_subscription.copy()
            updated_subscription["topics"] = ["product-updates"]

            mock_client.execute.return_value = {
                "updateNewsletterSubscription": updated_subscription
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.update_newsletter_subscription(
                    subscription_id, input_data, test_token
                )

            assert result == updated_subscription
            assert result["topics"] == ["product-updates"]
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_update_newsletter_subscription_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test subscription update with error"""
            subscription_id = "subscription-789"
            input_data: NewsletterSubscriptionInput = {"topics": ["invalid-topic"]}

            mock_client.execute.side_effect = Exception("Invalid topic")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.update_newsletter_subscription(
                    subscription_id, input_data, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_unsubscribe_from_newsletter_success(
            self, newsletter_client, mock_client, test_token
        ):
            """Test successful newsletter unsubscription"""
            subscription_id = "subscription-789"

            mock_client.execute.return_value = {"unsubscribeFromNewsletter": True}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.unsubscribe_from_newsletter(
                    subscription_id, test_token
                )

            assert result is True
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_unsubscribe_from_newsletter_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter unsubscription with error"""
            subscription_id = "subscription-789"

            mock_client.execute.side_effect = Exception("Subscription not found")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.unsubscribe_from_newsletter(
                    subscription_id, test_token
                )

            assert result is False

        @pytest.mark.asyncio
        async def test_get_my_newsletter_subscriptions_success(
            self,
            newsletter_client,
            mock_client,
            sample_subscription,
            test_token,
        ):
            """Test successful retrieval of user subscriptions"""
            subscriptions = [sample_subscription, sample_subscription.copy()]

            mock_client.execute.return_value = {
                "myNewsletterSubscriptions": subscriptions
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_my_newsletter_subscriptions(
                    test_token
                )

            assert result == subscriptions
            assert len(result) == 2
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_get_my_newsletter_subscriptions_empty(
            self, newsletter_client, mock_client, test_token
        ):
            """Test retrieval of user subscriptions when empty"""
            mock_client.execute.return_value = {"myNewsletterSubscriptions": []}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_my_newsletter_subscriptions(
                    test_token
                )

            assert result == []

        @pytest.mark.asyncio
        async def test_get_my_newsletter_subscriptions_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test retrieval of user subscriptions with error"""
            mock_client.execute.side_effect = Exception("Authentication failed")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_my_newsletter_subscriptions(
                    test_token
                )

            assert result == []

        @pytest.mark.asyncio
        async def test_get_newsletter_subscription_success(
            self,
            newsletter_client,
            mock_client,
            sample_subscription,
            test_token,
        ):
            """Test successful retrieval of single subscription"""
            subscription_id = "subscription-789"

            mock_client.execute.return_value = {
                "newsletterSubscription": sample_subscription
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_subscription(
                    subscription_id, test_token
                )

            assert result == sample_subscription
            assert result["id"] == subscription_id
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_get_newsletter_subscription_not_found(
            self, newsletter_client, mock_client, test_token
        ):
            """Test retrieval of subscription when not found"""
            subscription_id = "nonexistent-789"

            mock_client.execute.return_value = {"newsletterSubscription": None}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_subscription(
                    subscription_id, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_get_newsletter_subscription_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test retrieval of subscription with error"""
            subscription_id = "subscription-789"

            mock_client.execute.side_effect = Exception("Database error")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_subscription(
                    subscription_id, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_bulk_subscribe_success(
            self,
            newsletter_client,
            mock_client,
            sample_subscription,
            test_token,
        ):
            """Test successful bulk subscription"""
            user_ids = ["user-123", "user-456", "user-789"]
            input_data: NewsletterSubscriptionInput = {
                "newsletterId": "newsletter-123",
                "topics": ["product-updates"],
                "productId": "product-456",
            }

            subscriptions = [
                sample_subscription,
                {
                    **sample_subscription,
                    "id": "subscription-456",
                    "userId": "user-456",
                },
                {
                    **sample_subscription,
                    "id": "subscription-101",
                    "userId": "user-789",
                },
            ]

            mock_client.execute.return_value = {"bulkSubscribe": subscriptions}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.bulk_subscribe(
                    user_ids, input_data, test_token
                )

            assert result == subscriptions
            assert len(result) == 3
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_bulk_subscribe_empty_list(
            self, newsletter_client, mock_client, test_token
        ):
            """Test bulk subscription with empty user list"""
            user_ids = []
            input_data: NewsletterSubscriptionInput = {
                "newsletterId": "newsletter-123",
                "topics": ["product-updates"],
            }

            mock_client.execute.return_value = {"bulkSubscribe": []}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.bulk_subscribe(
                    user_ids, input_data, test_token
                )

            assert result == []

        @pytest.mark.asyncio
        async def test_bulk_subscribe_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test bulk subscription with error"""
            user_ids = ["user-123", "user-456"]
            input_data: NewsletterSubscriptionInput = {
                "newsletterId": "newsletter-123",
                "topics": ["product-updates"],
            }

            mock_client.execute.side_effect = Exception("Bulk operation failed")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.bulk_subscribe(
                    user_ids, input_data, test_token
                )

            assert result == []

    class TestNewsletterPreferences:
        """Test newsletter preferences operations (2 methods)"""

        @pytest.mark.asyncio
        async def test_get_newsletter_preferences_success(
            self, newsletter_client, mock_client, test_token
        ):
            """Test successful retrieval of user preferences"""
            expected_preferences: UserNewsletterPreferences = {
                "id": "pref-123",
                "userId": "user-123",
                "emailNotifications": True,
                "frequency": "WEEKLY",
                "topicPreferences": ["product-updates", "announcements"],
                "productPreferences": ["product-456"],
                "unsubscribeAll": False,
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
            }

            mock_client.execute.return_value = {
                "getUserNewsletterPreferences": expected_preferences
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_preferences(test_token)

            assert result == expected_preferences
            assert result["frequency"] == "WEEKLY"
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_get_newsletter_preferences_not_found(
            self, newsletter_client, mock_client, test_token
        ):
            """Test retrieval of preferences when not found"""
            mock_client.execute.return_value = {"getUserNewsletterPreferences": None}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_preferences(test_token)

            assert result is None

        @pytest.mark.asyncio
        async def test_get_newsletter_preferences_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test retrieval of preferences with error"""
            mock_client.execute.side_effect = Exception("Database error")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_preferences(test_token)

            assert result is None

        @pytest.mark.asyncio
        async def test_update_newsletter_preferences_success(
            self, newsletter_client, mock_client, test_token
        ):
            """Test successful update of user preferences"""
            input_data: NewsletterPreferencesInput = {
                "emailNotifications": False,
                "frequency": "MONTHLY",
                "topicPreferences": ["announcements"],
                "productPreferences": ["product-456", "product-789"],
                "unsubscribeAll": False,
            }

            updated_preferences: UserNewsletterPreferences = {
                "id": "pref-123",
                "userId": "user-123",
                "emailNotifications": False,
                "frequency": "MONTHLY",
                "topicPreferences": ["announcements"],
                "productPreferences": ["product-456", "product-789"],
                "unsubscribeAll": False,
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-02T00:00:00Z",
            }

            mock_client.execute.return_value = {
                "updateNewsletterPreferences": updated_preferences
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.update_newsletter_preferences(
                    input_data, test_token
                )

            assert result == updated_preferences
            assert result["frequency"] == "MONTHLY"
            assert result["emailNotifications"] is False
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_update_newsletter_preferences_unsubscribe_all(
            self, newsletter_client, mock_client, test_token
        ):
            """Test updating preferences to unsubscribe from all"""
            input_data: NewsletterPreferencesInput = {"unsubscribeAll": True}

            updated_preferences: UserNewsletterPreferences = {
                "id": "pref-123",
                "userId": "user-123",
                "emailNotifications": False,
                "frequency": "IMMEDIATE",
                "topicPreferences": [],
                "productPreferences": [],
                "unsubscribeAll": True,
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-02T00:00:00Z",
            }

            mock_client.execute.return_value = {
                "updateNewsletterPreferences": updated_preferences
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.update_newsletter_preferences(
                    input_data, test_token
                )

            assert result["unsubscribeAll"] is True

        @pytest.mark.asyncio
        async def test_update_newsletter_preferences_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test update of preferences with error"""
            input_data: NewsletterPreferencesInput = {"frequency": "INVALID"}

            mock_client.execute.side_effect = Exception("Invalid frequency")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.update_newsletter_preferences(
                    input_data, test_token
                )

            assert result is None

    class TestAnalyticsAndTracking:
        """Test analytics and tracking operations (2 methods)"""

        @pytest.mark.asyncio
        async def test_get_newsletter_stats_success(
            self, newsletter_client, mock_client, test_token
        ):
            """Test successful newsletter statistics retrieval"""
            newsletter_id = "newsletter-123"
            expected_stats: NewsletterStats = {
                "total": 1000,
                "sent": 950,
                "pending": 0,
                "failed": 50,
                "opened": 600,
                "clicked": 200,
                "sentRate": 0.95,
                "openRate": 0.632,
                "clickRate": 0.211,
                "clickToOpenRate": 0.333,
            }

            mock_client.execute.return_value = {"newsletterStats": expected_stats}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_stats(
                    newsletter_id, test_token
                )

            assert result == expected_stats
            assert result["total"] == 1000
            assert result["openRate"] == 0.632
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_get_newsletter_stats_zero_recipients(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter statistics with zero recipients"""
            newsletter_id = "newsletter-123"
            expected_stats: NewsletterStats = {
                "total": 0,
                "sent": 0,
                "pending": 0,
                "failed": 0,
                "opened": 0,
                "clicked": 0,
                "sentRate": 0.0,
                "openRate": 0.0,
                "clickRate": 0.0,
                "clickToOpenRate": 0.0,
            }

            mock_client.execute.return_value = {"newsletterStats": expected_stats}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_stats(
                    newsletter_id, test_token
                )

            assert result["total"] == 0

        @pytest.mark.asyncio
        async def test_get_newsletter_stats_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter statistics retrieval with error"""
            newsletter_id = "newsletter-123"

            mock_client.execute.side_effect = Exception("Stats not available")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_stats(
                    newsletter_id, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_get_newsletter_deliveries_success(
            self, newsletter_client, mock_client, test_token
        ):
            """Test successful newsletter deliveries retrieval"""
            newsletter_id = "newsletter-123"
            expected_deliveries: List[NewsletterDelivery] = [
                {
                    "id": "delivery-456",
                    "newsletterId": "newsletter-123",
                    "recipientId": "user-789",
                    "status": "sent",
                    "sentAt": "2024-01-01T00:00:00Z",
                    "failureReason": None,
                    "messageId": "msg-123",
                    "opened": True,
                    "openedAt": "2024-01-01T01:00:00Z",
                    "clicked": False,
                    "clickedAt": None,
                },
                {
                    "id": "delivery-457",
                    "newsletterId": "newsletter-123",
                    "recipientId": "user-790",
                    "status": "sent",
                    "sentAt": "2024-01-01T00:00:00Z",
                    "failureReason": None,
                    "messageId": "msg-124",
                    "opened": True,
                    "openedAt": "2024-01-01T01:30:00Z",
                    "clicked": True,
                    "clickedAt": "2024-01-01T02:00:00Z",
                },
            ]

            mock_client.execute.return_value = {
                "newsletterDeliveries": expected_deliveries
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_deliveries(
                    newsletter_id, test_token
                )

            assert result == expected_deliveries
            assert len(result) == 2
            assert result[1]["clicked"] is True
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_get_newsletter_deliveries_empty(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter deliveries retrieval with empty result"""
            newsletter_id = "newsletter-123"

            mock_client.execute.return_value = {"newsletterDeliveries": []}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_deliveries(
                    newsletter_id, test_token
                )

            assert result == []

        @pytest.mark.asyncio
        async def test_get_newsletter_deliveries_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter deliveries retrieval with error"""
            newsletter_id = "newsletter-123"

            mock_client.execute.side_effect = Exception("Deliveries not found")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_deliveries(
                    newsletter_id, test_token
                )

            assert result == []

    class TestUtilityMethods:
        """Test utility methods (2 methods)"""

        @pytest.mark.asyncio
        async def test_validate_cron_pattern_valid(
            self, newsletter_client, mock_client, test_token
        ):
            """Test validation of valid cron pattern"""
            pattern = "0 9 * * MON"

            mock_client.execute.return_value = {"validateCronPattern": True}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.validate_cron_pattern(
                    pattern, test_token
                )

            assert result is True
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_validate_cron_pattern_complex_valid(
            self, newsletter_client, mock_client, test_token
        ):
            """Test validation of complex valid cron pattern"""
            pattern = "0 0,12 * * *"  # Every day at midnight and noon

            mock_client.execute.return_value = {"validateCronPattern": True}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.validate_cron_pattern(
                    pattern, test_token
                )

            assert result is True

        @pytest.mark.asyncio
        async def test_validate_cron_pattern_invalid(
            self, newsletter_client, mock_client, test_token
        ):
            """Test validation of invalid cron pattern"""
            pattern = "invalid-pattern"

            mock_client.execute.return_value = {"validateCronPattern": False}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.validate_cron_pattern(
                    pattern, test_token
                )

            assert result is False
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_validate_cron_pattern_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test validation of cron pattern with error"""
            pattern = "0 9 * * MON"

            mock_client.execute.side_effect = Exception(
                "Validation service unavailable"
            )

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.validate_cron_pattern(
                    pattern, test_token
                )

            assert result is False

        @pytest.mark.asyncio
        async def test_get_scheduler_status_success(
            self, newsletter_client, mock_client, test_token
        ):
            """Test successful scheduler status retrieval"""
            expected_status = {
                "isRunning": True,
                "lastRun": "2024-01-01T08:00:00Z",
                "nextRun": "2024-01-01T09:00:00Z",
            }

            mock_client.execute.return_value = {"schedulerStatus": expected_status}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_scheduler_status(test_token)

            assert result == expected_status
            assert result["isRunning"] is True
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_get_scheduler_status_not_running(
            self, newsletter_client, mock_client, test_token
        ):
            """Test scheduler status when scheduler is not running"""
            expected_status = {
                "isRunning": False,
                "lastRun": "2024-01-01T08:00:00Z",
                "nextRun": None,
            }

            mock_client.execute.return_value = {"schedulerStatus": expected_status}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_scheduler_status(test_token)

            assert result["isRunning"] is False
            assert result["nextRun"] is None

        @pytest.mark.asyncio
        async def test_get_scheduler_status_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test scheduler status retrieval with error"""
            mock_client.execute.side_effect = Exception("Scheduler unavailable")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_scheduler_status(test_token)

            assert result is None

    class TestRBACOperations:
        """Test RBAC operations (4 methods)"""

        @pytest.mark.asyncio
        async def test_share_newsletter_success(
            self, newsletter_client, mock_client, test_token
        ):
            """Test successful newsletter sharing"""
            input_data: ShareNewsletterInput = {
                "newsletterId": "newsletter-123",
                "recipientEmails": ["user1@example.com", "user2@example.com"],
                "message": "Check out this newsletter!",
                "allowForwarding": True,
            }

            expected_result: NewsletterSharingResult = {
                "success": True,
                "sharedWith": ["user1@example.com", "user2@example.com"],
                "failedRecipients": [],
                "message": "Newsletter shared successfully",
            }

            mock_client.execute.return_value = {"shareNewsletter": expected_result}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.share_newsletter(
                    input_data, test_token
                )

            assert result == expected_result
            assert result["success"] is True
            assert len(result["sharedWith"]) == 2
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_share_newsletter_partial_failure(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter sharing with partial failure"""
            input_data: ShareNewsletterInput = {
                "newsletterId": "newsletter-123",
                "recipientEmails": [
                    "valid@example.com",
                    "invalid@example.com",
                ],
                "message": "Check this out",
            }

            expected_result: NewsletterSharingResult = {
                "success": True,
                "sharedWith": ["valid@example.com"],
                "failedRecipients": ["invalid@example.com"],
                "message": "Shared with some recipients",
            }

            mock_client.execute.return_value = {"shareNewsletter": expected_result}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.share_newsletter(
                    input_data, test_token
                )

            assert len(result["failedRecipients"]) == 1

        @pytest.mark.asyncio
        async def test_share_newsletter_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test newsletter sharing with error"""
            input_data: ShareNewsletterInput = {
                "newsletterId": "newsletter-123",
                "recipientEmails": ["user@example.com"],
            }

            mock_client.execute.side_effect = Exception("Sharing failed")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.share_newsletter(
                    input_data, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_assign_newsletter_permission_success(
            self, newsletter_client, mock_client, test_token
        ):
            """Test successful permission assignment"""
            input_data: AssignNewsletterPermissionInput = {
                "newsletterId": "newsletter-123",
                "userId": "user-456",
                "permission": "EDIT",
                "expiresAt": "2024-12-31T23:59:59Z",
            }

            expected_result: NewsletterPermissionResult = {
                "success": True,
                "message": "Permission assigned successfully",
                "permission": {
                    "id": "perm-789",
                    "newsletterId": "newsletter-123",
                    "userId": "user-456",
                    "permission": "EDIT",
                    "grantedBy": {
                        "id": "user-123",
                        "name": "Admin User",
                        "email": "admin@example.com",
                    },
                    "grantedAt": "2024-01-01T00:00:00Z",
                    "expiresAt": "2024-12-31T23:59:59Z",
                },
            }

            mock_client.execute.return_value = {
                "assignNewsletterPermission": expected_result
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.assign_newsletter_permission(
                    input_data, test_token
                )

            assert result == expected_result
            assert result["success"] is True
            assert result["permission"]["permission"] == "EDIT"
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_assign_newsletter_permission_admin(
            self, newsletter_client, mock_client, test_token
        ):
            """Test assigning admin permission"""
            input_data: AssignNewsletterPermissionInput = {
                "newsletterId": "newsletter-123",
                "userId": "user-456",
                "permission": "ADMIN",
            }

            expected_result: NewsletterPermissionResult = {
                "success": True,
                "message": "Admin permission assigned",
                "permission": {
                    "id": "perm-790",
                    "newsletterId": "newsletter-123",
                    "userId": "user-456",
                    "permission": "ADMIN",
                    "grantedBy": {
                        "id": "user-123",
                        "name": "Owner",
                        "email": "owner@example.com",
                    },
                    "grantedAt": "2024-01-01T00:00:00Z",
                    "expiresAt": None,
                },
            }

            mock_client.execute.return_value = {
                "assignNewsletterPermission": expected_result
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.assign_newsletter_permission(
                    input_data, test_token
                )

            assert result["permission"]["permission"] == "ADMIN"

        @pytest.mark.asyncio
        async def test_assign_newsletter_permission_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test permission assignment with error"""
            input_data: AssignNewsletterPermissionInput = {
                "newsletterId": "newsletter-123",
                "userId": "user-456",
                "permission": "INVALID",
            }

            mock_client.execute.side_effect = Exception("Invalid permission level")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.assign_newsletter_permission(
                    input_data, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_revoke_newsletter_permission_success(
            self, newsletter_client, mock_client, test_token
        ):
            """Test successful permission revocation"""
            input_data: RevokeNewsletterPermissionInput = {
                "newsletterId": "newsletter-123",
                "userId": "user-456",
            }

            expected_result: NewsletterPermissionResult = {
                "success": True,
                "message": "Permission revoked successfully",
                "permission": {
                    "id": "perm-789",
                    "newsletterId": "newsletter-123",
                    "userId": "user-456",
                },
            }

            mock_client.execute.return_value = {
                "revokeNewsletterPermission": expected_result
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.revoke_newsletter_permission(
                    input_data, test_token
                )

            assert result == expected_result
            assert result["success"] is True
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_revoke_newsletter_permission_not_found(
            self, newsletter_client, mock_client, test_token
        ):
            """Test permission revocation when permission not found"""
            input_data: RevokeNewsletterPermissionInput = {
                "newsletterId": "newsletter-123",
                "userId": "user-456",
            }

            expected_result: NewsletterPermissionResult = {
                "success": False,
                "message": "Permission not found",
                "permission": None,
            }

            mock_client.execute.return_value = {
                "revokeNewsletterPermission": expected_result
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.revoke_newsletter_permission(
                    input_data, test_token
                )

            assert result["success"] is False

        @pytest.mark.asyncio
        async def test_revoke_newsletter_permission_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test permission revocation with error"""
            input_data: RevokeNewsletterPermissionInput = {
                "newsletterId": "newsletter-123",
                "userId": "user-456",
            }

            mock_client.execute.side_effect = Exception("Revocation failed")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.revoke_newsletter_permission(
                    input_data, test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_get_newsletter_permissions_success(
            self, newsletter_client, mock_client, test_token
        ):
            """Test successful retrieval of newsletter permissions"""
            newsletter_id = "newsletter-123"

            expected_permissions: List[NewsletterPermission] = [
                {
                    "id": "perm-789",
                    "newsletterId": "newsletter-123",
                    "userId": "user-456",
                    "permission": "EDIT",
                    "grantedBy": {
                        "id": "user-123",
                        "name": "Admin",
                        "email": "admin@example.com",
                    },
                    "grantedAt": "2024-01-01T00:00:00Z",
                    "expiresAt": None,
                    "user": {
                        "id": "user-456",
                        "name": "Editor User",
                        "email": "editor@example.com",
                    },
                },
                {
                    "id": "perm-790",
                    "newsletterId": "newsletter-123",
                    "userId": "user-789",
                    "permission": "VIEW",
                    "grantedBy": {
                        "id": "user-123",
                        "name": "Admin",
                        "email": "admin@example.com",
                    },
                    "grantedAt": "2024-01-01T00:00:00Z",
                    "expiresAt": "2024-12-31T23:59:59Z",
                    "user": {
                        "id": "user-789",
                        "name": "Viewer User",
                        "email": "viewer@example.com",
                    },
                },
            ]

            mock_client.execute.return_value = {
                "newsletterPermissions": expected_permissions
            }

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_permissions(
                    newsletter_id, test_token
                )

            assert result == expected_permissions
            assert len(result) == 2
            assert result[0]["permission"] == "EDIT"
            assert result[1]["permission"] == "VIEW"
            mock_client.execute.assert_called_once()

        @pytest.mark.asyncio
        async def test_get_newsletter_permissions_empty(
            self, newsletter_client, mock_client, test_token
        ):
            """Test retrieval of permissions when empty"""
            newsletter_id = "newsletter-123"

            mock_client.execute.return_value = {"newsletterPermissions": []}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_permissions(
                    newsletter_id, test_token
                )

            assert result == []

        @pytest.mark.asyncio
        async def test_get_newsletter_permissions_error(
            self, newsletter_client, mock_client, test_token
        ):
            """Test retrieval of permissions with error"""
            newsletter_id = "newsletter-123"

            mock_client.execute.side_effect = Exception("Permission denied")

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_permissions(
                    newsletter_id, test_token
                )

            assert result == []

    class TestErrorHandling:
        """Test comprehensive error handling scenarios"""

        @pytest.mark.asyncio
        async def test_graphql_error_handling(
            self, newsletter_client, mock_client, test_token
        ):
            """Test graceful handling of GraphQL errors"""
            mock_client.execute.side_effect = Exception(
                "GraphQL Error: Field not found"
            )

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter(
                    "newsletter-123", test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_network_error_handling(
            self, newsletter_client, mock_client, test_token
        ):
            """Test graceful handling of network errors"""
            mock_client.execute.side_effect = Exception(
                "Network Error: Connection timeout"
            )

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletters(None, test_token)

            assert result == []

        @pytest.mark.asyncio
        async def test_authentication_error_handling(
            self, newsletter_client, mock_client, test_token
        ):
            """Test graceful handling of authentication errors"""
            mock_client.execute.side_effect = Exception(
                "Authentication Error: Invalid token"
            )

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.delete_newsletter(
                    "newsletter-123", test_token
                )

            assert result is False

        @pytest.mark.asyncio
        async def test_permission_error_handling(
            self, newsletter_client, mock_client, test_token
        ):
            """Test graceful handling of permission errors"""
            input_data: CreateNewsletterInput = {
                "title": "Test",
                "content": "Content",
                "subject": "Subject",
            }

            mock_client.execute.side_effect = Exception(
                "Permission Error: Insufficient privileges"
            )

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.create_newsletter(
                    input_data, test_token
                )

            assert result is None

    class TestEdgeCases:
        """Test edge cases and boundary conditions"""

        @pytest.mark.asyncio
        async def test_empty_response_handling(
            self, newsletter_client, mock_client, test_token
        ):
            """Test handling of empty responses"""
            mock_client.execute.return_value = {}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter(
                    "newsletter-123", test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_none_response_handling(
            self, newsletter_client, mock_client, test_token
        ):
            """Test handling of None responses"""
            mock_client.execute.return_value = None

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletters(None, test_token)

            # Should return [] because exception handler catches
            # the AttributeError
            assert result == []

        @pytest.mark.asyncio
        async def test_malformed_response_handling(
            self, newsletter_client, mock_client, test_token
        ):
            """Test handling of malformed responses"""
            mock_client.execute.return_value = {"unexpectedField": "unexpected_value"}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletter_stats(
                    "newsletter-123", test_token
                )

            assert result is None

        @pytest.mark.asyncio
        async def test_large_response_handling(
            self, newsletter_client, mock_client, test_token
        ):
            """Test handling of large responses"""
            large_newsletter_list = [
                {
                    "id": f"newsletter-{i}",
                    "title": f"Newsletter {i}",
                    "content": "<h1>Content</h1>" * 100,  # Large content
                    "subject": f"Subject {i}",
                    "topics": ["topic"] * 10,  # Many topics
                    "status": "SENT",
                    "productId": "product-456",
                    "isGeneral": False,
                    "scheduleType": "INSTANT",
                    "scheduledAt": None,
                    "cronPattern": None,
                    "recipientCount": 1000,
                    "createdAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-01T00:00:00Z",
                    "createdBy": {
                        "id": "user-1",
                        "name": "User",
                        "email": "user@example.com",
                    },
                    "brandingConfig": {},
                }
                for i in range(1000)  # Large list
            ]

            mock_client.execute.return_value = {"newsletters": large_newsletter_list}

            with patch.object(
                newsletter_client, "get_client", return_value=mock_client
            ):
                result = await newsletter_client.get_newsletters(None, test_token)

            assert result == large_newsletter_list
            assert len(result) == 1000

    class TestClientCreation:
        """Test GraphQL client creation"""

        @pytest.mark.asyncio
        async def test_get_client_creates_client_with_headers(
            self, newsletter_client, test_token
        ):
            """Test that get_client creates client with proper headers"""
            with patch(
                "workspaces_sdk.newsletter.get_default_headers"
            ) as mock_headers, patch(
                "workspaces_sdk.newsletter.RequestsHTTPTransport"
            ) as mock_transport, patch(
                "workspaces_sdk.newsletter.Client"
            ):

                mock_headers.return_value = {"x-product-id": "test-product"}

                newsletter_client.get_client(test_token)

                # Verify headers include auth token
                expected_headers = {
                    "x-product-id": "test-product",
                    "Authorization": f"Bearer {test_token}",
                }

                mock_transport.assert_called_once()
                call_args = mock_transport.call_args
                assert call_args[1]["url"] == newsletter_client.graphql_endpoint
                assert call_args[1]["headers"] == expected_headers


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
