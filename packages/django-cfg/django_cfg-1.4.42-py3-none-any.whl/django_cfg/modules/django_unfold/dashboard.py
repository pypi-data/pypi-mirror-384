"""
Dashboard Manager for Django CFG Unfold

Manages dashboard configuration, widgets, and navigation
based on the working configuration from the old version.
"""

from typing import Any, Dict, List

from django_cfg.modules.django_admin.icons import Icons

from ..base import BaseCfgModule
from .models.dashboard import StatCard, StatsCardsWidget
from .models.navigation import NavigationItem, NavigationSection


class DashboardManager(BaseCfgModule):
    """
    Dashboard configuration manager for Unfold.    
    """

    def __init__(self, config=None):
        """Initialize dashboard manager."""
        super().__init__()
        # Lazy load config to avoid circular import during settings generation
        self._config = config
        self._config_loaded = config is not None

    @property
    def config(self):
        """Lazy load config on first access."""
        if not self._config_loaded:
            try:
                self._config = self.get_config()
            except Exception:
                # Config cannot be loaded (e.g., during settings generation)
                # Set to None and mark as loaded to avoid repeated attempts
                self._config = None
            finally:
                self._config_loaded = True
        return self._config

    @staticmethod
    def _get_default_dropdown_items() -> List[Dict[str, Any]]:
        """Get default dropdown menu items for Unfold admin (lazy import to avoid circular imports)."""
        from django_cfg.config import get_default_dropdown_items
        dropdown_items = get_default_dropdown_items()

        # Convert SiteDropdownItem objects to dictionaries for Unfold
        return [item.to_dict() for item in dropdown_items]


    def get_navigation_config(self) -> List[Dict[str, Any]]:
        """Get complete default navigation configuration for Unfold sidebar."""
        navigation_sections = [
            NavigationSection(
                title="Dashboard",
                separator=True,
                collapsible=True,
                items=[
                    NavigationItem(title="Overview", icon=Icons.DASHBOARD, link="/admin/"),
                    NavigationItem(title="Settings", icon=Icons.SETTINGS, link="/admin/constance/config/"),
                    NavigationItem(title="Health Check", icon=Icons.HEALTH_AND_SAFETY, link="/cfg/health/drf/"),
                    NavigationItem(title="Endpoints Status", icon=Icons.API, link="/cfg/endpoints/drf/"),
                ]
            ),
        ]

        # Add Operations section (System & Monitoring tools)
        operations_items = []

        # RPC Dashboard (if enabled)
        if self.is_rpc_enabled():
            operations_items.append(
                NavigationItem(title="IPC/RPC Dashboard", icon=Icons.MONITOR_HEART, link="/cfg/ipc/admin/")
            )

        # Background Tasks (if enabled)
        if self.should_enable_tasks():
            operations_items.extend([
                NavigationItem(title="Background Tasks", icon=Icons.TASK, link="/admin/django_dramatiq/task/"),
                NavigationItem(title="Task Dashboard", icon=Icons.SETTINGS_APPLICATIONS, link="/cfg/tasks/admin/dashboard/"),
            ])

        # Maintenance Mode (if enabled)
        if self.is_maintenance_enabled():
            operations_items.append(
                NavigationItem(title="Maintenance", icon=Icons.BUILD, link="/admin/maintenance/cloudflaresite/")
            )

        # Add Operations section if there are any items
        if operations_items:
            navigation_sections.append(NavigationSection(
                title="Operations",
                separator=True,
                collapsible=True,
                items=operations_items
            ))

        # Add Accounts section if enabled
        if self.is_accounts_enabled():
            navigation_sections.append(NavigationSection(
                title="Users & Access",
                separator=True,
                collapsible=True,
                items=[
                    NavigationItem(title="Users", icon=Icons.PEOPLE, link="/admin/django_cfg_accounts/customuser/"),
                    NavigationItem(title="User Groups", icon=Icons.GROUP, link="/admin/auth/group/"),
                    NavigationItem(title="OTP Secrets", icon=Icons.SECURITY, link="/admin/django_cfg_accounts/otpsecret/"),
                    NavigationItem(title="Registration Sources", icon=Icons.LINK, link="/admin/django_cfg_accounts/registrationsource/"),
                    NavigationItem(title="User Registration Sources", icon=Icons.PERSON, link="/admin/django_cfg_accounts/userregistrationsource/"),
                ]
            ))

        # Add Support section if enabled
        if self.is_support_enabled():
            navigation_sections.append(NavigationSection(
                title="Support",
                separator=True,
                collapsible=True,
                items=[
                    NavigationItem(title="Tickets", icon=Icons.SUPPORT_AGENT, link="/admin/django_cfg_support/ticket/"),
                    NavigationItem(title="Messages", icon=Icons.CHAT, link="/admin/django_cfg_support/message/"),
                ]
            ))

        # Add Newsletter section if enabled
        if self.is_newsletter_enabled():
            navigation_sections.append(NavigationSection(
                title="Newsletter",
                separator=True,
                collapsible=True,
                items=[
                    NavigationItem(title="Newsletters", icon=Icons.EMAIL, link="/admin/django_cfg_newsletter/newsletter/"),
                    NavigationItem(title="Subscriptions", icon=Icons.PERSON_ADD, link="/admin/django_cfg_newsletter/newslettersubscription/"),
                    NavigationItem(title="Campaigns", icon=Icons.CAMPAIGN, link="/admin/django_cfg_newsletter/newslettercampaign/"),
                    NavigationItem(title="Email Logs", icon=Icons.MAIL_OUTLINE, link="/admin/django_cfg_newsletter/emaillog/"),
                ]
            ))

        # Add Leads section if enabled
        if self.is_leads_enabled():
            navigation_sections.append(NavigationSection(
                title="Leads",
                separator=True,
                collapsible=True,
                items=[
                    NavigationItem(title="Leads", icon=Icons.CONTACT_PAGE, link="/admin/django_cfg_leads/lead/"),
                ]
            ))

        # Add Agents section if enabled
        if self.is_agents_enabled():
            navigation_sections.append(NavigationSection(
                title="AI Agents",
                separator=True,
                collapsible=True,
                items=[
                    NavigationItem(title="Agent Definitions", icon=Icons.SMART_TOY, link="/admin/django_cfg_agents/agentdefinition/"),
                    NavigationItem(title="Agent Templates", icon=Icons.DESCRIPTION, link="/admin/django_cfg_agents/agenttemplate/"),
                    NavigationItem(title="Agent Executions", icon=Icons.PLAY_ARROW, link="/admin/django_cfg_agents/agentexecution/"),
                    NavigationItem(title="Workflow Executions", icon=Icons.AUTORENEW, link="/admin/django_cfg_agents/workflowexecution/"),
                    NavigationItem(title="Tool Executions", icon=Icons.BUILD, link="/admin/django_cfg_agents/toolexecution/"),
                    NavigationItem(title="Toolset Configurations", icon=Icons.SETTINGS, link="/admin/django_cfg_agents/toolsetconfiguration/"),
                ]
            ))

        # Add Knowledge Base section if enabled
        if self.is_knowbase_enabled():
            navigation_sections.append(NavigationSection(
                title="Knowledge Base",
                separator=True,
                collapsible=True,
                items=[
                    NavigationItem(title="Document Categories", icon=Icons.FOLDER, link="/admin/django_cfg_knowbase/documentcategory/"),
                    NavigationItem(title="Documents", icon=Icons.DESCRIPTION, link="/admin/django_cfg_knowbase/document/"),
                    NavigationItem(title="Document Chunks", icon=Icons.TEXT_SNIPPET, link="/admin/django_cfg_knowbase/documentchunk/"),
                    NavigationItem(title="Document Archives", icon=Icons.ARCHIVE, link="/admin/django_cfg_knowbase/documentarchive/"),
                    NavigationItem(title="Archive Items", icon=Icons.FOLDER_OPEN, link="/admin/django_cfg_knowbase/archiveitem/"),
                    NavigationItem(title="Archive Item Chunks", icon=Icons.SNIPPET_FOLDER, link="/admin/django_cfg_knowbase/archiveitemchunk/"),
                    NavigationItem(title="External Data", icon=Icons.CLOUD_SYNC, link="/admin/django_cfg_knowbase/externaldata/"),
                    NavigationItem(title="External Data Chunks", icon=Icons.AUTO_AWESOME_MOTION, link="/admin/django_cfg_knowbase/externaldatachunk/"),
                    NavigationItem(title="Chat Sessions", icon=Icons.CHAT, link="/admin/django_cfg_knowbase/chatsession/"),
                    NavigationItem(title="Chat Messages", icon=Icons.MESSAGE, link="/admin/django_cfg_knowbase/chatmessage/"),
                ]
            ))

        # Add Payments section if enabled (v2.0)
        if self.is_payments_enabled():
            payments_items = [
                # Core payment models (v2.0)
                NavigationItem(title="Payments", icon=Icons.ACCOUNT_BALANCE, link="/admin/payments/payment/"),
                NavigationItem(title="Currencies", icon=Icons.CURRENCY_BITCOIN, link="/admin/payments/currency/"),
                NavigationItem(title="User Balances", icon=Icons.ACCOUNT_BALANCE_WALLET, link="/admin/payments/userbalance/"),
                NavigationItem(title="Transactions", icon=Icons.RECEIPT_LONG, link="/admin/payments/transaction/"),
                NavigationItem(title="Withdrawal Requests", icon=Icons.DOWNLOAD, link="/admin/payments/withdrawalrequest/"),
            ]

            navigation_sections.append(NavigationSection(
                title="Payments",
                separator=True,
                collapsible=True,
                items=payments_items
            ))

        # Convert all NavigationSection objects to dictionaries
        return [section.to_dict() for section in navigation_sections]



    def get_unfold_config(self) -> Dict[str, Any]:
        """Get complete Unfold configuration based on working old version."""
        return {
            # Site branding and appearance
            "SITE_TITLE": "Admin",
            "SITE_HEADER": "Admin",
            "SITE_SUBHEADER": "",
            "SITE_URL": "/",
            "SITE_SYMBOL": "dashboard",

            # UI visibility controls
            "SHOW_HISTORY": True,
            "SHOW_VIEW_ON_SITE": True,
            "SHOW_BACK_BUTTON": False,

            # Dashboard callback
            "DASHBOARD_CALLBACK": "api.dashboard.callbacks.main_dashboard_callback",

            # Theme configuration
            "THEME": None,  # Auto-detect or force "dark"/"light"

            # Login page customization
            "LOGIN": {
                "redirect_after": lambda request: "/admin/",
            },

            # Design system
            "BORDER_RADIUS": "8px",
            "COLORS": {
                "base": {
                    "50": "249, 250, 251",
                    "100": "243, 244, 246",
                    "200": "229, 231, 235",
                    "300": "209, 213, 219",
                    "400": "156, 163, 175",
                    "500": "107, 114, 128",
                    "600": "75, 85, 99",
                    "700": "55, 65, 81",
                    "800": "31, 41, 55",
                    "900": "17, 24, 39",
                    "950": "3, 7, 18",
                },
                "primary": {
                    "50": "239, 246, 255",
                    "100": "219, 234, 254",
                    "200": "191, 219, 254",
                    "300": "147, 197, 253",
                    "400": "96, 165, 250",
                    "500": "59, 130, 246",
                    "600": "37, 99, 235",
                    "700": "29, 78, 216",
                    "800": "30, 64, 175",
                    "900": "30, 58, 138",
                    "950": "23, 37, 84",
                },
                "font": {
                    "subtle-light": "var(--color-base-500)",
                    "subtle-dark": "var(--color-base-400)",
                    "default-light": "var(--color-base-600)",
                    "default-dark": "var(--color-base-300)",
                    "important-light": "var(--color-base-900)",
                    "important-dark": "var(--color-base-100)",
                },
            },

            # Sidebar navigation - KEY STRUCTURE!
            "SIDEBAR": {
                "show_search": True,
                "command_search": True,
                "show_all_applications": True,
                "navigation": self.get_navigation_config(),
            },

            # Site dropdown menu - handled by config.py to allow extending
            # "SITE_DROPDOWN": self._get_default_dropdown_items(),

            # Command interface
            "COMMAND": {
                "search_models": True,
                "show_history": True,
            },

            # Multi-language support - DISABLED
            "SHOW_LANGUAGES": False,
        }

    def get_widgets_config(self) -> List[Dict[str, Any]]:
        """Get dashboard widgets configuration using Pydantic models."""
        # Create system overview widget with StatCard models
        system_overview_widget = StatsCardsWidget(
            title="System Overview",
            cards=[
                StatCard(
                    title="CPU Usage",
                    value="{{ cpu_percent }}%",
                    icon=Icons.MEMORY,
                    color="blue",
                ),
                StatCard(
                    title="Memory Usage",
                    value="{{ memory_percent }}%",
                    icon=Icons.STORAGE,
                    color="green",
                ),
                StatCard(
                    title="Disk Usage",
                    value="{{ disk_percent }}%",
                    icon=Icons.FOLDER,
                    color="orange",
                ),
            ]
        )

        # Convert to dictionaries for Unfold
        return [system_overview_widget.to_dict()]


# Lazy initialization to avoid circular imports
_dashboard_manager = None

def get_dashboard_manager() -> DashboardManager:
    """Get the global dashboard manager instance."""
    global _dashboard_manager
    if _dashboard_manager is None:
        _dashboard_manager = DashboardManager()
    return _dashboard_manager
