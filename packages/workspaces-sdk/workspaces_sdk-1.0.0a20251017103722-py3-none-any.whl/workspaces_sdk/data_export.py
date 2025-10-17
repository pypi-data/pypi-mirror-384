"""
Data Export Client for Workspaces SDK.

Provides comprehensive data export capabilities with support for multiple formats,  # noqa: E501
batch processing, scheduled exports, and real-time export status monitoring.
"""

from typing import Any, Dict, List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Data Export system
class ExportJob(TypedDict):
    id: str
    workspaceId: str
    exportType: str  # ExportType enum
    format: str  # ExportFormat enum
    status: str  # ExportStatus enum
    progress: Optional[float]
    recordsProcessed: Optional[int]
    totalRecords: Optional[int]
    downloadUrl: Optional[str]
    error: Optional[str]
    filters: Optional[Dict[str, Any]]
    includeDeleted: bool
    dateRange: Optional[Dict[str, str]]
    estimatedCompletion: Optional[str]
    fileSize: Optional[int]
    createdAt: str
    completedAt: Optional[str]
    expiresAt: Optional[str]


class ExportSchedule(TypedDict):
    id: str
    workspaceId: str
    exportType: str  # ExportType enum
    format: str  # ExportFormat enum
    schedule: Dict[str, Any]  # ScheduleConfig
    deliveryMethod: str  # DeliveryMethod enum
    deliveryConfig: Optional[Dict[str, Any]]
    filters: Optional[Dict[str, Any]]
    includeDeleted: bool
    lastRun: Optional[str]
    nextRun: Optional[str]
    status: str  # ScheduleStatus enum
    enabled: bool
    createdAt: str
    updatedAt: str


class BulkExportJob(TypedDict):
    id: str
    workspaceId: str
    exports: List[Dict[str, Any]]  # List of export configurations
    packageFormat: str  # PackageFormat enum
    status: str  # ExportStatus enum
    progress: Optional[float]
    downloadUrl: Optional[str]
    error: Optional[str]
    totalExports: int
    completedExports: int
    estimatedCompletion: Optional[str]
    createdAt: str
    completedAt: Optional[str]


class ExportTemplate(TypedDict):
    id: str
    name: str
    description: Optional[str]
    workspaceId: str
    exportType: str
    format: str
    defaultFilters: Optional[Dict[str, Any]]
    includeDeleted: bool
    isPublic: bool
    createdBy: str
    createdAt: str
    updatedAt: str


class PaginatedExportJobs(TypedDict):
    jobs: List[ExportJob]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class PaginatedExportSchedules(TypedDict):
    schedules: List[ExportSchedule]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class PaginatedExportTemplates(TypedDict):
    templates: List[ExportTemplate]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class ExportMetrics(TypedDict):
    totalExports: int
    successfulExports: int
    failedExports: int
    averageExportTime: Optional[float]
    totalDataExported: int  # in bytes
    popularFormats: List[Dict[str, Any]]
    popularTypes: List[Dict[str, Any]]


class CreateExportJobInput(TypedDict):
    workspaceId: str
    exportType: str  # ExportType enum
    format: str  # ExportFormat enum
    filters: Optional[Dict[str, Any]]
    includeDeleted: Optional[bool]
    dateRange: Optional[Dict[str, str]]


class CreateExportScheduleInput(TypedDict):
    workspaceId: str
    exportType: str
    format: str
    schedule: Dict[str, Any]  # ScheduleConfig
    deliveryMethod: str
    deliveryConfig: Optional[Dict[str, Any]]
    filters: Optional[Dict[str, Any]]
    includeDeleted: Optional[bool]


class CreateBulkExportInput(TypedDict):
    workspaceId: str
    exports: List[Dict[str, Any]]
    packageFormat: Optional[str]


class CreateExportTemplateInput(TypedDict):
    name: str
    description: Optional[str]
    workspaceId: str
    exportType: str
    format: str
    defaultFilters: Optional[Dict[str, Any]]
    includeDeleted: Optional[bool]
    isPublic: Optional[bool]


# Constants
EXPORT_TYPES = {
    "USERS": "USERS",
    "TEAMS": "TEAMS",
    "PROJECTS": "PROJECTS",
    "ANALYTICS": "ANALYTICS",
    "SETTINGS": "SETTINGS",
    "FULL_BACKUP": "FULL_BACKUP",
    "BILLING": "BILLING",
    "RBAC": "RBAC",
    "ACTIVITIES": "ACTIVITIES",
    "WORKSPACES": "WORKSPACES",
}

EXPORT_FORMATS = {
    "JSON": "JSON",
    "CSV": "CSV",
    "XML": "XML",
    "XLSX": "XLSX",
    "PDF": "PDF",
    "PARQUET": "PARQUET",
}

EXPORT_STATUS = {
    "PENDING": "PENDING",
    "PROCESSING": "PROCESSING",
    "COMPLETED": "COMPLETED",
    "FAILED": "FAILED",
    "CANCELLED": "CANCELLED",
    "EXPIRED": "EXPIRED",
}

DELIVERY_METHODS = {
    "DOWNLOAD": "DOWNLOAD",
    "EMAIL": "EMAIL",
    "S3": "S3",
    "WEBHOOK": "WEBHOOK",
    "FTP": "FTP",
}

PACKAGE_FORMATS = {"ZIP": "ZIP", "TAR": "TAR", "INDIVIDUAL": "INDIVIDUAL"}

SCHEDULE_FREQUENCIES = {
    "DAILY": "DAILY",
    "WEEKLY": "WEEKLY",
    "MONTHLY": "MONTHLY",
    "CUSTOM": "CUSTOM",
}


class DataExportClient:
    """
    Client for managing data export operations in the Workspaces platform.

    Provides comprehensive data export capabilities including:
    - Single and bulk export job creation and management
    - Scheduled exports with multiple delivery methods
    - Export templates for reusable configurations
    - Real-time export status monitoring
    - Export metrics and analytics
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Data Export client with a GraphQL endpoint.

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

    # Export Job Operations
    async def create_export_job(
        self, input_data: CreateExportJobInput, token: str
    ) -> Optional[ExportJob]:
        """
        Create a new data export job.

        Args:
            input_data (CreateExportJobInput): Export job configuration
            token (str): Authentication token

        Returns:
            Optional[ExportJob]: Created export job or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateExportJob($input: CreateExportJobInput!) {
                    createExportJob(input: $input) {
                        id
                        workspaceId
                        exportType
                        format
                        status
                        progress
                        recordsProcessed
                        totalRecords
                        downloadUrl
                        error
                        filters
                        includeDeleted
                        dateRange
                        estimatedCompletion
                        fileSize
                        createdAt
                        completedAt
                        expiresAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("createExportJob")
        except Exception as e:
            print(f"Create export job failed: {str(e)}")
            return None

    async def get_export_job(
        self, job_id: str, workspace_id: str, token: str
    ) -> Optional[ExportJob]:
        """
        Get details of a specific export job.

        Args:
            job_id (str): Export job ID
            workspace_id (str): Workspace ID for validation
            token (str): Authentication token

        Returns:
            Optional[ExportJob]: Export job details or None if not found
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetExportJob($jobId: ID!, $workspaceId: ID!) {
                    getExportJob(jobId: $jobId, workspaceId: $workspaceId) {
                        id
                        workspaceId
                        exportType
                        format
                        status
                        progress
                        recordsProcessed
                        totalRecords
                        downloadUrl
                        error
                        filters
                        includeDeleted
                        dateRange
                        estimatedCompletion
                        fileSize
                        createdAt
                        completedAt
                        expiresAt
                    }
                }
            """
            )

            variables = {"jobId": job_id, "workspaceId": workspace_id}

            result = client.execute(query, variable_values=variables)
            return result.get("getExportJob")
        except Exception as e:
            print(f"Get export job failed: {str(e)}")
            return None

    async def get_export_jobs(
        self,
        workspace_id: str,
        token: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[List[str]] = None,
        export_type: Optional[str] = None,
        format_filter: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> PaginatedExportJobs:
        """
        Get export jobs with pagination and filtering.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 20)
            status (List[str], optional): Filter by status
            export_type (str, optional): Filter by export type
            format_filter (str, optional): Filter by format
            from_date (str, optional): Filter from date (ISO format)
            to_date (str, optional): Filter to date (ISO format)
            sort_by (str, optional): Sort field
            sort_order (str, optional): Sort order (ASC/DESC)

        Returns:
            PaginatedExportJobs: Paginated export jobs
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetExportJobs(
                    $workspaceId: ID!
                    $page: Int
                    $pageSize: Int
                    $status: [ExportStatus!]
                    $exportType: ExportType
                    $format: ExportFormat
                    $fromDate: DateTime
                    $toDate: DateTime
                    $sortBy: String
                    $sortOrder: String
                ) {
                    getExportJobs(
                        workspaceId: $workspaceId
                        page: $page
                        pageSize: $pageSize
                        status: $status
                        exportType: $exportType
                        format: $format
                        fromDate: $fromDate
                        toDate: $toDate
                        sortBy: $sortBy
                        sortOrder: $sortOrder
                    ) {
                        jobs {
                            id
                            workspaceId
                            exportType
                            format
                            status
                            progress
                            recordsProcessed
                            totalRecords
                            downloadUrl
                            error
                            fileSize
                            createdAt
                            completedAt
                            expiresAt
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

            # Add optional parameters
            if status:
                variables["status"] = status
            if export_type:
                variables["exportType"] = export_type
            if format_filter:
                variables["format"] = format_filter
            if from_date:
                variables["fromDate"] = from_date
            if to_date:
                variables["toDate"] = to_date
            if sort_by:
                variables["sortBy"] = sort_by
            if sort_order:
                variables["sortOrder"] = sort_order

            result = client.execute(query, variable_values=variables)
            return result.get(
                "getExportJobs",
                {
                    "jobs": [],
                    "totalCount": 0,
                    "page": 1,
                    "pageSize": 20,
                    "totalPages": 0,
                },
            )
        except Exception as e:
            print(f"Get export jobs failed: {str(e)}")
            return {
                "jobs": [],
                "totalCount": 0,
                "page": 1,
                "pageSize": 20,
                "totalPages": 0,
            }

    async def cancel_export_job(
        self, job_id: str, workspace_id: str, token: str
    ) -> bool:
        """
        Cancel a pending or processing export job.

        Args:
            job_id (str): Export job ID to cancel
            workspace_id (str): Workspace ID for validation
            token (str): Authentication token

        Returns:
            bool: True if cancellation succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CancelExportJob($jobId: ID!, $workspaceId: ID!) {
                    cancelExportJob(jobId: $jobId, workspaceId: $workspaceId)
                }
            """
            )

            variables = {"jobId": job_id, "workspaceId": workspace_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("cancelExportJob", False)
        except Exception as e:
            print(f"Cancel export job failed: {str(e)}")
            return False

    async def delete_export_job(
        self, job_id: str, workspace_id: str, token: str
    ) -> bool:
        """
        Delete a completed or failed export job.

        Args:
            job_id (str): Export job ID to delete
            workspace_id (str): Workspace ID for validation
            token (str): Authentication token

        Returns:
            bool: True if deletion succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DeleteExportJob($jobId: ID!, $workspaceId: ID!) {
                    deleteExportJob(jobId: $jobId, workspaceId: $workspaceId)
                }
            """
            )

            variables = {"jobId": job_id, "workspaceId": workspace_id}

            result = client.execute(mutation, variable_values=variables)
            return result.get("deleteExportJob", False)
        except Exception as e:
            print(f"Delete export job failed: {str(e)}")
            return False

    # Bulk Export Operations
    async def create_bulk_export(
        self, input_data: CreateBulkExportInput, token: str
    ) -> Optional[BulkExportJob]:
        """
        Create a bulk export job with multiple export types.

        Args:
            input_data (CreateBulkExportInput): Bulk export configuration
            token (str): Authentication token

        Returns:
            Optional[BulkExportJob]: Created bulk export job or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateBulkExport($input: CreateBulkExportInput!) {
                    createBulkExport(input: $input) {
                        id
                        workspaceId
                        exports
                        packageFormat
                        status
                        progress
                        downloadUrl
                        error
                        totalExports
                        completedExports
                        estimatedCompletion
                        createdAt
                        completedAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("createBulkExport")
        except Exception as e:
            print(f"Create bulk export failed: {str(e)}")
            return None

    # Scheduled Export Operations
    async def create_export_schedule(
        self, input_data: CreateExportScheduleInput, token: str
    ) -> Optional[ExportSchedule]:
        """
        Create a scheduled export.

        Args:
            input_data (CreateExportScheduleInput): Schedule configuration
            token (str): Authentication token

        Returns:
            Optional[ExportSchedule]: Created export schedule or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateExportSchedule($input: CreateExportScheduleInput!) {  # noqa: E501
                    createExportSchedule(input: $input) {
                        id
                        workspaceId
                        exportType
                        format
                        schedule
                        deliveryMethod
                        deliveryConfig
                        filters
                        includeDeleted
                        lastRun
                        nextRun
                        status
                        enabled
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("createExportSchedule")
        except Exception as e:
            print(f"Create export schedule failed: {str(e)}")
            return None

    async def get_export_schedules(
        self,
        workspace_id: str,
        token: str,
        page: int = 1,
        page_size: int = 20,
        enabled_only: Optional[bool] = None,
    ) -> PaginatedExportSchedules:
        """
        Get export schedules with pagination.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 20)
            enabled_only (bool, optional): Filter by enabled status

        Returns:
            PaginatedExportSchedules: Paginated export schedules
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetExportSchedules(
                    $workspaceId: ID!
                    $page: Int
                    $pageSize: Int
                    $enabledOnly: Boolean
                ) {
                    getExportSchedules(
                        workspaceId: $workspaceId
                        page: $page
                        pageSize: $pageSize
                        enabledOnly: $enabledOnly
                    ) {
                        schedules {
                            id
                            workspaceId
                            exportType
                            format
                            schedule
                            deliveryMethod
                            deliveryConfig
                            lastRun
                            nextRun
                            status
                            enabled
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
                "getExportSchedules",
                {
                    "schedules": [],
                    "totalCount": 0,
                    "page": 1,
                    "pageSize": 20,
                    "totalPages": 0,
                },
            )
        except Exception as e:
            print(f"Get export schedules failed: {str(e)}")
            return {
                "schedules": [],
                "totalCount": 0,
                "page": 1,
                "pageSize": 20,
                "totalPages": 0,
            }

    async def update_export_schedule(
        self,
        schedule_id: str,
        workspace_id: str,
        enabled: Optional[bool] = None,
        schedule_config: Optional[Dict[str, Any]] = None,
        delivery_config: Optional[Dict[str, Any]] = None,
        token: str = None,
    ) -> Optional[ExportSchedule]:
        """
        Update an export schedule.

        Args:
            schedule_id (str): Schedule ID to update
            workspace_id (str): Workspace ID for validation
            enabled (bool, optional): Enable/disable the schedule
            schedule_config (Dict, optional): New schedule configuration
            delivery_config (Dict, optional): New delivery configuration
            token (str): Authentication token

        Returns:
            Optional[ExportSchedule]: Updated export schedule or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation UpdateExportSchedule(
                    $scheduleId: ID!
                    $workspaceId: ID!
                    $enabled: Boolean
                    $scheduleConfig: JSON
                    $deliveryConfig: JSON
                ) {
                    updateExportSchedule(
                        scheduleId: $scheduleId
                        workspaceId: $workspaceId
                        enabled: $enabled
                        scheduleConfig: $scheduleConfig
                        deliveryConfig: $deliveryConfig
                    ) {
                        id
                        workspaceId
                        exportType
                        format
                        schedule
                        deliveryMethod
                        deliveryConfig
                        enabled
                        nextRun
                        updatedAt
                    }
                }
            """
            )

            variables = {
                "scheduleId": schedule_id,
                "workspaceId": workspace_id,
            }

            if enabled is not None:
                variables["enabled"] = enabled
            if schedule_config:
                variables["scheduleConfig"] = schedule_config
            if delivery_config:
                variables["deliveryConfig"] = delivery_config

            result = client.execute(mutation, variable_values=variables)
            return result.get("updateExportSchedule")
        except Exception as e:
            print(f"Update export schedule failed: {str(e)}")
            return None

    async def delete_export_schedule(
        self, schedule_id: str, workspace_id: str, token: str
    ) -> bool:
        """
        Delete an export schedule.

        Args:
            schedule_id (str): Schedule ID to delete
            workspace_id (str): Workspace ID for validation
            token (str): Authentication token

        Returns:
            bool: True if deletion succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation DeleteExportSchedule($scheduleId: ID!, $workspaceId: ID!) {  # noqa: E501
                    deleteExportSchedule(scheduleId: $scheduleId, workspaceId: $workspaceId)
                }
            """
            )

            variables = {
                "scheduleId": schedule_id,
                "workspaceId": workspace_id,
            }

            result = client.execute(mutation, variable_values=variables)
            return result.get("deleteExportSchedule", False)
        except Exception as e:
            print(f"Delete export schedule failed: {str(e)}")
            return False

    # Export Template Operations
    async def create_export_template(
        self, input_data: CreateExportTemplateInput, token: str
    ) -> Optional[ExportTemplate]:
        """
        Create a reusable export template.

        Args:
            input_data (CreateExportTemplateInput): Template configuration
            token (str): Authentication token

        Returns:
            Optional[ExportTemplate]: Created export template or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateExportTemplate($input: CreateExportTemplateInput!) {  # noqa: E501
                    createExportTemplate(input: $input) {
                        id
                        name
                        description
                        workspaceId
                        exportType
                        format
                        defaultFilters
                        includeDeleted
                        isPublic
                        createdBy
                        createdAt
                        updatedAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("createExportTemplate")
        except Exception as e:
            print(f"Create export template failed: {str(e)}")
            return None

    async def get_export_templates(
        self,
        workspace_id: str,
        token: str,
        page: int = 1,
        page_size: int = 20,
        include_public: bool = True,
    ) -> PaginatedExportTemplates:
        """
        Get export templates with pagination.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 20)
            include_public (bool): Include public templates (default: True)

        Returns:
            PaginatedExportTemplates: Paginated export templates
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetExportTemplates(
                    $workspaceId: ID!
                    $page: Int
                    $pageSize: Int
                    $includePublic: Boolean
                ) {
                    getExportTemplates(
                        workspaceId: $workspaceId
                        page: $page
                        pageSize: $pageSize
                        includePublic: $includePublic
                    ) {
                        templates {
                            id
                            name
                            description
                            workspaceId
                            exportType
                            format
                            defaultFilters
                            includeDeleted
                            isPublic
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
                "workspaceId": workspace_id,
                "page": page,
                "pageSize": page_size,
                "includePublic": include_public,
            }

            result = client.execute(query, variable_values=variables)
            return result.get(
                "getExportTemplates",
                {
                    "templates": [],
                    "totalCount": 0,
                    "page": 1,
                    "pageSize": 20,
                    "totalPages": 0,
                },
            )
        except Exception as e:
            print(f"Get export templates failed: {str(e)}")
            return {
                "templates": [],
                "totalCount": 0,
                "page": 1,
                "pageSize": 20,
                "totalPages": 0,
            }

    # Analytics and Metrics
    async def get_export_metrics(
        self,
        workspace_id: str,
        token: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Optional[ExportMetrics]:
        """
        Get export metrics and analytics.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            from_date (str, optional): Start date for metrics (ISO format)
            to_date (str, optional): End date for metrics (ISO format)

        Returns:
            Optional[ExportMetrics]: Export metrics or None if failed
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetExportMetrics(
                    $workspaceId: ID!
                    $fromDate: DateTime
                    $toDate: DateTime
                ) {
                    getExportMetrics(
                        workspaceId: $workspaceId
                        fromDate: $fromDate
                        toDate: $toDate
                    ) {
                        totalExports
                        successfulExports
                        failedExports
                        averageExportTime
                        totalDataExported
                        popularFormats {
                            format
                            count
                            percentage
                        }
                        popularTypes {
                            type
                            count
                            percentage
                        }
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
            return result.get("getExportMetrics")
        except Exception as e:
            print(f"Get export metrics failed: {str(e)}")
            return None


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Data Export client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = DataExportClient(graphql_endpoint)


def get_client() -> DataExportClient:
    """Get the default Data Export client."""
    if _default_client is None:
        raise RuntimeError(
            "Data Export client not initialized. Call initialize() first."
        )
    return _default_client


# Convenience functions that use the default client
async def create_export_job(*args, **kwargs):
    return await get_client().create_export_job(*args, **kwargs)


async def get_export_job(*args, **kwargs):
    return await get_client().get_export_job(*args, **kwargs)


async def get_export_jobs(*args, **kwargs):
    return await get_client().get_export_jobs(*args, **kwargs)


async def cancel_export_job(*args, **kwargs):
    return await get_client().cancel_export_job(*args, **kwargs)


async def delete_export_job(*args, **kwargs):
    return await get_client().delete_export_job(*args, **kwargs)


async def create_bulk_export(*args, **kwargs):
    return await get_client().create_bulk_export(*args, **kwargs)


async def create_export_schedule(*args, **kwargs):
    return await get_client().create_export_schedule(*args, **kwargs)


async def get_export_schedules(*args, **kwargs):
    return await get_client().get_export_schedules(*args, **kwargs)


async def update_export_schedule(*args, **kwargs):
    return await get_client().update_export_schedule(*args, **kwargs)


async def delete_export_schedule(*args, **kwargs):
    return await get_client().delete_export_schedule(*args, **kwargs)


async def create_export_template(*args, **kwargs):
    return await get_client().create_export_template(*args, **kwargs)


async def get_export_templates(*args, **kwargs):
    return await get_client().get_export_templates(*args, **kwargs)


async def get_export_metrics(*args, **kwargs):
    return await get_client().get_export_metrics(*args, **kwargs)
