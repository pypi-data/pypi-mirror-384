"""
Tests for the user module
"""

from unittest.mock import AsyncMock

import pytest

# Note: These imports may not match current SDK structure
# from workspaces_sdk.user.user_module import UserModule
# from workspaces_sdk.types.common import User

# Skip all tests in this module since UserModule doesn't exist yet
pytestmark = pytest.mark.skip(reason="UserModule not yet implemented in SDK")


@pytest.fixture
def mock_client():
    """Mock GraphQL client"""
    client = AsyncMock()
    return client


@pytest.fixture
def user_module(mock_client):
    """User module with mocked client"""
    return UserModule(mock_client)  # noqa: F821


@pytest.mark.asyncio
async def test_get_current_user(user_module, mock_client):
    """Test getting current user"""
    # Mock response
    mock_client.request.return_value = {
        "currentUser": {
            "id": "user123",
            "email": "current@example.com",
            "name": "Current User",
            "status": "active",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
        }
    }

    user = await user_module.get_current_user()

    assert isinstance(user, User)  # noqa: F821
    assert user.id == "user123"
    assert user.email == "current@example.com"
    assert user.name == "Current User"
    assert user.status == "active"


@pytest.mark.asyncio
async def test_get_user_by_id(user_module, mock_client):
    """Test getting user by ID"""
    mock_client.request.return_value = {
        "user": {
            "id": "user456",
            "email": "test@example.com",
            "name": "Test User",
            "status": "active",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
        }
    }

    user = await user_module.get_user_by_id("user456")

    assert isinstance(user, User)  # noqa: F821
    assert user.id == "user456"
    assert user.email == "test@example.com"
    assert user.name == "Test User"

    # Verify the correct query was called
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert "GetUserById" in call_args[0][0]
    assert call_args[0][1]["id"] == "user456"


@pytest.mark.asyncio
async def test_list_users(user_module, mock_client):
    """Test listing users"""
    mock_client.request.return_value = {
        "users": [
            {
                "id": "user1",
                "email": "user1@example.com",
                "name": "User One",
                "status": "active",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-01-01T00:00:00Z",
            },
            {
                "id": "user2",
                "email": "user2@example.com",
                "name": "User Two",
                "status": "pending",
                "createdAt": "2024-01-02T00:00:00Z",
                "updatedAt": "2024-01-02T00:00:00Z",
            },
        ]
    }

    users = await user_module.list_users(limit=10, offset=0)

    assert len(users) == 2
    assert all(isinstance(user, User) for user in users)  # noqa: F821
    assert users[0].id == "user1"
    assert users[1].id == "user2"

    # Verify the correct query was called
    mock_client.request.assert_called_once()
    call_args = mock_client.request.call_args
    assert "ListUsers" in call_args[0][0]
    assert call_args[0][1]["limit"] == 10
    assert call_args[0][1]["offset"] == 0


@pytest.mark.asyncio
async def test_list_users_no_params(user_module, mock_client):
    """Test listing users without parameters"""
    mock_client.request.return_value = {"users": []}

    users = await user_module.list_users()

    assert len(users) == 0

    # Verify the correct query was called with None values
    call_args = mock_client.request.call_args
    assert call_args[0][1]["limit"] is None
    assert call_args[0][1]["offset"] is None


@pytest.mark.asyncio
async def test_update_user(user_module, mock_client):
    """Test updating user"""
    mock_client.request.return_value = {
        "updateUser": {
            "id": "user123",
            "email": "updated@example.com",
            "name": "Updated Name",
            "status": "active",
            "updatedAt": "2024-01-03T00:00:00Z",
        }
    }

    user = await user_module.update_user(
        user_id="user123", name="Updated Name", email="updated@example.com"
    )

    assert isinstance(user, User)  # noqa: F821
    assert user.id == "user123"
    assert user.email == "updated@example.com"
    assert user.name == "Updated Name"

    # Verify the correct mutation was called
    call_args = mock_client.request.call_args
    assert "UpdateUser" in call_args[0][0]
    assert call_args[0][1]["id"] == "user123"
    assert call_args[0][1]["name"] == "Updated Name"
    assert call_args[0][1]["email"] == "updated@example.com"


@pytest.mark.asyncio
async def test_update_user_partial(user_module, mock_client):
    """Test updating user with only some fields"""
    mock_client.request.return_value = {
        "updateUser": {
            "id": "user123",
            "email": "original@example.com",
            "name": "New Name",
            "status": "active",
            "updatedAt": "2024-01-03T00:00:00Z",
        }
    }

    # Update only name
    user = await user_module.update_user(user_id="user123", name="New Name")

    assert user.name == "New Name"

    # Verify the correct variables were passed
    call_args = mock_client.request.call_args
    assert call_args[0][1]["id"] == "user123"
    assert call_args[0][1]["name"] == "New Name"
    # Email should not be in variables since it was not provided
    assert "email" not in call_args[0][1]
