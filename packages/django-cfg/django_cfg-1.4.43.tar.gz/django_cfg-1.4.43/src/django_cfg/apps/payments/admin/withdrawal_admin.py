"""
Withdrawal Admin interface for Payments v2.0.

Manual approval workflow for withdrawal requests.
"""

from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from django_cfg.modules.django_admin import (
    ActionVariant,
    DateTimeDisplayConfig,
    DisplayMixin,
    Icons,
    MoneyDisplayConfig,
    OptimizedModelAdmin,
    StatusBadgeConfig,
    action,
    display,
)
from django_cfg.modules.django_admin.utils.badges import StatusBadge
from django_cfg.modules.django_logging import get_logger

from ..models import WithdrawalRequest
from .filters import RecentActivityFilter, WithdrawalStatusFilter

logger = get_logger("withdrawal_admin")


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(OptimizedModelAdmin, DisplayMixin, ModelAdmin):
    """
    Withdrawal Request admin for Payments v2.0.

    Features:
    - Manual approval workflow
    - Admin tracking
    - Status management
    """

    # Performance optimization
    select_related_fields = ['user', 'currency', 'admin_user']
    annotations = {}

    # List configuration
    list_display = [
        'withdrawal_id_display',
        'user_display',
        'amount_display',
        'currency_display',
        'status_display',
        'admin_display',
        'created_display'
    ]

    list_filter = [
        WithdrawalStatusFilter,
        RecentActivityFilter,
        'currency',
        'status',
        'created_at'
    ]

    search_fields = [
        'id',
        'internal_withdrawal_id',
        'user__username',
        'user__email',
        'wallet_address',
        'admin_user__username'
    ]

    readonly_fields = [
        'id',
        'internal_withdrawal_id',
        'created_at',
        'updated_at',
        'approved_at',
        'completed_at',
        'rejected_at',
        'cancelled_at',
        'status_changed_at',
        'withdrawal_details_display'
    ]

    fieldsets = (
        ('Request Information', {
            'fields': (
                'id',
                'internal_withdrawal_id',
                'user',
                'status',
                'amount_usd',
                'currency',
                'wallet_address'
            )
        }),
        ('Fee Calculation', {
            'fields': (
                'network_fee_usd',
                'service_fee_usd',
                'total_fee_usd',
                'final_amount_usd'
            ),
            'classes': ('collapse',)
        }),
        ('Admin Actions', {
            'fields': (
                'admin_user',
                'admin_notes'
            )
        }),
        ('Transaction Details', {
            'fields': (
                'transaction_hash',
                'crypto_amount'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'approved_at',
                'completed_at',
                'rejected_at',
                'cancelled_at',
                'status_changed_at'
            ),
            'classes': ('collapse',)
        }),
        ('Withdrawal Details', {
            'fields': ('withdrawal_details_display',),
            'classes': ('collapse',)
        })
    )

    # Register actions
    actions = ['approve_withdrawals', 'reject_withdrawals', 'mark_as_completed']

    # Display methods
    @display(description="Withdrawal ID")
    def withdrawal_id_display(self, obj):
        """Withdrawal ID display with badge."""
        # Show internal_withdrawal_id if available, otherwise use UUID
        withdrawal_id = obj.internal_withdrawal_id if obj.internal_withdrawal_id else str(obj.id)[:16]
        return StatusBadge.create(
            text=withdrawal_id,
            variant="info"
        )

    @display(description="User", header=True)
    def user_display(self, obj):
        """User display with avatar."""
        return self.display_user_with_avatar(obj, 'user')

    @display(description="Amount")
    def amount_display(self, obj):
        """Amount display in USD."""
        config = MoneyDisplayConfig(
            currency="USD",
            show_sign=False,
            thousand_separator=True
        )
        return self.display_money_amount(obj, 'amount_usd', config)

    @display(description="Currency")
    def currency_display(self, obj):
        """Currency display with token+network."""
        if not obj.currency:
            return StatusBadge.create(text="N/A", variant="secondary")

        # Display token and network
        text = obj.currency.token
        if obj.currency.network:
            text += f" ({obj.currency.network})"

        config = StatusBadgeConfig(show_icons=True, icon=Icons.CURRENCY_BITCOIN)
        return StatusBadge.create(text=text, variant="primary", config=config)

    @display(description="Status", label=True)
    def status_display(self, obj):
        """Status display with withdrawal-specific colors."""
        status_mappings = {
            'pending': 'warning',
            'approved': 'info',
            'processing': 'primary',
            'completed': 'success',
            'rejected': 'danger',
            'cancelled': 'secondary'
        }

        config = StatusBadgeConfig(
            custom_mappings=status_mappings,
            show_icons=True
        )

        return self.display_status_auto(obj, 'status', config)

    @display(description="Admin")
    def admin_display(self, obj):
        """Admin user display."""
        if not obj.admin_user:
            return "-"
        return self.display_user_simple(obj, 'admin_user')

    @display(description="Created")
    def created_display(self, obj):
        """Created time display."""
        return self.display_datetime_relative(
            obj,
            'created_at',
            DateTimeDisplayConfig(show_relative=True, show_seconds=False)
        )

    # Readonly field displays
    def withdrawal_details_display(self, obj):
        """Detailed withdrawal information for detail view."""
        if not obj.pk:
            return "Save to see details"

        # Build details HTML
        details = []

        details.append(f"<strong>Withdrawal ID:</strong> {obj.id}")
        details.append(f"<strong>User:</strong> {obj.user.username} ({obj.user.email})")
        details.append(f"<strong>Amount:</strong> ${obj.amount_usd:.2f} USD")
        details.append(f"<strong>Currency:</strong> {obj.currency.code}")
        details.append(f"<strong>Wallet Address:</strong> <code>{obj.wallet_address}</code>")
        details.append(f"<strong>Status:</strong> {obj.get_status_display()}")

        if obj.admin_user:
            details.append(f"<strong>Approved By:</strong> {obj.admin_user.username}")

        if obj.admin_notes:
            details.append(f"<strong>Admin Notes:</strong> {obj.admin_notes}")

        if obj.transaction_hash:
            details.append(f"<strong>Transaction Hash:</strong> <code>{obj.transaction_hash}</code>")

        if obj.crypto_amount:
            details.append(f"<strong>Crypto Amount:</strong> {obj.crypto_amount:.8f} {obj.currency.token}")

        if obj.approved_at:
            details.append(f"<strong>Approved At:</strong> {obj.approved_at}")

        if obj.completed_at:
            details.append(f"<strong>Completed At:</strong> {obj.completed_at}")

        return format_html("<br>".join(details))

    withdrawal_details_display.short_description = "Withdrawal Details"

    # Actions
    @action(description="Approve withdrawals", variant=ActionVariant.SUCCESS)
    def approve_withdrawals(self, request, queryset):
        """Approve selected withdrawal requests."""
        from django.utils import timezone

        updated = queryset.filter(status='pending').update(
            status='approved',
            admin_user=request.user,
            approved_at=timezone.now(),
            status_changed_at=timezone.now()
        )

        self.message_user(
            request,
            f"Successfully approved {updated} withdrawal(s).",
            level='SUCCESS'
        )

    @action(description="Reject withdrawals", variant=ActionVariant.DANGER)
    def reject_withdrawals(self, request, queryset):
        """Reject selected withdrawal requests."""
        from django.utils import timezone

        updated = queryset.filter(status='pending').update(
            status='rejected',
            admin_user=request.user,
            admin_notes="Rejected via bulk action",
            rejected_at=timezone.now(),
            status_changed_at=timezone.now()
        )

        self.message_user(
            request,
            f"Successfully rejected {updated} withdrawal(s).",
            level='WARNING'
        )

    @action(description="Mark as completed", variant=ActionVariant.SUCCESS)
    def mark_as_completed(self, request, queryset):
        """Mark approved/processing withdrawals as completed."""
        from django.utils import timezone

        updated = queryset.filter(status__in=['approved', 'processing']).update(
            status='completed',
            completed_at=timezone.now(),
            status_changed_at=timezone.now()
        )

        self.message_user(
            request,
            f"Successfully marked {updated} withdrawal(s) as completed.",
            level='SUCCESS'
        )
