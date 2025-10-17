"""
Analytics Client for Workspaces SDK.

Provides comprehensive usage tracking, metrics collection, and insights generation  # noqa: E501
capabilities for workspace operations with real-time analytics and advanced reporting.  # noqa: E501
"""

from typing import Any, Dict, List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Analytics system
class AnalyticsEvent(TypedDict):
    id: str
    eventName: str
    properties: Optional[Dict[str, Any]]
    userId: str
    workspaceId: str
    sessionId: Optional[str]
    userAgent: Optional[str]
    ipAddress: Optional[str]
    referrer: Optional[str]
    path: Optional[str]
    timestamp: str
    createdAt: str


class EventCount(TypedDict):
    eventName: str
    count: int
    percentage: float


class DailyActivity(TypedDict):
    date: str
    activeUsers: int
    sessions: int
    events: int
    pageViews: int
    uniqueVisitors: int


class UserActivity(TypedDict):
    userId: str
    userName: Optional[str]
    userEmail: Optional[str]
    firstSeen: str
    lastSeen: str
    totalSessions: int
    totalEvents: int
    averageSessionDuration: Optional[float]
    topEvents: List[EventCount]


class SessionAnalytics(TypedDict):
    sessionId: str
    userId: str
    startTime: str
    endTime: Optional[str]
    duration: Optional[float]  # in minutes
    pageViews: int
    events: int
    bounceRate: Optional[float]
    exitPage: Optional[str]
    entryPage: Optional[str]
    userAgent: Optional[str]
    device: Optional[str]
    browser: Optional[str]
    os: Optional[str]


class PageAnalytics(TypedDict):
    path: str
    title: Optional[str]
    views: int
    uniqueVisitors: int
    averageTimeOnPage: Optional[float]
    bounceRate: Optional[float]
    exitRate: Optional[float]
    entrances: int


class FeatureUsage(TypedDict):
    featureName: str
    usageCount: int
    uniqueUsers: int
    adoptionRate: float
    averageUsagePerUser: float
    retentionRate: Optional[float]


class UsageTrends(TypedDict):
    growthRate: Optional[float]
    predictedUsage: Optional[float]
    averageDailyUsage: Optional[float]
    weeklyTrend: Optional[float]
    monthlyTrend: Optional[float]


class AnalyticsSummary(TypedDict):
    totalEvents: int
    uniqueUsers: int
    sessionCount: int
    averageSessionDuration: Optional[float]
    topEvents: List[EventCount]
    userActivity: List[DailyActivity]
    trends: Optional[UsageTrends]
    peakHours: List[Dict[str, Any]]


class WorkspaceAnalytics(TypedDict):
    workspaceId: str
    overview: Dict[str, Any]
    trends: Dict[str, Any]
    topPages: List[PageAnalytics]
    topFeatures: List[FeatureUsage]
    userEngagement: Dict[str, Any]
    performance: Dict[str, Any]


class AnalyticsReport(TypedDict):
    id: str
    workspaceId: str
    reportType: str  # DAILY, WEEKLY, MONTHLY, CUSTOM
    format: str  # JSON, CSV, PDF
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    downloadUrl: Optional[str]
    includeCharts: bool
    dateFrom: str
    dateTo: str
    filters: Optional[Dict[str, Any]]
    generatedAt: Optional[str]
    expiresAt: Optional[str]
    createdAt: str


class AnalyticsDashboard(TypedDict):
    overview: Dict[str, Any]
    realTimeMetrics: Dict[str, Any]
    topMetrics: List[Dict[str, Any]]
    recentActivity: List[AnalyticsEvent]
    alerts: List[Dict[str, Any]]
    quickInsights: List[str]


class ConversionFunnel(TypedDict):
    name: str
    steps: List[Dict[str, Any]]
    conversionRate: float
    dropOffPoints: List[Dict[str, Any]]
    averageTimeToConvert: Optional[float]


class Cohort(TypedDict):
    cohortDate: str
    userCount: int
    retentionRates: List[float]  # retention for each period
    totalRevenue: Optional[float]
    averageLifetimeValue: Optional[float]


class PaginatedAnalyticsEvents(TypedDict):
    events: List[AnalyticsEvent]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class PaginatedUserActivity(TypedDict):
    users: List[UserActivity]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class PaginatedSessionAnalytics(TypedDict):
    sessions: List[SessionAnalytics]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class PaginatedReports(TypedDict):
    reports: List[AnalyticsReport]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


# Input types
class TrackEventInput(TypedDict):
    eventName: str
    properties: Optional[Dict[str, Any]]
    userId: Optional[str]
    workspaceId: Optional[str]
    sessionId: Optional[str]
    timestamp: Optional[str]


class GenerateReportInput(TypedDict):
    workspaceId: str
    reportType: str  # DAILY, WEEKLY, MONTHLY, CUSTOM
    dateFrom: Optional[str]
    dateTo: Optional[str]
    format: Optional[str]  # JSON, CSV, PDF
    includeCharts: Optional[bool]
    filters: Optional[Dict[str, Any]]


class CreateFunnelInput(TypedDict):
    name: str
    workspaceId: str
    steps: List[Dict[str, Any]]
    filters: Optional[Dict[str, Any]]


# Constants
EVENT_TYPES = {
    "PAGE_VIEW": "PAGE_VIEW",
    "CLICK": "CLICK",
    "FORM_SUBMIT": "FORM_SUBMIT",
    "USER_LOGIN": "USER_LOGIN",
    "USER_LOGOUT": "USER_LOGOUT",
    "USER_SIGNUP": "USER_SIGNUP",
    "FEATURE_USED": "FEATURE_USED",
    "API_CALL": "API_CALL",
    "ERROR": "ERROR",
    "CUSTOM": "CUSTOM",
}

REPORT_TYPES = {
    "DAILY": "DAILY",
    "WEEKLY": "WEEKLY",
    "MONTHLY": "MONTHLY",
    "CUSTOM": "CUSTOM",
}

REPORT_FORMATS = {"JSON": "JSON", "CSV": "CSV", "PDF": "PDF", "XLSX": "XLSX"}

ANALYTICS_PERIODS = {
    "LAST_7_DAYS": "LAST_7_DAYS",
    "LAST_30_DAYS": "LAST_30_DAYS",
    "LAST_90_DAYS": "LAST_90_DAYS",
    "LAST_YEAR": "LAST_YEAR",
    "CUSTOM": "CUSTOM",
}


class AnalyticsClient:
    """
    Client for managing analytics and insights in the Workspaces platform.

    Provides comprehensive analytics capabilities including:
    - Event tracking and data collection
    - User behavior analysis and insights
    - Performance metrics and monitoring
    - Advanced reporting and visualization
    - Real-time analytics and alerts
    - Conversion funnel analysis
    - Cohort analysis and retention metrics
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Analytics client with a GraphQL endpoint.

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

    # Event Tracking Operations
    async def track_event(
        self, input_data: TrackEventInput, token: str
    ) -> Optional[AnalyticsEvent]:
        """
        Track an analytics event.

        Args:
            input_data (TrackEventInput): Event data to track
            token (str): Authentication token

        Returns:
            Optional[AnalyticsEvent]: Tracked event or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation TrackEvent($input: TrackEventInput!) {
                    trackEvent(input: $input) {
                        id
                        eventName
                        properties
                        userId
                        workspaceId
                        sessionId
                        userAgent
                        ipAddress
                        referrer
                        path
                        timestamp
                        createdAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("trackEvent")
        except Exception as e:
            print(f"Track event failed: {str(e)}")
            return None

    async def track_batch_events(
        self, events: List[TrackEventInput], token: str
    ) -> List[AnalyticsEvent]:
        """
        Track multiple events in a single batch.

        Args:
            events (List[TrackEventInput]): List of events to track
            token (str): Authentication token

        Returns:
            List[AnalyticsEvent]: List of tracked events
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation TrackBatchEvents($events: [TrackEventInput!]!) {
                    trackBatchEvents(events: $events) {
                        id
                        eventName
                        properties
                        userId
                        workspaceId
                        timestamp
                        createdAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"events": events})
            return result.get("trackBatchEvents", [])
        except Exception as e:
            print(f"Track batch events failed: {str(e)}")
            return []

    # Analytics Query Operations
    async def get_analytics_summary(
        self,
        workspace_id: str,
        token: str,
        date_from: str,
        date_to: str,
        metrics: Optional[List[str]] = None,
    ) -> Optional[AnalyticsSummary]:
        """
        Get analytics summary for a workspace and date range.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            date_from (str): Start date (ISO format)
            date_to (str): End date (ISO format)
            metrics (List[str], optional): Specific metrics to include

        Returns:
            Optional[AnalyticsSummary]: Analytics summary or None if failed
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAnalyticsSummary(
                    $workspaceId: ID!
                    $dateFrom: DateTime!
                    $dateTo: DateTime!
                    $metrics: [String!]
                ) {
                    getAnalyticsSummary(
                        workspaceId: $workspaceId
                        dateFrom: $dateFrom
                        dateTo: $dateTo
                        metrics: $metrics
                    ) {
                        totalEvents
                        uniqueUsers
                        sessionCount
                        averageSessionDuration
                        topEvents {
                            eventName
                            count
                            percentage
                        }
                        userActivity {
                            date
                            activeUsers
                            sessions
                            events
                            pageViews
                            uniqueVisitors
                        }
                        trends {
                            growthRate
                            predictedUsage
                            averageDailyUsage
                            weeklyTrend
                            monthlyTrend
                        }
                        peakHours {
                            hour
                            count
                            percentage
                        }
                    }
                }
            """
            )

            variables = {
                "workspaceId": workspace_id,
                "dateFrom": date_from,
                "dateTo": date_to,
            }
            if metrics:
                variables["metrics"] = metrics

            result = client.execute(query, variable_values=variables)
            return result.get("getAnalyticsSummary")
        except Exception as e:
            print(f"Get analytics summary failed: {str(e)}")
            return None

    async def get_workspace_analytics(
        self, workspace_id: str, token: str, period: str = "LAST_30_DAYS"
    ) -> Optional[WorkspaceAnalytics]:
        """
        Get comprehensive workspace analytics.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            period (str): Analytics period (default: LAST_30_DAYS)

        Returns:
            Optional[WorkspaceAnalytics]: Workspace analytics or None if failed
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetWorkspaceAnalytics(
                    $workspaceId: ID!
                    $period: AnalyticsPeriod
                ) {
                    getWorkspaceAnalytics(
                        workspaceId: $workspaceId
                        period: $period
                    ) {
                        workspaceId
                        overview {
                            totalUsers
                            activeUsers
                            totalEvents
                            avgSessionDuration
                        }
                        trends {
                            userGrowth
                            engagementTrend
                            featureAdoption
                        }
                        topPages {
                            path
                            title
                            views
                            uniqueVisitors
                            averageTimeOnPage
                            bounceRate
                            exitRate
                            entrances
                        }
                        topFeatures {
                            featureName
                            usageCount
                            uniqueUsers
                            adoptionRate
                            averageUsagePerUser
                            retentionRate
                        }
                        userEngagement {
                            averageSessionsPerUser
                            averageTimePerSession
                            returnUserRate
                            newUserRate
                        }
                        performance {
                            averagePageLoadTime
                            errorRate
                            apiResponseTime
                        }
                    }
                }
            """
            )

            variables = {"workspaceId": workspace_id, "period": period}

            result = client.execute(query, variable_values=variables)
            return result.get("getWorkspaceAnalytics")
        except Exception as e:
            print(f"Get workspace analytics failed: {str(e)}")
            return None

    async def get_analytics_events(
        self,
        workspace_id: str,
        token: str,
        page: int = 1,
        page_size: int = 50,
        event_name: Optional[str] = None,
        user_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> PaginatedAnalyticsEvents:
        """
        Get analytics events with pagination and filtering.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 50)
            event_name (str, optional): Filter by event name
            user_id (str, optional): Filter by user ID
            from_date (str, optional): Filter from date (ISO format)
            to_date (str, optional): Filter to date (ISO format)
            sort_by (str, optional): Sort field
            sort_order (str, optional): Sort order (ASC/DESC)

        Returns:
            PaginatedAnalyticsEvents: Paginated analytics events
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAnalyticsEvents(
                    $workspaceId: ID!
                    $page: Int
                    $pageSize: Int
                    $eventName: String
                    $userId: ID
                    $fromDate: DateTime
                    $toDate: DateTime
                    $sortBy: String
                    $sortOrder: String
                ) {
                    getAnalyticsEvents(
                        workspaceId: $workspaceId
                        page: $page
                        pageSize: $pageSize
                        eventName: $eventName
                        userId: $userId
                        fromDate: $fromDate
                        toDate: $toDate
                        sortBy: $sortBy
                        sortOrder: $sortOrder
                    ) {
                        events {
                            id
                            eventName
                            properties
                            userId
                            workspaceId
                            sessionId
                            userAgent
                            ipAddress
                            referrer
                            path
                            timestamp
                            createdAt
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
            if event_name:
                variables["eventName"] = event_name
            if user_id:
                variables["userId"] = user_id
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
                "getAnalyticsEvents",
                {
                    "events": [],
                    "totalCount": 0,
                    "page": 1,
                    "pageSize": 50,
                    "totalPages": 0,
                },
            )
        except Exception as e:
            print(f"Get analytics events failed: {str(e)}")
            return {
                "events": [],
                "totalCount": 0,
                "page": 1,
                "pageSize": 50,
                "totalPages": 0,
            }

    async def get_user_activity(
        self,
        workspace_id: str,
        token: str,
        page: int = 1,
        page_size: int = 20,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> PaginatedUserActivity:
        """
        Get user activity analytics with pagination.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 20)
            from_date (str, optional): Filter from date (ISO format)
            to_date (str, optional): Filter to date (ISO format)
            sort_by (str, optional): Sort field
            sort_order (str, optional): Sort order (ASC/DESC)

        Returns:
            PaginatedUserActivity: Paginated user activity
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetUserActivity(
                    $workspaceId: ID!
                    $page: Int
                    $pageSize: Int
                    $fromDate: DateTime
                    $toDate: DateTime
                    $sortBy: String
                    $sortOrder: String
                ) {
                    getUserActivity(
                        workspaceId: $workspaceId
                        page: $page
                        pageSize: $pageSize
                        fromDate: $fromDate
                        toDate: $toDate
                        sortBy: $sortBy
                        sortOrder: $sortOrder
                    ) {
                        users {
                            userId
                            userName
                            userEmail
                            firstSeen
                            lastSeen
                            totalSessions
                            totalEvents
                            averageSessionDuration
                            topEvents {
                                eventName
                                count
                                percentage
                            }
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
                "getUserActivity",
                {
                    "users": [],
                    "totalCount": 0,
                    "page": 1,
                    "pageSize": 20,
                    "totalPages": 0,
                },
            )
        except Exception as e:
            print(f"Get user activity failed: {str(e)}")
            return {
                "users": [],
                "totalCount": 0,
                "page": 1,
                "pageSize": 20,
                "totalPages": 0,
            }

    async def get_session_analytics(
        self,
        workspace_id: str,
        token: str,
        page: int = 1,
        page_size: int = 20,
        user_id: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> PaginatedSessionAnalytics:
        """
        Get session analytics with pagination and filtering.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 20)
            user_id (str, optional): Filter by user ID
            from_date (str, optional): Filter from date (ISO format)
            to_date (str, optional): Filter to date (ISO format)

        Returns:
            PaginatedSessionAnalytics: Paginated session analytics
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetSessionAnalytics(
                    $workspaceId: ID!
                    $page: Int
                    $pageSize: Int
                    $userId: ID
                    $fromDate: DateTime
                    $toDate: DateTime
                ) {
                    getSessionAnalytics(
                        workspaceId: $workspaceId
                        page: $page
                        pageSize: $pageSize
                        userId: $userId
                        fromDate: $fromDate
                        toDate: $toDate
                    ) {
                        sessions {
                            sessionId
                            userId
                            startTime
                            endTime
                            duration
                            pageViews
                            events
                            bounceRate
                            exitPage
                            entryPage
                            userAgent
                            device
                            browser
                            os
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

            if user_id:
                variables["userId"] = user_id
            if from_date:
                variables["fromDate"] = from_date
            if to_date:
                variables["toDate"] = to_date

            result = client.execute(query, variable_values=variables)
            return result.get(
                "getSessionAnalytics",
                {
                    "sessions": [],
                    "totalCount": 0,
                    "page": 1,
                    "pageSize": 20,
                    "totalPages": 0,
                },
            )
        except Exception as e:
            print(f"Get session analytics failed: {str(e)}")
            return {
                "sessions": [],
                "totalCount": 0,
                "page": 1,
                "pageSize": 20,
                "totalPages": 0,
            }

    # Reporting Operations
    async def generate_analytics_report(
        self, input_data: GenerateReportInput, token: str
    ) -> Optional[AnalyticsReport]:
        """
        Generate an analytics report.

        Args:
            input_data (GenerateReportInput): Report configuration
            token (str): Authentication token

        Returns:
            Optional[AnalyticsReport]: Generated report job or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation GenerateAnalyticsReport($input: GenerateReportInput!) {  # noqa: E501
                    generateAnalyticsReport(input: $input) {
                        id
                        workspaceId
                        reportType
                        format
                        status
                        downloadUrl
                        includeCharts
                        dateFrom
                        dateTo
                        filters
                        generatedAt
                        expiresAt
                        createdAt
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("generateAnalyticsReport")
        except Exception as e:
            print(f"Generate analytics report failed: {str(e)}")
            return None

    async def get_analytics_reports(
        self,
        workspace_id: str,
        token: str,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
    ) -> PaginatedReports:
        """
        Get analytics reports with pagination.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 20)
            status (str, optional): Filter by status

        Returns:
            PaginatedReports: Paginated analytics reports
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAnalyticsReports(
                    $workspaceId: ID!
                    $page: Int
                    $pageSize: Int
                    $status: String
                ) {
                    getAnalyticsReports(
                        workspaceId: $workspaceId
                        page: $page
                        pageSize: $pageSize
                        status: $status
                    ) {
                        reports {
                            id
                            workspaceId
                            reportType
                            format
                            status
                            downloadUrl
                            includeCharts
                            dateFrom
                            dateTo
                            generatedAt
                            expiresAt
                            createdAt
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
            if status:
                variables["status"] = status

            result = client.execute(query, variable_values=variables)
            return result.get(
                "getAnalyticsReports",
                {
                    "reports": [],
                    "totalCount": 0,
                    "page": 1,
                    "pageSize": 20,
                    "totalPages": 0,
                },
            )
        except Exception as e:
            print(f"Get analytics reports failed: {str(e)}")
            return {
                "reports": [],
                "totalCount": 0,
                "page": 1,
                "pageSize": 20,
                "totalPages": 0,
            }

    # Advanced Analytics Operations
    async def get_analytics_dashboard(
        self, workspace_id: str, token: str
    ) -> Optional[AnalyticsDashboard]:
        """
        Get analytics dashboard with real-time metrics.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token

        Returns:
            Optional[AnalyticsDashboard]: Analytics dashboard or None if failed
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAnalyticsDashboard($workspaceId: ID!) {
                    getAnalyticsDashboard(workspaceId: $workspaceId) {
                        overview {
                            totalUsers
                            activeUsers
                            totalSessions
                            conversionRate
                        }
                        realTimeMetrics {
                            currentActiveUsers
                            currentSessions
                            eventsPerSecond
                            topPages
                        }
                        topMetrics {
                            name
                            value
                            change
                            trend
                        }
                        recentActivity {
                            id
                            eventName
                            userId
                            timestamp
                        }
                        alerts {
                            type
                            message
                            severity
                            timestamp
                        }
                        quickInsights
                    }
                }
            """
            )

            result = client.execute(
                query, variable_values={"workspaceId": workspace_id}
            )
            return result.get("getAnalyticsDashboard")
        except Exception as e:
            print(f"Get analytics dashboard failed: {str(e)}")
            return None

    async def create_conversion_funnel(
        self, input_data: CreateFunnelInput, token: str
    ) -> Optional[ConversionFunnel]:
        """
        Create a conversion funnel analysis.

        Args:
            input_data (CreateFunnelInput): Funnel configuration
            token (str): Authentication token

        Returns:
            Optional[ConversionFunnel]: Created funnel or None if failed
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation CreateConversionFunnel($input: CreateFunnelInput!) {
                    createConversionFunnel(input: $input) {
                        name
                        steps {
                            name
                            eventName
                            userCount
                            conversionRate
                            dropOffRate
                        }
                        conversionRate
                        dropOffPoints {
                            stepIndex
                            dropOffRate
                            userCount
                        }
                        averageTimeToConvert
                    }
                }
            """
            )

            result = client.execute(mutation, variable_values={"input": input_data})
            return result.get("createConversionFunnel")
        except Exception as e:
            print(f"Create conversion funnel failed: {str(e)}")
            return None

    async def get_cohort_analysis(
        self,
        workspace_id: str,
        token: str,
        cohort_type: str = "WEEKLY",
        period_count: int = 12,
    ) -> List[Cohort]:
        """
        Get cohort analysis for user retention.

        Args:
            workspace_id (str): Workspace ID
            token (str): Authentication token
            cohort_type (str): Cohort type (DAILY, WEEKLY, MONTHLY)
            period_count (int): Number of periods to analyze

        Returns:
            List[Cohort]: Cohort analysis data
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetCohortAnalysis(
                    $workspaceId: ID!
                    $cohortType: String!
                    $periodCount: Int!
                ) {
                    getCohortAnalysis(
                        workspaceId: $workspaceId
                        cohortType: $cohortType
                        periodCount: $periodCount
                    ) {
                        cohortDate
                        userCount
                        retentionRates
                        totalRevenue
                        averageLifetimeValue
                    }
                }
            """
            )

            variables = {
                "workspaceId": workspace_id,
                "cohortType": cohort_type,
                "periodCount": period_count,
            }

            result = client.execute(query, variable_values=variables)
            return result.get("getCohortAnalysis", [])
        except Exception as e:
            print(f"Get cohort analysis failed: {str(e)}")
            return []


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Analytics client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = AnalyticsClient(graphql_endpoint)


def get_client() -> AnalyticsClient:
    """Get the default Analytics client."""
    if _default_client is None:
        raise RuntimeError("Analytics client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def track_event(*args, **kwargs):
    return await get_client().track_event(*args, **kwargs)


async def track_batch_events(*args, **kwargs):
    return await get_client().track_batch_events(*args, **kwargs)


async def get_analytics_summary(*args, **kwargs):
    return await get_client().get_analytics_summary(*args, **kwargs)


async def get_workspace_analytics(*args, **kwargs):
    return await get_client().get_workspace_analytics(*args, **kwargs)


async def get_analytics_events(*args, **kwargs):
    return await get_client().get_analytics_events(*args, **kwargs)


async def get_user_activity(*args, **kwargs):
    return await get_client().get_user_activity(*args, **kwargs)


async def get_session_analytics(*args, **kwargs):
    return await get_client().get_session_analytics(*args, **kwargs)


async def generate_analytics_report(*args, **kwargs):
    return await get_client().generate_analytics_report(*args, **kwargs)


async def get_analytics_reports(*args, **kwargs):
    return await get_client().get_analytics_reports(*args, **kwargs)


async def get_analytics_dashboard(*args, **kwargs):
    return await get_client().get_analytics_dashboard(*args, **kwargs)


async def create_conversion_funnel(*args, **kwargs):
    return await get_client().create_conversion_funnel(*args, **kwargs)


async def get_cohort_analysis(*args, **kwargs):
    return await get_client().get_cohort_analysis(*args, **kwargs)
