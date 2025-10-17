"""
Usage Client for Workspaces SDK.

Provides access to usage tracking and analytics functionality including quota
assignments, usage monitoring, analytics, and usage management.
"""

from typing import Any, List, Optional, TypedDict

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from .config import get_default_headers


# Type definitions for Usage system
class Usage(TypedDict):
    id: str
    quotaAssignmentId: str
    amount: float
    description: str
    lastUpdated: str
    tags: Optional[Any]
    productId: str
    timestamp: str


class DailyUsage(TypedDict):
    date: str
    usage: float
    count: int


class UsageByType(TypedDict):
    resourceType: str
    usage: float
    count: int
    percentage: float


class UsageTrends(TypedDict):
    growthRate: Optional[float]
    predictedUsage: Optional[float]
    averageDailyUsage: Optional[float]


class PeakUsage(TypedDict):
    maxDailyUsage: float
    peakDate: str
    peakHour: Optional[int]


class QuotaUsageAnalytics(TypedDict):
    dailyUsage: List[DailyUsage]
    usageByType: List[UsageByType]
    trends: Optional[UsageTrends]
    peakUsage: Optional[PeakUsage]


class QuotaAssignment(TypedDict):
    id: str
    name: str
    limits: Any
    reusable: bool
    subscriptionId: str
    usages: List[Usage]
    recentUsages: List[Usage]
    totalUsageCount: int
    currentUsageSum: float
    usageAnalytics: Optional[QuotaUsageAnalytics]
    createdAt: str
    endtime: str


class QuotaAssignmentWithAnalytics(TypedDict):
    id: str
    name: str
    limits: Any
    reusable: bool
    subscriptionId: str
    createdAt: str
    endtime: str
    totalUsageCount: int
    currentUsageSum: float
    limitLeft: float
    usagePercentage: float
    recentUsages: List[Usage]
    analytics: QuotaUsageAnalytics
    status: str  # QuotaStatus enum
    healthScore: float


class PaginatedUsages(TypedDict):
    usages: List[Usage]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class PaginatedQuotaAssignments(TypedDict):
    quotaAssignments: List[QuotaAssignment]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class PaginatedQuotaAssignmentsWithAnalytics(TypedDict):
    quotaAssignments: List[QuotaAssignmentWithAnalytics]
    totalCount: int
    page: int
    pageSize: int
    totalPages: int


class QuotaAssignmentSummary(TypedDict):
    currentUsageSum: int
    usageCount: int
    usages: List[Usage]
    createdAt: str
    endtime: str
    id: str
    name: str
    limits: Any


class SubscriptionWithQuotas(TypedDict):
    id: str
    createdAt: str
    status: str
    quotas: List[QuotaAssignmentSummary]


class SubscriptionQuotaUsageWithFilter(TypedDict):
    pageSize: int
    totalCount: int
    totalPages: int
    page: int
    usages: List[Usage]


class QuotaCheckResult(TypedDict):
    limitLeft: int
    noLimit: bool


class QuotaUsageAndLimit(TypedDict):
    limit: int
    limitLeft: int
    noLimit: bool


class QuotaUsageSummary(TypedDict):
    quotaName: str
    quotaId: str
    usage: float
    limit: float
    percentage: float
    status: str


class UsageActivity(TypedDict):
    id: str
    quotaName: str
    description: str
    amount: float
    timestamp: str
    tags: Optional[Any]


class UsageDashboard(TypedDict):
    totalUsage: float
    totalQuotas: int
    activeQuotas: int
    healthyQuotas: int
    warningQuotas: int
    criticalQuotas: int
    exhaustedQuotas: int
    topUsageByQuota: List[QuotaUsageSummary]
    overallTrends: UsageTrends
    recentActivities: List[UsageActivity]


class TagsAndResourceTypes(TypedDict):
    tags: List[str]
    resourceTypes: List[str]


class UsageClient:
    """
    Client for managing usage tracking and analytics in the Workspaces platform.  # noqa: E501

    Provides methods to track usage, retrieve analytics, manage quota assignments,  # noqa: E501
    and monitor resource consumption with proper authentication and error handling.  # noqa: E501
    """

    def __init__(self, graphql_endpoint: str):
        """
        Initialize the Usage client with a GraphQL endpoint.

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

    # Usage Query Operations
    async def get_all_quota_assignments(
        self,
        billing_account_id: str,
        token: str,
        page: int = 1,
        page_size: int = 10,
        search_query: Optional[str] = None,
        status: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        amount_min: Optional[float] = None,
        amount_max: Optional[float] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> PaginatedQuotaAssignments:
        """
        Retrieves quota assignments with pagination and filtering.

        Args:
            billing_account_id (str): ID of the billing account
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 10)
            search_query (str, optional): Search query
            status (List[str], optional): Filter by status
            from_date (str, optional): Filter from date (ISO format)
            to_date (str, optional): Filter to date (ISO format)
            amount_min (float, optional): Minimum amount filter
            amount_max (float, optional): Maximum amount filter
            sort_by (str, optional): Sort field
            sort_order (str, optional): Sort order

        Returns:
            PaginatedQuotaAssignments: Paginated quota assignments
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAllQuotasAssignment(
                    $billingAccountId: ID!
                    $page: Int
                    $pageSize: Int
                    $searchQuery: String
                    $status: [QuotaStatus!]
                    $fromDate: DateTime
                    $toDate: DateTime
                    $amountMin: Float
                    $amountMax: Float
                    $sortBy: String
                    $sortOrder: String
                ) {
                    getAllQuotasAssignment(
                        billingAccountId: $billingAccountId
                        page: $page
                        pageSize: $pageSize
                        searchQuery: $searchQuery
                        status: $status
                        fromDate: $fromDate
                        toDate: $toDate
                        amountMin: $amountMin
                        amountMax: $amountMax
                        sortBy: $sortBy
                        sortOrder: $sortOrder
                    ) {
                        quotaAssignments {
                            id
                            name
                            limits
                            reusable
                            subscriptionId
                            recentUsages {
                                id
                                amount
                                description
                                timestamp
                            }
                            totalUsageCount
                            currentUsageSum
                            createdAt
                            endtime
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
                "billingAccountId": billing_account_id,
                "page": page,
                "pageSize": page_size,
            }

            # Add optional parameters
            if search_query:
                variables["searchQuery"] = search_query
            if status:
                variables["status"] = status
            if from_date:
                variables["fromDate"] = from_date
            if to_date:
                variables["toDate"] = to_date
            if amount_min is not None:
                variables["amountMin"] = amount_min
            if amount_max is not None:
                variables["amountMax"] = amount_max
            if sort_by:
                variables["sortBy"] = sort_by
            if sort_order:
                variables["sortOrder"] = sort_order

            result = client.execute(query, variable_values=variables)
            return result.get(
                "getAllQuotasAssignment",
                {
                    "quotaAssignments": [],
                    "totalCount": 0,
                    "page": 1,
                    "pageSize": 10,
                    "totalPages": 0,
                },
            )
        except Exception as e:
            print(f"Get all quota assignments failed: {str(e)}")
            return {
                "quotaAssignments": [],
                "totalCount": 0,
                "page": 1,
                "pageSize": 10,
                "totalPages": 0,
            }

    async def get_quota_assignments_with_analytics(
        self,
        billing_account_id: str,
        token: str,
        page: int = 1,
        page_size: int = 10,
        search_query: Optional[str] = None,
        status: Optional[List[str]] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        amount_min: Optional[float] = None,
        amount_max: Optional[float] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> PaginatedQuotaAssignmentsWithAnalytics:
        """
        Enhanced quota assignment query with analytics, pagination and filtering.  # noqa: E501

        Args:
            billing_account_id (str): ID of the billing account
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 10)
            search_query (str, optional): Search query
            status (List[str], optional): Filter by status
            from_date (str, optional): Filter from date (ISO format)
            to_date (str, optional): Filter to date (ISO format)
            amount_min (float, optional): Minimum amount filter
            amount_max (float, optional): Maximum amount filter
            sort_by (str, optional): Sort field
            sort_order (str, optional): Sort order

        Returns:
            PaginatedQuotaAssignmentsWithAnalytics: Enhanced quota assignments with analytics
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetQuotaAssignmentsWithAnalytics(
                    $billingAccountId: ID!
                    $page: Int
                    $pageSize: Int
                    $searchQuery: String
                    $status: [QuotaStatus!]
                    $fromDate: DateTime
                    $toDate: DateTime
                    $amountMin: Float
                    $amountMax: Float
                    $sortBy: String
                    $sortOrder: String
                ) {
                    getQuotaAssignmentsWithAnalytics(
                        billingAccountId: $billingAccountId
                        page: $page
                        pageSize: $pageSize
                        searchQuery: $searchQuery
                        status: $status
                        fromDate: $fromDate
                        toDate: $toDate
                        amountMin: $amountMin
                        amountMax: $amountMax
                        sortBy: $sortBy
                        sortOrder: $sortOrder
                    ) {
                        quotaAssignments {
                            id
                            name
                            limits
                            reusable
                            subscriptionId
                            createdAt
                            endtime
                            totalUsageCount
                            currentUsageSum
                            limitLeft
                            usagePercentage
                            recentUsages {
                                id
                                amount
                                description
                                timestamp
                            }
                            analytics {
                                dailyUsage {
                                    date
                                    usage
                                    count
                                }
                                usageByType {
                                    resourceType
                                    usage
                                    count
                                    percentage
                                }
                                trends {
                                    growthRate
                                    predictedUsage
                                    averageDailyUsage
                                }
                                peakUsage {
                                    maxDailyUsage
                                    peakDate
                                    peakHour
                                }
                            }
                            status
                            healthScore
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
                "billingAccountId": billing_account_id,
                "page": page,
                "pageSize": page_size,
            }

            # Add optional parameters
            if search_query:
                variables["searchQuery"] = search_query
            if status:
                variables["status"] = status
            if from_date:
                variables["fromDate"] = from_date
            if to_date:
                variables["toDate"] = to_date
            if amount_min is not None:
                variables["amountMin"] = amount_min
            if amount_max is not None:
                variables["amountMax"] = amount_max
            if sort_by:
                variables["sortBy"] = sort_by
            if sort_order:
                variables["sortOrder"] = sort_order

            result = client.execute(query, variable_values=variables)
            return result.get(
                "getQuotaAssignmentsWithAnalytics",
                {
                    "quotaAssignments": [],
                    "totalCount": 0,
                    "page": 1,
                    "pageSize": 10,
                    "totalPages": 0,
                },
            )
        except Exception as e:
            print(f"Get quota assignments with analytics failed: {str(e)}")
            return {
                "quotaAssignments": [],
                "totalCount": 0,
                "page": 1,
                "pageSize": 10,
                "totalPages": 0,
            }

    async def get_quota_usage_and_limit(
        self, billing_account_id: str, quota_name: str, token: str
    ) -> Optional[QuotaUsageAndLimit]:
        """
        Gets usage and limit information for a specific quota.

        Args:
            billing_account_id (str): ID of the billing account
            quota_name (str): Name of the quota
            token (str): Authentication token

        Returns:
            Optional[QuotaUsageAndLimit]: Quota usage and limit info or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetQuotaUsageAndLimit($billingAccountId: ID!, $quotaName: String!) {  # noqa: E501
                    getQuotaUsageAndLimit(billingAccountId: $billingAccountId, quotaName: $quotaName) {
                        limit
                        limitLeft
                        noLimit
                    }
                }
            """
            )

            variables = {
                "billingAccountId": billing_account_id,
                "quotaName": quota_name,
            }

            result = client.execute(query, variable_values=variables)
            return result.get("getQuotaUsageAndLimit")
        except Exception as e:
            print(f"Get quota usage and limit failed: {str(e)}")
            return None

    async def check_quota_exhausted(
        self, billing_account_id: str, quota_name: str, token: str
    ) -> Optional[QuotaCheckResult]:
        """
        Checks if a quota is exhausted.

        Args:
            billing_account_id (str): ID of the billing account
            quota_name (str): Name of the quota to check
            token (str): Authentication token

        Returns:
            Optional[QuotaCheckResult]: Quota check result or None if failed
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query CheckQuotaExhausted($billingAccountId: ID!, $quotaName: String!) {  # noqa: E501
                    checkQuotaExhausted(billingAccountId: $billingAccountId, quotaName: $quotaName) {
                        limitLeft
                        noLimit
                    }
                }
            """
            )

            variables = {
                "billingAccountId": billing_account_id,
                "quotaName": quota_name,
            }

            result = client.execute(query, variable_values=variables)
            return result.get("checkQuotaExhausted")
        except Exception as e:
            print(f"Check quota exhausted failed: {str(e)}")
            return None

    async def get_quota_usage_details(
        self,
        quota_assignment_id: str,
        token: str,
        page: int = 1,
        page_size: int = 10,
        search_query: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        resource_type: Optional[str] = None,
        entity: Optional[str] = None,
        amount_min: Optional[float] = None,
        amount_max: Optional[float] = None,
        tags: Optional[List[str]] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> Optional[PaginatedUsages]:
        """
        Gets detailed usage information for a quota assignment.

        Args:
            quota_assignment_id (str): ID of the quota assignment
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 10)
            search_query (str, optional): Search query
            from_date (str, optional): Filter from date (ISO format)
            to_date (str, optional): Filter to date (ISO format)
            resource_type (str, optional): Filter by resource type
            entity (str, optional): Filter by entity
            amount_min (float, optional): Minimum amount filter
            amount_max (float, optional): Maximum amount filter
            tags (List[str], optional): Filter by tags
            sort_by (str, optional): Sort field
            sort_order (str, optional): Sort order

        Returns:
            Optional[PaginatedUsages]: Paginated usage details or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetQuotaUsageDetails(
                    $quotaAssignmentId: ID!
                    $page: Int
                    $pageSize: Int
                    $searchQuery: String
                    $fromDate: DateTime
                    $toDate: DateTime
                    $resourceType: String
                    $entity: String
                    $amountMin: Float
                    $amountMax: Float
                    $tags: [String!]
                    $sortBy: String
                    $sortOrder: String
                ) {
                    getQuotaUsageDetails(
                        quotaAssignmentId: $quotaAssignmentId
                        page: $page
                        pageSize: $pageSize
                        searchQuery: $searchQuery
                        fromDate: $fromDate
                        toDate: $toDate
                        resourceType: $resourceType
                        entity: $entity
                        amountMin: $amountMin
                        amountMax: $amountMax
                        tags: $tags
                        sortBy: $sortBy
                        sortOrder: $sortOrder
                    ) {
                        usages {
                            id
                            amount
                            description
                            lastUpdated
                            tags
                            productId
                            timestamp
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
                "quotaAssignmentId": quota_assignment_id,
                "page": page,
                "pageSize": page_size,
            }

            # Add optional parameters
            if search_query:
                variables["searchQuery"] = search_query
            if from_date:
                variables["fromDate"] = from_date
            if to_date:
                variables["toDate"] = to_date
            if resource_type:
                variables["resourceType"] = resource_type
            if entity:
                variables["entity"] = entity
            if amount_min is not None:
                variables["amountMin"] = amount_min
            if amount_max is not None:
                variables["amountMax"] = amount_max
            if tags:
                variables["tags"] = tags
            if sort_by:
                variables["sortBy"] = sort_by
            if sort_order:
                variables["sortOrder"] = sort_order

            result = client.execute(query, variable_values=variables)
            return result.get("getQuotaUsageDetails")
        except Exception as e:
            print(f"Get quota usage details failed: {str(e)}")
            return None

    async def get_subscription_usage_overview(
        self,
        billing_account_id: str,
        token: str,
        page: int = 1,
        page_size: int = 10,
    ) -> List[SubscriptionWithQuotas]:
        """
        Enhanced subscription overview with better pagination and filtering.

        Args:
            billing_account_id (str): ID of the billing account
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 10)

        Returns:
            List[SubscriptionWithQuotas]: List of subscriptions with quota information  # noqa: E501
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetSubscriptionUsageOverview(
                    $billingAccountId: ID!
                    $page: Int
                    $pageSize: Int
                ) {
                    getSubscriptionUsageOverview(
                        billingAccountId: $billingAccountId
                        page: $page
                        pageSize: $pageSize
                    ) {
                        id
                        createdAt
                        status
                        quotas {
                            currentUsageSum
                            usageCount
                            createdAt
                            endtime
                            id
                            name
                            limits
                        }
                    }
                }
            """
            )

            variables = {
                "billingAccountId": billing_account_id,
                "page": page,
                "pageSize": page_size,
            }

            result = client.execute(query, variable_values=variables)
            return result.get("getSubscriptionUsageOverview", [])
        except Exception as e:
            print(f"Get subscription usage overview failed: {str(e)}")
            return []

    async def get_subscription_usages(
        self,
        billing_account_id: str,
        token: str,
        page: int = 1,
        page_size: int = 10,
        search_query: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        resource_type: Optional[str] = None,
        entity: Optional[str] = None,
    ) -> SubscriptionQuotaUsageWithFilter:
        """
        Get filtered and paginated subscription usage data.

        Args:
            billing_account_id (str): ID of the billing account
            token (str): Authentication token
            page (int): Page number (default: 1)
            page_size (int): Items per page (default: 10)
            search_query (str, optional): Search query
            from_date (str, optional): Start date for filtering
            to_date (str, optional): End date for filtering
            resource_type (str, optional): Filter by resource type
            entity (str, optional): Filter by entity

        Returns:
            SubscriptionQuotaUsageWithFilter: Filtered subscription usage data with pagination  # noqa: E501
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetSubscriptionUsages(
                    $billingAccountId: ID!
                    $page: Int
                    $pageSize: Int
                    $searchQuery: String
                    $fromDate: DateTime
                    $toDate: DateTime
                    $resourceType: String
                    $entity: String
                ) {
                    getSubscriptionUsages(
                        billingAccountId: $billingAccountId
                        page: $page
                        pageSize: $pageSize
                        searchQuery: $searchQuery
                        fromDate: $fromDate
                        toDate: $toDate
                        resourceType: $resourceType
                        entity: $entity
                    ) {
                        usages {
                            id
                            quotaAssignmentId
                            subscriptionId
                            amount
                            resourceType
                            entity
                            tags
                            createdAt
                        }
                        totalCount
                        page
                        pageSize
                        hasNextPage
                        hasPreviousPage
                    }
                }
            """
            )

            variables = {
                "billingAccountId": billing_account_id,
                "page": page,
                "pageSize": page_size,
            }
            if search_query is not None:
                variables["searchQuery"] = search_query
            if from_date is not None:
                variables["fromDate"] = from_date
            if to_date is not None:
                variables["toDate"] = to_date
            if resource_type is not None:
                variables["resourceType"] = resource_type
            if entity is not None:
                variables["entity"] = entity

            result = client.execute(query, variable_values=variables)
            return result.get(
                "getSubscriptionUsages",
                {
                    "usages": [],
                    "totalCount": 0,
                    "page": page,
                    "pageSize": page_size,
                    "hasNextPage": False,
                    "hasPreviousPage": False,
                },
            )
        except Exception as e:
            print(f"Get subscription usages failed: {str(e)}")
            return {
                "usages": [],
                "totalCount": 0,
                "page": page,
                "pageSize": page_size,
                "hasNextPage": False,
                "hasPreviousPage": False,
            }

    async def get_quota_analytics(
        self,
        quota_assignment_id: str,
        token: str,
        period: str = "LAST_30_DAYS",
    ) -> Optional[QuotaUsageAnalytics]:
        """
        Get usage analytics for a specific quota assignment.

        Args:
            quota_assignment_id (str): ID of the quota assignment
            token (str): Authentication token
            period (str): Analytics period (LAST_7_DAYS, LAST_30_DAYS, etc.)

        Returns:
            Optional[QuotaUsageAnalytics]: Usage analytics or None if failed
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetQuotaAnalytics($quotaAssignmentId: ID!, $period: AnalyticsPeriod) {  # noqa: E501
                    getQuotaAnalytics(quotaAssignmentId: $quotaAssignmentId, period: $period) {
                        dailyUsage {
                            date
                            usage
                            count
                        }
                        usageByType {
                            resourceType
                            usage
                            count
                            percentage
                        }
                        trends {
                            growthRate
                            predictedUsage
                            averageDailyUsage
                        }
                        peakUsage {
                            maxDailyUsage
                            peakDate
                            peakHour
                        }
                    }
                }
            """
            )

            variables = {
                "quotaAssignmentId": quota_assignment_id,
                "period": period,
            }

            result = client.execute(query, variable_values=variables)
            return result.get("getQuotaAnalytics")
        except Exception as e:
            print(f"Get quota analytics failed: {str(e)}")
            return None

    async def get_usage_dashboard(
        self, billing_account_id: str, token: str, period: str = "LAST_30_DAYS"
    ) -> Optional[UsageDashboard]:
        """
        Get usage summary across all quota assignments.

        Args:
            billing_account_id (str): ID of the billing account
            token (str): Authentication token
            period (str): Analytics period (LAST_7_DAYS, LAST_30_DAYS, etc.)

        Returns:
            Optional[UsageDashboard]: Usage dashboard or None if failed
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetUsageDashboard($billingAccountId: ID!, $period: AnalyticsPeriod) {  # noqa: E501
                    getUsageDashboard(billingAccountId: $billingAccountId, period: $period) {
                        totalUsage
                        totalQuotas
                        activeQuotas
                        healthyQuotas
                        warningQuotas
                        criticalQuotas
                        exhaustedQuotas
                        topUsageByQuota {
                            quotaName
                            quotaId
                            usage
                            limit
                            percentage
                            status
                        }
                        overallTrends {
                            growthRate
                            predictedUsage
                            averageDailyUsage
                        }
                        recentActivities {
                            id
                            quotaName
                            description
                            amount
                            timestamp
                            tags
                        }
                    }
                }
            """
            )

            variables = {
                "billingAccountId": billing_account_id,
                "period": period,
            }

            result = client.execute(query, variable_values=variables)
            return result.get("getUsageDashboard")
        except Exception as e:
            print(f"Get usage dashboard failed: {str(e)}")
            return None

    async def get_available_tags_and_resource_types(
        self, billing_account_id: str, token: str
    ) -> Optional[TagsAndResourceTypes]:
        """
        Get available tags and resource types for filtering.

        Args:
            billing_account_id (str): ID of the billing account
            token (str): Authentication token

        Returns:
            Optional[TagsAndResourceTypes]: Available tags and resource types or None if failed  # noqa: E501
        """
        try:
            client = self.get_client(token)
            query = gql(
                """
                query GetAvailableTagsAndResourceTypes($billingAccountId: ID!) {  # noqa: E501
                    getAvailableTagsAndResourceTypes(billingAccountId: $billingAccountId) {
                        tags
                        resourceTypes
                    }
                }
            """
            )

            variables = {"billingAccountId": billing_account_id}

            result = client.execute(query, variable_values=variables)
            return result.get("getAvailableTagsAndResourceTypes")
        except Exception as e:
            print(f"Get available tags and resource types failed: {str(e)}")
            return None

    # Usage Mutation Operations
    async def add_usage(
        self,
        billing_account_id: str,
        quota_name: str,
        value: int,
        description: str,
        token: str,
        tags: Optional[Any] = None,
        hash_value: Optional[str] = None,
    ) -> bool:
        """
        Adds usage to a quota.

        Args:
            billing_account_id (str): ID of the billing account
            quota_name (str): Name of the quota
            value (int): Usage amount to add
            description (str): Description of the usage
            token (str): Authentication token
            tags (Any, optional): Additional tags
            hash_value (str, optional): Unique hash for deduplication

        Returns:
            bool: True if usage addition succeeded, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation AddUsage(
                    $billingAccountId: ID!
                    $quotaName: String!
                    $value: Int!
                    $description: String!
                    $tags: JSON
                    $hash: String
                ) {
                    addUsage(
                        billingAccountId: $billingAccountId
                        quotaName: $quotaName
                        value: $value
                        description: $description
                        tags: $tags
                        hash: $hash
                    )
                }
            """
            )

            variables = {
                "billingAccountId": billing_account_id,
                "quotaName": quota_name,
                "value": value,
                "description": description,
            }

            if tags:
                variables["tags"] = tags
            if hash_value:
                variables["hash"] = hash_value

            result = client.execute(mutation, variable_values=variables)
            return result.get("addUsage", False)
        except Exception as e:
            print(f"Add usage failed: {str(e)}")
            return False

    async def free_up_usage(
        self,
        billing_account_id: str,
        quota_name: str,
        value: int,
        token: str,
        description: Optional[str] = None,
        tags: Optional[Any] = None,
        hash_value: Optional[str] = None,
    ) -> bool:
        """
        Frees up usage from a quota (reduces usage).

        Args:
            billing_account_id (str): ID of the billing account
            quota_name (str): Name of the quota
            value (int): Usage amount to free up
            token (str): Authentication token
            description (str, optional): Description of the freed usage
            tags (Any, optional): Additional tags
            hash_value (str, optional): Unique hash for deduplication

        Returns:
            bool: True if usage freed up successfully, False otherwise
        """
        try:
            client = self.get_client(token)
            mutation = gql(
                """
                mutation FreeUpUsage(
                    $billingAccountId: ID!
                    $quotaName: String!
                    $value: Int!
                    $description: String
                    $tags: JSON
                    $hash: String
                ) {
                    freeUpUsage(
                        billingAccountId: $billingAccountId
                        quotaName: $quotaName
                        value: $value
                        description: $description
                        tags: $tags
                        hash: $hash
                    )
                }
            """
            )

            variables = {
                "billingAccountId": billing_account_id,
                "quotaName": quota_name,
                "value": value,
            }

            if description:
                variables["description"] = description
            if tags:
                variables["tags"] = tags
            if hash_value:
                variables["hash"] = hash_value

            result = client.execute(mutation, variable_values=variables)
            return result.get("freeUpUsage", False)
        except Exception as e:
            print(f"Free up usage failed: {str(e)}")
            return False


# Create convenience functions that use a default client
_default_client = None


def initialize(graphql_endpoint: str):
    """
    Initialize the default Usage client with the GraphQL endpoint.

    Args:
        graphql_endpoint (str): The GraphQL endpoint URL
    """
    global _default_client
    _default_client = UsageClient(graphql_endpoint)


def get_client() -> UsageClient:
    """Get the default Usage client."""
    if _default_client is None:
        raise RuntimeError("Usage client not initialized. Call initialize() first.")
    return _default_client


# Convenience functions that use the default client
async def get_all_quota_assignments(*args, **kwargs):
    return await get_client().get_all_quota_assignments(*args, **kwargs)


async def get_quota_assignments_with_analytics(*args, **kwargs):
    return await get_client().get_quota_assignments_with_analytics(*args, **kwargs)


async def get_quota_usage_and_limit(*args, **kwargs):
    return await get_client().get_quota_usage_and_limit(*args, **kwargs)


async def check_quota_exhausted(*args, **kwargs):
    return await get_client().check_quota_exhausted(*args, **kwargs)


async def get_quota_usage_details(*args, **kwargs):
    return await get_client().get_quota_usage_details(*args, **kwargs)


async def get_subscription_usage_overview(*args, **kwargs):
    return await get_client().get_subscription_usage_overview(*args, **kwargs)


async def get_quota_analytics(*args, **kwargs):
    return await get_client().get_quota_analytics(*args, **kwargs)


async def get_usage_dashboard(*args, **kwargs):
    return await get_client().get_usage_dashboard(*args, **kwargs)


async def get_available_tags_and_resource_types(*args, **kwargs):
    return await get_client().get_available_tags_and_resource_types(*args, **kwargs)


async def add_usage(*args, **kwargs):
    return await get_client().add_usage(*args, **kwargs)


async def free_up_usage(*args, **kwargs):
    return await get_client().free_up_usage(*args, **kwargs)
