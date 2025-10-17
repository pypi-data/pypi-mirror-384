"""
Comprehensive test suite for Workspace Invitation functionality.

Tests cover:
- Invitation CRUD operations
- Member management
- Pagination, filtering, search, and sorting
- Exception handling
- Edge cases and error scenarios
- Performance tests
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from typing import Dict, Any, List, Optional

# Import the workspace module components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from workspaces_sdk.workspace import (
    WorkspaceClient,
    Invitation,
    InvitationResponse,
    InviteUserResponse,
    InvitationFilter,
    InvitationSort,
    InvitationPagination,
    PaginatedInvitations,
    WorkspaceMember,
    MemberSort,
    MemberPagination,
    PaginatedMembers,
    InviteStatus,
    InviteAction,
    SortDirection,
    InvitationSortField,
    MemberSortField,
    WorkspaceException,
    InvitationNotFoundError,
    InvitationAlreadyAcceptedError,
    InvitationNotPendingError,
    MemberNotFoundError,
    WorkspaceNotFoundError,
    InsufficientPermissionsError
)


class TestWorkspaceInvitationClient:
    """Comprehensive test suite for WorkspaceClient invitation features"""

    @pytest.fixture
    def client(self):
        """Create a WorkspaceClient instance for testing"""
        return WorkspaceClient("http://localhost:3602/graphql")

    @pytest.fixture
    def mock_token(self):
        """Mock authentication token"""
        return "mock-jwt-token-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

    @pytest.fixture
    def mock_workspace_id(self):
        """Mock workspace ID"""
        return "workspace-550e8400-e29b-41d4-a716-446655440000"

    @pytest.fixture
    def mock_invitation(self) -> Invitation:
        """Mock invitation data factory"""
        return {
            "id": "invitation-1",
            "email": "newuser@example.com",
            "status": InviteStatus.INVITED.value,
            "roleIds": ["role-admin", "role-developer"],
            "workspaceID": "workspace-550e8400-e29b-41d4-a716-446655440000",
            "workspace": {
                "id": "workspace-550e8400-e29b-41d4-a716-446655440000",
                "name": "Test Workspace"
            },
            "invitedUserID": "user-inviter-123",
            "invitedBy": {
                "id": "user-inviter-123",
                "name": "Admin User",
                "email": "admin@example.com"
            },
            "createdAt": "2025-01-01T00:00:00Z",
            "updatedAt": "2025-01-01T00:00:00Z"
        }

    @pytest.fixture
    def mock_workspace_member(self) -> WorkspaceMember:
        """Mock workspace member data factory"""
        return {
            "id": "member-1",
            "workspaceID": "workspace-550e8400-e29b-41d4-a716-446655440000",
            "userID": "user-123",
            "workspace": {
                "id": "workspace-550e8400-e29b-41d4-a716-446655440000",
                "name": "Test Workspace"
            },
            "user": {
                "id": "user-123",
                "name": "John Doe",
                "email": "john@example.com"
            }
        }

    @pytest.fixture
    def mock_paginated_invitations(self, mock_invitation) -> PaginatedInvitations:
        """Mock paginated invitations data factory"""
        return {
            "invitations": [
                mock_invitation,
                {**mock_invitation, "id": "invitation-2", "email": "user2@example.com"},
                {**mock_invitation, "id": "invitation-3", "email": "user3@example.com"}
            ],
            "totalCount": 15,
            "totalPages": 2,
            "currentPage": 1,
            "pageSize": 10,
            "hasNextPage": True,
            "hasPreviousPage": False
        }

    @pytest.fixture
    def mock_paginated_members(self, mock_workspace_member) -> PaginatedMembers:
        """Mock paginated members data factory"""
        return {
            "members": [
                mock_workspace_member,
                {**mock_workspace_member, "id": "member-2", "user": {"id": "user-456", "name": "Jane Smith", "email": "jane@example.com"}},
                {**mock_workspace_member, "id": "member-3", "user": {"id": "user-789", "name": "Bob Johnson", "email": "bob@example.com"}}
            ],
            "totalCount": 25,
            "totalPages": 1,
            "currentPage": 1,
            "pageSize": 50,
            "hasNextPage": False,
            "hasPreviousPage": False
        }

    # =========================================================================
    # INVITE USER TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_invite_user_success(self, client, mock_token, mock_workspace_id):
        """Test successful user invitation"""
        email = "newuser@example.com"
        role_ids = ["role-admin", "role-developer"]

        expected_response = {"email": email}

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"inviteUser": expected_response}
            mock_get_client.return_value = mock_gql_client

            result = await client.invite_user(mock_workspace_id, email, role_ids, mock_token)

            assert result == expected_response
            assert result["email"] == email

            # Verify mutation was called with correct variables
            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["input"]["workspaceID"] == mock_workspace_id
            assert call_args[1]["variable_values"]["input"]["email"] == email
            assert call_args[1]["variable_values"]["input"]["roleIds"] == role_ids

    @pytest.mark.asyncio
    async def test_invite_user_workspace_not_found(self, client, mock_token):
        """Test invitation to non-existent workspace"""
        workspace_id = "non-existent-workspace"
        email = "user@example.com"
        role_ids = ["role-1"]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("WORKSPACE_NOT_FOUND")
            mock_get_client.return_value = mock_gql_client

            with pytest.raises(WorkspaceNotFoundError) as exc_info:
                await client.invite_user(workspace_id, email, role_ids, mock_token)

            assert exc_info.value.code == "WORKSPACE_NOT_FOUND"
            assert workspace_id in exc_info.value.details["workspaceId"]

    @pytest.mark.asyncio
    async def test_invite_user_insufficient_permissions(self, client, mock_token, mock_workspace_id):
        """Test invitation without sufficient permissions"""
        email = "user@example.com"
        role_ids = ["role-admin"]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("INSUFFICIENT_PERMISSIONS")
            mock_get_client.return_value = mock_gql_client

            with pytest.raises(InsufficientPermissionsError) as exc_info:
                await client.invite_user(mock_workspace_id, email, role_ids, mock_token)

            assert exc_info.value.code == "INSUFFICIENT_PERMISSIONS"
            assert "invite users" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_invite_user_already_member(self, client, mock_token, mock_workspace_id):
        """Test inviting user who is already a member"""
        email = "existing@example.com"
        role_ids = ["role-1"]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("User is already a member")
            mock_get_client.return_value = mock_gql_client

            with pytest.raises(WorkspaceException) as exc_info:
                await client.invite_user(mock_workspace_id, email, role_ids, mock_token)

            assert exc_info.value.code == "USER_ALREADY_MEMBER"
            assert email in exc_info.value.details["email"]

    @pytest.mark.asyncio
    async def test_invite_user_invalid_email(self, client, mock_token, mock_workspace_id):
        """Test invitation with invalid email format"""
        invalid_email = "not-an-email"
        role_ids = ["role-1"]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Invalid email format")
            mock_get_client.return_value = mock_gql_client

            with pytest.raises(WorkspaceException) as exc_info:
                await client.invite_user(mock_workspace_id, invalid_email, role_ids, mock_token)

            assert exc_info.value.code == "INVALID_EMAIL"
            assert invalid_email in exc_info.value.details["email"]

    # =========================================================================
    # GET WORKSPACE INVITATIONS TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_invitations_basic(self, client, mock_token, mock_workspace_id, mock_paginated_invitations):
        """Test basic invitation retrieval without filters"""
        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getWorkspaceInvitations": mock_paginated_invitations}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_workspace_invitations(mock_workspace_id, mock_token)

            assert result == mock_paginated_invitations
            assert len(result["invitations"]) == 3
            assert result["totalCount"] == 15
            assert result["hasNextPage"] is True

    @pytest.mark.asyncio
    async def test_get_invitations_with_pagination(self, client, mock_token, mock_workspace_id):
        """Test invitation retrieval with pagination"""
        pagination = {"page": 2, "pageSize": 5}
        paginated_result = {
            "invitations": [],
            "totalCount": 15,
            "totalPages": 3,
            "currentPage": 2,
            "pageSize": 5,
            "hasNextPage": True,
            "hasPreviousPage": True
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getWorkspaceInvitations": paginated_result}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_workspace_invitations(
                mock_workspace_id,
                mock_token,
                pagination=pagination
            )

            assert result["currentPage"] == 2
            assert result["pageSize"] == 5
            assert result["hasNextPage"] is True
            assert result["hasPreviousPage"] is True

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["pagination"] == pagination

    @pytest.mark.asyncio
    async def test_get_invitations_with_filter(self, client, mock_token, mock_workspace_id, mock_invitation):
        """Test invitation retrieval with status filter"""
        filter_input = {"status": InviteStatus.INVITED.value}
        filtered_result = {
            "invitations": [mock_invitation],
            "totalCount": 1,
            "totalPages": 1,
            "currentPage": 1,
            "pageSize": 10,
            "hasNextPage": False,
            "hasPreviousPage": False
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getWorkspaceInvitations": filtered_result}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_workspace_invitations(
                mock_workspace_id,
                mock_token,
                filter=filter_input
            )

            assert result["totalCount"] == 1
            assert result["invitations"][0]["status"] == InviteStatus.INVITED.value

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["filter"] == filter_input

    @pytest.mark.asyncio
    async def test_get_invitations_with_search(self, client, mock_token, mock_workspace_id, mock_invitation):
        """Test invitation retrieval with search"""
        search_term = "john@example.com"
        search_result = {
            "invitations": [mock_invitation],
            "totalCount": 1,
            "totalPages": 1,
            "currentPage": 1,
            "pageSize": 10,
            "hasNextPage": False,
            "hasPreviousPage": False
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getWorkspaceInvitations": search_result}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_workspace_invitations(
                mock_workspace_id,
                mock_token,
                search=search_term
            )

            assert result["totalCount"] == 1

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["search"] == search_term

    @pytest.mark.asyncio
    async def test_get_invitations_with_sort(self, client, mock_token, mock_workspace_id, mock_paginated_invitations):
        """Test invitation retrieval with sorting"""
        sort_input = {
            "field": InvitationSortField.CREATED_AT.value,
            "direction": SortDirection.DESC.value
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getWorkspaceInvitations": mock_paginated_invitations}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_workspace_invitations(
                mock_workspace_id,
                mock_token,
                sort=sort_input
            )

            assert len(result["invitations"]) > 0

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["sort"] == sort_input

    @pytest.mark.asyncio
    async def test_get_invitations_combined_query(self, client, mock_token, mock_workspace_id, mock_invitation):
        """Test invitation retrieval with filter + search + sort + pagination"""
        filter_input = {"status": InviteStatus.INVITED.value}
        search_term = "example.com"
        sort_input = {"field": InvitationSortField.EMAIL.value, "direction": SortDirection.ASC.value}
        pagination = {"page": 1, "pageSize": 20}

        combined_result = {
            "invitations": [mock_invitation],
            "totalCount": 5,
            "totalPages": 1,
            "currentPage": 1,
            "pageSize": 20,
            "hasNextPage": False,
            "hasPreviousPage": False
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getWorkspaceInvitations": combined_result}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_workspace_invitations(
                mock_workspace_id,
                mock_token,
                filter=filter_input,
                search=search_term,
                sort=sort_input,
                pagination=pagination
            )

            assert result["totalCount"] == 5
            assert result["currentPage"] == 1

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["filter"] == filter_input
            assert call_args[1]["variable_values"]["search"] == search_term
            assert call_args[1]["variable_values"]["sort"] == sort_input
            assert call_args[1]["variable_values"]["pagination"] == pagination

    @pytest.mark.asyncio
    async def test_get_invitations_empty_result(self, client, mock_token, mock_workspace_id):
        """Test invitation retrieval with empty result"""
        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getWorkspaceInvitations": None}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_workspace_invitations(mock_workspace_id, mock_token)

            assert result["invitations"] == []
            assert result["totalCount"] == 0
            assert result["hasNextPage"] is False

    @pytest.mark.asyncio
    async def test_get_invitations_workspace_not_found(self, client, mock_token):
        """Test get invitations for non-existent workspace"""
        workspace_id = "non-existent"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("WORKSPACE_NOT_FOUND")
            mock_get_client.return_value = mock_gql_client

            with pytest.raises(WorkspaceNotFoundError) as exc_info:
                await client.get_workspace_invitations(workspace_id, mock_token)

            assert exc_info.value.code == "WORKSPACE_NOT_FOUND"

    # =========================================================================
    # RESEND INVITATION TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_resend_invitation_success(self, client, mock_token, mock_invitation):
        """Test successful invitation resend"""
        invitation_id = "invitation-1"
        updated_invitation = {
            **mock_invitation,
            "updatedAt": "2025-01-02T00:00:00Z"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"resendInvitation": updated_invitation}
            mock_get_client.return_value = mock_gql_client

            result = await client.resend_invitation(invitation_id, mock_token)

            assert result == updated_invitation
            assert result["id"] == invitation_id
            assert result["updatedAt"] == "2025-01-02T00:00:00Z"

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["invitationID"] == invitation_id

    @pytest.mark.asyncio
    async def test_resend_invitation_not_found(self, client, mock_token):
        """Test resending non-existent invitation"""
        invitation_id = "non-existent"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("INVITATION_NOT_FOUND")
            mock_get_client.return_value = mock_gql_client

            with pytest.raises(InvitationNotFoundError) as exc_info:
                await client.resend_invitation(invitation_id, mock_token)

            assert exc_info.value.code == "INVITATION_NOT_FOUND"
            assert invitation_id in exc_info.value.details["invitationId"]

    @pytest.mark.asyncio
    async def test_resend_invitation_already_accepted(self, client, mock_token):
        """Test resending already accepted invitation"""
        invitation_id = "accepted-invitation"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("INVITATION_ALREADY_ACCEPTED")
            mock_get_client.return_value = mock_gql_client

            with pytest.raises(InvitationAlreadyAcceptedError) as exc_info:
                await client.resend_invitation(invitation_id, mock_token)

            assert exc_info.value.code == "INVITATION_ALREADY_ACCEPTED"

    @pytest.mark.asyncio
    async def test_resend_invitation_not_pending(self, client, mock_token):
        """Test resending invitation that is not pending"""
        invitation_id = "rejected-invitation"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("INVITATION_NOT_PENDING")
            mock_get_client.return_value = mock_gql_client

            with pytest.raises(InvitationNotPendingError) as exc_info:
                await client.resend_invitation(invitation_id, mock_token)

            assert exc_info.value.code == "INVITATION_NOT_PENDING"

    # =========================================================================
    # CANCEL INVITATION TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_cancel_invitation_success(self, client, mock_token, mock_invitation):
        """Test successful invitation cancellation"""
        invitation_id = "invitation-1"
        cancelled_invitation = {
            **mock_invitation,
            "status": InviteStatus.REJECTED.value,
            "updatedAt": "2025-01-02T00:00:00Z"
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"cancelInvitation": cancelled_invitation}
            mock_get_client.return_value = mock_gql_client

            result = await client.cancel_invitation(invitation_id, mock_token)

            assert result == cancelled_invitation
            assert result["status"] == InviteStatus.REJECTED.value

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["invitationID"] == invitation_id

    @pytest.mark.asyncio
    async def test_cancel_invitation_not_found(self, client, mock_token):
        """Test cancelling non-existent invitation"""
        invitation_id = "non-existent"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("INVITATION_NOT_FOUND")
            mock_get_client.return_value = mock_gql_client

            with pytest.raises(InvitationNotFoundError) as exc_info:
                await client.cancel_invitation(invitation_id, mock_token)

            assert exc_info.value.code == "INVITATION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_cancel_invitation_already_accepted(self, client, mock_token):
        """Test cancelling already accepted invitation"""
        invitation_id = "accepted-invitation"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("INVITATION_ALREADY_ACCEPTED")
            mock_get_client.return_value = mock_gql_client

            with pytest.raises(InvitationAlreadyAcceptedError) as exc_info:
                await client.cancel_invitation(invitation_id, mock_token)

            assert exc_info.value.code == "INVITATION_ALREADY_ACCEPTED"

    # =========================================================================
    # GET WORKSPACE MEMBERS TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_get_members_basic(self, client, mock_token, mock_workspace_id, mock_paginated_members):
        """Test basic member retrieval"""
        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getWorkspaceMembers": mock_paginated_members}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_workspace_members(mock_workspace_id, mock_token)

            assert result == mock_paginated_members
            assert len(result["members"]) == 3
            assert result["totalCount"] == 25

    @pytest.mark.asyncio
    async def test_get_members_with_search(self, client, mock_token, mock_workspace_id, mock_workspace_member):
        """Test member retrieval with search"""
        search_term = "john"
        search_result = {
            "members": [mock_workspace_member],
            "totalCount": 1,
            "totalPages": 1,
            "currentPage": 1,
            "pageSize": 50,
            "hasNextPage": False,
            "hasPreviousPage": False
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getWorkspaceMembers": search_result}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_workspace_members(
                mock_workspace_id,
                mock_token,
                search=search_term
            )

            assert result["totalCount"] == 1
            assert "john" in result["members"][0]["user"]["email"].lower()

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["search"] == search_term

    @pytest.mark.asyncio
    async def test_get_members_with_sort(self, client, mock_token, mock_workspace_id, mock_paginated_members):
        """Test member retrieval with sorting"""
        sort_input = {
            "field": MemberSortField.EMAIL.value,
            "direction": SortDirection.ASC.value
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getWorkspaceMembers": mock_paginated_members}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_workspace_members(
                mock_workspace_id,
                mock_token,
                sort=sort_input
            )

            assert len(result["members"]) > 0

            call_args = mock_gql_client.execute.call_args
            assert call_args[1]["variable_values"]["sort"] == sort_input

    @pytest.mark.asyncio
    async def test_get_members_with_pagination(self, client, mock_token, mock_workspace_id):
        """Test member retrieval with pagination"""
        pagination = {"page": 1, "pageSize": 10}
        paginated_result = {
            "members": [],
            "totalCount": 100,
            "totalPages": 10,
            "currentPage": 1,
            "pageSize": 10,
            "hasNextPage": True,
            "hasPreviousPage": False
        }

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getWorkspaceMembers": paginated_result}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_workspace_members(
                mock_workspace_id,
                mock_token,
                pagination=pagination
            )

            assert result["currentPage"] == 1
            assert result["pageSize"] == 10
            assert result["totalCount"] == 100
            assert result["hasNextPage"] is True

    @pytest.mark.asyncio
    async def test_get_members_empty_result(self, client, mock_token, mock_workspace_id):
        """Test member retrieval with empty result"""
        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"getWorkspaceMembers": None}
            mock_get_client.return_value = mock_gql_client

            result = await client.get_workspace_members(mock_workspace_id, mock_token)

            assert result["members"] == []
            assert result["totalCount"] == 0

    # =========================================================================
    # EDGE CASES AND ERROR SCENARIOS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_invite_user_with_empty_role_list(self, client, mock_token, mock_workspace_id):
        """Test invitation with empty role list"""
        email = "user@example.com"
        role_ids = []

        expected_response = {"email": email}

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"inviteUser": expected_response}
            mock_get_client.return_value = mock_gql_client

            result = await client.invite_user(mock_workspace_id, email, role_ids, mock_token)

            assert result["email"] == email

    @pytest.mark.asyncio
    async def test_invite_user_with_many_roles(self, client, mock_token, mock_workspace_id):
        """Test invitation with many roles"""
        email = "poweruser@example.com"
        role_ids = [f"role-{i}" for i in range(1, 11)]  # 10 roles

        expected_response = {"email": email}

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"inviteUser": expected_response}
            mock_get_client.return_value = mock_gql_client

            result = await client.invite_user(mock_workspace_id, email, role_ids, mock_token)

            assert result["email"] == email
            call_args = mock_gql_client.execute.call_args
            assert len(call_args[1]["variable_values"]["input"]["roleIds"]) == 10

    @pytest.mark.asyncio
    async def test_network_error_handling(self, client, mock_token, mock_workspace_id):
        """Test handling of network errors"""
        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Network connection failed")
            mock_get_client.return_value = mock_gql_client

            with pytest.raises(WorkspaceException) as exc_info:
                await client.invite_user(mock_workspace_id, "user@example.com", ["role-1"], mock_token)

            assert "Network connection failed" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, client, mock_workspace_id):
        """Test handling of authentication errors"""
        invalid_token = "invalid-token"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = Exception("Authentication failed")
            mock_get_client.return_value = mock_gql_client

            with pytest.raises(WorkspaceException):
                await client.get_workspace_invitations(mock_workspace_id, invalid_token)

    @pytest.mark.asyncio
    async def test_unicode_email_handling(self, client, mock_token, mock_workspace_id):
        """Test handling of unicode characters in email"""
        unicode_email = "用户@example.com"
        role_ids = ["role-1"]

        expected_response = {"email": unicode_email}

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.return_value = {"inviteUser": expected_response}
            mock_get_client.return_value = mock_gql_client

            result = await client.invite_user(mock_workspace_id, unicode_email, role_ids, mock_token)

            assert result["email"] == unicode_email

    # =========================================================================
    # PERFORMANCE TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_bulk_invitation_simulation(self, client, mock_token, mock_workspace_id):
        """Test performance of multiple concurrent invitations"""
        emails = [f"user{i}@example.com" for i in range(50)]
        role_ids = ["role-1"]

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_gql_client.execute.side_effect = [
                {"inviteUser": {"email": email}}
                for email in emails
            ]
            mock_get_client.return_value = mock_gql_client

            start_time = time.time()

            tasks = [
                client.invite_user(mock_workspace_id, email, role_ids, mock_token)
                for email in emails
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.time()
            execution_time = end_time - start_time

            # Should complete within reasonable time
            assert execution_time < 5.0  # 5 seconds for 50 operations
            assert len(results) == 50

    @pytest.mark.asyncio
    async def test_pagination_iteration(self, client, mock_token, mock_workspace_id):
        """Test iterating through paginated results"""
        page_size = 10
        total_count = 25

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()

            # Mock responses for 3 pages
            mock_responses = [
                {
                    "getWorkspaceInvitations": {
                        "invitations": [{"id": f"inv-{i}", "email": f"user{i}@example.com"} for i in range(10)],
                        "totalCount": total_count,
                        "totalPages": 3,
                        "currentPage": 1,
                        "pageSize": page_size,
                        "hasNextPage": True,
                        "hasPreviousPage": False
                    }
                },
                {
                    "getWorkspaceInvitations": {
                        "invitations": [{"id": f"inv-{i}", "email": f"user{i}@example.com"} for i in range(10, 20)],
                        "totalCount": total_count,
                        "totalPages": 3,
                        "currentPage": 2,
                        "pageSize": page_size,
                        "hasNextPage": True,
                        "hasPreviousPage": True
                    }
                },
                {
                    "getWorkspaceInvitations": {
                        "invitations": [{"id": f"inv-{i}", "email": f"user{i}@example.com"} for i in range(20, 25)],
                        "totalCount": total_count,
                        "totalPages": 3,
                        "currentPage": 3,
                        "pageSize": page_size,
                        "hasNextPage": False,
                        "hasPreviousPage": True
                    }
                }
            ]

            mock_gql_client.execute.side_effect = mock_responses
            mock_get_client.return_value = mock_gql_client

            all_invitations = []
            page = 1

            while True:
                result = await client.get_workspace_invitations(
                    mock_workspace_id,
                    mock_token,
                    pagination={"page": page, "pageSize": page_size}
                )

                all_invitations.extend(result["invitations"])

                if not result["hasNextPage"]:
                    break

                page += 1

            assert len(all_invitations) == total_count


# Integration Tests
class TestWorkspaceInvitationIntegration:
    """Integration tests for complete invitation workflows"""

    @pytest.mark.asyncio
    async def test_complete_invitation_lifecycle(self):
        """Test complete invitation workflow: invite → resend → accept"""
        client = WorkspaceClient("http://localhost:3602/graphql")
        token = "test-token"
        workspace_id = "workspace-1"

        with patch.object(client, 'get_client') as mock_get_client:
            mock_gql_client = MagicMock()
            mock_get_client.return_value = mock_gql_client

            # Mock responses for complete workflow
            mock_gql_client.execute.side_effect = [
                # 1. Invite user
                {"inviteUser": {"email": "newuser@example.com"}},
                # 2. Get invitations (verify created)
                {
                    "getWorkspaceInvitations": {
                        "invitations": [
                            {
                                "id": "inv-1",
                                "email": "newuser@example.com",
                                "status": "invited",
                                "createdAt": "2025-01-01T00:00:00Z"
                            }
                        ],
                        "totalCount": 1,
                        "currentPage": 1,
                        "pageSize": 10,
                        "totalPages": 1,
                        "hasNextPage": False,
                        "hasPreviousPage": False
                    }
                },
                # 3. Resend invitation
                {
                    "resendInvitation": {
                        "id": "inv-1",
                        "email": "newuser@example.com",
                        "status": "invited",
                        "updatedAt": "2025-01-02T00:00:00Z"
                    }
                }
            ]

            # 1. Invite user
            invite_response = await client.invite_user(
                workspace_id, "newuser@example.com", ["role-1"], token
            )
            assert invite_response["email"] == "newuser@example.com"

            # 2. Verify invitation was created
            invitations = await client.get_workspace_invitations(workspace_id, token)
            assert invitations["totalCount"] == 1
            assert invitations["invitations"][0]["email"] == "newuser@example.com"

            # 3. Resend invitation
            resent = await client.resend_invitation("inv-1", token)
            assert resent["id"] == "inv-1"
            assert resent["updatedAt"] == "2025-01-02T00:00:00Z"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short", "--cov=workspaces_sdk.workspace", "--cov-report=html"])
