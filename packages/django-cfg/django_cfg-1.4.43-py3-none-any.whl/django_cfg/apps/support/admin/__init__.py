"""
Support admin interfaces using Django-CFG admin system.

Refactored admin interfaces with Material Icons and optimized queries.
"""

from .filters import MessageSenderEmailFilter, TicketUserEmailFilter, TicketUserNameFilter
from .resources import MessageResource, TicketResource
from .support_admin import MessageAdmin, TicketAdmin

__all__ = [
    'TicketAdmin',
    'MessageAdmin',
    'TicketUserEmailFilter',
    'TicketUserNameFilter',
    'MessageSenderEmailFilter',
    'TicketResource',
    'MessageResource',
]
