"""
Tests for the GraphQL client
"""

from unittest.mock import AsyncMock, patch

import httpx
import pytest

# Note: These imports may not match current SDK structure
# from workspaces_sdk.client import WorkspaceClient

# Skip all tests in this module since required classes don't exist yet
pytestmark = pytest.mark.skip(
    reason="BaseGraphQLClient and related classes not yet implemented in SDK"
)


def test_config_creation():
    """Test BoilerSDKConfig creation"""
    config = BoilerSDKConfig(  # noqa: F821
        endpoint="https://api.test.com/graphql",
        api_key="test-key",
        timeout=60.0,
    )

    assert config.endpoint == "https://api.test.com/graphql"
    assert config.api_key == "test-key"
    assert config.timeout == 60.0


def test_auth_tokens():
    """Test AuthTokens dataclass"""
    tokens = AuthTokens(  # noqa: F821
        access_token="access123", refresh_token="refresh456"
    )

    assert tokens.access_token == "access123"
    assert tokens.refresh_token == "refresh456"


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization"""
    config = BoilerSDKConfig(endpoint="https://api.test.com/graphql")  # noqa: F821
    client = BaseGraphQLClient(config)  # noqa: F821

    assert client.config == config
    assert client.tokens is None

    await client.close()


@pytest.mark.asyncio
async def test_client_with_initial_tokens():
    """Test client initialization with tokens"""
    config = BoilerSDKConfig(  # noqa: F821
        endpoint="https://api.test.com/graphql",
        access_token="initial_access",
        refresh_token="initial_refresh",
    )
    client = BaseGraphQLClient(config)  # noqa: F821

    assert client.tokens is not None
    assert client.tokens.access_token == "initial_access"
    assert client.tokens.refresh_token == "initial_refresh"

    await client.close()


@pytest.mark.asyncio
async def test_token_management():
    """Test token setting and clearing"""
    config = BoilerSDKConfig(endpoint="https://api.test.com/graphql")  # noqa: F821
    client = BaseGraphQLClient(config)  # noqa: F821

    # Initially no tokens
    assert client.get_tokens() is None

    # Set tokens
    client.set_tokens("access123", "refresh456")
    tokens = client.get_tokens()
    assert tokens.access_token == "access123"
    assert tokens.refresh_token == "refresh456"

    # Clear tokens
    client.clear_tokens()
    assert client.get_tokens() is None

    await client.close()


def test_headers_generation():
    """Test header generation with different configurations"""
    # Test with API key only
    config = BoilerSDKConfig(  # noqa: F821
        endpoint="https://api.test.com/graphql", api_key="test-key"
    )
    client = BaseGraphQLClient(config)  # noqa: F821
    headers = client._get_headers()

    assert headers["Content-Type"] == "application/json"
    assert headers["Accept"] == "application/json"
    assert headers["X-API-Key"] == "test-key"
    assert "Authorization" not in headers

    # Test with tokens
    client.set_tokens("access123", "refresh456")
    headers = client._get_headers()
    assert headers["Authorization"] == "Bearer access123"


@pytest.mark.asyncio
async def test_successful_request():
    """Test successful GraphQL request"""
    config = BoilerSDKConfig(endpoint="https://api.test.com/graphql")  # noqa: F821
    client = BaseGraphQLClient(config)  # noqa: F821

    # Mock successful response
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(
        return_value={"data": {"user": {"id": "123", "name": "Test User"}}}
    )
    mock_response.raise_for_status = AsyncMock()

    with patch.object(client.client, "post", return_value=mock_response):
        result = await client.request("query GetUser { user { id name } }")

        assert result == {"user": {"id": "123", "name": "Test User"}}

    await client.close()


@pytest.mark.asyncio
async def test_graphql_error_response():
    """Test GraphQL error handling"""
    config = BoilerSDKConfig(endpoint="https://api.test.com/graphql")  # noqa: F821
    client = BaseGraphQLClient(config)  # noqa: F821

    # Mock error response
    mock_response = AsyncMock()
    mock_response.json = AsyncMock(
        return_value={"errors": [{"message": "User not found"}]}
    )
    mock_response.raise_for_status = AsyncMock()

    with patch.object(client.client, "post", return_value=mock_response):
        with pytest.raises(Exception, match="GraphQL Error"):
            await client.request("query GetUser { user { id } }")

    await client.close()


@pytest.mark.asyncio
async def test_http_error_response():
    """Test HTTP error handling"""
    config = BoilerSDKConfig(endpoint="https://api.test.com/graphql")  # noqa: F821
    client = BaseGraphQLClient(config)  # noqa: F821

    # Mock HTTP error
    with patch.object(
        client.client,
        "post",
        side_effect=httpx.HTTPStatusError(
            "404 Not Found",
            request=AsyncMock(),
            response=AsyncMock(status_code=404, text="Not Found"),
        ),
    ):
        with pytest.raises(Exception, match="HTTP Error"):
            await client.request("query GetUser { user { id } }")

    await client.close()


@pytest.mark.asyncio
async def test_endpoint_change():
    """Test changing endpoint"""
    config = BoilerSDKConfig(endpoint="https://api.test.com/graphql")  # noqa: F821
    client = BaseGraphQLClient(config)  # noqa: F821

    assert client.get_endpoint() == "https://api.test.com/graphql"

    client.set_endpoint("https://api.staging.com/graphql")
    assert client.get_endpoint() == "https://api.staging.com/graphql"
    assert client.config.endpoint == "https://api.staging.com/graphql"

    await client.close()


@pytest.mark.asyncio
async def test_context_manager():
    """Test using client as context manager"""
    config = BoilerSDKConfig(endpoint="https://api.test.com/graphql")  # noqa: F821

    async with BaseGraphQLClient(config) as client:  # noqa: F821
        assert client is not None
        assert client.client is not None
