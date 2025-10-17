import pytest
import asyncio
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List, Optional

# Import the newsletter module components (assuming they will be implemented)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from workspaces_sdk.newsletter import (
    NewsletterClient,
    Newsletter,
    NewsletterSubscription,
    NewsletterDelivery,
    NewsletterStats,
    CreateNewsletterInput,
    UpdateNewsletterInput,
    NewsletterSubscriptionInput,
    NewsletterFilterInput,
    PaginatedNewsletters,
    PaginationInfo,
    NewsletterPreferencesInput,
    UserNewsletterPreferences,
    ShareNewsletterInput,
    NewsletterSharingResult,
    AssignNewsletterPermissionInput,
    RevokeNewsletterPermissionInput,
    NewsletterPermissionResult,
    NewsletterPermission
)


class TestNewsletterClient:
    """Comprehensive test suite for NewsletterClient"""

    @pytest.fixture
    def client(self):
        """Create a NewsletterClient instance for testing"""
        return NewsletterClient("http://localhost:4000/graphql")

    @pytest.fixture
    def mock_token(self):
        """Mock authentication token"""
        return "mock-jwt-token-12345"

    @pytest.fixture
    def mock_newsletter(self) -> Newsletter:
        """Mock newsletter data factory"""
        return {
            "id": "newsletter-1",
            "title": "Test Newsletter",
            "content": "<h1>Test Content</h1><p>Newsletter body content</p>",
            "subject": "Test Newsletter Subject",
            "productId": "product-1",
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
                "id": "user-1",
                "name": "Test User",
                "email": "test@example.com"
            },
            "brandingConfig": None
        }

    @pytest.fixture
    def mock_newsletter_subscription(self) -> NewsletterSubscription:
        """Mock newsletter subscription data factory"""
        return {
            "id": "subscription-1",
            "userId": "user-1",
            "newsletterId": "newsletter-1",
            "status": "ACTIVE",
            "topics": ["product-updates"],
            "productId": "product-1",
            "subscribedAt": "2024-01-01T00:00:00Z",
            "unsubscribedAt": None,
            "metadata": {"source": "api", "campaign": "test"},
            "user": {
                "id": "user-1",
                "name": "Test User",
                "email": "test@example.com"
            },
            "newsletter": {
                "id": "newsletter-1",
                "title": "Test Newsletter",
                "description": "Test newsletter description"
            }
        }

    @pytest.fixture
    def mock_newsletter_delivery(self) -> NewsletterDelivery:
        """Mock newsletter delivery data factory"""
        return {
            "id": "delivery-1",
            "newsletterId": "newsletter-1",
            "recipientId": "recipient-1",
            "status": "sent",
            "sentAt": "2024-01-01T12:00:00Z",
            "failureReason": None,
            "messageId": "msg-abc123",
            "opened": False,
            "openedAt": None,
            "clicked": False,
            "clickedAt": None
        }

    @pytest.fixture
    def mock_newsletter_stats(self) -> NewsletterStats:
        """Mock newsletter statistics data factory"""
        return {
            "total": 100,
            "sent": 95,
            "pending": 3,
            "failed": 2,
            "opened": 42,
            "clicked": 18,
            "sentRate": 95.0,
            "openRate": 44.2,
            "clickRate": 18.9,
            "clickToOpenRate": 42.8
        }

    @pytest.fixture
    def mock_paginated_newsletters(self, mock_newsletter) -> PaginatedNewsletters:
        """Mock paginated newsletters data factory"""
        return {
            "newsletters": [
                mock_newsletter,
                {**mock_newsletter, "id": "newsletter-2", "title": "Second Newsletter"},
                {**mock_newsletter, "id": "newsletter-3", "title": "Third Newsletter"}
            ],
            "pagination": {
                "currentPage": 1,
                "pageSize": 10,
                "totalPages": 5,
                "totalCount": 45,
                "hasNextPage": True,
                "hasPreviousPage": False
            }
        }

    @pytest.fixture
    def mock_user_newsletter_preferences(self) -> UserNewsletterPreferences:
        """Mock user newsletter preferences data factory"""
        return {
            "id": "preferences-1",
            "userId": "user-1",
            "emailNotifications": True,
            "frequency": "DAILY",
            "topicPreferences": ["product-updates", "announcements"],
            "productPreferences": ["product-1", "product-2"],
            "unsubscribeAll": False,
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z"
        }

    @pytest.fixture
    def mock_newsletter_sharing_result(self) -> NewsletterSharingResult:
        """Mock newsletter sharing result data factory"""
        return {
            "success": True,
            "sharedWith": ["user1@example.com", "user2@example.com"],
            "failedRecipients": [],
            "message": "Newsletter shared successfully"
        }

    @pytest.fixture
    def mock_newsletter_permission_result(self) -> NewsletterPermissionResult:
        """Mock newsletter permission result data factory"""
        return {
            "success": True,
            "message": "Permission assigned successfully",
            "permission": {
                "id": "permission-1",
                "newsletterId": "newsletter-1",
                "userId": "user-2",
                "permission": "EDIT",
                "grantedBy": {
                    "id": "user-1",
                    "name": "Admin User",
                    "email": "admin@example.com"
                },
                "grantedAt": "2024-01-01T00:00:00Z",
                "expiresAt": None
            }
        }

    @pytest.fixture
    def mock_newsletter_permission(self) -> NewsletterPermission:
        """Mock newsletter permission data factory"""
        return {
            "id": "permission-1",
            "newsletterId": "newsletter-1",
            "userId": "user-2",
            "permission": "EDIT",
            "grantedBy": {
                "id": "user-1",
                "name": "Admin User",
                "email": "admin@example.com"
            },
            "grantedAt": "2024-01-01T00:00:00Z",
            "expiresAt": None,
            "user": {
                "id": "user-2",
                "name": "Editor User",
                "email": "editor@example.com"
            }
        }

    # Newsletter CRUD Operations Tests
    @pytest.mark.asyncio
    async def test_create_newsletter_success(self, client, mock_token, mock_newsletter):
        """Test successful newsletter creation"""
        input_data: CreateNewsletterInput = {
            "title": "Test Newsletter",
            "content": "<h1>Test Content</h1>",
            "subject": "Test Subject",
            "productId": "product-1",
            "topics": ["product-updates"],
            "isGeneral": False,
            "scheduleType": "INSTANT"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"createNewsletter": mock_newsletter}
            mock_get_client.return_value = mock_gql_client

            result = await client.create_newsletter(input_data, mock_token)

            assert result == mock_newsletter
            mock_gql_client.execute.assert_called_once()

            # Verify the GraphQL mutation was called with correct variables
            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["input"] == input_data

    @pytest.mark.asyncio
    async def test_create_newsletter_with_branding(self, client, mock_token):
        """Test newsletter creation with branding configuration"""
        input_data: CreateNewsletterInput = {
            "title": "Branded Newsletter",
            "content": "<p>Branded content</p>",
            "subject": "Branded Subject",
            "brandingConfig": {
                "primaryColor": "#007bff",
                "logo": "https://example.com/logo.png",
                "footer": "Custom footer text"
            }
        }

        expected_newsletter = {
            "id": "newsletter-branded",
            "title": "Branded Newsletter",
            "brandingConfig": input_data["brandingConfig"]
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"createNewsletter": expected_newsletter}
            mock_get_client.return_value = mock_gql_client

            result = await client.create_newsletter(input_data, mock_token)

            assert result["brandingConfig"] == input_data["brandingConfig"]
            assert result["title"] == "Branded Newsletter"

    @pytest.mark.asyncio
    async def test_create_newsletter_scheduled(self, client, mock_token):
        """Test newsletter creation with scheduling"""
        input_data: CreateNewsletterInput = {
            "title": "Scheduled Newsletter",
            "content": "<p>Scheduled content</p>",
            "subject": "Scheduled Subject",
            "scheduleType": "SCHEDULED",
            "scheduledAt": "2024-12-25T09:00:00Z",
            "cronPattern": "0 9 * * MON"
        }

        expected_newsletter = {
            "id": "newsletter-scheduled",
            "title": "Scheduled Newsletter",
            "scheduleType": "SCHEDULED",
            "scheduledAt": "2024-12-25T09:00:00Z",
            "cronPattern": "0 9 * * MON",
            "status": "SCHEDULED"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"createNewsletter": expected_newsletter}
            mock_get_client.return_value = mock_gql_client

            result = await client.create_newsletter(input_data, mock_token)

            assert result["scheduleType"] == "SCHEDULED"
            assert result["cronPattern"] == "0 9 * * MON"
            assert result["status"] == "SCHEDULED"

    @pytest.mark.asyncio
    async def test_create_newsletter_failure(self, client, mock_token):
        """Test newsletter creation failure handling"""
        input_data: CreateNewsletterInput = {
            "title": "",  # Invalid empty title
            "content": "<p>Test content</p>",
            "subject": "Test Subject"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Validation error: Title is required")
            mock_get_client.return_value = mock_gql_client

            result = await client.create_newsletter(input_data, mock_token)

            # Should return None on error (graceful fallback)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_newsletter_success(self, client, mock_token, mock_newsletter):
        """Test successful newsletter retrieval"""
        newsletter_id = "newsletter-123"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newsletter": mock_newsletter}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter(newsletter_id, mock_token)

            assert result == mock_newsletter
            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["id"] == newsletter_id

    @pytest.mark.asyncio
    async def test_get_newsletter_not_found(self, client, mock_token):
        """Test newsletter not found handling"""
        newsletter_id = "non-existent-newsletter"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Newsletter not found")
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter(newsletter_id, mock_token)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_newsletters_with_filters(self, client, mock_token, mock_newsletter):
        """Test retrieving newsletters with filters"""
        filter_input: NewsletterFilterInput = {
            "status": "DRAFT",
            "productId": "product-1",
            "topics": ["product-updates"],
            "isGeneral": False,
            "createdAfter": "2024-01-01T00:00:00Z",
            "createdBefore": "2024-12-31T23:59:59Z"
        }

        expected_newsletters = [
            mock_newsletter,
            {**mock_newsletter, "id": "newsletter-2", "title": "Second Newsletter"}
        ]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newsletters": expected_newsletters}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletters(filter_input, mock_token)

            assert len(result) == 2
            assert result[0]["id"] == "newsletter-1"
            assert result[1]["id"] == "newsletter-2"

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["filter"] == filter_input

    @pytest.mark.asyncio
    async def test_get_newsletters_empty_result(self, client, mock_token):
        """Test retrieving newsletters with empty result"""
        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newsletters": []}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletters(None, mock_token)

            assert result == []
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_update_newsletter_success(self, client, mock_token, mock_newsletter):
        """Test successful newsletter update"""
        newsletter_id = "newsletter-1"
        update_data: UpdateNewsletterInput = {
            "title": "Updated Newsletter Title",
            "content": "<h1>Updated Content</h1>",
            "topics": ["new-topic", "updated-topic"]
        }

        updated_newsletter = {
            **mock_newsletter,
            "title": "Updated Newsletter Title",
            "content": "<h1>Updated Content</h1>",
            "topics": ["new-topic", "updated-topic"],
            "updatedAt": "2024-01-02T00:00:00Z"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"updateNewsletter": updated_newsletter}
            mock_get_client.return_value = mock_gql_client

            result = await client.update_newsletter(newsletter_id, update_data, mock_token)

            assert result["title"] == "Updated Newsletter Title"
            assert result["topics"] == ["new-topic", "updated-topic"]

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["id"] == newsletter_id
            assert call_args[1]["variable_values"]["input"] == update_data

    @pytest.mark.asyncio
    async def test_delete_newsletter_success(self, client, mock_token):
        """Test successful newsletter deletion"""
        newsletter_id = "newsletter-1"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"deleteNewsletter": True}
            mock_get_client.return_value = mock_gql_client

            result = await client.delete_newsletter(newsletter_id, mock_token)

            assert result is True
            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["id"] == newsletter_id

    @pytest.mark.asyncio
    async def test_delete_newsletter_failure(self, client, mock_token):
        """Test newsletter deletion failure"""
        newsletter_id = "protected-newsletter"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Cannot delete newsletter")
            mock_get_client.return_value = mock_gql_client

            result = await client.delete_newsletter(newsletter_id, mock_token)

            assert result is False

    # Newsletter Delivery Operations Tests
    @pytest.mark.asyncio
    async def test_send_newsletter_success(self, client, mock_token, mock_newsletter):
        """Test successful newsletter sending"""
        newsletter_id = "newsletter-1"
        sent_newsletter = {
            **mock_newsletter,
            "status": "SENDING",
            "recipientCount": 250,
            "updatedAt": "2024-01-01T14:30:00Z"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"sendNewsletter": sent_newsletter}
            mock_get_client.return_value = mock_gql_client

            result = await client.send_newsletter(newsletter_id, mock_token)

            assert result["status"] == "SENDING"
            assert result["recipientCount"] == 250
            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["id"] == newsletter_id

    @pytest.mark.asyncio
    async def test_schedule_newsletter_success(self, client, mock_token):
        """Test successful newsletter scheduling"""
        newsletter_id = "newsletter-1"
        scheduled_newsletter = {
            "id": newsletter_id,
            "status": "SCHEDULED",
            "scheduledAt": "2024-12-25T09:00:00Z"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"scheduleNewsletter": scheduled_newsletter}
            mock_get_client.return_value = mock_gql_client

            result = await client.schedule_newsletter(newsletter_id, mock_token)

            assert result["status"] == "SCHEDULED"
            assert result["scheduledAt"] == "2024-12-25T09:00:00Z"

    @pytest.mark.asyncio
    async def test_cancel_newsletter_schedule_success(self, client, mock_token):
        """Test successful newsletter schedule cancellation"""
        newsletter_id = "newsletter-1"
        cancelled_newsletter = {
            "id": newsletter_id,
            "status": "DRAFT",
            "scheduledAt": None
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"cancelNewsletterSchedule": cancelled_newsletter}
            mock_get_client.return_value = mock_gql_client

            result = await client.cancel_newsletter_schedule(newsletter_id, mock_token)

            assert result["status"] == "DRAFT"
            assert result["scheduledAt"] is None

    # Subscription Management Tests
    @pytest.mark.asyncio
    async def test_subscribe_to_newsletter_success(self, client, mock_token, mock_newsletter_subscription):
        """Test successful newsletter subscription"""
        subscription_input: NewsletterSubscriptionInput = {
            "newsletterId": "newsletter-1",
            "topics": ["product-updates", "announcements"],
            "productId": "product-1",
            "metadata": {"source": "web", "campaign": "signup"}
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"subscribeToNewsletter": mock_newsletter_subscription}
            mock_get_client.return_value = mock_gql_client

            result = await client.subscribe_to_newsletter(subscription_input, mock_token)

            assert result == mock_newsletter_subscription
            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["input"] == subscription_input

    @pytest.mark.asyncio
    async def test_subscribe_to_topics_only(self, client, mock_token):
        """Test subscription to topics without specific newsletter"""
        subscription_input: NewsletterSubscriptionInput = {
            "topics": ["general-announcements", "security-updates"],
            "metadata": {"preference": "essential-only"}
        }

        topic_subscription = {
            "id": "subscription-topics",
            "userId": "user-1",
            "newsletterId": None,
            "status": "ACTIVE",
            "topics": ["general-announcements", "security-updates"],
            "metadata": {"preference": "essential-only"}
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"subscribeToNewsletter": topic_subscription}
            mock_get_client.return_value = mock_gql_client

            result = await client.subscribe_to_newsletter(subscription_input, mock_token)

            assert result["newsletterId"] is None
            assert result["topics"] == ["general-announcements", "security-updates"]
            assert result["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_update_newsletter_subscription_success(self, client, mock_token, mock_newsletter_subscription):
        """Test successful subscription update"""
        subscription_id = "subscription-1"
        update_input: NewsletterSubscriptionInput = {
            "topics": ["product-updates", "feature-releases"],
            "metadata": {"frequency": "weekly", "format": "digest"}
        }

        updated_subscription = {
            **mock_newsletter_subscription,
            "topics": ["product-updates", "feature-releases"],
            "metadata": {"frequency": "weekly", "format": "digest"}
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"updateNewsletterSubscription": updated_subscription}
            mock_get_client.return_value = mock_gql_client

            result = await client.update_newsletter_subscription(subscription_id, update_input, mock_token)

            assert result["topics"] == ["product-updates", "feature-releases"]
            assert result["metadata"]["frequency"] == "weekly"

    @pytest.mark.asyncio
    async def test_unsubscribe_from_newsletter_success(self, client, mock_token):
        """Test successful newsletter unsubscription"""
        subscription_id = "subscription-1"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"unsubscribeFromNewsletter": True}
            mock_get_client.return_value = mock_gql_client

            result = await client.unsubscribe_from_newsletter(subscription_id, mock_token)

            assert result is True
            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["subscriptionId"] == subscription_id

    @pytest.mark.asyncio
    async def test_get_my_newsletter_subscriptions(self, client, mock_token, mock_newsletter_subscription):
        """Test retrieving user's newsletter subscriptions"""
        subscriptions = [
            mock_newsletter_subscription,
            {
                **mock_newsletter_subscription,
                "id": "subscription-2",
                "status": "PAUSED",
                "topics": ["security-updates"]
            }
        ]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"myNewsletterSubscriptions": subscriptions}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_my_newsletter_subscriptions(mock_token)

            assert len(result) == 2
            assert result[0]["status"] == "ACTIVE"
            assert result[1]["status"] == "PAUSED"

    # Bulk Operations Tests
    @pytest.mark.asyncio
    async def test_bulk_subscribe_success(self, client, mock_token):
        """Test successful bulk subscription operation"""
        user_ids = ["user-1", "user-2", "user-3", "user-4", "user-5"]
        subscription_input: NewsletterSubscriptionInput = {
            "topics": ["product-launch", "company-news"],
            "productId": "product-1",
            "metadata": {"campaign": "bulk-signup", "source": "import"}
        }

        bulk_subscriptions = [
            {
                "id": f"subscription-{i}",
                "userId": f"user-{i}",
                "status": "ACTIVE",
                "topics": ["product-launch", "company-news"],
                "productId": "product-1"
            }
            for i in range(1, 6)
        ]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"bulkSubscribe": bulk_subscriptions}
            mock_get_client.return_value = mock_gql_client

            result = await client.bulk_subscribe(user_ids, subscription_input, mock_token)

            assert len(result) == 5
            assert all(sub["status"] == "ACTIVE" for sub in result)
            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["userIds"] == user_ids
            assert call_args[1]["variable_values"]["input"] == subscription_input

    @pytest.mark.asyncio
    async def test_bulk_subscribe_empty_users(self, client, mock_token):
        """Test bulk subscription with empty user list"""
        user_ids = []
        subscription_input: NewsletterSubscriptionInput = {
            "topics": ["test-topic"]
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"bulkSubscribe": []}
            mock_get_client.return_value = mock_gql_client

            result = await client.bulk_subscribe(user_ids, subscription_input, mock_token)

            assert result == []

    @pytest.mark.asyncio
    async def test_bulk_subscribe_failure(self, client, mock_token):
        """Test bulk subscription failure handling"""
        user_ids = ["user-1", "user-2"]
        subscription_input: NewsletterSubscriptionInput = {
            "topics": ["invalid-topic"]
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Bulk operation failed")
            mock_get_client.return_value = mock_gql_client

            result = await client.bulk_subscribe(user_ids, subscription_input, mock_token)

            assert result == []

    # Analytics and Tracking Tests
    @pytest.mark.asyncio
    async def test_get_newsletter_stats_success(self, client, mock_token, mock_newsletter_stats):
        """Test successful newsletter statistics retrieval"""
        newsletter_id = "newsletter-1"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newsletterStats": mock_newsletter_stats}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_stats(newsletter_id, mock_token)

            assert result == mock_newsletter_stats
            assert result["total"] == 100
            assert result["sent"] == 95
            assert result["opened"] == 42
            assert result["clicked"] == 18
            assert pytest.approx(result["openRate"]) == 44.2
            assert pytest.approx(result["clickToOpenRate"]) == 42.8

    @pytest.mark.asyncio
    async def test_get_newsletter_stats_zero_division(self, client, mock_token):
        """Test newsletter statistics with zero values"""
        newsletter_id = "newsletter-empty"
        empty_stats = {
            "total": 0,
            "sent": 0,
            "pending": 0,
            "failed": 0,
            "opened": 0,
            "clicked": 0,
            "sentRate": 0.0,
            "openRate": 0.0,
            "clickRate": 0.0,
            "clickToOpenRate": 0.0
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newsletterStats": empty_stats}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_stats(newsletter_id, mock_token)

            assert result["total"] == 0
            assert result["openRate"] == 0.0
            assert result["clickRate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_newsletter_deliveries_success(self, client, mock_token, mock_newsletter_delivery):
        """Test successful newsletter deliveries retrieval"""
        newsletter_id = "newsletter-1"
        deliveries = [
            mock_newsletter_delivery,
            {
                **mock_newsletter_delivery,
                "id": "delivery-2",
                "opened": True,
                "openedAt": "2024-01-01T14:30:00Z",
                "clicked": True,
                "clickedAt": "2024-01-01T14:45:00Z"
            },
            {
                **mock_newsletter_delivery,
                "id": "delivery-3",
                "status": "failed",
                "failureReason": "Invalid email address"
            }
        ]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newsletterDeliveries": deliveries}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_deliveries(newsletter_id, mock_token)

            assert len(result) == 3
            assert result[0]["opened"] is False
            assert result[1]["opened"] is True
            assert result[1]["clicked"] is True
            assert result[2]["status"] == "failed"
            assert result[2]["failureReason"] == "Invalid email address"

    # Utility Methods Tests
    @pytest.mark.asyncio
    async def test_validate_cron_pattern_valid(self, client, mock_token):
        """Test validation of valid cron patterns"""
        valid_patterns = [
            "0 9 * * MON",           # Every Monday at 9 AM
            "0 0 1 * *",             # First day of every month at midnight
            "*/15 * * * *",          # Every 15 minutes
            "0 8-18 * * 1-5",        # Business hours on weekdays
            "0 2 * * SUN"            # Every Sunday at 2 AM
        ]

        for pattern in valid_patterns:
            with patch.object(client, 'get_client') as mock_get_client:
                mock_gql_client = MagicMock()
                mock_gql_client.execute.return_value = {"validateCronPattern": True}
                mock_get_client.return_value = mock_gql_client

                result = await client.validate_cron_pattern(pattern, mock_token)

                assert result is True
                call_args = mock_gql_client.execute.call_args
                assert call_args[1]["variable_values"]["pattern"] == pattern

    @pytest.mark.asyncio
    async def test_validate_cron_pattern_invalid(self, client, mock_token):
        """Test validation of invalid cron patterns"""
        invalid_patterns = [
            "invalid-pattern",
            "0 25 * * *",            # Invalid hour (25)
            "0 0 32 * *",            # Invalid day (32)
            "0 0 * 13 *",            # Invalid month (13)
            "0 0 * * 8",             # Invalid day of week (8)
            ""                       # Empty pattern
        ]

        for pattern in invalid_patterns:
            with patch.object(client, 'get_client') as mock_get_client:
                mock_gql_client = MagicMock()
                mock_gql_client.execute.return_value = {"validateCronPattern": False}
                mock_get_client.return_value = mock_gql_client

                result = await client.validate_cron_pattern(pattern, mock_token)

                assert result is False

    @pytest.mark.asyncio
    async def test_get_scheduler_status_running(self, client, mock_token):
        """Test scheduler status when running"""
        scheduler_status = {
            "isRunning": True,
            "lastRun": "2024-01-01T09:00:00Z",
            "nextRun": "2024-01-01T10:00:00Z"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"schedulerStatus": scheduler_status}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_scheduler_status(mock_token)

            assert result["isRunning"] is True
            assert result["lastRun"] == "2024-01-01T09:00:00Z"
            assert result["nextRun"] == "2024-01-01T10:00:00Z"

    @pytest.mark.asyncio
    async def test_get_scheduler_status_stopped(self, client, mock_token):
        """Test scheduler status when stopped"""
        scheduler_status = {
            "isRunning": False,
            "lastRun": "2024-01-01T08:00:00Z",
            "nextRun": None
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"schedulerStatus": scheduler_status}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_scheduler_status(mock_token)

            assert result["isRunning"] is False
            assert result["lastRun"] == "2024-01-01T08:00:00Z"
            assert result["nextRun"] is None

    # New Methods Tests - Pagination
    @pytest.mark.asyncio
    async def test_get_newsletters_paginated_success(self, client, mock_token, mock_paginated_newsletters):
        """Test successful paginated newsletters retrieval"""
        filter_input: NewsletterFilterInput = {
            "status": "DRAFT",
            "productId": "product-1"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newslettersPaginated": mock_paginated_newsletters}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletters_paginated(filter_input, page=1, page_size=10, token=mock_token)

            assert result == mock_paginated_newsletters
            assert len(result["newsletters"]) == 3
            assert result["pagination"]["currentPage"] == 1
            assert result["pagination"]["hasNextPage"] is True

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["filter"] == filter_input
            assert call_args[1]["variable_values"]["page"] == 1
            assert call_args[1]["variable_values"]["pageSize"] == 10

    @pytest.mark.asyncio
    async def test_get_newsletters_paginated_last_page(self, client, mock_token, mock_newsletter):
        """Test paginated newsletters on last page"""
        paginated_data = {
            "newsletters": [mock_newsletter],
            "pagination": {
                "currentPage": 5,
                "pageSize": 10,
                "totalPages": 5,
                "totalCount": 45,
                "hasNextPage": False,
                "hasPreviousPage": True
            }
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newslettersPaginated": paginated_data}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletters_paginated(None, page=5, page_size=10, token=mock_token)

            assert result["pagination"]["hasNextPage"] is False
            assert result["pagination"]["hasPreviousPage"] is True
            assert result["pagination"]["currentPage"] == 5

    @pytest.mark.asyncio
    async def test_get_newsletters_paginated_empty_result(self, client, mock_token):
        """Test paginated newsletters with empty result"""
        empty_paginated_data = {
            "newsletters": [],
            "pagination": {
                "currentPage": 1,
                "pageSize": 10,
                "totalPages": 0,
                "totalCount": 0,
                "hasNextPage": False,
                "hasPreviousPage": False
            }
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newslettersPaginated": empty_paginated_data}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletters_paginated(None, page=1, page_size=10, token=mock_token)

            assert result["newsletters"] == []
            assert result["pagination"]["totalCount"] == 0

    @pytest.mark.asyncio
    async def test_get_newsletters_paginated_failure(self, client, mock_token):
        """Test paginated newsletters failure handling"""
        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Database connection error")
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletters_paginated(None, page=1, page_size=10, token=mock_token)

            assert result is None

    # New Methods Tests - Newsletter Subscription by ID
    @pytest.mark.asyncio
    async def test_get_newsletter_subscription_success(self, client, mock_token, mock_newsletter_subscription):
        """Test successful newsletter subscription retrieval by ID"""
        subscription_id = "subscription-1"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newsletterSubscription": mock_newsletter_subscription}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_subscription(subscription_id, mock_token)

            assert result == mock_newsletter_subscription
            assert result["id"] == "subscription-1"
            assert result["status"] == "ACTIVE"

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["id"] == subscription_id

    @pytest.mark.asyncio
    async def test_get_newsletter_subscription_not_found(self, client, mock_token):
        """Test newsletter subscription not found handling"""
        subscription_id = "non-existent-subscription"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Subscription not found")
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_subscription(subscription_id, mock_token)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_newsletter_subscription_with_null_newsletter(self, client, mock_token):
        """Test newsletter subscription with null newsletter (topic-only subscription)"""
        subscription_data = {
            "id": "subscription-topics",
            "userId": "user-1",
            "newsletterId": None,
            "status": "ACTIVE",
            "topics": ["general-updates"],
            "productId": None,
            "subscribedAt": "2024-01-01T00:00:00Z",
            "unsubscribedAt": None,
            "metadata": {},
            "user": {"id": "user-1", "name": "Test User", "email": "test@example.com"},
            "newsletter": None
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newsletterSubscription": subscription_data}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_subscription("subscription-topics", mock_token)

            assert result["newsletterId"] is None
            assert result["newsletter"] is None

    # New Methods Tests - User Preferences
    @pytest.mark.asyncio
    async def test_update_newsletter_preferences_success(self, client, mock_token, mock_user_newsletter_preferences):
        """Test successful newsletter preferences update"""
        preferences_input: NewsletterPreferencesInput = {
            "emailNotifications": True,
            "frequency": "DAILY",
            "topicPreferences": ["product-updates", "announcements"],
            "productPreferences": ["product-1", "product-2"],
            "unsubscribeAll": False
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"updateNewsletterPreferences": mock_user_newsletter_preferences}
            mock_get_client.return_value = mock_gql_client

            result = await client.update_newsletter_preferences(preferences_input, mock_token)

            assert result == mock_user_newsletter_preferences
            assert result["frequency"] == "DAILY"
            assert result["emailNotifications"] is True

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["input"] == preferences_input

    @pytest.mark.asyncio
    async def test_update_newsletter_preferences_unsubscribe_all(self, client, mock_token):
        """Test newsletter preferences with unsubscribe all"""
        preferences_input: NewsletterPreferencesInput = {
            "unsubscribeAll": True,
            "emailNotifications": False
        }

        unsubscribed_preferences = {
            "id": "preferences-1",
            "userId": "user-1",
            "emailNotifications": False,
            "frequency": "IMMEDIATE",
            "topicPreferences": [],
            "productPreferences": [],
            "unsubscribeAll": True,
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-02T00:00:00Z"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"updateNewsletterPreferences": unsubscribed_preferences}
            mock_get_client.return_value = mock_gql_client

            result = await client.update_newsletter_preferences(preferences_input, mock_token)

            assert result["unsubscribeAll"] is True
            assert result["emailNotifications"] is False
            assert result["topicPreferences"] == []

    @pytest.mark.asyncio
    async def test_update_newsletter_preferences_failure(self, client, mock_token):
        """Test newsletter preferences update failure"""
        preferences_input: NewsletterPreferencesInput = {
            "frequency": "INVALID_FREQUENCY"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Invalid frequency value")
            mock_get_client.return_value = mock_gql_client

            result = await client.update_newsletter_preferences(preferences_input, mock_token)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_newsletter_preferences_success(self, client, mock_token, mock_user_newsletter_preferences):
        """Test successful newsletter preferences retrieval"""
        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getUserNewsletterPreferences": mock_user_newsletter_preferences}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_preferences(mock_token)

            assert result == mock_user_newsletter_preferences
            assert result["userId"] == "user-1"
            assert result["frequency"] == "DAILY"

    @pytest.mark.asyncio
    async def test_get_newsletter_preferences_not_found(self, client, mock_token):
        """Test newsletter preferences not found (first time user)"""
        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getUserNewsletterPreferences": None}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_preferences(mock_token)

            assert result is None

    @pytest.mark.asyncio
    async def test_get_newsletter_preferences_failure(self, client, mock_token):
        """Test newsletter preferences retrieval failure"""
        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Database error")
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_preferences(mock_token)

            assert result is None

    # New Methods Tests - Force Process Delivery
    @pytest.mark.asyncio
    async def test_force_process_newsletter_delivery_success(self, client, mock_token, mock_newsletter):
        """Test successful force processing of newsletter delivery"""
        newsletter_id = "newsletter-1"
        processed_newsletter = {
            **mock_newsletter,
            "status": "SENDING",
            "recipientCount": 250,
            "updatedAt": "2024-01-02T00:00:00Z"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"forceProcessNewsletterDelivery": processed_newsletter}
            mock_get_client.return_value = mock_gql_client

            result = await client.force_process_newsletter_delivery(newsletter_id, mock_token)

            assert result == processed_newsletter
            assert result["status"] == "SENDING"

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["id"] == newsletter_id

    @pytest.mark.asyncio
    async def test_force_process_newsletter_delivery_failed_newsletter(self, client, mock_token):
        """Test force processing of failed newsletter deliveries"""
        newsletter_id = "failed-newsletter"
        reprocessed_newsletter = {
            "id": newsletter_id,
            "title": "Failed Newsletter",
            "status": "SENDING",
            "recipientCount": 100,
            "updatedAt": "2024-01-02T00:00:00Z"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"forceProcessNewsletterDelivery": reprocessed_newsletter}
            mock_get_client.return_value = mock_gql_client

            result = await client.force_process_newsletter_delivery(newsletter_id, mock_token)

            assert result["status"] == "SENDING"

    @pytest.mark.asyncio
    async def test_force_process_newsletter_delivery_failure(self, client, mock_token):
        """Test force processing failure handling"""
        newsletter_id = "invalid-newsletter"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Newsletter not found")
            mock_get_client.return_value = mock_gql_client

            result = await client.force_process_newsletter_delivery(newsletter_id, mock_token)

            assert result is None

    # New Methods Tests - Share Newsletter
    @pytest.mark.asyncio
    async def test_share_newsletter_success(self, client, mock_token, mock_newsletter_sharing_result):
        """Test successful newsletter sharing"""
        share_input: ShareNewsletterInput = {
            "newsletterId": "newsletter-1",
            "recipientEmails": ["user1@example.com", "user2@example.com"],
            "message": "Check out this newsletter!",
            "allowForwarding": True
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"shareNewsletter": mock_newsletter_sharing_result}
            mock_get_client.return_value = mock_gql_client

            result = await client.share_newsletter(share_input, mock_token)

            assert result == mock_newsletter_sharing_result
            assert result["success"] is True
            assert len(result["sharedWith"]) == 2
            assert result["failedRecipients"] == []

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["input"] == share_input

    @pytest.mark.asyncio
    async def test_share_newsletter_partial_failure(self, client, mock_token):
        """Test newsletter sharing with partial failures"""
        share_input: ShareNewsletterInput = {
            "newsletterId": "newsletter-1",
            "recipientEmails": ["valid@example.com", "invalid-email", "another@example.com"],
            "message": "Newsletter share"
        }

        partial_result = {
            "success": True,
            "sharedWith": ["valid@example.com", "another@example.com"],
            "failedRecipients": ["invalid-email"],
            "message": "Newsletter shared with 2 out of 3 recipients"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"shareNewsletter": partial_result}
            mock_get_client.return_value = mock_gql_client

            result = await client.share_newsletter(share_input, mock_token)

            assert result["success"] is True
            assert len(result["sharedWith"]) == 2
            assert len(result["failedRecipients"]) == 1

    @pytest.mark.asyncio
    async def test_share_newsletter_failure(self, client, mock_token):
        """Test newsletter sharing failure"""
        share_input: ShareNewsletterInput = {
            "newsletterId": "non-existent",
            "recipientEmails": ["user@example.com"]
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Newsletter not found")
            mock_get_client.return_value = mock_gql_client

            result = await client.share_newsletter(share_input, mock_token)

            assert result is None

    # New Methods Tests - Assign Newsletter Permission
    @pytest.mark.asyncio
    async def test_assign_newsletter_permission_success(self, client, mock_token, mock_newsletter_permission_result):
        """Test successful newsletter permission assignment"""
        permission_input: AssignNewsletterPermissionInput = {
            "newsletterId": "newsletter-1",
            "userId": "user-2",
            "permission": "EDIT",
            "expiresAt": None
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"assignNewsletterPermission": mock_newsletter_permission_result}
            mock_get_client.return_value = mock_gql_client

            result = await client.assign_newsletter_permission(permission_input, mock_token)

            assert result == mock_newsletter_permission_result
            assert result["success"] is True
            assert result["permission"]["permission"] == "EDIT"

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["input"] == permission_input

    @pytest.mark.asyncio
    async def test_assign_newsletter_permission_with_expiry(self, client, mock_token):
        """Test newsletter permission assignment with expiry date"""
        permission_input: AssignNewsletterPermissionInput = {
            "newsletterId": "newsletter-1",
            "userId": "user-3",
            "permission": "VIEW",
            "expiresAt": "2024-12-31T23:59:59Z"
        }

        permission_result = {
            "success": True,
            "message": "Permission assigned with expiry",
            "permission": {
                "id": "permission-2",
                "newsletterId": "newsletter-1",
                "userId": "user-3",
                "permission": "VIEW",
                "grantedBy": {"id": "user-1", "name": "Admin", "email": "admin@example.com"},
                "grantedAt": "2024-01-01T00:00:00Z",
                "expiresAt": "2024-12-31T23:59:59Z"
            }
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"assignNewsletterPermission": permission_result}
            mock_get_client.return_value = mock_gql_client

            result = await client.assign_newsletter_permission(permission_input, mock_token)

            assert result["permission"]["expiresAt"] == "2024-12-31T23:59:59Z"

    @pytest.mark.asyncio
    async def test_assign_newsletter_permission_failure(self, client, mock_token):
        """Test newsletter permission assignment failure"""
        permission_input: AssignNewsletterPermissionInput = {
            "newsletterId": "newsletter-1",
            "userId": "user-2",
            "permission": "INVALID_PERMISSION"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Invalid permission type")
            mock_get_client.return_value = mock_gql_client

            result = await client.assign_newsletter_permission(permission_input, mock_token)

            assert result is None

    # New Methods Tests - Revoke Newsletter Permission
    @pytest.mark.asyncio
    async def test_revoke_newsletter_permission_success(self, client, mock_token):
        """Test successful newsletter permission revocation"""
        revoke_input: RevokeNewsletterPermissionInput = {
            "newsletterId": "newsletter-1",
            "userId": "user-2"
        }

        revoke_result = {
            "success": True,
            "message": "Permission revoked successfully",
            "permission": {
                "id": "permission-1",
                "newsletterId": "newsletter-1",
                "userId": "user-2"
            }
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"revokeNewsletterPermission": revoke_result}
            mock_get_client.return_value = mock_gql_client

            result = await client.revoke_newsletter_permission(revoke_input, mock_token)

            assert result == revoke_result
            assert result["success"] is True

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["input"] == revoke_input

    @pytest.mark.asyncio
    async def test_revoke_newsletter_permission_not_found(self, client, mock_token):
        """Test revoking non-existent permission"""
        revoke_input: RevokeNewsletterPermissionInput = {
            "newsletterId": "newsletter-1",
            "userId": "user-nonexistent"
        }

        revoke_result = {
            "success": False,
            "message": "Permission not found",
            "permission": None
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"revokeNewsletterPermission": revoke_result}
            mock_get_client.return_value = mock_gql_client

            result = await client.revoke_newsletter_permission(revoke_input, mock_token)

            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_revoke_newsletter_permission_failure(self, client, mock_token):
        """Test newsletter permission revocation failure"""
        revoke_input: RevokeNewsletterPermissionInput = {
            "newsletterId": "newsletter-1",
            "userId": "user-2"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Database error")
            mock_get_client.return_value = mock_gql_client

            result = await client.revoke_newsletter_permission(revoke_input, mock_token)

            assert result is None

    # New Methods Tests - Get Newsletter Permissions
    @pytest.mark.asyncio
    async def test_get_newsletter_permissions_success(self, client, mock_token, mock_newsletter_permission):
        """Test successful newsletter permissions retrieval"""
        newsletter_id = "newsletter-1"
        permissions = [
            mock_newsletter_permission,
            {
                **mock_newsletter_permission,
                "id": "permission-2",
                "userId": "user-3",
                "permission": "VIEW",
                "user": {"id": "user-3", "name": "Viewer", "email": "viewer@example.com"}
            },
            {
                **mock_newsletter_permission,
                "id": "permission-3",
                "userId": "user-4",
                "permission": "ADMIN",
                "user": {"id": "user-4", "name": "Admin", "email": "admin2@example.com"}
            }
        ]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newsletterPermissions": permissions}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_permissions(newsletter_id, mock_token)

            assert len(result) == 3
            assert result[0]["permission"] == "EDIT"
            assert result[1]["permission"] == "VIEW"
            assert result[2]["permission"] == "ADMIN"

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["newsletterId"] == newsletter_id

    @pytest.mark.asyncio
    async def test_get_newsletter_permissions_empty(self, client, mock_token):
        """Test newsletter permissions with no permissions assigned"""
        newsletter_id = "newsletter-new"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newsletterPermissions": []}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_permissions(newsletter_id, mock_token)

            assert result == []
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_get_newsletter_permissions_with_expired(self, client, mock_token):
        """Test newsletter permissions including expired permissions"""
        newsletter_id = "newsletter-1"
        permissions = [
            {
                "id": "permission-active",
                "newsletterId": newsletter_id,
                "userId": "user-2",
                "permission": "EDIT",
                "grantedBy": {"id": "user-1", "name": "Admin", "email": "admin@example.com"},
                "grantedAt": "2024-01-01T00:00:00Z",
                "expiresAt": None,
                "user": {"id": "user-2", "name": "Editor", "email": "editor@example.com"}
            },
            {
                "id": "permission-expired",
                "newsletterId": newsletter_id,
                "userId": "user-3",
                "permission": "VIEW",
                "grantedBy": {"id": "user-1", "name": "Admin", "email": "admin@example.com"},
                "grantedAt": "2023-01-01T00:00:00Z",
                "expiresAt": "2023-12-31T23:59:59Z",
                "user": {"id": "user-3", "name": "Temp Viewer", "email": "temp@example.com"}
            }
        ]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"newsletterPermissions": permissions}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_permissions(newsletter_id, mock_token)

            assert len(result) == 2
            assert result[0]["expiresAt"] is None
            assert result[1]["expiresAt"] == "2023-12-31T23:59:59Z"

    @pytest.mark.asyncio
    async def test_get_newsletter_permissions_failure(self, client, mock_token):
        """Test newsletter permissions retrieval failure"""
        newsletter_id = "invalid-newsletter"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Newsletter not found")
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter_permissions(newsletter_id, mock_token)

            assert result == []

    # Error Handling Tests
    @pytest.mark.asyncio
    async def test_network_error_handling(self, client, mock_token):
        """Test handling of network errors"""
        input_data: CreateNewsletterInput = {
            "title": "Test Newsletter",
            "content": "<p>Test content</p>",
            "subject": "Test Subject"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Network connection failed")
            mock_get_client.return_value = mock_gql_client

            result = await client.create_newsletter(input_data, mock_token)

            # Should return None on network error (graceful fallback)
            assert result is None

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, client):
        """Test handling of authentication errors"""
        invalid_token = "invalid-token"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Authentication failed")
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletters(None, invalid_token)

            assert result == []  # Should return empty list on auth error

    @pytest.mark.asyncio
    async def test_graphql_error_handling(self, client, mock_token):
        """Test handling of GraphQL specific errors"""
        newsletter_id = "newsletter-1"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("GraphQL syntax error")
            mock_get_client.return_value = mock_gql_client

            result = await client.get_newsletter(newsletter_id, mock_token)

            assert result is None

    # Performance Tests
    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, client, mock_token):
        """Test performance of bulk operations"""
        # Simulate bulk subscription for 1000 users
        user_ids = [f"user-{i}" for i in range(1000)]
        subscription_input: NewsletterSubscriptionInput = {
            "topics": ["performance-test"]
        }

        bulk_subscriptions = [
            {"id": f"sub-{i}", "userId": f"user-{i}", "status": "ACTIVE"}
            for i in range(1000)
        ]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"bulkSubscribe": bulk_subscriptions}
            mock_get_client.return_value = mock_gql_client

            start_time = time.time()

            result = await client.bulk_subscribe(user_ids, subscription_input, mock_token)

            end_time = time.time()
            execution_time = end_time - start_time

            assert len(result) == 1000
            assert execution_time < 10.0  # Should complete within 10 seconds

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, client, mock_token):
        """Test handling of concurrent operations"""
        newsletter_ids = [f"newsletter-{i}" for i in range(10)]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = [
                {"newsletter": {"id": newsletter_id, "title": f"Newsletter {i}"}}
                for i, newsletter_id in enumerate(newsletter_ids)
            ]
            mock_get_client.return_value = mock_gql_client

            # Run concurrent operations
            tasks = [
                client.get_newsletter(newsletter_id, mock_token)
                for newsletter_id in newsletter_ids
            ]

            results = await asyncio.gather(*tasks)

            assert len(results) == 10
            for i, result in enumerate(results):
                assert result["id"] == f"newsletter-{i}"


# Integration Tests
class TestNewsletterIntegration:
    """Integration tests for complete newsletter workflows"""

    @pytest.mark.asyncio
    async def test_complete_newsletter_lifecycle(self):
        """Test complete newsletter workflow: create, subscribe, send, track"""
        client = NewsletterClient("http://localhost:4000/graphql")
        token = "test-token"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_get_client.return_value = mock_gql_client

            # Mock responses for complete workflow
            mock_gql_client.execute.side_effect = [
                # Create newsletter
                {"createNewsletter": {"id": "newsletter-1", "status": "DRAFT", "title": "Integration Test"}},
                # Subscribe user
                {"subscribeToNewsletter": {"id": "subscription-1", "status": "ACTIVE", "userId": "user-1"}},
                # Send newsletter
                {"sendNewsletter": {"id": "newsletter-1", "status": "SENDING", "recipientCount": 1}},
                # Get statistics
                {"newsletterStats": {"total": 1, "sent": 1, "opened": 0, "clicked": 0, "openRate": 0.0}}
            ]

            # 1. Create newsletter
            newsletter = await client.create_newsletter({
                "title": "Integration Test Newsletter",
                "content": "<p>Test content</p>",
                "subject": "Integration Test"
            }, token)
            assert newsletter["id"] == "newsletter-1"
            assert newsletter["status"] == "DRAFT"

            # 2. Subscribe user
            subscription = await client.subscribe_to_newsletter({
                "newsletterId": "newsletter-1",
                "topics": ["integration-test"]
            }, token)
            assert subscription["status"] == "ACTIVE"

            # 3. Send newsletter
            sent_newsletter = await client.send_newsletter("newsletter-1", token)
            assert sent_newsletter["status"] == "SENDING"
            assert sent_newsletter["recipientCount"] == 1

            # 4. Get statistics
            stats = await client.get_newsletter_stats("newsletter-1", token)
            assert stats["total"] == 1
            assert stats["sent"] == 1

    @pytest.mark.asyncio
    async def test_subscription_management_workflow(self):
        """Test subscription management workflow"""
        client = NewsletterClient("http://localhost:4000/graphql")
        token = "test-token"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_get_client.return_value = mock_gql_client

            # Mock responses for subscription workflow
            mock_gql_client.execute.side_effect = [
                # Initial subscription
                {"subscribeToNewsletter": {"id": "sub-1", "status": "ACTIVE", "topics": ["initial"]}},
                # Update subscription
                {"updateNewsletterSubscription": {"id": "sub-1", "topics": ["updated", "new"]}},
                # Get user subscriptions
                {"myNewsletterSubscriptions": [{"id": "sub-1", "status": "ACTIVE", "topics": ["updated", "new"]}]},
                # Unsubscribe
                {"unsubscribeFromNewsletter": True}
            ]

            # 1. Subscribe
            subscription = await client.subscribe_to_newsletter({
                "topics": ["initial"]
            }, token)
            assert subscription["status"] == "ACTIVE"

            # 2. Update preferences
            updated_subscription = await client.update_newsletter_subscription(
                "sub-1",
                {"topics": ["updated", "new"]},
                token
            )
            assert "updated" in updated_subscription["topics"]
            assert "new" in updated_subscription["topics"]

            # 3. Get user subscriptions
            user_subscriptions = await client.get_my_newsletter_subscriptions(token)
            assert len(user_subscriptions) == 1
            assert user_subscriptions[0]["status"] == "ACTIVE"

            # 4. Unsubscribe
            unsubscribe_result = await client.unsubscribe_from_newsletter("sub-1", token)
            assert unsubscribe_result is True


# Edge Cases and Error Scenarios
class TestNewsletterEdgeCases:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_empty_and_null_inputs(self):
        """Test handling of empty and null inputs"""
        client = NewsletterClient("http://localhost:4000/graphql")
        token = "test-token"

        # Test empty newsletter title
        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Validation error")
            mock_get_client.return_value = mock_gql_client

            result = await client.create_newsletter({
                "title": "",
                "content": "Content",
                "subject": "Subject"
            }, token)

            assert result is None

    @pytest.mark.asyncio
    async def test_large_content_handling(self):
        """Test handling of large newsletter content"""
        client = NewsletterClient("http://localhost:4000/graphql")
        token = "test-token"

        # Create large content (simulate 1MB of HTML content)
        large_content = "<p>" + "A" * 1000000 + "</p>"

        input_data: CreateNewsletterInput = {
            "title": "Large Content Newsletter",
            "content": large_content,
            "subject": "Large Content Test"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {
                "createNewsletter": {
                    "id": "large-newsletter",
                    "title": "Large Content Newsletter",
                    "content": large_content[:100] + "...",  # Truncated in response
                    "status": "DRAFT"
                }
            }
            mock_get_client.return_value = mock_gql_client

            result = await client.create_newsletter(input_data, token)

            assert result is not None
            assert result["id"] == "large-newsletter"
            assert len(result["content"]) > 100  # Content should be handled

    @pytest.mark.asyncio
    async def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters"""
        client = NewsletterClient("http://localhost:4000/graphql")
        token = "test-token"

        unicode_content = {
            "title": "测试通讯 🚀 Newsletter",
            "content": "<p>Special chars: àáâãäåæçèéêë 🎉 €£¥ ©®™</p>",
            "subject": "Unicøde Tëst Sübject"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"createNewsletter": unicode_content}
            mock_get_client.return_value = mock_gql_client

            result = await client.create_newsletter(unicode_content, token)

            assert result["title"] == "测试通讯 🚀 Newsletter"
            assert "🎉" in result["content"]
            assert "Unicøde" in result["subject"]


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])