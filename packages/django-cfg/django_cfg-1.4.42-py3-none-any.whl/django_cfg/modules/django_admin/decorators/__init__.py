"""
Django Admin Decorators - Wrappers for Unfold decorators.

Provides consistent, type-safe decorators with our admin utilities integration.
"""

from .actions import action
from .display import display

__all__ = [
    'display',
    'action',
]
