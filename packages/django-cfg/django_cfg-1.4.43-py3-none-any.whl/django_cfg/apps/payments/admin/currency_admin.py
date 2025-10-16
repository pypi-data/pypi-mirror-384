"""
Currency Admin interface for Payments v2.0.

Simple currency management for NowPayments tokens+networks.
"""

from django.contrib import admin
from unfold.admin import ModelAdmin

from django_cfg.modules.django_admin import (
    ActionVariant,
    DisplayMixin,
    Icons,
    OptimizedModelAdmin,
    StatusBadgeConfig,
    action,
    display,
)
from django_cfg.modules.django_admin.utils.badges import StatusBadge
from django_cfg.modules.django_logging import get_logger

from ..models import Currency

logger = get_logger("currency_admin")


@admin.register(Currency)
class CurrencyAdmin(OptimizedModelAdmin, DisplayMixin, ModelAdmin):
    """Currency admin for Payments v2.0 (simplified token+network model)."""

    # Performance optimization
    select_related_fields = []
    prefetch_related_fields = []

    list_display = [
        'code_display',
        'name_display',
        'token_display',
        'network_display',
        'status_display',
        'sort_order_display',
        'updated_display'
    ]

    list_filter = [
        'is_active',
        'token',
        'network',
        'updated_at'
    ]

    search_fields = ['code', 'name', 'token', 'network']

    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Currency Information', {
            'fields': (
                'code',
                'name',
                'token',
                'network',
                'symbol'
            )
        }),
        ('Provider Settings', {
            'fields': (
                'provider',
                'min_amount_usd',
                'decimal_places'
            )
        }),
        ('Display Settings', {
            'fields': (
                'is_active',
                'sort_order'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    # Register bulk actions
    actions = ['activate_currencies', 'deactivate_currencies']

    @display(description="Code")
    def code_display(self, obj):
        """Currency code display with badge."""
        config = StatusBadgeConfig(show_icons=True, icon=Icons.CURRENCY_BITCOIN)
        return StatusBadge.create(text=obj.code, variant="primary", config=config)

    @display(description="Name")
    def name_display(self, obj):
        """Currency name display."""
        return obj.name or "-"

    @display(description="Token")
    def token_display(self, obj):
        """Token display."""
        config = StatusBadgeConfig(show_icons=True, icon=Icons.ATTACH_MONEY)
        return StatusBadge.create(text=obj.token, variant="info", config=config)

    @display(description="Network")
    def network_display(self, obj):
        """Network display."""
        if not obj.network:
            return StatusBadge.create(text="N/A", variant="secondary")

        config = StatusBadgeConfig(show_icons=True, icon=Icons.CLOUD)
        return StatusBadge.create(text=obj.network, variant="warning", config=config)

    @display(description="Status", label=True)
    def status_display(self, obj):
        """Status display with appropriate icons."""
        status = "Active" if obj.is_active else "Inactive"

        config = StatusBadgeConfig(
            custom_mappings={
                "Active": "success",
                "Inactive": "secondary"
            },
            show_icons=True,
            icon=Icons.CHECK_CIRCLE if obj.is_active else Icons.CANCEL
        )

        return self.display_status_auto(
            type('obj', (), {'status': status})(),
            'status',
            config
        )

    @display(description="Sort Order")
    def sort_order_display(self, obj):
        """Sort order display."""
        return obj.sort_order

    @display(description="Updated")
    def updated_display(self, obj):
        """Updated time display."""
        return self.display_datetime_relative(obj, 'updated_at')

    # Bulk actions
    @action(description="Activate currencies", variant=ActionVariant.SUCCESS)
    def activate_currencies(self, request, queryset):
        """Activate selected currencies."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} currency(ies).", level='SUCCESS')

    @action(description="Deactivate currencies", variant=ActionVariant.WARNING)
    def deactivate_currencies(self, request, queryset):
        """Deactivate selected currencies."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {updated} currency(ies).", level='WARNING')
