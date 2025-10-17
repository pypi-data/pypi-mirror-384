from typing import Any, Dict, List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Enhanced Actor-Based RBAC system
class CreateResourceInput(TypedDict):
    name: str
    identifier: str
    resourceTypeName: str
    parentResourceId: Optional[str]
    metadata: Optional[Dict[str, Any]]
    productID: Optional[str]


class CreateResourceVisibilityInput(TypedDict):
    resourceId: str
    visibilityType: str
    scopeType: Optional[str]
    scopeId: Optional[str]
    allowedUserIds: Optional[List[str]]
    allowedTeamIds: Optional[List[str]]
    allowedRoleIds: Optional[List[str]]


class CreateResourceVisibilityInputEnhanced(TypedDict):
    resourceId: str
    visibilityType: str
    scopeType: Optional[str]
    scopeId: Optional[str]
    allowedUserIds: Optional[List[str]]
    allowedTeamIds: Optional[List[str]]
    allowedRoleIds: Optional[List[str]]
    allowedAgentIds: Optional[List[str]]


class PermissionCheckInput(TypedDict):
    permission: str
    resource: str


class ActorPermissionCheckInput(TypedDict):
    actorId: str
    permission: str
    resource: str


class BulkPermissionCheckInput(TypedDict):
    permissions: List[PermissionCheckInput]


class BulkActorPermissionCheckInput(TypedDict):
    checks: List[ActorPermissionCheckInput]


class PermissionResult(TypedDict):
    permission: str
    resource: str
    allow: bool
    reason: Optional[str]


class Resource(TypedDict):
    id: str
    name: str
    identifier: str
    resourceType: Dict[str, Any]
    workspace: Dict[str, Any]
    parentResourceId: Optional[str]
    metadata: Dict[str, Any]
    isActive: bool
    createdAt: str
    updatedAt: str


class ResourceVisibility(TypedDict):
    id: str
    resourceId: str
    visibilityType: str
    scopeType: Optional[str]
    scopeId: Optional[str]
    allowedUserIds: List[str]
    allowedTeamIds: List[str]
    allowedRoleIds: List[str]
    allowedAgentIds: List[str]
    createdAt: str


class ResourcePermission(TypedDict):
    id: str
    resource: Dict[str, Any]
    permission: Dict[str, Any]
    user: Optional[Dict[str, Any]]
    role: Optional[Dict[str, Any]]
    team: Optional[Dict[str, Any]]
    actor: Optional[Dict[str, Any]]
    conditions: Optional[Dict[str, Any]]
    createdAt: str
    expiresAt: Optional[str]


# Actor-based RBAC types
class Actor(TypedDict):
    id: str
    type: str  # USER or AGENT
    userId: Optional[str]
    agentId: Optional[str]
    user: Optional[Dict[str, Any]]
    agent: Optional[Dict[str, Any]]
    isActive: bool
    workspaceId: str
    createdAt: str
    updatedAt: str


class Agent(TypedDict):
    id: str
    name: str
    type: str  # BOT, SERVICE_ACCOUNT, API_CLIENT, DELEGATED_AGENT
    capabilities: Dict[str, Any]
    configuration: Dict[str, Any]
    delegatedBy: Optional[str]
    delegator: Optional[Dict[str, Any]]
    isActive: bool
    workspaceId: str
    actor: Optional[Actor]
    createdAt: str
    updatedAt: str


class ActorPermission(TypedDict):
    id: str
    actorId: str
    resourceId: str
    permissionId: str
    actor: Actor
    resource: Dict[str, Any]
    permission: Dict[str, Any]
    delegatedBy: Optional[str]
    delegator: Optional[Dict[str, Any]]
    conditions: Optional[Dict[str, Any]]
    expiresAt: Optional[str]
    createdAt: str


class ActorRole(TypedDict):
    id: str
    actorId: str
    roleId: str
    actor: Actor
    role: Dict[str, Any]
    delegatedBy: Optional[str]
    delegator: Optional[Dict[str, Any]]
    expiresAt: Optional[str]
    createdAt: str


# Input types for Actor operations
class CreateActorInput(TypedDict):
    type: str  # USER or AGENT
    userId: Optional[str]
    agentId: Optional[str]
    workspaceId: str


class CreateAgentInput(TypedDict):
    name: str
    type: str  # BOT, SERVICE_ACCOUNT, API_CLIENT, DELEGATED_AGENT
    capabilities: Optional[Dict[str, Any]]
    configuration: Optional[Dict[str, Any]]
    delegatedBy: Optional[str]
    workspaceId: str


class AssignActorPermissionInput(TypedDict):
    actorId: str
    resourceId: str
    permissionId: str
    conditions: Optional[Dict[str, Any]]
    delegatedBy: Optional[str]
    expiresAt: Optional[str]


class AssignActorRoleInput(TypedDict):
    actorId: str
    roleId: str
    delegatedBy: Optional[str]
    expiresAt: Optional[str]


# Constants
RESOURCE_TYPES = {
    "workspace": "workspace",
    "project": "project",
    "team": "team",
    "workflow": "workflow",
    "bot": "bot",
    "knowledgeBase": "knowledgeBase",
    "billingAccount": "billingAccount",
    "plan": "plan",
    "supportTicket": "supportTicket",
    "newsLetter": "newsLetter",
}

ACTOR_TYPES = {"USER": "USER", "AGENT": "AGENT"}

AGENT_TYPES = {
    "BOT": "BOT",
    "SERVICE_ACCOUNT": "SERVICE_ACCOUNT",
    "API_CLIENT": "API_CLIENT",
    "DELEGATED_AGENT": "DELEGATED_AGENT",
}

PERMISSIONS = {
    "create": "create",
    "read": "read",
    "update": "update",
    "delete": "delete",
    "execute": "execute",
    "manage": "manage",
}

VISIBILITY_TYPES = {
    "public": "public",
    "private": "private",
    "workspace": "workspace",
    "team": "team",
    "project": "project",
    "custom": "custom",
}

# Complete resource types with their allowed permissions as defined in the RBAC system  # noqa: E501
RESOURCE_TYPE_PERMISSIONS = {
    "workspace": {
        "description": "Top-level workspace container",
        "parent_type": None,
        "allowed_permissions": [
            "create:project",
            "create:team",
            "create:billingAccount",
            "workspace.read",
            "workspace.update",
            "workspace.delete",
            "workspace.all",
            "workspace.getWorkspaceMembers",
            "workspace.manageRolesAndUserPermissions",
            "workspace.invite",
            "workspace.archive",
            "workspace.unarchive",
            "workspace.manageTeamRoles",
        ],
    },
    "project": {
        "description": "Project within workspace",
        "parent_type": "workspace",
        "allowed_permissions": [
            "project.read",
            "project.update",
            "project.delete",
            "project.all",
            "project.archive",
            "project.unarchive",
            "project.addMember",
            "project.removeMember",
        ],
    },
    "workflow": {
        "description": "Workflow within project",
        "parent_type": "project",
        "allowed_permissions": [
            "workflow.read",
            "workflow.update",
            "workflow.delete",
            "workflow.execute",
            "workflow.all",
        ],
    },
    "bot": {
        "description": "Bot within project",
        "parent_type": "project",
        "allowed_permissions": [
            "bot.read",
            "bot.update",
            "bot.delete",
            "bot.all",
        ],
    },
    "team": {
        "description": "Team within workspace",
        "parent_type": "workspace",
        "allowed_permissions": [
            "team.read",
            "team.update",
            "team.delete",
            "team.all",
            "team.addMember",
            "team.removeMember",
            "team.archive",
            "team.reactivate",
        ],
    },
    "billingAccount": {
        "description": "Billing account within workspace",
        "parent_type": "workspace",
        "allowed_permissions": [
            "billingAccount.read",
            "billingAccount.update",
            "billingAccount.delete",
            "billingAccount.all",
        ],
    },
    "knowledgeBase": {
        "description": "Knowledge base within project",
        "parent_type": "project",
        "allowed_permissions": [
            "knowledgeBase.read",
            "knowledgeBase.update",
            "knowledgeBase.delete",
            "knowledgeBase.all",
        ],
    },
    "plan": {
        "description": "Subscription plan entity (system-level)",
        "parent_type": None,
        "allowed_permissions": [
            "plan.read",
            "plan.update",
            "plan.delete",
            "plan.all",
        ],
    },
    "supportTicket": {
        "description": "Support ticket within workspace",
        "parent_type": "workspace",
        "allowed_permissions": [
            "supportTicket.read",
            "supportTicket.update",
            "supportTicket.delete",
            "supportTicket.all",
        ],
    },
    "newsLetter": {
        "description": "Newsletter entity (system-level)",
        "parent_type": None,
        "allowed_permissions": [
            "newsLetter.read",
            "newsLetter.update",
            "newsLetter.delete",
            "newsLetter.all",
        ],
    },
}


# Helper functions for resource type information
def get_resource_type_info(resource_type: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a specific resource type including its allowed permissions.  # noqa: E501

    Args:
        resource_type (str): The resource type name

    Returns:
        Optional[Dict]: Resource type information or None if not found
    """
    return RESOURCE_TYPE_PERMISSIONS.get(resource_type)


def get_allowed_permissions(resource_type: str) -> List[str]:
    """
    Get the list of allowed permissions for a specific resource type.

    Args:
        resource_type (str): The resource type name

    Returns:
        List[str]: List of allowed permissions for the resource type
    """
    info = get_resource_type_info(resource_type)
    return info["allowed_permissions"] if info else []


def get_resource_hierarchy() -> Dict[str, List[str]]:
    """
    Get the resource type hierarchy showing parent-child relationships.

    Returns:
        Dict[str, List[str]]: Dictionary mapping parent types to their child types  # noqa: E501
    """
    hierarchy = {}
    for resource_type, info in RESOURCE_TYPE_PERMISSIONS.items():
        parent = info.get("parent_type")
        if parent:
            if parent not in hierarchy:
                hierarchy[parent] = []
            hierarchy[parent].append(resource_type)
    return hierarchy


def list_all_permissions() -> List[str]:
    """
    Get a complete list of all permissions across all resource types.

    Returns:
        List[str]: Sorted list of all unique permissions
    """
    all_permissions = set()
    for info in RESOURCE_TYPE_PERMISSIONS.values():
        all_permissions.update(info["allowed_permissions"])
    return sorted(list(all_permissions))


class RBACClient:
    def __init__(self, graphql_endpoint: str):
        """
        Initialize the RBAC client with a GraphQL endpoint.

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

    # Resource Management
    async def create_resource(
        self,
        name: str,
        identifier: str,
        resource_type_name: str,
        token: str,
        parent_resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        product_id: Optional[str] = None,
    ) -> Optional[Resource]:
        """
        Creates a new resource in the RBAC system.

        Args:
            name (str): Resource name
            identifier (str): Resource identifier (external ID)
            resource_type_name (str): Type of resource (from RESOURCE_TYPES)
            token (str): Authentication token
            parent_resource_id (str, optional): Parent resource ID
            metadata (Dict, optional): Resource metadata
            product_id (str, optional): Product ID

        Returns:
            Optional[Resource]: The created resource or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateResource($input: CreateResourceInput!) {
                    createResource(input: $input) {
                        id
                        name
                        identifier
                        resourceType {
                            id
                            name
                        }
                        workspace {
                            id
                        }
                        parentResourceId
                        metadata
                        isActive
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {
                "input": {
                    "name": name,
                    "identifier": identifier,
                    "resourceTypeName": resource_type_name,
                    "parentResourceId": parent_resource_id,
                    "metadata": metadata or {},
                    "productID": product_id,
                }
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("createResource")
        except Exception as e:
            print(f"Create resource failed: {str(e)}")
            return None

    async def update_resource(
        self,
        resource_id: str,
        name: str,
        identifier: str,
        resource_type_name: str,
        token: str,
        parent_resource_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        product_id: Optional[str] = None,
    ) -> Optional[Resource]:
        """
        Updates an existing resource in the RBAC system.

        Args:
            resource_id (str): ID of the resource to update
            name (str): Updated resource name
            identifier (str): Updated resource identifier
            resource_type_name (str): Type of resource
            token (str): Authentication token
            parent_resource_id (str, optional): Parent resource ID
            metadata (Dict, optional): Updated resource metadata
            product_id (str, optional): Product ID

        Returns:
            Optional[Resource]: The updated resource or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateResource($id: ID!, $input: CreateResourceInput!) {  # noqa: E501
                    updateResource(id: $id, input: $input) {
                        id
                        name
                        identifier
                        metadata
                        updatedAt
                    }
                }
            """
            )

            variables = {
                "id": resource_id,
                "input": {
                    "name": name,
                    "identifier": identifier,
                    "resourceTypeName": resource_type_name,
                    "parentResourceId": parent_resource_id,
                    "metadata": metadata or {},
                    "productID": product_id,
                },
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("updateResource")
        except Exception as e:
            print(f"Update resource failed: {str(e)}")
            return None

    async def bulk_create_resources(
        self, resources: List[CreateResourceInput], token: str
    ) -> Optional[List[Resource]]:
        """
        Creates multiple resources in a single operation.

        Args:
            resources (List[CreateResourceInput]): List of resources to create
            token (str): Authentication token

        Returns:
            Optional[List[Resource]]: List of created resources or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation BulkCreateResources($resources: [CreateResourceInput!]!) {  # noqa: E501
                    bulkCreateResources(resources: $resources) {
                        id
                        name
                        identifier
                        resourceType {
                            name
                        }
                        createdAt
                    }
                }
            """
            )

            variables = {"resources": resources}

            result = client.execute(mutation, variable_values=variables)
            return result.get("bulkCreateResources")
        except Exception as e:
            print(f"Bulk create resources failed: {str(e)}")
            return None

    # Resource Queries - Actor-based
    async def get_accessible_resources(
        self, actor_id: str, token: str, resource_type_id: Optional[str] = None
    ) -> List[Resource]:
        """
        Retrieves all resources that an actor can access.

        Args:
            actor_id (str): Actor ID (user or agent)
            token (str): Authentication token
            resource_type_id (str, optional): Filter by resource type

        Returns:
            List[Resource]: List of accessible resources
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAccessibleResources($actorId: String!, $resourceTypeId: String) {  # noqa: E501
                    getAccessibleResources(actorId: $actorId, resourceTypeId: $resourceTypeId) {
                        id
                        name
                        identifier
                        resourceType {
                            name
                        }
                        workspace {
                            id
                            name
                        }
                        metadata
                        createdAt
                        createdBy {
                            id
                            email
                        }
                    }
                }
            """
            )

            variables = {
                "actorId": actor_id,
                "resourceTypeId": resource_type_id,
            }

            result = client.execute(query, variable_values=variables)
            return result.get("getAccessibleResources", [])
        except Exception as e:
            print(f"Get accessible resources failed: {str(e)}")
            return []

    async def get_resource_permissions(
        self, resource_id: str, token: str
    ) -> List[ResourcePermission]:
        """
        Retrieves all permissions associated with a specific resource.

        Args:
            resource_id (str): Resource ID
            token (str): Authentication token

        Returns:
            List[ResourcePermission]: List of resource permissions
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetResourcePermissions($resourceId: String!) {
                    getResourcePermissions(resourceId: $resourceId) {
                        id
                        permission {
                            name
                            description
                        }
                        user {
                            id
                            email
                        }
                        role {
                            id
                            name
                        }
                        team {
                            id
                            name
                        }
                        conditions
                        createdAt
                        expiresAt
                    }
                }
            """
            )

            variables = {"resourceId": resource_id}

            result = client.execute(query, variable_values=variables)
            return result.get("getResourcePermissions", [])
        except Exception as e:
            print(f"Get resource permissions failed: {str(e)}")
            return []

    async def update_resource_visibility_enhanced(
        self,
        visibility_id: str,
        resource_id: str,
        visibility_type: str,
        token: str,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None,
        allowed_user_ids: Optional[List[str]] = None,
        allowed_team_ids: Optional[List[str]] = None,
        allowed_role_ids: Optional[List[str]] = None,
        allowed_agent_ids: Optional[List[str]] = None,
    ) -> Optional[ResourceVisibility]:
        """
        Updates existing visibility settings for a resource with enhanced Agent support.

        Args:
            visibility_id (str): Visibility ID to update
            resource_id (str): Resource ID
            visibility_type (str): Type of visibility
            token (str): Authentication token
            scope_type (str, optional): Scope type
            scope_id (str, optional): Scope ID
            allowed_user_ids (List[str], optional): List of allowed user IDs
            allowed_team_ids (List[str], optional): List of allowed team IDs
            allowed_role_ids (List[str], optional): List of allowed role IDs
            allowed_agent_ids (List[str], optional): List of allowed agent IDs

        Returns:
            Optional[ResourceVisibility]: Updated visibility settings or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateResourceVisibilityEnhanced($id: ID!, $input: CreateResourceVisibilityEnhancedInput!) {  # noqa: E501
                    updateResourceVisibilityEnhanced(id: $id, input: $input) {
                        id
                        visibilityType
                        scopeType
                        scopeId
                        allowedUserIds
                        allowedTeamIds
                        allowedRoleIds
                        allowedAgentIds
                        updatedAt
                        createdBy {
                            id
                            email
                        }
                    }
                }
            """
            )

            variables = {
                "id": visibility_id,
                "input": {
                    "resourceId": resource_id,
                    "visibilityType": visibility_type,
                    "scopeType": scope_type,
                    "scopeId": scope_id,
                    "allowedUserIds": allowed_user_ids or [],
                    "allowedTeamIds": allowed_team_ids or [],
                    "allowedRoleIds": allowed_role_ids or [],
                    "allowedAgentIds": allowed_agent_ids or [],
                },
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("updateResourceVisibilityEnhanced")
        except Exception as e:
            print(f"Update enhanced resource visibility failed: {str(e)}")
            return None

    async def remove_resource_visibility(self, visibility_id: str, token: str) -> bool:
        """
        Removes visibility settings for a resource.

        Args:
            visibility_id (str): Visibility ID to remove
            token (str): Authentication token

        Returns:
            bool: True if successfully removed, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation RemoveResourceVisibility($id: ID!) {
                    removeResourceVisibility(id: $id)
                }
            """
            )

            variables = {"id": visibility_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("removeResourceVisibility", False)
        except Exception as e:
            print(f"Remove resource visibility failed: {str(e)}")
            return False

    async def get_resource_visibility(
        self, resource_id: str, token: str
    ) -> List[ResourceVisibility]:
        """
        Retrieves visibility settings for a specific resource.

        Args:
            resource_id (str): Resource ID
            token (str): Authentication token

        Returns:
            List[ResourceVisibility]: List of visibility settings
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetResourceVisibility($resourceId: String!) {
                    getResourceVisibility(resourceId: $resourceId) {
                        id
                        visibilityType
                        scopeType
                        scopeId
                        allowedUserIds
                        allowedTeamIds
                        allowedRoleIds
                        createdAt
                        createdBy {
                            id
                            email
                        }
                    }
                }
            """
            )

            variables = {"resourceId": resource_id}

            result = client.execute(query, variable_values=variables)
            return result.get("getResourceVisibility", [])
        except Exception as e:
            print(f"Get resource visibility failed: {str(e)}")
            return []

    # Actor Management
    async def create_actor(
        self,
        actor_type: str,
        token: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> Optional[Actor]:
        """
        Creates a new actor in the RBAC system.

        Args:
            actor_type (str): Type of actor (USER or AGENT)
            token (str): Authentication token
            user_id (str, optional): User ID for USER actors
            agent_id (str, optional): Agent ID for AGENT actors

        Returns:
            Optional[Actor]: The created actor or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateActor($input: CreateActorInput!) {
                    createActor(input: $input) {
                        id
                        type
                        userId
                        agentId
                        user {
                            id
                            name
                            email
                        }
                        agent {
                            id
                            name
                            type
                        }
                        isActive
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {
                "input": {
                    "type": actor_type,
                    "userId": user_id,
                    "agentId": agent_id,
                }
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("createActor")
        except Exception as e:
            print(f"Create actor failed: {str(e)}")
            return None

    async def get_actors(self, workspace_id: str, token: str) -> List[Actor]:
        """
        Retrieves all actors in a workspace.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token

        Returns:
            List[Actor]: List of actors in the workspace
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetActors($workspaceId: String!) {
                    getActors(workspaceId: $workspaceId) {
                        id
                        type
                        userId
                        agentId
                        user {
                            id
                            name
                            email
                        }
                        agent {
                            id
                            name
                            type
                        }
                        isActive
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"workspaceId": workspace_id}

            result = client.execute(query, variable_values=variables)
            return result.get("getActors", [])
        except Exception as e:
            print(f"Get actors failed: {str(e)}")
            return []

    async def get_actor(self, actor_id: str, token: str) -> Optional[Actor]:
        """
        Retrieves a specific actor by ID.

        Args:
            actor_id (str): Actor ID
            token (str): Authentication token

        Returns:
            Optional[Actor]: Actor details or None if not found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetActor($id: ID!) {
                    getActor(id: $id) {
                        id
                        type
                        userId
                        agentId
                        user {
                            id
                            name
                            email
                        }
                        agent {
                            id
                            name
                            type
                        }
                        isActive
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"id": actor_id}

            result = client.execute(query, variable_values=variables)
            return result.get("getActor")
        except Exception as e:
            print(f"Get actor failed: {str(e)}")
            return None

    # Agent Management
    async def create_agent(
        self,
        name: str,
        agent_type: str,
        token: str,
        capabilities: Optional[Dict[str, Any]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        delegated_by: Optional[str] = None,
    ) -> Optional[Agent]:
        """
        Creates a new agent in the RBAC system.

        Args:
            name (str): Agent name
            agent_type (str): Type of agent (BOT, SERVICE_ACCOUNT, etc.)
            token (str): Authentication token
            capabilities (Dict, optional): Agent capabilities
            configuration (Dict, optional): Agent configuration
            delegated_by (str, optional): User who created the agent

        Returns:
            Optional[Agent]: The created agent or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateAgent($input: CreateAgentInput!) {
                    createAgent(input: $input) {
                        id
                        name
                        type
                        capabilities
                        configuration
                        delegatedBy
                        delegator {
                            id
                            name
                            email
                        }
                        isActive
                        actor {
                            id
                            type
                        }
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {
                "input": {
                    "name": name,
                    "type": agent_type,
                    "capabilities": capabilities or {},
                    "configuration": configuration or {},
                    "delegatedBy": delegated_by,
                }
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("createAgent")
        except Exception as e:
            print(f"Create agent failed: {str(e)}")
            return None

    async def get_agents(self, workspace_id: str, token: str) -> List[Agent]:
        """
        Retrieves all agents in a workspace.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token

        Returns:
            List[Agent]: List of agents in the workspace
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAgents($workspaceId: String!) {
                    getAgents(workspaceId: $workspaceId) {
                        id
                        name
                        type
                        capabilities
                        configuration
                        delegatedBy
                        delegator {
                            id
                            name
                            email
                        }
                        isActive
                        actor {
                            id
                            type
                        }
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"workspaceId": workspace_id}

            result = client.execute(query, variable_values=variables)
            return result.get("getAgents", [])
        except Exception as e:
            print(f"Get agents failed: {str(e)}")
            return []

    async def get_agent(self, agent_id: str, token: str) -> Optional[Agent]:
        """
        Retrieves a specific agent by ID.

        Args:
            agent_id (str): Agent ID
            token (str): Authentication token

        Returns:
            Optional[Agent]: Agent details or None if not found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAgent($id: ID!) {
                    getAgent(id: $id) {
                        id
                        name
                        type
                        capabilities
                        configuration
                        delegatedBy
                        delegator {
                            id
                            name
                            email
                        }
                        isActive
                        actor {
                            id
                            type
                        }
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"id": agent_id}

            result = client.execute(query, variable_values=variables)
            return result.get("getAgent")
        except Exception as e:
            print(f"Get agent failed: {str(e)}")
            return None

    # Actor Permission Checking
    async def check_actor_permission(
        self, actor_id: str, permission: str, resource: str, token: str
    ) -> bool:
        """
        Checks a single permission for an actor (user or agent).

        Args:
            actor_id (str): Actor ID
            permission (str): Permission to check
            resource (str): Resource identifier
            token (str): Authentication token

        Returns:
            bool: True if permission is allowed, False otherwise
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query CheckActorPermission($actorId: String!, $permission: String!, $resource: String!) {  # noqa: E501
                    checkActorPermission(actorId: $actorId, permission: $permission, resource: $resource)
                }
            """
            )

            variables = {
                "actorId": actor_id,
                "permission": permission,
                "resource": resource,
            }

            result = client.execute(query, variable_values=variables)
            return result.get("checkActorPermission", False)
        except Exception as e:
            print(f"Check actor permission failed: {str(e)}")
            return False

    async def check_multiple_actor_permissions(
        self, permission_checks: List[ActorPermissionCheckInput], token: str
    ) -> List[PermissionResult]:
        """
        Checks multiple permissions for actors in a single request.

        Args:
            permission_checks (List[ActorPermissionCheckInput]): List of permission checks  # noqa: E501
            token (str): Authentication token

        Returns:
            List[PermissionResult]: List of permission results
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query CheckMultipleActorPermissions($input: BulkActorPermissionCheckInput!) {  # noqa: E501
                    checkMultipleActorPermissions(input: $input) {
                        permission
                        resource
                        allow
                        reason
                    }
                }
            """
            )

            variables = {"input": {"checks": permission_checks}}

            result = client.execute(query, variable_values=variables)
            return result.get("checkMultipleActorPermissions", [])
        except Exception as e:
            print(f"Multiple actor permission check failed: {str(e)}")
            return [
                {
                    "permission": check["permission"],
                    "resource": check["resource"],
                    "allow": False,
                    "reason": f"Error: {str(e)}",
                }
                for check in permission_checks
            ]

    # Actor Permission Assignment
    async def assign_permission_to_actor(
        self,
        actor_id: str,
        resource_id: str,
        permission_id: str,
        token: str,
        conditions: Optional[Dict[str, Any]] = None,
        delegated_by: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> Optional[ActorPermission]:
        """
        Assigns a permission directly to an actor.

        Args:
            actor_id (str): Actor ID
            resource_id (str): Resource ID
            permission_id (str): Permission ID
            token (str): Authentication token
            conditions (Dict, optional): Permission conditions
            delegated_by (str, optional): Delegator user ID
            expires_at (str, optional): Expiration timestamp

        Returns:
            Optional[ActorPermission]: The created permission assignment or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation AssignPermissionToActor($input: AssignActorPermissionInput!) {  # noqa: E501
                    assignPermissionToActor(input: $input) {
                        id
                        actorId
                        resourceId
                        permissionId
                        actor {
                            id
                            type
                        }
                        resource {
                            id
                            identifier
                        }
                        permission {
                            id
                            name
                        }
                        delegatedBy
                        delegator {
                            id
                            name
                            email
                        }
                        conditions
                        expiresAt
                        createdAt
                    }
                }
            """
            )

            variables = {
                "input": {
                    "actorId": actor_id,
                    "resourceId": resource_id,
                    "permissionId": permission_id,
                    "conditions": conditions,
                    "delegatedBy": delegated_by,
                    "expiresAt": expires_at,
                }
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("assignPermissionToActor")
        except Exception as e:
            print(f"Assign permission to actor failed: {str(e)}")
            return None

    async def assign_role_to_actor(
        self,
        actor_id: str,
        role_id: str,
        token: str,
        delegated_by: Optional[str] = None,
        expires_at: Optional[str] = None,
    ) -> Optional[ActorRole]:
        """
        Assigns a role to an actor.

        Args:
            actor_id (str): Actor ID
            role_id (str): Role ID
            token (str): Authentication token
            delegated_by (str, optional): Delegator user ID
            expires_at (str, optional): Expiration timestamp

        Returns:
            Optional[ActorRole]: The created role assignment or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation AssignRoleToActor($input: AssignActorRoleInput!) {
                    assignRoleToActor(input: $input) {
                        id
                        actorId
                        roleId
                        actor {
                            id
                            type
                        }
                        role {
                            id
                            name
                            description
                        }
                        delegatedBy
                        delegator {
                            id
                            name
                            email
                        }
                        expiresAt
                        createdAt
                    }
                }
            """
            )

            variables = {
                "input": {
                    "actorId": actor_id,
                    "roleId": role_id,
                    "delegatedBy": delegated_by,
                    "expiresAt": expires_at,
                }
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("assignRoleToActor")
        except Exception as e:
            print(f"Assign role to actor failed: {str(e)}")
            return None

    # Agent Permission Delegation
    async def delegate_permission_to_agent(
        self,
        agent_id: str,
        resource_id: str,
        permission_id: str,
        delegator_id: str,
        token: str,
        expires_at: Optional[str] = None,
    ) -> Optional[ActorPermission]:
        """
        Delegates a permission to an agent on behalf of a user.

        Args:
            agent_id (str): Agent ID
            resource_id (str): Resource ID
            permission_id (str): Permission ID
            delegator_id (str): User ID who is delegating
            token (str): Authentication token
            expires_at (str, optional): Expiration timestamp

        Returns:
            Optional[ActorPermission]: The delegated permission or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DelegatePermissionToAgent(
                    $agentId: String!
                    $resourceId: String!
                    $permissionId: String!
                    $delegatorId: String!
                    $expiresAt: DateTime
                ) {
                    delegatePermissionToAgent(
                        agentId: $agentId
                        resourceId: $resourceId
                        permissionId: $permissionId
                        delegatorId: $delegatorId
                        expiresAt: $expiresAt
                    ) {
                        id
                        actorId
                        resourceId
                        permissionId
                        delegatedBy
                        delegator {
                            id
                            name
                            email
                        }
                        expiresAt
                        createdAt
                    }
                }
            """
            )

            variables = {
                "agentId": agent_id,
                "resourceId": resource_id,
                "permissionId": permission_id,
                "delegatorId": delegator_id,
                "expiresAt": expires_at,
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("delegatePermissionToAgent")
        except Exception as e:
            print(f"Delegate permission to agent failed: {str(e)}")
            return None

    async def get_actor_permissions(
        self, actor_id: str, token: str
    ) -> List[ActorPermission]:
        """
        Retrieves all permissions for a specific actor.

        Args:
            actor_id (str): Actor ID
            token (str): Authentication token

        Returns:
            List[ActorPermission]: List of actor permissions
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetActorPermissions($actorId: String!) {
                    getActorPermissions(actorId: $actorId) {
                        id
                        actorId
                        resourceId
                        permissionId
                        actor {
                            id
                            type
                        }
                        resource {
                            id
                            identifier
                            name
                        }
                        permission {
                            id
                            name
                            description
                        }
                        delegatedBy
                        delegator {
                            id
                            name
                            email
                        }
                        conditions
                        expiresAt
                        createdAt
                    }
                }
            """
            )

            variables = {"actorId": actor_id}

            result = client.execute(query, variable_values=variables)
            return result.get("getActorPermissions", [])
        except Exception as e:
            print(f"Get actor permissions failed: {str(e)}")
            return []

    async def get_actor_roles(self, actor_id: str, token: str) -> List[ActorRole]:
        """
        Retrieves all roles for a specific actor.

        Args:
            actor_id (str): Actor ID
            token (str): Authentication token

        Returns:
            List[ActorRole]: List of actor roles
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetActorRoles($actorId: String!) {
                    getActorRoles(actorId: $actorId) {
                        id
                        actorId
                        roleId
                        actor {
                            id
                            type
                        }
                        role {
                            id
                            name
                            description
                        }
                        delegatedBy
                        delegator {
                            id
                            name
                            email
                        }
                        expiresAt
                        createdAt
                    }
                }
            """
            )

            variables = {"actorId": actor_id}

            result = client.execute(query, variable_values=variables)
            return result.get("getActorRoles", [])
        except Exception as e:
            print(f"Get actor roles failed: {str(e)}")
            return []

    # Enhanced Resource Visibility with Agent Support
    async def create_resource_visibility_enhanced(
        self,
        resource_id: str,
        visibility_type: str,
        token: str,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None,
        allowed_user_ids: Optional[List[str]] = None,
        allowed_team_ids: Optional[List[str]] = None,
        allowed_role_ids: Optional[List[str]] = None,
        allowed_agent_ids: Optional[List[str]] = None,
    ) -> Optional[ResourceVisibility]:
        """
        Sets enhanced visibility rules for a resource including agent support.

        Args:
            resource_id (str): Resource ID
            visibility_type (str): Type of visibility
            token (str): Authentication token
            scope_type (str, optional): Scope type
            scope_id (str, optional): Scope ID
            allowed_user_ids (List[str], optional): List of allowed user IDs
            allowed_team_ids (List[str], optional): List of allowed team IDs
            allowed_role_ids (List[str], optional): List of allowed role IDs
            allowed_agent_ids (List[str], optional): List of allowed agent IDs

        Returns:
            Optional[ResourceVisibility]: Created visibility settings or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateResourceVisibilityEnhanced($input: CreateResourceVisibilityInputEnhanced!) {  # noqa: E501
                    createResourceVisibilityEnhanced(input: $input) {
                        id
                        resourceId
                        visibilityType
                        scopeType
                        scopeId
                        allowedUserIds
                        allowedTeamIds
                        allowedRoleIds
                        allowedAgentIds
                        createdAt
                        createdBy {
                            id
                            email
                        }
                    }
                }
            """
            )

            variables = {
                "input": {
                    "resourceId": resource_id,
                    "visibilityType": visibility_type,
                    "scopeType": scope_type,
                    "scopeId": scope_id,
                    "allowedUserIds": allowed_user_ids or [],
                    "allowedTeamIds": allowed_team_ids or [],
                    "allowedRoleIds": allowed_role_ids or [],
                    "allowedAgentIds": allowed_agent_ids or [],
                }
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("createResourceVisibilityEnhanced")
        except Exception as e:
            print(f"Create enhanced resource visibility failed: {str(e)}")
            return None

    # Additional missing RBAC operations
    async def delete_actor(self, actor_id: str, token: str) -> bool:
        """Delete an actor from the RBAC system."""
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DeleteActor($id: ID!) {
                    deleteActor(id: $id)
                }
            """
            )

            variables = {"id": actor_id}
            result = client.execute(mutation, variable_values=variables)
            return result.get("deleteActor", False)
        except Exception as e:
            print(f"Delete actor failed: {str(e)}")
            return False

    async def delete_agent(self, agent_id: str, token: str) -> bool:
        """Delete an agent from the RBAC system."""
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DeleteAgent($id: ID!) {
                    deleteAgent(id: $id)
                }
            """
            )

            variables = {"id": agent_id}
            result = client.execute(mutation, variable_values=variables)
            return result.get("deleteAgent", False)
        except Exception as e:
            print(f"Delete agent failed: {str(e)}")
            return False

    async def remove_permission_from_actor(
        self, actor_id: str, resource_id: str, permission_id: str, token: str
    ) -> bool:
        """Remove a permission from an actor."""
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation RemovePermissionFromActor($actorId: String!, $resourceId: String!, $permissionId: String!) {  # noqa: E501
                    removePermissionFromActor(actorId: $actorId, resourceId: $resourceId, permissionId: $permissionId)
                }
            """
            )

            variables = {
                "actorId": actor_id,
                "resourceId": resource_id,
                "permissionId": permission_id,
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("removePermissionFromActor", False)
        except Exception as e:
            print(f"Remove permission from actor failed: {str(e)}")
            return False

    async def remove_role_from_actor(
        self, actor_id: str, role_id: str, token: str
    ) -> bool:
        """Remove a role from an actor."""
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation RemoveRoleFromActor($actorId: String!, $roleId: String!) {  # noqa: E501
                    removeRoleFromActor(actorId: $actorId, roleId: $roleId)
                }
            """
            )

            variables = {"actorId": actor_id, "roleId": role_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("removeRoleFromActor", False)
        except Exception as e:
            print(f"Remove role from actor failed: {str(e)}")
            return False

    async def delegate_role_to_agent(
        self,
        agent_id: str,
        role_id: str,
        delegator_id: str,
        token: str,
        expires_at: Optional[str] = None,
    ) -> Optional[ActorRole]:
        """Delegate a role to an agent on behalf of a user."""
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DelegateRoleToAgent(
                    $agentId: String!
                    $roleId: String!
                    $delegatorId: String!
                    $expiresAt: DateTime
                ) {
                    delegateRoleToAgent(
                        agentId: $agentId
                        roleId: $roleId
                        delegatorId: $delegatorId
                        expiresAt: $expiresAt
                    ) {
                        id
                        actorId
                        roleId
                        delegatedBy
                        delegator {
                            id
                            name
                            email
                        }
                        expiresAt
                        createdAt
                    }
                }
            """
            )

            variables = {
                "agentId": agent_id,
                "roleId": role_id,
                "delegatorId": delegator_id,
                "expiresAt": expires_at,
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("delegateRoleToAgent")
        except Exception as e:
            print(f"Delegate role to agent failed: {str(e)}")
            return None

    async def check_scoped_create_permission(
        self,
        actor_id: str,
        scope_resource_id: str,
        scope_resource_type: str,
        target_resource_type: str,
        token: str,
        workspace_id: Optional[str] = None,
    ) -> bool:
        """Check if an actor has scoped create permission."""
        try:
            client = self.get_client(token)
            query = gql(
                """
                query CheckScopedCreatePermission(
                    $actorId: String!
                    $scopeResourceId: String!
                    $scopeResourceType: String!
                    $targetResourceType: String!
                    $workspaceId: String
                ) {
                    checkScopedCreatePermission(
                        actorId: $actorId
                        scopeResourceId: $scopeResourceId
                        scopeResourceType: $scopeResourceType
                        targetResourceType: $targetResourceType
                        workspaceId: $workspaceId
                    )
                }
            """
            )

            variables = {
                "actorId": actor_id,
                "scopeResourceId": scope_resource_id,
                "scopeResourceType": scope_resource_type,
                "targetResourceType": target_resource_type,
                "workspaceId": workspace_id,
            }

            result = client.execute(query, variable_values=variables)
            return result.get("checkScopedCreatePermission", False)
        except Exception as e:
            print(f"Check scoped create permission failed: {str(e)}")
            return False

    async def get_delegated_permissions(
        self, agent_id: str, token: str
    ) -> List[ActorPermission]:
        """Get permissions delegated to an agent."""
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetDelegatedPermissions($agentId: String!) {
                    getDelegatedPermissions(agentId: $agentId) {
                        id
                        actorId
                        resourceId
                        permissionId
                        actor {
                            id
                            type
                        }
                        resource {
                            id
                            identifier
                            name
                        }
                        permission {
                            id
                            name
                            description
                        }
                        delegatedBy
                        delegator {
                            id
                            name
                            email
                        }
                        conditions
                        expiresAt
                        createdAt
                    }
                }
            """
            )

            variables = {"agentId": agent_id}

            result = client.execute(query, variable_values=variables)
            return result.get("getDelegatedPermissions", [])
        except Exception as e:
            print(f"Get delegated permissions failed: {str(e)}")
            return []

    # ============================================================================
    # UNIFIED TRACKING OPERATION
    # ============================================================================

    async def track_operation(
        self,
        operation_name: str,
        token: str,
        rbac_check: Optional[Dict[str, Any]] = None,
        activity_options: Optional[Dict[str, Any]] = None,
        usage_options: Optional[Dict[str, Any]] = None,
        notification_options: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        product_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Track an operation with unified RBAC, activity, usage, and notification tracking.  # noqa: E501

        Args:
            operation_name (str): Name of the operation (e.g., 'createProject', 'updateTeam')  # noqa: E501
            token (str): Authentication token
            rbac_check (dict, optional): RBAC validation options
                - action (str): Permission action
                - resourceType (str): Resource type
                - resourceId (str): Resource ID
                - workspaceId (str): Workspace ID
                - skipRbacCheck (bool): Skip RBAC validation
            activity_options (dict, optional): Activity tracking options
                - enabled (bool): Enable activity tracking (default: True)
                - activityType (str): Activity type
                - description (str): Activity description
                - metadata (dict): Additional metadata
                - workspaceId (str): Workspace context
                - teamId (str): Team context
                - projectId (str): Project context
                - targetUserId (str): Target user ID
                - resourceType (str): Resource type
                - resourceId (str): Resource ID
            usage_options (dict, optional): Usage tracking options
                - enabled (bool): Enable usage tracking
                - billingAccountId (str): Billing account ID (required for usage tracking)  # noqa: E501
                - addUsage (bool): Add usage (True) or free up usage (False)
                - description (str): Usage description
                - tags (dict): Usage tags
                - quotaName (str): Quota name override
                - value (float): Usage value override
            notification_options (dict, optional): Notification options
                - enabled (bool): Enable notifications
                - title (str): Notification title (required)
                - message (str): Notification message (required)
                - type (str): Notification type (info, success, warning, error)
                - redirectUrl (str): Redirect URL
                - appName (str): App name
                - email (bool): Send email notification
                - sms (bool): Send SMS notification
                - userIds (list): Target user IDs (required)
            success (bool): Operation success status (default: True)
            error_message (str, optional): Error message if operation failed
            product_id (str, optional): Product ID (default: 'workspace')

        Returns:
            dict: Tracking result with status for each component
                - success (bool): Overall success
                - rbacSuccess (bool): RBAC validation result
                - activitySuccess (bool): Activity logging result
                - usageSuccess (bool): Usage tracking result
                - notificationSuccess (bool): Notification result
                - message (str): Result message

        Example:
            >>> result = await rbac_client.track_operation(
            ...     operation_name='createProject',
            ...     token='your-token',
            ...     rbac_check={'workspaceId': 'workspace-123'},
            ...     activity_options={
            ...         'description': 'Created project "My Project"',
            ...         'metadata': {'projectName': 'My Project'},
            ...         'workspaceId': 'workspace-123'
            ...     }
            ... )
            >>> print(result['success'])  # True if all tracking succeeded
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation TrackOperation($input: TrackOperationInput!) {
                    trackOperation(input: $input) {
                        success
                        rbacSuccess
                        activitySuccess
                        usageSuccess
                        notificationSuccess
                        message
                    }
                }
            """
            )

            # Build input
            input_data = {"operationName": operation_name, "success": success}

            if rbac_check:
                input_data["rbacCheck"] = rbac_check

            if activity_options:
                input_data["activityOptions"] = activity_options

            if usage_options:
                input_data["usageOptions"] = usage_options

            if notification_options:
                input_data["notificationOptions"] = notification_options

            if error_message:
                input_data["errorMessage"] = error_message

            if product_id:
                input_data["productId"] = product_id

            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get(
                "trackOperation",
                {
                    "success": False,
                    "rbacSuccess": False,
                    "activitySuccess": False,
                    "usageSuccess": False,
                    "notificationSuccess": False,
                    "message": "No response from server",
                },
            )
        except Exception as e:
            print(f"Track operation failed: {str(e)}")
            return {
                "success": False,
                "rbacSuccess": False,
                "activitySuccess": False,
                "usageSuccess": False,
                "notificationSuccess": False,
                "message": str(e),
            }


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default RBAC client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = RBACClient(graphql_endpoint)


def get_client() -> RBACClient:
    """Get the default RBAC client."""
    if _default_client is None:
        raise RuntimeError("RBAC client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def create_resource(*args, **kwargs):
    return await get_client().create_resource(*args, **kwargs)


async def update_resource(*args, **kwargs):
    return await get_client().update_resource(*args, **kwargs)


async def bulk_create_resources(*args, **kwargs):
    return await get_client().bulk_create_resources(*args, **kwargs)


async def get_accessible_resources(*args, **kwargs):
    return await get_client().get_accessible_resources(*args, **kwargs)


async def get_resource_permissions(*args, **kwargs):
    return await get_client().get_resource_permissions(*args, **kwargs)


async def remove_resource_visibility(*args, **kwargs):
    return await get_client().remove_resource_visibility(*args, **kwargs)


async def get_resource_visibility(*args, **kwargs):
    return await get_client().get_resource_visibility(*args, **kwargs)


# Actor and Agent convenience functions
async def create_actor(*args, **kwargs):
    return await get_client().create_actor(*args, **kwargs)


async def get_actors(*args, **kwargs):
    return await get_client().get_actors(*args, **kwargs)


async def get_actor(*args, **kwargs):
    return await get_client().get_actor(*args, **kwargs)


async def create_agent(*args, **kwargs):
    return await get_client().create_agent(*args, **kwargs)


async def get_agents(*args, **kwargs):
    return await get_client().get_agents(*args, **kwargs)


async def get_agent(*args, **kwargs):
    return await get_client().get_agent(*args, **kwargs)


async def check_actor_permission(*args, **kwargs):
    return await get_client().check_actor_permission(*args, **kwargs)


async def check_multiple_actor_permissions(*args, **kwargs):
    return await get_client().check_multiple_actor_permissions(*args, **kwargs)


async def assign_permission_to_actor(*args, **kwargs):
    return await get_client().assign_permission_to_actor(*args, **kwargs)


async def assign_role_to_actor(*args, **kwargs):
    return await get_client().assign_role_to_actor(*args, **kwargs)


async def delegate_permission_to_agent(*args, **kwargs):
    return await get_client().delegate_permission_to_agent(*args, **kwargs)


async def get_actor_permissions(*args, **kwargs):
    return await get_client().get_actor_permissions(*args, **kwargs)


async def get_actor_roles(*args, **kwargs):
    return await get_client().get_actor_roles(*args, **kwargs)


async def create_resource_visibility_enhanced(*args, **kwargs):
    return await get_client().create_resource_visibility_enhanced(*args, **kwargs)


async def update_resource_visibility_enhanced(*args, **kwargs):
    return await get_client().update_resource_visibility_enhanced(*args, **kwargs)


# Additional convenience functions for missing operations
async def delete_actor(*args, **kwargs):
    return await get_client().delete_actor(*args, **kwargs)


async def delete_agent(*args, **kwargs):
    return await get_client().delete_agent(*args, **kwargs)


async def remove_permission_from_actor(*args, **kwargs):
    return await get_client().remove_permission_from_actor(*args, **kwargs)


async def remove_role_from_actor(*args, **kwargs):
    return await get_client().remove_role_from_actor(*args, **kwargs)


async def delegate_role_to_agent(*args, **kwargs):
    return await get_client().delegate_role_to_agent(*args, **kwargs)


async def check_scoped_create_permission(*args, **kwargs):
    return await get_client().check_scoped_create_permission(*args, **kwargs)


async def get_delegated_permissions(*args, **kwargs):
    return await get_client().get_delegated_permissions(*args, **kwargs)


async def track_operation(*args, **kwargs):
    """
    Track an operation with unified RBAC, activity, usage, and notification tracking.  # noqa: E501

    Convenience function that uses the default RBAC client.

    See RBACClient.track_operation() for detailed documentation.
    """
    return await get_client().track_operation(*args, **kwargs)
