"""
Tests for the main SDK class
"""

from workspaces_sdk import WorkspaceClient


def test_sdk_initialization():
    """Test SDK can be initialized"""
    sdk = WorkspaceClient(
        endpoint="https://api.test.com/graphql", api_key="test-api-key"
    )

    assert sdk.endpoint == "https://api.test.com/graphql"
    assert sdk.api_key == "test-api-key"
    assert sdk.rbac is not None
    assert sdk.billing is not None
    assert sdk.store is not None


def test_sdk_token_management():
    """Test token management methods"""
    sdk = WorkspaceClient(endpoint="https://api.test.com/graphql")

    # Set token
    sdk.set_token("jwt_token_123")
    assert sdk.token == "jwt_token_123"
    assert sdk._headers.get("Authorization") == "Bearer jwt_token_123"


def test_sdk_endpoint_initialization():
    """Test SDK endpoint initialization"""
    sdk = WorkspaceClient(endpoint="https://api.test.com/graphql")
    assert sdk.endpoint == "https://api.test.com/graphql"


def test_sdk_with_api_key():
    """Test SDK initialization with API key"""
    sdk = WorkspaceClient(
        endpoint="https://api.test.com/graphql", api_key="test-api-key-123"
    )

    assert sdk.api_key == "test-api-key-123"
    assert sdk._headers.get("X-API-Key") == "test-api-key-123"
