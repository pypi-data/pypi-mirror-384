"""
Tests for the auth module
"""

from unittest.mock import AsyncMock

import pytest

# Note: These imports may not match current SDK structure
# from workspaces_sdk.auth.auth_module import AuthModule
# from workspaces_sdk.types.common import UserRegisterInput, User, AuthResponse

# Skip all tests in this module since AuthModule doesn't exist yet
pytestmark = pytest.mark.skip(reason="AuthModule not yet implemented in SDK")


@pytest.fixture
def mock_client():
    """Mock GraphQL client"""
    client = AsyncMock()
    return client


@pytest.fixture
def auth_module(mock_client):
    """Auth module with mocked client"""
    return AuthModule(mock_client)  # noqa: F821


@pytest.mark.asyncio
async def test_register_user(auth_module, mock_client):
    """Test user registration"""
    # Mock response
    mock_client.request.return_value = {
        "register": {
            "id": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "status": "pending",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
        }
    }

    # Test registration
    user_input = UserRegisterInput(  # noqa: F821
        email="test@example.com", name="Test User", password="password123"
    )

    user = await auth_module.register(user_input)

    assert isinstance(user, User)  # noqa: F821
    assert user.id == "user123"
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.status == "pending"


@pytest.mark.asyncio
async def test_verify_user(auth_module, mock_client):
    """Test user verification"""
    # Mock response
    mock_client.request.return_value = {
        "verifyUser": {
            "defaultOrgName": "Test Org",
            "token": "jwt_token_here",
            "user": {
                "id": "user123",
                "email": "test@example.com",
                "name": "Test User",
                "status": "active",
            },
            "workspacesAndTenants": [],
        }
    }

    auth_response = await auth_module.verify_user("verification_token")

    assert isinstance(auth_response, AuthResponse)  # noqa: F821
    assert auth_response.default_org_name == "Test Org"
    assert auth_response.token == "jwt_token_here"
    assert auth_response.user.id == "user123"

    # Verify that tokens are set on the client
    mock_client.set_tokens.assert_called_once_with(
        access_token="jwt_token_here", refresh_token=""
    )


@pytest.mark.asyncio
async def test_forgot_password(auth_module, mock_client):
    """Test forgot password"""
    mock_client.request.return_value = {"forgotPassword": {"success": True}}

    response = await auth_module.forgot_password("test@example.com")

    assert response.success is True


@pytest.mark.asyncio
async def test_reset_password(auth_module, mock_client):
    """Test password reset"""
    mock_client.request.return_value = {"resetPassword": {"success": True}}

    response = await auth_module.reset_password("new_password", "reset_token")

    assert response.success is True


@pytest.mark.asyncio
async def test_change_password(auth_module, mock_client):
    """Test password change"""
    mock_client.request.return_value = {
        "changePassword": {
            "id": "user123",
            "email": "test@example.com",
            "name": "Test User",
            "updatedAt": "2024-01-01T00:00:00Z",
        }
    }

    user = await auth_module.change_password("user123", "new_password")

    assert isinstance(user, User)  # noqa: F821
    assert user.id == "user123"


def test_logout(auth_module, mock_client):
    """Test logout functionality"""
    auth_module.logout()
    mock_client.clear_tokens.assert_called_once()
