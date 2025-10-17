"""
Settings Client for Workspaces SDK.

Provides comprehensive configuration management for user preferences, workspace settings,  # noqa: E501
and system configurations with support for profiles, notifications, privacy controls,  # noqa: E501
and advanced configuration templates.
"""

from typing import Any, Dict, List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Settings system
class ProfileSettings(TypedDict):
    displayName: Optional[str]
    timezone: Optional[str]
    language: Optional[str]
    theme: Optional[str]
    avatarUrl: Optional[str]
    bio: Optional[str]
    website: Optional[str]
    location: Optional[str]


class NotificationSettings(TypedDict):
    email: bool
    push: bool
    desktop: bool
    frequency: str  # IMMEDIATE, HOURLY, DAILY, WEEKLY
    mentions: bool
    updates: bool
    marketing: bool
    security: bool


class PrivacySettings(TypedDict):
    profileVisibility: str  # PUBLIC, WORKSPACE, PRIVATE
    activityTracking: bool
    dataSharing: bool
    analytics: bool
    cookieConsent: bool
    searchEngineIndexing: bool


class IntegrationSettings(TypedDict):
    connectedServices: List[Dict[str, Any]]
    apiKeys: List[Dict[str, Any]]
    webhooks: List[Dict[str, Any]]
    oauthTokens: List[Dict[str, Any]]


class UserSettings(TypedDict):
    id: str
    userId: str
    workspaceId: Optional[str]
    profile: Optional[ProfileSettings]
    notifications: Optional[NotificationSettings]
    privacy: Optional[PrivacySettings]
    integrations: Optional[IntegrationSettings]
    customSettings: Optional[Dict[str, Any]]
    createdAt: str
    updatedAt: str


class GeneralSettings(TypedDict):
    name: str
    description: Optional[str]
    timezone: str
    workingHours: Dict[str, Any]
    logo: Optional[str]
    primaryColor: Optional[str]
    customDomain: Optional[str]
    defaultLanguage: str


class SecuritySettings(TypedDict):
    twoFactorRequired: bool
    passwordPolicy: Dict[str, Any]
    sessionTimeout: int  # in minutes
    ipWhitelist: List[str]
    ssoEnabled: bool
    ssoProvider: Optional[str]
    auditLogging: bool
    dataRetentionDays: int


class WorkspaceIntegrationSettings(TypedDict):
    allowedServices: List[str]
    webhookEndpoints: List[Dict[str, Any]]
    apiAccess: Dict[str, Any]
    externalConnections: List[Dict[str, Any]]


class BillingSettings(TypedDict):
    plan: str
    usage: Dict[str, Any]
    limits: Dict[str, Any]
    billingCycle: str  # MONTHLY, YEARLY
    paymentMethod: Optional[Dict[str, Any]]
    invoiceEmails: List[str]
    autoRenewal: bool


class WorkspaceSettings(TypedDict):
    id: str
    workspaceId: str
    general: Optional[GeneralSettings]
    security: Optional[SecuritySettings]
    integrations: Optional[WorkspaceIntegrationSettings]
    billing: Optional[BillingSettings]
    customSettings: Optional[Dict[str, Any]]
    createdAt: str
    updatedAt: str


class FeatureFlag(TypedDict):
    id: str
    name: str
    key: str
    enabled: bool
    description: Optional[str]
    configuration: Optional[Dict[str, Any]]
    rolloutPercentage: Optional[float]
    targetUsers: Optional[List[str]]
    targetWorkspaces: Optional[List[str]]
    startDate: Optional[str]
    endDate: Optional[str]
    createdAt: str
    updatedAt: str


class SettingsTemplate(TypedDict):
    id: str
    name: str
    description: Optional[str]
    category: str  # USER, WORKSPACE, FEATURE
    templateData: Dict[str, Any]
    isDefault: bool
    isPublic: bool
    tags: List[str]
    createdBy: str
    createdAt: str
    updatedAt: str


class PaginatedUserSettings(TypedDict):
    settings: List[UserSettings]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class PaginatedWorkspaceSettings(TypedDict):
    settings: List[WorkspaceSettings]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class PaginatedFeatureFlags(TypedDict):
    flags: List[FeatureFlag]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class PaginatedSettingsTemplates(TypedDict):
    templates: List[SettingsTemplate]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class SettingsAuditLog(TypedDict):
    id: str
    userId: str
    workspaceId: Optional[str]
    action: str  # CREATE, UPDATE, DELETE, VIEW
    category: str  # USER, WORKSPACE, FEATURE
    settingKey: str
    oldValue: Optional[Any]
    newValue: Optional[Any]
    metadata: Optional[Dict[str, Any]]
    timestamp: str


class SettingsMetrics(TypedDict):
    totalUsers: int
    activeUsers: int
    settingsCategories: List[Dict[str, Any]]
    mostChangedSettings: List[Dict[str, Any]]
    configurationHealth: float


# Input types
class UpdateUserSettingsInput(TypedDict):
    userId: str
    workspaceId: Optional[str]
    category: str  # profile, notifications, privacy, integrations
    settings: Dict[str, Any]


class UpdateWorkspaceSettingsInput(TypedDict):
    workspaceId: str
    section: str  # general, security, integrations, billing
    settings: Dict[str, Any]


class ConfigureFeatureFlagInput(TypedDict):
    workspaceId: str
    flagKey: str
    enabled: bool
    configuration: Optional[Dict[str, Any]]
    rolloutPercentage: Optional[float]
    targetUsers: Optional[List[str]]


class CreateSettingsTemplateInput(TypedDict):
    name: str
    description: Optional[str]
    category: str
    templateData: Dict[str, Any]
    isDefault: Optional[bool]
    isPublic: Optional[bool]
    tags: Optional[List[str]]


# Constants
SETTINGS_CATEGORIES = {
    "PROFILE": "PROFILE",
    "NOTIFICATIONS": "NOTIFICATIONS",
    "PRIVACY": "PRIVACY",
    "INTEGRATIONS": "INTEGRATIONS",
    "CUSTOM": "CUSTOM",
}

WORKSPACE_SECTIONS = {
    "GENERAL": "GENERAL",
    "SECURITY": "SECURITY",
    "INTEGRATIONS": "INTEGRATIONS",
    "BILLING": "BILLING",
    "CUSTOM": "CUSTOM",
}

NOTIFICATION_FREQUENCIES = {
    "IMMEDIATE": "IMMEDIATE",
    "HOURLY": "HOURLY",
    "DAILY": "DAILY",
    "WEEKLY": "WEEKLY",
    "NEVER": "NEVER",
}

PROFILE_VISIBILITY = {
    "PUBLIC": "PUBLIC",
    "WORKSPACE": "WORKSPACE",
    "PRIVATE": "PRIVATE",
}

THEMES = {"LIGHT": "LIGHT", "DARK": "DARK", "AUTO": "AUTO", "CUSTOM": "CUSTOM"}


class SettingsClient:
    """
    Client for managing settings and configuration in the Workspaces platform.

    Provides comprehensive settings management including:
    - User preferences and profile settings
    - Workspace configuration and policies
    - Feature flag management
    - Settings templates and defaults
    - Configuration audit and compliance
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Settings client with a GraphQL endpoint.

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

    # User Settings Operations
    async def get_user_settings(
        self,
        user_id: str,
        token: str,
        workspace_id: Optional[str] = None,
        category: Optional[str] = None,
    ) -> Optional[UserSettings]:
        """
        Get user settings with optional filtering by category.

        Args:
            user_id (str): User ID to get settings for
            token (str): Authentication token
            workspace_id (str, optional): Workspace context
            category (str, optional): Settings category to retrieve

        Returns:
            Optional[UserSettings]: User settings or None if not found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetUserSettings(
                    $userId: ID!
                    $workspaceId: ID
                    $category: String
                ) {
                    getUserSettings(
                        userId: $userId
                        workspaceId: $workspaceId
                        category: $category
                    ) {
                        id
                        userId
                        workspaceId
                        profile {
                            displayName
                            timezone
                            language
                            theme
                            avatarUrl
                            bio
                            website
                            location
                        }
                        notifications {
                            email
                            push
                            desktop
                            frequency
                            mentions
                            updates
                            marketing
                            security
                        }
                        privacy {
                            profileVisibility
                            activityTracking
                            dataSharing
                            analytics
                            cookieConsent
                            searchEngineIndexing
                        }
                        integrations {
                            connectedServices
                            apiKeys
                            webhooks
                            oauthTokens
                        }
                        customSettings
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"userId": user_id}
            if workspace_id:
                variables["workspaceId"] = workspace_id
            if category:
                variables["category"] = category

            result = client.execute(query, variable_values=variables)
            return result.get("getUserSettings")
        except Exception as e:
            print(f"Get user settings failed: {str(e)}")
            return None

    async def update_user_settings(
        self, input_data: UpdateUserSettingsInput, token: str
    ) -> Optional[UserSettings]:
        """
        Update user settings for a specific category.

        Args:
            input_data (UpdateUserSettingsInput): Settings update data
            token (str): Authentication token

        Returns:
            Optional[UserSettings]: Updated user settings or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateUserSettings($input: UpdateUserSettingsInput!) {
                    updateUserSettings(input: $input) {
                        id
                        userId
                        workspaceId
                        profile {
                            displayName
                            timezone
                            language
                            theme
                            avatarUrl
                            bio
                            website
                            location
                        }
                        notifications {
                            email
                            push
                            desktop
                            frequency
                            mentions
                            updates
                            marketing
                            security
                        }
                        privacy {
                            profileVisibility
                            activityTracking
                            dataSharing
                            analytics
                            cookieConsent
                            searchEngineIndexing
                        }
                        integrations {
                            connectedServices
                            apiKeys
                            webhooks
                            oauthTokens
                        }
                        customSettings
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("updateUserSettings")
        except Exception as e:
            print(f"Update user settings failed: {str(e)}")
            return None

    async def reset_user_settings(
        self,
        user_id: str,
        workspace_id: Optional[str],
        category: str,
        token: str,
    ) -> bool:
        """
        Reset user settings to default values for a category.

        Args:
            user_id (str): User ID
            workspace_id (str, optional): Workspace ID
            category (str): Settings category to reset
            token (str): Authentication token

        Returns:
            bool: True if reset succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ResetUserSettings(
                    $userId: ID!
                    $workspaceId: ID
                    $category: String!
                ) {
                    resetUserSettings(
                        userId: $userId
                        workspaceId: $workspaceId
                        category: $category
                    )
                }
            """
            )

            variables = {"userId": user_id, "category": category}
            if workspace_id:
                variables["workspaceId"] = workspace_id

            result = client.execute(mutation, variable_values=variables)
            return result.get("resetUserSettings", False)
        except Exception as e:
            print(f"Reset user settings failed: {str(e)}")
            return False

    # Workspace Settings Operations
    async def get_workspace_settings(
        self, workspace_id: str, token: str, section: Optional[str] = None
    ) -> Optional[WorkspaceSettings]:
        """
        Get workspace settings with optional filtering by section.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            section (str, optional): Settings section to retrieve

        Returns:
            Optional[WorkspaceSettings]: Workspace settings or None if not found  # noqa: E501
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetWorkspaceSettings(
                    $workspaceId: ID!
                    $section: String
                ) {
                    getWorkspaceSettings(
                        workspaceId: $workspaceId
                        section: $section
                    ) {
                        id
                        workspaceId
                        general {
                            name
                            description
                            timezone
                            workingHours
                            logo
                            primaryColor
                            customDomain
                            defaultLanguage
                        }
                        security {
                            twoFactorRequired
                            passwordPolicy
                            sessionTimeout
                            ipWhitelist
                            ssoEnabled
                            ssoProvider
                            auditLogging
                            dataRetentionDays
                        }
                        integrations {
                            allowedServices
                            webhookEndpoints
                            apiAccess
                            externalConnections
                        }
                        billing {
                            plan
                            usage
                            limits
                            billingCycle
                            paymentMethod
                            invoiceEmails
                            autoRenewal
                        }
                        customSettings
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            variables = {"workspaceId": workspace_id}
            if section:
                variables["section"] = section

            result = client.execute(query, variable_values=variables)
            return result.get("getWorkspaceSettings")
        except Exception as e:
            print(f"Get workspace settings failed: {str(e)}")
            return None

    async def update_workspace_settings(
        self, input_data: UpdateWorkspaceSettingsInput, token: str
    ) -> Optional[WorkspaceSettings]:
        """
        Update workspace settings for a specific section.

        Args:
            input_data (UpdateWorkspaceSettingsInput): Settings update data
            token (str): Authentication token

        Returns:
            Optional[WorkspaceSettings]: Updated workspace settings or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateWorkspaceSettings($input: UpdateWorkspaceSettingsInput!) {  # noqa: E501
                    updateWorkspaceSettings(input: $input) {
                        id
                        workspaceId
                        general {
                            name
                            description
                            timezone
                            workingHours
                            logo
                            primaryColor
                            customDomain
                            defaultLanguage
                        }
                        security {
                            twoFactorRequired
                            passwordPolicy
                            sessionTimeout
                            ipWhitelist
                            ssoEnabled
                            ssoProvider
                            auditLogging
                            dataRetentionDays
                        }
                        integrations {
                            allowedServices
                            webhookEndpoints
                            apiAccess
                            externalConnections
                        }
                        billing {
                            plan
                            usage
                            limits
                            billingCycle
                            paymentMethod
                            invoiceEmails
                            autoRenewal
                        }
                        customSettings
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("updateWorkspaceSettings")
        except Exception as e:
            print(f"Update workspace settings failed: {str(e)}")
            return None

    # Feature Flag Operations
    async def get_feature_flags(
        self,
        workspace_id: str,
        token: str,
        page: int = 1,
        page_size: int = 20,
        enabled_only: Optional[bool] = None,
    ) -> PaginatedFeatureFlags:
        """
        Get feature flags for a workspace with pagination.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 20)
            enabled_only (bool, optional): Filter by enabled status

        Returns:
            PaginatedFeatureFlags: Paginated feature flags
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetFeatureFlags(
                    $workspaceId: ID!
                    $page: Int
                    $pageSize: Int
                    $enabledOnly: Boolean
                ) {
                    getFeatureFlags(
                        workspaceId: $workspaceId
                        page: $page
                        pageSize: $pageSize
                        enabledOnly: $enabledOnly
                    ) {
                        flags {
                            id
                            name
                            key
                            enabled
                            description
                            configuration
                            rolloutPercentage
                            targetUsers
                            targetWorkspaces
                            startDate
                            endDate
                            createdAt
                            updatedAt
                        }
                        totalCount
                        page
                        pageSize
                        totalPages
                    }
                }
            """
            )

            variables = {
                "workspaceId": workspace_id,
                "page": page,
                "pageSize": page_size,
            }
            if enabled_only is not None:
                variables["enabledOnly"] = enabled_only

            result = client.execute(query, variable_values=variables)
            return result.get(
                "getFeatureFlags",
                {
                    "flags": [],
                    "totalCount": 0,
                    "page": 1,
                    "pageSize": 20,
                    "totalPages": 0,
                },
            )
        except Exception as e:
            print(f"Get feature flags failed: {str(e)}")
            return {
                "flags": [],
                "totalCount": 0,
                "page": 1,
                "pageSize": 20,
                "totalPages": 0,
            }

    async def configure_feature_flag(
        self, input_data: ConfigureFeatureFlagInput, token: str
    ) -> Optional[FeatureFlag]:
        """
        Configure a feature flag for a workspace.

        Args:
            input_data (ConfigureFeatureFlagInput): Feature flag configuration
            token (str): Authentication token

        Returns:
            Optional[FeatureFlag]: Updated feature flag or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ConfigureFeatureFlag($input: ConfigureFeatureFlagInput!) {  # noqa: E501
                    configureFeatureFlag(input: $input) {
                        id
                        name
                        key
                        enabled
                        description
                        configuration
                        rolloutPercentage
                        targetUsers
                        targetWorkspaces
                        startDate
                        endDate
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("configureFeatureFlag")
        except Exception as e:
            print(f"Configure feature flag failed: {str(e)}")
            return None

    async def check_feature_flag(
        self,
        workspace_id: str,
        flag_key: str,
        user_id: Optional[str],
        token: str,
    ) -> bool:
        """
        Check if a feature flag is enabled for a specific context.

        Args:
            workspace_id (str): Workspace ID
            flag_key (str): Feature flag key
            user_id (str, optional): User ID for user-specific flags
            token (str): Authentication token

        Returns:
            bool: True if feature is enabled, False otherwise
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query CheckFeatureFlag(
                    $workspaceId: ID!
                    $flagKey: String!
                    $userId: ID
                ) {
                    checkFeatureFlag(
                        workspaceId: $workspaceId
                        flagKey: $flagKey
                        userId: $userId
                    )
                }
            """
            )

            variables = {"workspaceId": workspace_id, "flagKey": flag_key}
            if user_id:
                variables["userId"] = user_id

            result = client.execute(query, variable_values=variables)
            return result.get("checkFeatureFlag", False)
        except Exception as e:
            print(f"Check feature flag failed: {str(e)}")
            return False

    # Settings Templates Operations
    async def create_settings_template(
        self, input_data: CreateSettingsTemplateInput, token: str
    ) -> Optional[SettingsTemplate]:
        """
        Create a reusable settings template.

        Args:
            input_data (CreateSettingsTemplateInput): Template data
            token (str): Authentication token

        Returns:
            Optional[SettingsTemplate]: Created template or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateSettingsTemplate($input: CreateSettingsTemplateInput!) {  # noqa: E501
                    createSettingsTemplate(input: $input) {
                        id
                        name
                        description
                        category
                        templateData
                        isDefault
                        isPublic
                        tags
                        createdBy
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("createSettingsTemplate")
        except Exception as e:
            print(f"Create settings template failed: {str(e)}")
            return None

    async def get_settings_templates(
        self,
        token: str,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        include_public: bool = True,
    ) -> PaginatedSettingsTemplates:
        """
        Get settings templates with pagination and filtering.

        Args:
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 20)
            category (str, optional): Filter by category
            include_public (bool): Include public templates (default: True)

        Returns:
            PaginatedSettingsTemplates: Paginated settings templates
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetSettingsTemplates(
                    $page: Int
                    $pageSize: Int
                    $category: String
                    $includePublic: Boolean
                ) {
                    getSettingsTemplates(
                        page: $page
                        pageSize: $pageSize
                        category: $category
                        includePublic: $includePublic
                    ) {
                        templates {
                            id
                            name
                            description
                            category
                            templateData
                            isDefault
                            isPublic
                            tags
                            createdBy
                            createdAt
                            updatedAt
                        }
                        totalCount
                        page
                        pageSize
                        totalPages
                    }
                }
            """
            )

            variables = {
                "page": page,
                "pageSize": page_size,
                "includePublic": include_public,
            }
            if category:
                variables["category"] = category

            result = client.execute(query, variable_values=variables)
            return result.get(
                "getSettingsTemplates",
                {
                    "templates": [],
                    "totalCount": 0,
                    "page": 1,
                    "pageSize": 20,
                    "totalPages": 0,
                },
            )
        except Exception as e:
            print(f"Get settings templates failed: {str(e)}")
            return {
                "templates": [],
                "totalCount": 0,
                "page": 1,
                "pageSize": 20,
                "totalPages": 0,
            }

    async def apply_settings_template(
        self,
        template_id: str,
        target_id: str,
        target_type: str,  # USER or WORKSPACE
        token: str,
    ) -> bool:
        """
        Apply a settings template to a user or workspace.

        Args:
            template_id (str): Template ID to apply
            target_id (str): Target user or workspace ID
            target_type (str): Target type (USER or WORKSPACE)
            token (str): Authentication token

        Returns:
            bool: True if template applied successfully, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation ApplySettingsTemplate(
                    $templateId: ID!
                    $targetId: ID!
                    $targetType: String!
                ) {
                    applySettingsTemplate(
                        templateId: $templateId
                        targetId: $targetId
                        targetType: $targetType
                    )
                }
            """
            )

            variables = {
                "templateId": template_id,
                "targetId": target_id,
                "targetType": target_type,
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("applySettingsTemplate", False)
        except Exception as e:
            print(f"Apply settings template failed: {str(e)}")
            return False

    # Analytics and Audit Operations
    async def get_settings_audit_log(
        self,
        workspace_id: str,
        token: str,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> List[SettingsAuditLog]:
        """
        Get settings audit log with filtering.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 20)
            user_id (str, optional): Filter by user
            action (str, optional): Filter by action
            from_date (str, optional): Filter from date (ISO format)
            to_date (str, optional): Filter to date (ISO format)

        Returns:
            List[SettingsAuditLog]: Settings audit log entries
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetSettingsAuditLog(
                    $workspaceId: ID!
                    $page: Int
                    $pageSize: Int
                    $userId: ID
                    $action: String
                    $fromDate: DateTime
                    $toDate: DateTime
                ) {
                    getSettingsAuditLog(
                        workspaceId: $workspaceId
                        page: $page
                        pageSize: $pageSize
                        userId: $userId
                        action: $action
                        fromDate: $fromDate
                        toDate: $toDate
                    ) {
                        id
                        userId
                        workspaceId
                        action
                        category
                        settingKey
                        oldValue
                        newValue
                        metadata
                        timestamp
                    }
                }
            """
            )

            variables = {
                "workspaceId": workspace_id,
                "page": page,
                "pageSize": page_size,
            }

            if user_id:
                variables["userId"] = user_id
            if action:
                variables["action"] = action
            if from_date:
                variables["fromDate"] = from_date
            if to_date:
                variables["toDate"] = to_date

            result = client.execute(query, variable_values=variables)
            return result.get("getSettingsAuditLog", [])
        except Exception as e:
            print(f"Get settings audit log failed: {str(e)}")
            return []

    async def get_settings_metrics(
        self,
        workspace_id: str,
        token: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Optional[SettingsMetrics]:
        """
        Get settings usage metrics and analytics.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            from_date (str, optional): Start date for metrics (ISO format)
            to_date (str, optional): End date for metrics (ISO format)

        Returns:
            Optional[SettingsMetrics]: Settings metrics or None if failed
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetSettingsMetrics(
                    $workspaceId: ID!
                    $fromDate: DateTime
                    $toDate: DateTime
                ) {
                    getSettingsMetrics(
                        workspaceId: $workspaceId
                        fromDate: $fromDate
                        toDate: $toDate
                    ) {
                        totalUsers
                        activeUsers
                        settingsCategories {
                            category
                            userCount
                            changeCount
                        }
                        mostChangedSettings {
                            settingKey
                            changeCount
                            category
                        }
                        configurationHealth
                    }
                }
            """
            )

            variables = {"workspaceId": workspace_id}
            if from_date:
                variables["fromDate"] = from_date
            if to_date:
                variables["toDate"] = to_date

            result = client.execute(query, variable_values=variables)
            return result.get("getSettingsMetrics")
        except Exception as e:
            print(f"Get settings metrics failed: {str(e)}")
            return None


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Settings client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = SettingsClient(graphql_endpoint)


def get_client() -> SettingsClient:
    """Get the default Settings client."""
    if _default_client is None:
        raise RuntimeError("Settings client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def get_user_settings(*args, **kwargs):
    return await get_client().get_user_settings(*args, **kwargs)


async def update_user_settings(*args, **kwargs):
    return await get_client().update_user_settings(*args, **kwargs)


async def reset_user_settings(*args, **kwargs):
    return await get_client().reset_user_settings(*args, **kwargs)


async def get_workspace_settings(*args, **kwargs):
    return await get_client().get_workspace_settings(*args, **kwargs)


async def update_workspace_settings(*args, **kwargs):
    return await get_client().update_workspace_settings(*args, **kwargs)


async def get_feature_flags(*args, **kwargs):
    return await get_client().get_feature_flags(*args, **kwargs)


async def configure_feature_flag(*args, **kwargs):
    return await get_client().configure_feature_flag(*args, **kwargs)


async def check_feature_flag(*args, **kwargs):
    return await get_client().check_feature_flag(*args, **kwargs)


async def create_settings_template(*args, **kwargs):
    return await get_client().create_settings_template(*args, **kwargs)


async def get_settings_templates(*args, **kwargs):
    return await get_client().get_settings_templates(*args, **kwargs)


async def apply_settings_template(*args, **kwargs):
    return await get_client().apply_settings_template(*args, **kwargs)


async def get_settings_audit_log(*args, **kwargs):
    return await get_client().get_settings_audit_log(*args, **kwargs)


async def get_settings_metrics(*args, **kwargs):
    return await get_client().get_settings_metrics(*args, **kwargs)
