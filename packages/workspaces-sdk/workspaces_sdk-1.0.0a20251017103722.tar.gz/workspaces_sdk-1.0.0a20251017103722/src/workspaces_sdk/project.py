"""
Project Client for Workspaces SDK.

Provides access to project management functionality including creating,
updating, archiving, and managing projects and project members.
"""

from typing import List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Project system
class CreateProjectInput(TypedDict):
    name: str


class EditProjectInput(TypedDict):
    id: str
    name: str


class RemoveProjectMemberInput(TypedDict):
    projectID: str
    userID: str
    id: str


class UpdateProjectMemberRoleInput(TypedDict):
    projectID: str
    userID: str
    role: str


class User(TypedDict):
    id: str
    name: Optional[str]
    email: str


class ProjectMember(TypedDict):
    id: str
    projectID: str
    userID: str
    project: Optional["Project"]
    user: Optional[User]
    createdAt: Optional[str]
    role: Optional[str]


class Project(TypedDict):
    id: str
    name: str
    workspaceID: str
    userID: str
    key: str
    createdAt: Optional[str]
    archived: bool
    projectMembers: Optional[List[ProjectMember]]


class WorkspaceProjects(TypedDict):
    workspaceID: str
    projects: List[Project]


class ProjectClient:
    """
    Client for managing projects in the Workspaces platform.

    Provides methods to create, update, retrieve, archive, and manage projects
    and their members with proper authentication and error handling.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Project client with a GraphQL endpoint.

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

    # Project Query Operations
    async def get_project(self, project_id: str, token: str) -> Optional[Project]:
        """
        Retrieves a specific project by ID.

        Args:
            project_id (str): Project ID
            token (str): Authentication token

        Returns:
            Optional[Project]: Project details or None if not found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetProject($id: ID!) {
                    getProject(id: $id) {
                        id
                        name
                        workspaceID
                        userID
                        key
                        createdAt
                        archived
                        projectMembers {
                            id
                            projectID
                            userID
                            user {
                                id
                                name
                                email
                            }
                            createdAt
                            role
                        }
                    }
                }
            """
            )

            variables = {"id": project_id}

            result = client.execute(query, variable_values=variables)
            return result.get("getProject")
        except Exception as e:
            print(f"Get project failed: {str(e)}")
            return None

    async def get_workspace_projects(
        self, workspace_ids: List[str], token: str
    ) -> List[WorkspaceProjects]:
        """
        Retrieves all projects for given workspace IDs.

        Args:
            workspace_ids (List[str]): List of workspace IDs
            token (str): Authentication token

        Returns:
            List[WorkspaceProjects]: List of workspace projects
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetWorkspaceProjects($workspaceIDs: [ID!]) {
                    getWorkspaceProjects(workspaceIDs: $workspaceIDs) {
                        workspaceID
                        projects {
                            id
                            name
                            workspaceID
                            userID
                            key
                            createdAt
                            archived
                            projectMembers {
                                id
                                projectID
                                userID
                                role
                                createdAt
                            }
                        }
                    }
                }
            """
            )

            variables = {"workspaceIDs": workspace_ids}

            result = client.execute(query, variable_values=variables)
            return result.get("getWorkspaceProjects", [])
        except Exception as e:
            print(f"Get workspace projects failed: {str(e)}")
            return []

    # Project Mutation Operations
    async def create_project(self, name: str, token: str) -> Optional[Project]:
        """
        Creates a new project.

        Args:
            name (str): Project name
            token (str): Authentication token

        Returns:
            Optional[Project]: The created project or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateProject($input: createProjectInput!) {
                    createProject(input: $input) {
                        id
                        name
                        workspaceID
                        userID
                        key
                        createdAt
                        archived
                    }
                }
            """
            )

            input_data = {"name": name}
            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get("createProject")
        except Exception as e:
            print(f"Create project failed: {str(e)}")
            return None

    async def edit_project(
        self, project_id: str, name: str, token: str
    ) -> Optional[Project]:
        """
        Edits an existing project.

        Args:
            project_id (str): Project ID
            name (str): New project name
            token (str): Authentication token

        Returns:
            Optional[Project]: The updated project or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation EditProject($input: editProjectInput!) {
                    editProject(input: $input) {
                        id
                        name
                        workspaceID
                        userID
                        key
                        createdAt
                        archived
                    }
                }
            """
            )

            input_data = {"id": project_id, "name": name}
            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get("editProject")
        except Exception as e:
            print(f"Edit project failed: {str(e)}")
            return None

    async def archive_project(self, project_id: str, token: str) -> Optional[Project]:
        """
        Archives a project.

        Args:
            project_id (str): Project ID
            token (str): Authentication token

        Returns:
            Optional[Project]: The archived project or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ArchiveProject($id: ID!) {
                    archiveProject(id: $id) {
                        id
                        name
                        workspaceID
                        userID
                        key
                        createdAt
                        archived
                    }
                }
            """
            )

            variables = {"id": project_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("archiveProject")
        except Exception as e:
            print(f"Archive project failed: {str(e)}")
            return None

    async def unarchive_project(self, project_id: str, token: str) -> Optional[Project]:
        """
        Unarchives a project.

        Args:
            project_id (str): Project ID
            token (str): Authentication token

        Returns:
            Optional[Project]: The unarchived project or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UnarchiveProject($id: ID!) {
                    unarchiveProject(id: $id) {
                        id
                        name
                        workspaceID
                        userID
                        key
                        createdAt
                        archived
                    }
                }
            """
            )

            variables = {"id": project_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("unarchiveProject")
        except Exception as e:
            print(f"Unarchive project failed: {str(e)}")
            return None

    async def switch_project(self, project_id: str, token: str) -> Optional[str]:
        """
        Switches to a different project.

        Args:
            project_id (str): Project ID to switch to
            token (str): Authentication token

        Returns:
            Optional[str]: New token or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation SwitchProject($projID: ID!) {
                    switchProject(projID: $projID)
                }
            """
            )

            variables = {"projID": project_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("switchProject")
        except Exception as e:
            print(f"Switch project failed: {str(e)}")
            return None

    # Project Member Operations
    async def remove_project_member(
        self, project_id: str, user_id: str, member_id: str, token: str
    ) -> bool:
        """
        Removes a member from a project.

        Args:
            project_id (str): Project ID
            user_id (str): User ID to remove
            member_id (str): Project member ID
            token (str): Authentication token

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation RemoveProjectMember($input: RemoveProjectMemberInput!) {  # noqa: E501
                    removeProjectMember(input: $input)
                }
            """
            )

            input_data = {
                "projectID": project_id,
                "userID": user_id,
                "id": member_id,
            }
            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get("removeProjectMember", False)
        except Exception as e:
            print(f"Remove project member failed: {str(e)}")
            return False

    async def update_project_member_role(
        self, project_id: str, user_id: str, role: str, token: str
    ) -> Optional[ProjectMember]:
        """
        Updates a project member's role.

        Args:
            project_id (str): Project ID
            user_id (str): User ID
            role (str): New role
            token (str): Authentication token

        Returns:
            Optional[ProjectMember]: The updated project member or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateProjectMemberRole($input: UpdateProjectMemberRoleInput!) {  # noqa: E501
                    updateProjectMemberRole(input: $input) {
                        id
                        projectID
                        userID
                        role
                        createdAt
                        user {
                            id
                            name
                            email
                        }
                    }
                }
            """
            )

            input_data = {
                "projectID": project_id,
                "userID": user_id,
                "role": role,
            }
            variables = {"input": input_data}

            result = client.execute(mutation, variable_values=variables)
            return result.get("updateProjectMemberRole")
        except Exception as e:
            print(f"Update project member role failed: {str(e)}")
            return None


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Project client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = ProjectClient(graphql_endpoint)


def get_client() -> ProjectClient:
    """Get the default Project client."""
    if _default_client is None:
        raise RuntimeError("Project client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def get_project(*args, **kwargs):
    return await get_client().get_project(*args, **kwargs)


async def get_workspace_projects(*args, **kwargs):
    return await get_client().get_workspace_projects(*args, **kwargs)


async def create_project(*args, **kwargs):
    return await get_client().create_project(*args, **kwargs)


async def edit_project(*args, **kwargs):
    return await get_client().edit_project(*args, **kwargs)


async def archive_project(*args, **kwargs):
    return await get_client().archive_project(*args, **kwargs)


async def unarchive_project(*args, **kwargs):
    return await get_client().unarchive_project(*args, **kwargs)


async def switch_project(*args, **kwargs):
    return await get_client().switch_project(*args, **kwargs)


async def remove_project_member(*args, **kwargs):
    return await get_client().remove_project_member(*args, **kwargs)


async def update_project_member_role(*args, **kwargs):
    return await get_client().update_project_member_role(*args, **kwargs)
