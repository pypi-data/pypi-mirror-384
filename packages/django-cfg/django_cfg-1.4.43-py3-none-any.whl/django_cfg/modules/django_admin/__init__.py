"""
Django Admin Utilities - Universal HTML Builder System

Clean, type-safe admin utilities with no HTML duplication.
"""

# Core utilities
# Decorators
from .decorators import action, display

# Icons
from .icons import IconCategories, Icons

# Admin mixins
from .mixins.display_mixin import DisplayMixin
from .mixins.optimization_mixin import OptimizedModelAdmin
from .mixins.standalone_actions_mixin import StandaloneActionsMixin, standalone_action
from .models.action_models import ActionConfig, ActionVariant
from .models.badge_models import BadgeConfig, BadgeVariant, StatusBadgeConfig

# Configuration models
from .models.display_models import DateTimeDisplayConfig, MoneyDisplayConfig, UserDisplayConfig
from .utils.badges import CounterBadge, ProgressBadge, StatusBadge
from .utils.displays import DateTimeDisplay, MoneyDisplay, StatusDisplay, UserDisplay

__version__ = "1.0.0"

__all__ = [
    # Display utilities
    "UserDisplay",
    "MoneyDisplay",
    "StatusDisplay",
    "DateTimeDisplay",

    # Badge utilities
    "StatusBadge",
    "ProgressBadge",
    "CounterBadge",

    # Icons
    "Icons",
    "IconCategories",

    # Admin mixins
    "OptimizedModelAdmin",
    "DisplayMixin",
    "StandaloneActionsMixin",
    "standalone_action",

    # Configuration models
    "UserDisplayConfig",
    "MoneyDisplayConfig",
    "DateTimeDisplayConfig",
    "BadgeConfig",
    "BadgeVariant",
    "StatusBadgeConfig",
    "ActionVariant",
    "ActionConfig",

    # Decorators
    "display",
    "action",
]
