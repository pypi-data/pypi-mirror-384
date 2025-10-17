"""
Workspace Client for Workspaces SDK.

Provides access to workspace management functionality including creating,
updating, managing workspaces, invitations, and members.
"""

from enum import Enum
from typing import List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Enum types for better type safety
class InviteStatus(str, Enum):
    """Invitation status enum"""

    INVITED = "invited"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class InviteAction(str, Enum):
    """Invitation action enum"""

    ACCEPT = "accept"
    REJECT = "reject"


class SortDirection(str, Enum):
    """Sort direction enum"""

    ASC = "ASC"
    DESC = "DESC"


class InvitationSortField(str, Enum):
    """Invitation sort field enum"""

    CREATED_AT = "createdAt"
    UPDATED_AT = "updatedAt"
    EMAIL = "email"
    STATUS = "status"


class MemberSortField(str, Enum):
    """Member sort field enum"""

    EMAIL = "email"
    NAME = "name"


# Custom exception classes for workspace operations
class WorkspaceException(Exception):
    """Base exception for workspace operations"""

    def __init__(self, message: str, code: str, details: Optional[dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class InvitationNotFoundError(WorkspaceException):
    """Raised when invitation is not found"""

    def __init__(self, invitation_id: str):
        super().__init__(
            f"Invitation with ID {invitation_id} not found",
            "INVITATION_NOT_FOUND",
            {"invitationId": invitation_id},
        )


class InvitationAlreadyAcceptedError(WorkspaceException):
    """Raised when trying to modify an accepted invitation"""

    def __init__(self):
        super().__init__(
            "Invitation has already been accepted",
            "INVITATION_ALREADY_ACCEPTED",
        )


class InvitationNotPendingError(WorkspaceException):
    """Raised when invitation is not in pending status"""

    def __init__(self, current_status: str):
        super().__init__(
            f"Invitation is not pending (current status: {current_status})",
            "INVITATION_NOT_PENDING",
            {"currentStatus": current_status},
        )


class MemberNotFoundError(WorkspaceException):
    """Raised when workspace member is not found"""

    def __init__(self, member_id: str):
        super().__init__(
            f"Workspace member with ID {member_id} not found",
            "MEMBER_NOT_FOUND",
            {"memberId": member_id},
        )


class WorkspaceNotFoundError(WorkspaceException):
    """Raised when workspace is not found"""

    def __init__(self, workspace_id: str):
        super().__init__(
            f"Workspace with ID {workspace_id} not found",
            "WORKSPACE_NOT_FOUND",
            {"workspaceId": workspace_id},
        )


class InsufficientPermissionsError(WorkspaceException):
    """Raised when user lacks required permissions"""

    def __init__(self, action: str, resource: str):
        super().__init__(
            f"Insufficient permissions to {action} on {resource}",
            "INSUFFICIENT_PERMISSIONS",
            {"action": action, "resource": resource},
        )


# Type definitions for Workspace system
class CreateWorkspaceInput(TypedDict):
    name: str
    type: Optional[str]
    tenantID: str


class UpdateWorkspaceInput(TypedDict):
    id: str
    name: Optional[str]
    type: Optional[str]
    status: Optional[str]


class InviteUserInput(TypedDict):
    workspaceID: str
    email: str
    roleIds: List[str]


class InvitationActionInput(TypedDict):
    inviteToken: str
    action: str  # "accept" or "reject"
    user: Optional[dict]
    userID: Optional[str]


class User(TypedDict):
    id: str
    name: Optional[str]
    email: str


class Organization(TypedDict):
    id: str
    name: str


class Tenant(TypedDict):
    id: str
    name: Optional[str]


class BillingAccount(TypedDict):
    id: str
    accountName: str
    billingAddress: str


class StoreItemOnWorkSpace(TypedDict):
    id: str


class StoreOrder(TypedDict):
    id: str


class Workspace(TypedDict):
    id: str
    name: str
    type: str
    ownerId: Optional[str]
    createdAt: str
    updatedAt: Optional[str]
    status: str
    billingAccounts: Optional[List[BillingAccount]]
    storeItems: Optional[List[StoreItemOnWorkSpace]]
    storeOrders: Optional[List[StoreOrder]]
    workspaceMembers: Optional[List["WorkspaceMember"]]
    tenantID: str
    orgID: str
    org: Organization
    tenant: Tenant


class WorkspaceMember(TypedDict):
    id: str
    workspaceID: str
    userID: str
    workspace: Workspace
    user: User


class Invitation(TypedDict):
    id: str
    email: str
    status: str
    roleIds: List[str]
    workspaceID: str
    workspace: Optional[Workspace]
    invitedUserID: str
    invitedBy: User
    createdAt: str
    updatedAt: Optional[str]


class InvitationResponse(TypedDict):
    status: str
    workspace: Optional[Workspace]


class InviteUserResponse(TypedDict):
    email: str


# New types for pagination and filtering
class InvitationFilter(TypedDict, total=False):
    """Filter options for invitations"""

    status: str  # 'invited', 'accepted', 'rejected', 'expired'
    includeExpired: bool


class InvitationSort(TypedDict):
    """Sort options for invitations"""

    field: str  # 'createdAt', 'updatedAt', 'email', 'status'
    direction: str  # 'ASC', 'DESC'


class InvitationPagination(TypedDict):
    """Pagination options for invitations"""

    page: int
    pageSize: int


class PaginatedInvitations(TypedDict):
    """Paginated invitations response"""

    invitations: List[Invitation]
    totalCount: int
    totalPages: int
    currentPage: int
    pageSize: int
    hasNextPage: bool
    hasPreviousPage: bool


class MemberSort(TypedDict):
    """Sort options for members"""

    field: str  # 'email', 'name'
    direction: str  # 'ASC', 'DESC'


class MemberPagination(TypedDict):
    """Pagination options for members"""

    page: int
    pageSize: int


class PaginatedMembers(TypedDict):
    """Paginated members response"""

    members: List[WorkspaceMember]
    totalCount: int
    totalPages: int
    currentPage: int
    pageSize: int
    hasNextPage: bool
    hasPreviousPage: bool


class ProductEndpoint(TypedDict):
    workspaceID: str
    productEndpoint: str


class SubscribedProduct(TypedDict):
    id: str
    workspaceID: str
    productID: str


class WorkspaceMemberOut(TypedDict):
    count: int
    members: List[WorkspaceMember]


class WorkspaceClient:
    """
    Client for managing workspaces in the Workspaces platform.

    Provides methods to create, update, retrieve, delete, and manage workspaces,  # noqa: E501
    invitations, and members with proper authentication and error handling.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Workspace client with a GraphQL endpoint.

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

    # Workspace Query Operations
    async def get_workspace(self, workspace_id: str, token: str) -> Optional[Workspace]:
        """
        Retrieves a specific workspace by ID.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token

        Returns:
            Optional[Workspace]: Workspace details or None if not found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetWorkspace($id: ID!) {
                    workspace(id: $id) {
                        id
                        name
                        type
                        ownerId
                        createdAt
                        updatedAt
                        status
                        tenantID
                        orgID
                        org {
                            id
                            name
                        }
                        tenant {
                            id
                        }
                        workspaceMembers {
                            id
                            workspaceID
                            userID
                            user {
                                id
                                name
                                email
                            }
                        }
                    }
                }
            """
            )

            variables = {"id": workspace_id}

            result = client.execute(query, variable_values=variables)
            return result.get("workspace")
        except Exception as e:
            print(f"Get workspace failed: {str(e)}")
            return None

    async def get_workspaces(
        self, token: str, tenant_id: Optional[str] = None
    ) -> List[Workspace]:
        """
        Retrieves all workspaces for a tenant.

        Args:
            token (str): Authentication token
            tenant_id (str, optional): Tenant ID to filter

        Returns:
            List[Workspace]: List of workspaces
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetWorkspaces($tenantID: ID) {
                    workspaces(tenantID: $tenantID) {
                        id
                        name
                        type
                        ownerId
                        createdAt
                        updatedAt
                        status
                        tenantID
                        orgID
                        org {
                            id
                            name
                        }
                        tenant {
                            id
                        }
                    }
                }
            """
            )

            variables = {"tenantID": tenant_id}

            result = client.execute(query, variable_values=variables)
            return result.get("workspaces", [])
        except Exception as e:
            print(f"Get workspaces failed: {str(e)}")
            return []

    async def get_subscribed_products(
        self,
        token: str,
        workspace_id: Optional[str] = None,
        product_id: Optional[str] = None,
    ) -> List[SubscribedProduct]:
        """
        Retrieves subscribed products for a workspace.

        Args:
            token (str): Authentication token
            workspace_id (str, optional): Workspace ID to filter
            product_id (str, optional): Product ID to filter

        Returns:
            List[SubscribedProduct]: List of subscribed products
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetSubscribedProducts($workspaceID: ID, $productID: ID) {
                    subscribedProducts(workspaceID: $workspaceID, productID: $productID) {  # noqa: E501
                        id
                        workspaceID
                        productID
                    }
                }
            """
            )

            variables = {"workspaceID": workspace_id, "productID": product_id}

            result = client.execute(query, variable_values=variables)
            return result.get("subscribedProducts", [])
        except Exception as e:
            print(f"Get subscribed products failed: {str(e)}")
            return []

    async def get_product_endpoints(
        self, workspace_ids: List[str], product_id: str, token: str
    ) -> List[ProductEndpoint]:
        """
        Retrieves product endpoints for workspaces.

        Args:
            workspace_ids (List[str]): List of workspace IDs
            product_id (str): Product ID
            token (str): Authentication token

        Returns:
            List[ProductEndpoint]: List of product endpoints
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetProductEndpoints($workspaceIDs: [ID!]!, $productID: ID!) {  # noqa: E501
                    getProductEndpoints(workspaceIDs: $workspaceIDs, productID: $productID) {
                        workspaceID
                        productEndpoint
                    }
                }
            """
            )

            variables = {
                "workspaceIDs": workspace_ids,
                "productID": product_id,
            }

            result = client.execute(query, variable_values=variables)
            return result.get("getProductEndpoints", [])
        except Exception as e:
            print(f"Get product endpoints failed: {str(e)}")
            return []

    async def get_workspace_members(
        self,
        workspace_id: str,
        token: str,
        search: Optional[str] = None,
        sort: Optional[MemberSort] = None,
        pagination: Optional[MemberPagination] = None,
    ) -> PaginatedMembers:
        """
        Retrieves workspace members with search, sorting, and pagination.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            search (Optional[str]): Optional search by user name or email
            sort (Optional[MemberSort]): Optional sorting configuration
            pagination (Optional[MemberPagination]): Optional pagination configuration  # noqa: E501

        Returns:
            PaginatedMembers: Paginated members with metadata

        Raises:
            WorkspaceNotFoundError: If workspace is not found
            InsufficientPermissionsError: If user lacks permission to view members
            WorkspaceException: For other errors

        Example:
            >>> members = await client.get_workspace_members(
            ...     workspace_id="workspace-123",
            ...     token="auth-token",
            ...     search="john",
            ...     sort={"field": "email", "direction": "ASC"},
            ...     pagination={"page": 1, "pageSize": 50}
            ... )
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetWorkspaceMembers(
                    $workspaceID: ID!
                    $search: String
                    $sort: MemberSortInput
                    $pagination: MemberPaginationInput
                ) {
                    getWorkspaceMembers(
                        workspaceID: $workspaceID
                        search: $search
                        sort: $sort
                        pagination: $pagination
                    ) {
                        members {
                            id
                            workspaceID
                            userID
                            workspace {
                                id
                                name
                            }
                            user {
                                id
                                name
                                email
                            }
                        }
                        totalCount
                        totalPages
                        currentPage
                        pageSize
                        hasNextPage
                        hasPreviousPage
                    }
                }
            """
            )

            variables = {
                "workspaceID": workspace_id,
                "search": search,
                "sort": sort,
                "pagination": pagination,
            }

            result = client.execute(query, variable_values=variables)
            data = result.get("getWorkspaceMembers")

            if not data:
                return {
                    "members": [],
                    "totalCount": 0,
                    "totalPages": 0,
                    "currentPage": 1,
                    "pageSize": (pagination.get("pageSize", 50) if pagination else 50),
                    "hasNextPage": False,
                    "hasPreviousPage": False,
                }

            return data

        except Exception as e:
            error_str = str(e)

            # Parse GraphQL errors and raise specific exceptions
            if "WORKSPACE_NOT_FOUND" in error_str:
                raise WorkspaceNotFoundError(workspace_id)
            elif "INSUFFICIENT_PERMISSIONS" in error_str:
                raise InsufficientPermissionsError(
                    "view members", f"workspace {workspace_id}"
                )
            else:
                print(f"Get workspace members failed: {error_str}")
                raise WorkspaceException(
                    f"Failed to get workspace members: {error_str}",
                    "GET_MEMBERS_FAILED",
                    {"workspaceId": workspace_id},
                )

    async def get_workspace_invitations(
        self,
        workspace_id: str,
        token: str,
        filter: Optional[InvitationFilter] = None,
        search: Optional[str] = None,
        sort: Optional[InvitationSort] = None,
        pagination: Optional[InvitationPagination] = None,
    ) -> PaginatedInvitations:
        """
        Retrieves invitations for a workspace with advanced filtering, search, sorting, and pagination.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            filter (Optional[InvitationFilter]): Optional filter by status or expiry  # noqa: E501
            search (Optional[str]): Optional search by email or inviter name
            sort (Optional[InvitationSort]): Optional sorting configuration
            pagination (Optional[InvitationPagination]): Optional pagination configuration  # noqa: E501

        Returns:
            PaginatedInvitations: Paginated invitations with metadata

        Raises:
            WorkspaceNotFoundError: If workspace is not found
            InsufficientPermissionsError: If user lacks permission to view invitations
            WorkspaceException: For other errors

        Example:
            >>> invitations = await client.get_workspace_invitations(
            ...     workspace_id="workspace-123",
            ...     token="auth-token",
            ...     filter={"status": "invited"},
            ...     search="john@example.com",
            ...     sort={"field": "createdAt", "direction": "DESC"},
            ...     pagination={"page": 1, "pageSize": 20}
            ... )
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetWorkspaceInvitations(
                    $workspaceID: ID!
                    $filter: InvitationFilterInput
                    $search: String
                    $sort: InvitationSortInput
                    $pagination: InvitationPaginationInput
                ) {
                    getWorkspaceInvitations(
                        workspaceID: $workspaceID
                        filter: $filter
                        search: $search
                        sort: $sort
                        pagination: $pagination
                    ) {
                        invitations {
                            id
                            email
                            status
                            roleIds
                            workspaceID
                            workspace {
                                id
                                name
                            }
                            invitedUserID
                            invitedBy {
                                id
                                name
                                email
                            }
                            createdAt
                            updatedAt
                        }
                        totalCount
                        totalPages
                        currentPage
                        pageSize
                        hasNextPage
                        hasPreviousPage
                    }
                }
            """
            )

            variables = {
                "workspaceID": workspace_id,
                "filter": filter,
                "search": search,
                "sort": sort,
                "pagination": pagination,
            }

            result = client.execute(query, variable_values=variables)
            data = result.get("getWorkspaceInvitations")

            if not data:
                return {
                    "invitations": [],
                    "totalCount": 0,
                    "totalPages": 0,
                    "currentPage": 1,
                    "pageSize": (pagination.get("pageSize", 10) if pagination else 10),
                    "hasNextPage": False,
                    "hasPreviousPage": False,
                }

            return data

        except Exception as e:
            error_str = str(e)

            # Parse GraphQL errors and raise specific exceptions
            if "WORKSPACE_NOT_FOUND" in error_str:
                raise WorkspaceNotFoundError(workspace_id)
            elif "INSUFFICIENT_PERMISSIONS" in error_str:
                raise InsufficientPermissionsError(
                    "view invitations", f"workspace {workspace_id}"
                )
            else:
                print(f"Get workspace invitations failed: {error_str}")
                raise WorkspaceException(
                    f"Failed to get workspace invitations: {error_str}",
                    "GET_INVITATIONS_FAILED",
                    {"workspaceId": workspace_id},
                )

    # Workspace Mutation Operations
    async def create_workspace(
        self,
        name: str,
        tenant_id: str,
        token: str,
        workspace_type: Optional[str] = None,
    ) -> Optional[Workspace]:
        """
        Creates a new workspace.

        Args:
            name (str): Workspace name
            tenant_id (str): Tenant ID
            token (str): Authentication token
            workspace_type (str, optional): Workspace type ("workspace" or "user")  # noqa: E501

        Returns:
            Optional[Workspace]: The created workspace or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateWorkspace($input: CreateWorkspaceInput!) {
                    createWorkspace(input: $input) {
                        id
                        name
                        type
                        ownerId
                        createdAt
                        updatedAt
                        status
                        tenantID
                        orgID
                    }
                }
            """
            )

            input_data = {"name": name, "tenantID": tenant_id}

            if workspace_type:
                input_data["type"] = workspace_type

            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get("createWorkspace")
        except Exception as e:
            print(f"Create workspace failed: {str(e)}")
            return None

    async def update_workspace(
        self,
        workspace_id: str,
        token: str,
        name: Optional[str] = None,
        workspace_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Optional[Workspace]:
        """
        Updates an existing workspace.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            name (str, optional): New workspace name
            workspace_type (str, optional): New workspace type
            status (str, optional): New workspace status

        Returns:
            Optional[Workspace]: The updated workspace or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateWorkspace($input: UpdateWorkspaceInput!) {
                    updateWorkspace(input: $input) {
                        id
                        name
                        type
                        ownerId
                        createdAt
                        updatedAt
                        status
                        tenantID
                        orgID
                    }
                }
            """
            )

            update_input = {"id": workspace_id}

            if name is not None:
                update_input["name"] = name
            if workspace_type is not None:
                update_input["type"] = workspace_type
            if status is not None:
                update_input["status"] = status

            variables = {"input": update_input}

            result = client.execute(mutation, variable_values=variables)
            return result.get("updateWorkspace")
        except Exception as e:
            print(f"Update workspace failed: {str(e)}")
            return None

    async def delete_workspace(
        self, workspace_id: str, token: str
    ) -> Optional[Workspace]:
        """
        Deletes a workspace.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token

        Returns:
            Optional[Workspace]: The deleted workspace or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DeleteWorkspace($id: ID!) {
                    deleteWorkspace(id: $id) {
                        id
                        name
                        type
                        status
                    }
                }
            """
            )

            variables = {"id": workspace_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("deleteWorkspace")
        except Exception as e:
            print(f"Delete workspace failed: {str(e)}")
            return None

    async def archive_workspace(
        self, workspace_id: str, token: str
    ) -> Optional[Workspace]:
        """
        Archives a workspace.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token

        Returns:
            Optional[Workspace]: The archived workspace or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ArchiveWorkspace($id: ID!) {
                    archieveWorkspace(id: $id) {
                        id
                        name
                        type
                        status
                    }
                }
            """
            )

            variables = {"id": workspace_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("archieveWorkspace")
        except Exception as e:
            print(f"Archive workspace failed: {str(e)}")
            return None

    async def reactivate_workspace(
        self, workspace_id: str, token: str
    ) -> Optional[Workspace]:
        """
        Reactivates an archived workspace.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token

        Returns:
            Optional[Workspace]: The reactivated workspace or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ReactivateWorkspace($id: ID!) {
                    reActivateWorkspace(id: $id) {
                        id
                        name
                        type
                        status
                    }
                }
            """
            )

            variables = {"id": workspace_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("reActivateWorkspace")
        except Exception as e:
            print(f"Reactivate workspace failed: {str(e)}")
            return None

    async def switch_workspace(self, workspace_id: str, token: str) -> Optional[str]:
        """
        Switches to a different workspace.

        Args:
            workspace_id (str): Workspace ID to switch to
            token (str): Authentication token

        Returns:
            Optional[str]: New token or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation SwitchWorkspace($workspaceID: ID!) {
                    switchWorkspace(workspaceID: $workspaceID)
                }
            """
            )

            variables = {"workspaceID": workspace_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("switchWorkspace")
        except Exception as e:
            print(f"Switch workspace failed: {str(e)}")
            return None

    # Invitation Operations
    async def invite_user(
        self, workspace_id: str, email: str, role_ids: List[str], token: str
    ) -> InviteUserResponse:
        """
        Invites a user to a workspace with specified roles.

        Args:
            workspace_id (str): Workspace ID
            email (str): User email to invite
            role_ids (List[str]): List of role IDs to assign
            token (str): Authentication token

        Returns:
            InviteUserResponse: Invitation response with email confirmation

        Raises:
            WorkspaceNotFoundError: If workspace is not found
            InsufficientPermissionsError: If user lacks permission to invite
            WorkspaceException: For other errors (invalid email, duplicate invitation, etc.)  # noqa: E501

        Example:
            >>> response = await client.invite_user(
            ...     workspace_id="workspace-123",
            ...     email="newuser@example.com",
            ...     role_ids=["role-admin", "role-developer"],
            ...     token="auth-token"
            ... )
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation InviteUser($input: InviteUserInput!) {
                    inviteUser(input: $input) {
                        email
                    }
                }
            """
            )

            input_data = {
                "workspaceID": workspace_id,
                "email": email,
                "roleIds": role_ids,
            }

            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get("inviteUser")

        except Exception as e:
            error_str = str(e)

            # Parse GraphQL errors and raise specific exceptions
            if "WORKSPACE_NOT_FOUND" in error_str:
                raise WorkspaceNotFoundError(workspace_id)
            elif "INSUFFICIENT_PERMISSIONS" in error_str:
                raise InsufficientPermissionsError(
                    "invite users", f"workspace {workspace_id}"
                )
            elif "already a member" in error_str.lower():
                raise WorkspaceException(
                    f"User {email} is already a member of this workspace",
                    "USER_ALREADY_MEMBER",
                    {"email": email, "workspaceId": workspace_id},
                )
            elif "invalid email" in error_str.lower():
                raise WorkspaceException(
                    f"Invalid email format: {email}",
                    "INVALID_EMAIL",
                    {"email": email},
                )
            else:
                print(f"Invite user failed: {error_str}")
                raise WorkspaceException(
                    f"Failed to invite user: {error_str}",
                    "INVITE_USER_FAILED",
                    {"workspaceId": workspace_id, "email": email},
                )

    async def handle_invitation(
        self,
        invite_token: str,
        action: str,
        token: str,
        user_data: Optional[dict] = None,
        user_id: Optional[str] = None,
    ) -> Optional[InvitationResponse]:
        """
        Handles an invitation (accept or reject).

        Args:
            invite_token (str): Invitation token
            action (str): Action to take ("accept" or "reject")
            token (str): Authentication token
            user_data (dict, optional): User registration data (for new users)
            user_id (str, optional): User ID (for existing users)

        Returns:
            Optional[InvitationResponse]: Invitation response or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation HandleInvitation($input: InvitationActionInput!) {
                    handleInvitation(input: $input) {
                        status
                        workspace {
                            id
                            name
                        }
                    }
                }
            """
            )

            input_data = {"inviteToken": invite_token, "action": action}

            if user_data:
                input_data["user"] = user_data
            if user_id:
                input_data["userID"] = user_id

            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get("handleInvitation")
        except Exception as e:
            print(f"Handle invitation failed: {str(e)}")
            return None

    async def resend_invitation(self, invitation_id: str, token: str) -> Invitation:
        """
        Resends an invitation email with a new token.

        Args:
            invitation_id (str): Invitation ID
            token (str): Authentication token

        Returns:
            Invitation: The updated invitation with new timestamp

        Raises:
            InvitationNotFoundError: If invitation is not found
            InvitationAlreadyAcceptedError: If invitation was already accepted
            InvitationNotPendingError: If invitation status is not 'invited'
            InsufficientPermissionsError: If user lacks permission to resend
            WorkspaceException: For other errors

        Example:
            >>> invitation = await client.resend_invitation(
            ...     invitation_id="invitation-456",
            ...     token="auth-token"
            ... )
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ResendInvitation($invitationID: ID!) {
                    resendInvitation(invitationID: $invitationID) {
                        id
                        email
                        status
                        roleIds
                        workspaceID
                        workspace {
                            id
                            name
                        }
                        invitedUserID
                        invitedBy {
                            id
                            name
                            email
                        }
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"invitationID": invitation_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("resendInvitation")

        except Exception as e:
            error_str = str(e)

            # Parse GraphQL errors and raise specific exceptions
            if "INVITATION_NOT_FOUND" in error_str:
                raise InvitationNotFoundError(invitation_id)
            elif "INVITATION_ALREADY_ACCEPTED" in error_str:
                raise InvitationAlreadyAcceptedError()
            elif (
                "INVITATION_NOT_PENDING" in error_str
                or "not pending" in error_str.lower()
            ):
                raise InvitationNotPendingError("unknown")
            elif "INSUFFICIENT_PERMISSIONS" in error_str:
                raise InsufficientPermissionsError(
                    "resend invitation", f"invitation {invitation_id}"
                )
            else:
                print(f"Resend invitation failed: {error_str}")
                raise WorkspaceException(
                    f"Failed to resend invitation: {error_str}",
                    "RESEND_INVITATION_FAILED",
                    {"invitationId": invitation_id},
                )

    async def cancel_invitation(self, invitation_id: str, token: str) -> Invitation:
        """
        Cancels/revokes a pending invitation.

        Args:
            invitation_id (str): Invitation ID
            token (str): Authentication token

        Returns:
            Invitation: The cancelled invitation with updated status

        Raises:
            InvitationNotFoundError: If invitation is not found
            InvitationAlreadyAcceptedError: If invitation was already accepted
            InsufficientPermissionsError: If user lacks permission to cancel
            WorkspaceException: For other errors

        Example:
            >>> invitation = await client.cancel_invitation(
            ...     invitation_id="invitation-456",
            ...     token="auth-token"
            ... )
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CancelInvitation($invitationID: ID!) {
                    cancelInvitation(invitationID: $invitationID) {
                        id
                        email
                        status
                        roleIds
                        workspaceID
                        workspace {
                            id
                            name
                        }
                        invitedUserID
                        invitedBy {
                            id
                            name
                            email
                        }
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"invitationID": invitation_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("cancelInvitation")

        except Exception as e:
            error_str = str(e)

            # Parse GraphQL errors and raise specific exceptions
            if "INVITATION_NOT_FOUND" in error_str:
                raise InvitationNotFoundError(invitation_id)
            elif "INVITATION_ALREADY_ACCEPTED" in error_str:
                raise InvitationAlreadyAcceptedError()
            elif "INSUFFICIENT_PERMISSIONS" in error_str:
                raise InsufficientPermissionsError(
                    "cancel invitation", f"invitation {invitation_id}"
                )
            else:
                print(f"Cancel invitation failed: {error_str}")
                raise WorkspaceException(
                    f"Failed to cancel invitation: {error_str}",
                    "CANCEL_INVITATION_FAILED",
                    {"invitationId": invitation_id},
                )

    # Member Management Operations
    async def remove_workspace_member(
        self, workspace_id: str, user_id: str, token: str
    ) -> Optional[WorkspaceMember]:
        """
        Removes a member from a workspace.

        Args:
            workspace_id (str): Workspace ID
            user_id (str): User ID to remove
            token (str): Authentication token

        Returns:
            Optional[WorkspaceMember]: The removed member or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation RemoveWorkspaceMember($workspaceID: ID!, $userID: ID!) {  # noqa: E501
                    removeWorkspaceMember(workspaceID: $workspaceID, userID: $userID) {
                        id
                        workspaceID
                        userID
                        user {
                            id
                            name
                            email
                        }
                    }
                }
            """
            )

            variables = {"workspaceID": workspace_id, "userID": user_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("removeWorkspaceMember")
        except Exception as e:
            print(f"Remove workspace member failed: {str(e)}")
            return None

    async def update_member_role(
        self, workspace_id: str, user_id: str, role_id: str, token: str
    ) -> Optional[WorkspaceMember]:
        """
        Updates a member's role in a workspace.

        Args:
            workspace_id (str): Workspace ID
            user_id (str): User ID
            role_id (str): New role ID
            token (str): Authentication token

        Returns:
            Optional[WorkspaceMember]: The updated member or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateMemberRole($workspaceID: ID!, $userID: ID!, $roleId: String!) {  # noqa: E501
                    updateMemberRole(workspaceID: $workspaceID, userID: $userID, roleId: $roleId) {
                        id
                        workspaceID
                        userID
                        user {
                            id
                            name
                            email
                        }
                    }
                }
            """
            )

            variables = {
                "workspaceID": workspace_id,
                "userID": user_id,
                "roleId": role_id,
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("updateMemberRole")
        except Exception as e:
            print(f"Update member role failed: {str(e)}")
            return None


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Workspace client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = WorkspaceClient(graphql_endpoint)


def get_client() -> WorkspaceClient:
    """Get the default Workspace client."""
    if _default_client is None:
        raise RuntimeError("Workspace client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def get_workspace(*args, **kwargs):
    return await get_client().get_workspace(*args, **kwargs)


async def get_workspaces(*args, **kwargs):
    return await get_client().get_workspaces(*args, **kwargs)


async def get_subscribed_products(*args, **kwargs):
    return await get_client().get_subscribed_products(*args, **kwargs)


async def get_product_endpoints(*args, **kwargs):
    return await get_client().get_product_endpoints(*args, **kwargs)


async def get_workspace_members(*args, **kwargs):
    return await get_client().get_workspace_members(*args, **kwargs)


async def get_workspace_invitations(*args, **kwargs):
    return await get_client().get_workspace_invitations(*args, **kwargs)


async def create_workspace(*args, **kwargs):
    return await get_client().create_workspace(*args, **kwargs)


async def update_workspace(*args, **kwargs):
    return await get_client().update_workspace(*args, **kwargs)


async def delete_workspace(*args, **kwargs):
    return await get_client().delete_workspace(*args, **kwargs)


async def archive_workspace(*args, **kwargs):
    return await get_client().archive_workspace(*args, **kwargs)


async def reactivate_workspace(*args, **kwargs):
    return await get_client().reactivate_workspace(*args, **kwargs)


async def switch_workspace(*args, **kwargs):
    return await get_client().switch_workspace(*args, **kwargs)


async def invite_user(*args, **kwargs):
    return await get_client().invite_user(*args, **kwargs)


async def handle_invitation(*args, **kwargs):
    return await get_client().handle_invitation(*args, **kwargs)


async def resend_invitation(*args, **kwargs):
    return await get_client().resend_invitation(*args, **kwargs)


async def cancel_invitation(*args, **kwargs):
    return await get_client().cancel_invitation(*args, **kwargs)


async def remove_workspace_member(*args, **kwargs):
    return await get_client().remove_workspace_member(*args, **kwargs)


async def update_member_role(*args, **kwargs):
    return await get_client().update_member_role(*args, **kwargs)
