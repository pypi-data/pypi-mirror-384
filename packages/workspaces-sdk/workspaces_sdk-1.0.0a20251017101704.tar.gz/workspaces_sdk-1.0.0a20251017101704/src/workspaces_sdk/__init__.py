"""
Workspaces SDK - Python SDK for Workspaces API with Enhanced Actor-based RBAC

This SDK provides comprehensive access to the Workspaces platform with full support  # noqa: E501
for the Enhanced Actor-based RBAC system including AI agent management and delegation,  # noqa: E501
plus complete billing, payment, subscription management, configuration, quota, usage,  # noqa: E501
tracking, store management, organization, workspace, newsletter functionality and project management functionality.  # noqa: E501
"""

from .addon import AddonClient
from .analytics import AnalyticsClient
from .billing import BillingClient
from .client import WorkspaceClient
from .configuration import ConfigClient
from .credit import CreditClient
from .data_export import DataExportClient
from .newsletter import NewsletterClient
from .notification import NotificationClient
from .organization import OrganizationClient
from .payment import PaymentClient
from .plan import PlanClient
from .project import ProjectClient
from .quota import QuotaClient
from .rbac import RBACClient
from .settings import SettingsClient
from .store import StoreClient
from .team import TeamClient
from .usage import UsageClient
from .workspace import WorkspaceClient as WorkspaceModuleClient

__version__ = "1.0.0"
__all__ = [
    "WorkspaceClient",
    "RBACClient",
    "AddonClient",
    "BillingClient",
    "CreditClient",
    "PaymentClient",
    "PlanClient",
    "ConfigClient",
    "QuotaClient",
    "UsageClient",
    "StoreClient",
    "NotificationClient",
    "NewsletterClient",
    "DataExportClient",
    "SettingsClient",
    "AnalyticsClient",
    "OrganizationClient",
    "WorkspaceModuleClient",
    "ProjectClient",
    "TeamClient",
]
# Trigger workflow - testing CI/CD
# Trigger workflow - testing grep fix
# Trigger workflow - testing PyPI version fix
