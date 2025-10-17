"""
Team Management Module

This module provides comprehensive team management functionality including:
- Creating, updating, and deleting teams
- Managing team members
- Team role assignments
- Retrieving teams by workspace
"""

from typing import Any, Dict, List, Optional

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


class TeamClient:
    """
    Client for managing teams and team members.
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Team client.

        Args:
            graphql_endpoint (str): The GraphQL endpoint URL
        """
        self.graphql_endpoint = graphql_endpoint

    def get_client(self, token: str) -> Client:
        """
        Create a GraphQL client with authentication.

        Args:
            token (str): Authentication token

        Returns:
            Client: Configured GraphQL client
        """
        headers = get_default_headers(token)
        transport = RequestsHTTPTransport(url=self.graphql_endpoint, headers=headers)
        return Client(transport=transport, fetch_schema_from_transport=True)

    async def create_team(
        self, name: str, workspace_id: str, token: str
    ) -> Dict[str, Any]:
        """
        Create a new team in a workspace.

        Args:
            name (str): Team name
            workspace_id (str): Workspace ID
            token (str): Authentication token

        Returns:
            dict: Created team information

        Example:
            >>> team = await client.create_team("Dev Team", "workspace-123", token)  # noqa: E501
            >>> print(team['id'])
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateTeam($name: String!, $workspaceID: ID!) {
                    createTeam(name: $name, workspaceID: $workspaceID) {
                        id
                        name
                        status
                        workspaceID
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"name": name, "workspaceID": workspace_id}
            result = client.execute(mutation, variable_values=variables)
            return result.get("createTeam")
        except Exception as e:
            print(f"Create team failed: {str(e)}")
            raise

    async def get_team(self, team_id: str, token: str) -> Optional[Dict[str, Any]]:
        """
        Get team details by ID.

        Args:
            team_id (str): Team ID
            token (str): Authentication token

        Returns:
            dict: Team information including members, or None if not found

        Example:
            >>> team = await client.get_team("team-123", token)
            >>> print(team['name'])
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetTeam($id: ID!) {
                    getTeam(id: $id) {
                        id
                        name
                        status
                        workspaceID
                        createdAt
                        updatedAt
                        users {
                            id
                            email
                            name
                        }
                    }
                }
            """
            )

            variables = {"id": team_id}
            result = client.execute(query, variable_values=variables)
            return result.get("getTeam")
        except Exception as e:
            print(f"Get team failed: {str(e)}")
            return None

    async def get_teams_by_workspace(
        self,
        workspace_id: str,
        token: str,
        items_per_page: Optional[int] = None,
        page: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all teams in a workspace with pagination and search.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            items_per_page (int, optional): Number of items per page
            page (int, optional): Page number
            search (str, optional): Search query

        Returns:
            dict: Response containing count and teams list

        Example:
            >>> result = await client.get_teams_by_workspace(
            ...     "workspace-123",
            ...     token,
            ...     items_per_page=10,
            ...     page=1
            ... )
            >>> print(f"Found {result['count']} teams")
            >>> for team in result['teams']:
            ...     print(team['name'])
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetTeamsByWorkspace(
                    $workspaceID: ID!
                    $itemsPerPage: Int
                    $page: Int
                    $search: String
                ) {
                    getTeamByWorkspaceID(
                        workspaceID: $workspaceID
                        itemsPerPage: $itemsPerPage
                        page: $page
                        search: $search
                    ) {
                        count
                        teams {
                            id
                            name
                            status
                            workspaceID
                            createdAt
                            updatedAt
                        }
                    }
                }
            """
            )

            variables = {"workspaceID": workspace_id}
            if items_per_page is not None:
                variables["itemsPerPage"] = items_per_page
            if page is not None:
                variables["page"] = page
            if search is not None:
                variables["search"] = search

            result = client.execute(query, variable_values=variables)
            return result.get("getTeamByWorkspaceID", {"count": 0, "teams": []})
        except Exception as e:
            print(f"Get teams by workspace failed: {str(e)}")
            return {"count": 0, "teams": []}

    async def get_team_members(
        self,
        team_id: str,
        token: str,
        items_per_page: Optional[int] = None,
        page: Optional[int] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get all members of a team with pagination and search.

        Args:
            team_id (str): Team ID
            token (str): Authentication token
            items_per_page (int, optional): Number of items per page
            page (int, optional): Page number
            search (str, optional): Search query

        Returns:
            dict: Response containing count and users list

        Example:
            >>> result = await client.get_team_members(
            ...     "team-123",
            ...     token,
            ...     items_per_page=10,
            ...     page=1
            ... )
            >>> print(f"Team has {result['count']} members")
            >>> for user in result['users']:
            ...     print(user['email'])
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetTeamMembers(
                    $teamID: ID!
                    $itemsPerPage: Int
                    $page: Int
                    $search: String
                ) {
                    getTeamMembers(
                        teamID: $teamID
                        itemsPerPage: $itemsPerPage
                        page: $page
                        search: $search
                    ) {
                        count
                        users {
                            id
                            email
                            name
                            status
                            createdAt
                            updatedAt
                        }
                    }
                }
            """
            )

            variables = {"teamID": team_id}
            if items_per_page is not None:
                variables["itemsPerPage"] = items_per_page
            if page is not None:
                variables["page"] = page
            if search is not None:
                variables["search"] = search

            result = client.execute(query, variable_values=variables)
            return result.get("getTeamMembers", {"count": 0, "users": []})
        except Exception as e:
            print(f"Get team members failed: {str(e)}")
            return {"count": 0, "users": []}

    async def update_team(
        self,
        team_id: str,
        token: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update team information.

        Args:
            team_id (str): Team ID
            token (str): Authentication token
            name (str, optional): New team name
            status (str, optional): New team status
            workspace_id (str, optional): New workspace ID

        Returns:
            dict: Updated team information

        Example:
            >>> team = await client.update_team(
            ...     "team-123",
            ...     token,
            ...     name="Updated Team Name"
            ... )
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateTeam($id: ID!, $input: UpdateTeamInput!) {
                    updateTeam(id: $id, input: $input) {
                        id
                        name
                        status
                        workspaceID
                        updatedAt
                    }
                }
            """
            )

            input_data = {}
            if name is not None:
                input_data["name"] = name
            if status is not None:
                input_data["status"] = status
            if workspace_id is not None:
                input_data["workspaceID"] = workspace_id

            variables = {"id": team_id, "input": input_data}
            result = client.execute(mutation, variable_values=variables)
            return result.get("updateTeam")
        except Exception as e:
            print(f"Update team failed: {str(e)}")
            raise

    async def archive_team(self, team_id: str, token: str) -> Dict[str, Any]:
        """
        Archive a team.

        Args:
            team_id (str): Team ID
            token (str): Authentication token

        Returns:
            dict: Archived team information
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ArchiveTeam($id: ID!) {
                    archiveTeam(id: $id) {
                        id
                        name
                        status
                        updatedAt
                    }
                }
            """
            )

            variables = {"id": team_id}
            result = client.execute(mutation, variable_values=variables)
            return result.get("archiveTeam")
        except Exception as e:
            print(f"Archive team failed: {str(e)}")
            raise

    async def reactivate_team(self, team_id: str, token: str) -> Dict[str, Any]:
        """
        Reactivate an archived team.

        Args:
            team_id (str): Team ID
            token (str): Authentication token

        Returns:
            dict: Reactivated team information
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ReactivateTeam($id: ID!) {
                    reactivateTeam(id: $id) {
                        id
                        name
                        status
                        updatedAt
                    }
                }
            """
            )

            variables = {"id": team_id}
            result = client.execute(mutation, variable_values=variables)
            return result.get("reactivateTeam")
        except Exception as e:
            print(f"Reactivate team failed: {str(e)}")
            raise

    async def delete_team(self, team_id: str, token: str) -> Dict[str, Any]:
        """
        Delete a team permanently.

        Args:
            team_id (str): Team ID
            token (str): Authentication token

        Returns:
            dict: Deleted team information
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DeleteTeam($id: ID!) {
                    deleteTeam(id: $id) {
                        id
                        name
                        status
                    }
                }
            """
            )

            variables = {"id": team_id}
            result = client.execute(mutation, variable_values=variables)
            return result.get("deleteTeam")
        except Exception as e:
            print(f"Delete team failed: {str(e)}")
            raise

    async def add_user_to_team(
        self, team_id: str, user_email: str, token: str
    ) -> Dict[str, Any]:
        """
        Add a user to a team.

        Args:
            team_id (str): Team ID
            user_email (str): User email
            token (str): Authentication token

        Returns:
            dict: Updated team information with users

        Example:
            >>> team = await client.add_user_to_team(
            ...     "team-123",
            ...     "user@example.com",
            ...     token
            ... )
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation AddUserToTeam($teamID: ID!, $userEmail: String!) {
                    addUserToTeam(teamID: $teamID, userEmail: $userEmail) {
                        id
                        name
                        status
                        workspaceID
                        users {
                            id
                            email
                            name
                        }
                    }
                }
            """
            )

            variables = {"teamID": team_id, "userEmail": user_email}
            result = client.execute(mutation, variable_values=variables)
            return result.get("addUserToTeam")
        except Exception as e:
            print(f"Add user to team failed: {str(e)}")
            raise

    async def remove_user_from_team(
        self, team_id: str, user_id: str, token: str
    ) -> Dict[str, Any]:
        """
        Remove a user from a team.

        Args:
            team_id (str): Team ID
            user_id (str): User ID
            token (str): Authentication token

        Returns:
            dict: Updated team information with users

        Example:
            >>> team = await client.remove_user_from_team(
            ...     "team-123",
            ...     "user-456",
            ...     token
            ... )
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation RemoveUserFromTeam($teamID: ID!, $userID: ID!) {
                    removeUserFromTeam(teamID: $teamID, userID: $userID) {
                        id
                        name
                        status
                        workspaceID
                        users {
                            id
                            email
                            name
                        }
                    }
                }
            """
            )

            variables = {"teamID": team_id, "userID": user_id}
            result = client.execute(mutation, variable_values=variables)
            return result.get("removeUserFromTeam")
        except Exception as e:
            print(f"Remove user from team failed: {str(e)}")
            raise

    async def assign_role_to_team(
        self, team_id: str, role_id: str, token: str
    ) -> Dict[str, Any]:
        """
        Assign a role to a team.

        Args:
            team_id (str): Team ID
            role_id (str): Role ID
            token (str): Authentication token

        Returns:
            dict: Team role assignment information
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation AssignRoleToTeam($input: AssignTeamRoleInput!) {
                    assignRoleToTeam(input: $input) {
                        id
                        teamId
                        roleId
                        assignedAt
                    }
                }
            """
            )

            variables = {"input": {"teamId": team_id, "roleId": role_id}}
            result = client.execute(mutation, variable_values=variables)
            return result.get("assignRoleToTeam")
        except Exception as e:
            print(f"Assign role to team failed: {str(e)}")
            raise

    async def remove_role_from_team(
        self, team_id: str, role_id: str, token: str
    ) -> bool:
        """
        Remove a role from a team.

        Args:
            team_id (str): Team ID
            role_id (str): Role ID
            token (str): Authentication token

        Returns:
            bool: True if successful
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation RemoveRoleFromTeam($roleId: String!, $teamId: String!) {  # noqa: E501
                    removeRoleFromTeam(roleId: $roleId, teamId: $teamId)
                }
            """
            )

            variables = {"roleId": role_id, "teamId": team_id}
            result = client.execute(mutation, variable_values=variables)
            return result.get("removeRoleFromTeam", False)
        except Exception as e:
            print(f"Remove role from team failed: {str(e)}")
            return False

    async def get_team_roles(self, team_id: str, token: str) -> List[Dict[str, Any]]:
        """
        Get all roles assigned to a team.

        Args:
            team_id (str): Team ID
            token (str): Authentication token

        Returns:
            list: List of team role assignments
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetTeamRoles($teamId: String!) {
                    getTeamRoles(teamId: $teamId) {
                        id
                        teamId
                        roleId
                        assignedAt
                        role {
                            id
                            name
                            description
                        }
                    }
                }
            """
            )

            variables = {"teamId": team_id}
            result = client.execute(query, variable_values=variables)
            return result.get("getTeamRoles", [])
        except Exception as e:
            print(f"Get team roles failed: {str(e)}")
            return []


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Team client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = TeamClient(graphql_endpoint)


def get_client() -> TeamClient:
    """Get the default Team client."""
    if _default_client is None:
        raise RuntimeError("Team client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def create_team(*args, **kwargs):
    """Create a new team. See TeamClient.create_team() for details."""
    return await get_client().create_team(*args, **kwargs)


async def get_team(*args, **kwargs):
    """Get team details. See TeamClient.get_team() for details."""
    return await get_client().get_team(*args, **kwargs)


async def get_teams_by_workspace(*args, **kwargs):
    """Get teams by workspace. See TeamClient.get_teams_by_workspace() for details."""  # noqa: E501
    return await get_client().get_teams_by_workspace(*args, **kwargs)


async def get_team_members(*args, **kwargs):
    """Get team members. See TeamClient.get_team_members() for details."""
    return await get_client().get_team_members(*args, **kwargs)


async def update_team(*args, **kwargs):
    """Update team. See TeamClient.update_team() for details."""
    return await get_client().update_team(*args, **kwargs)


async def archive_team(*args, **kwargs):
    """Archive team. See TeamClient.archive_team() for details."""
    return await get_client().archive_team(*args, **kwargs)


async def reactivate_team(*args, **kwargs):
    """Reactivate team. See TeamClient.reactivate_team() for details."""
    return await get_client().reactivate_team(*args, **kwargs)


async def delete_team(*args, **kwargs):
    """Delete team. See TeamClient.delete_team() for details."""
    return await get_client().delete_team(*args, **kwargs)


async def add_user_to_team(*args, **kwargs):
    """Add user to team. See TeamClient.add_user_to_team() for details."""
    return await get_client().add_user_to_team(*args, **kwargs)


async def remove_user_from_team(*args, **kwargs):
    """Remove user from team. See TeamClient.remove_user_from_team() for details."""  # noqa: E501
    return await get_client().remove_user_from_team(*args, **kwargs)


async def assign_role_to_team(*args, **kwargs):
    """Assign role to team. See TeamClient.assign_role_to_team() for details."""  # noqa: E501
    return await get_client().assign_role_to_team(*args, **kwargs)


async def remove_role_from_team(*args, **kwargs):
    """Remove role from team. See TeamClient.remove_role_from_team() for details."""  # noqa: E501
    return await get_client().remove_role_from_team(*args, **kwargs)


async def get_team_roles(*args, **kwargs):
    """Get team roles. See TeamClient.get_team_roles() for details."""
    return await get_client().get_team_roles(*args, **kwargs)
