"""
Balance Admin interfaces for Payments v2.0.

Clean, modern admin interfaces for balance and transactions.
"""

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from django_cfg.modules.django_admin import (
    ActionVariant,
    DateTimeDisplayConfig,
    DisplayMixin,
    MoneyDisplayConfig,
    OptimizedModelAdmin,
    action,
    display,
)
from django_cfg.modules.django_admin.utils.badges import StatusBadge
from django_cfg.modules.django_logging import get_logger

from ..models import Transaction, UserBalance
from .filters import BalanceRangeFilter, RecentActivityFilter, TransactionTypeFilter

logger = get_logger("balance_admin")


@admin.register(UserBalance)
class UserBalanceAdmin(OptimizedModelAdmin, DisplayMixin, ModelAdmin):
    """
    UserBalance admin for Payments v2.0.

    Features:
    - Clean display utilities
    - Automatic query optimization
    - ORM-based balance tracking
    """

    # Performance optimization
    select_related_fields = ['user']
    annotations = {
        'transaction_count': Count('user__payment_transactions_v2')
    }

    # List configuration
    list_display = [
        'user_display',
        'balance_display',
        'status_display',
        'deposited_display',
        'withdrawn_display',
        'transaction_count_display',
        'updated_display'
    ]

    list_filter = [
        BalanceRangeFilter,
        RecentActivityFilter,
        'created_at',
        'updated_at',
    ]

    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name'
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'last_transaction_at',
        'balance_breakdown_display'
    ]

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Balance Details', {
            'fields': (
                'balance_usd',
                'total_deposited',
                'total_withdrawn'
            )
        }),
        ('Timestamps', {
            'fields': (
                'last_transaction_at',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
        ('Balance Breakdown', {
            'fields': ('balance_breakdown_display',),
            'classes': ('collapse',)
        })
    )

    # Register actions
    actions = ['reset_zero_balances']

    # Display methods
    @display(description="User", header=True)
    def user_display(self, obj):
        """User display with avatar using Unfold header feature."""
        if not obj.user:
            return ["No user", "", ""]

        return [
            obj.user.get_full_name() or obj.user.username,
            obj.user.email,
            obj.user.get_full_name()[:2].upper() if obj.user.get_full_name() else obj.user.username[:2].upper()
        ]

    @display(description="Balance", ordering="balance_usd")
    def balance_display(self, obj):
        """Balance display using utilities."""
        return self.display_money_amount(
            obj,
            'balance_usd',
            MoneyDisplayConfig(currency="USD", show_sign=False)
        )

    @display(description="Status", label={
        "Empty": "danger",
        "Low Balance": "warning",
        "Active": "success",
        "High Balance": "info"
    })
    def status_display(self, obj):
        """Status display using Unfold label feature."""
        if obj.balance_usd <= 0:
            return "Empty"
        elif obj.balance_usd < 10:
            return "Low Balance"
        elif obj.balance_usd < 100:
            return "Active"
        else:
            return "High Balance"

    @display(description="Total Deposited")
    def deposited_display(self, obj):
        """Total deposited display."""
        return self.display_money_amount(
            obj,
            'total_deposited',
            MoneyDisplayConfig(currency="USD", show_sign=False)
        )

    @display(description="Total Withdrawn")
    def withdrawn_display(self, obj):
        """Total withdrawn display."""
        return self.display_money_amount(
            obj,
            'total_withdrawn',
            MoneyDisplayConfig(currency="USD", show_sign=False)
        )

    @display(description="Transactions")
    def transaction_count_display(self, obj):
        """Transaction count using utilities."""
        count = getattr(obj, 'transaction_count', 0)
        return self.display_count_simple(
            obj,
            'transaction_count',
            'transactions'
        )

    @display(description="Updated")
    def updated_display(self, obj):
        """Updated time using utilities."""
        return self.display_datetime_relative(
            obj,
            'updated_at',
            DateTimeDisplayConfig(show_relative=True, show_seconds=False)
        )

    # Readonly field displays
    def balance_breakdown_display(self, obj):
        """Detailed balance breakdown for detail view."""
        if not obj.pk:
            return "Save to see breakdown"

        # Build breakdown HTML
        details = []

        details.append(f"<strong>Current Balance:</strong> ${obj.balance_usd:.2f} USD")
        details.append(f"<strong>Total Deposited:</strong> ${obj.total_deposited:.2f} USD")
        details.append(f"<strong>Total Withdrawn:</strong> ${obj.total_withdrawn:.2f} USD")

        # Calculate net
        net = obj.total_deposited - obj.total_withdrawn
        details.append(f"<strong>Net Deposits:</strong> ${net:.2f} USD")

        if obj.last_transaction_at:
            details.append(f"<strong>Last Transaction:</strong> {obj.last_transaction_at}")

        # Transaction count
        txn_count = Transaction.objects.filter(user=obj.user).count()
        details.append(f"<strong>Total Transactions:</strong> {txn_count}")

        return format_html("<br>".join(details))

    balance_breakdown_display.short_description = "Balance Breakdown"

    # Actions
    @action(description="Reset zero balances", variant=ActionVariant.WARNING)
    def reset_zero_balances(self, request, queryset):
        """Reset balances that are zero."""
        updated = queryset.filter(balance_usd=0).update(
            total_deposited=0,
            total_withdrawn=0
        )
        self.message_user(
            request,
            f"Successfully reset {updated} zero balance(s).",
            level='WARNING'
        )


@admin.register(Transaction)
class TransactionAdmin(OptimizedModelAdmin, DisplayMixin, ModelAdmin):
    """
    Transaction admin for Payments v2.0.

    Clean interface for transaction management.
    """

    # Performance optimization
    select_related_fields = ['user']

    # List configuration
    list_display = [
        'transaction_id_display',
        'user_display',
        'type_display',
        'amount_display',
        'balance_after_display',
        'created_display'
    ]

    list_filter = [
        'transaction_type',
        TransactionTypeFilter,
        RecentActivityFilter,
        'created_at'
    ]

    search_fields = [
        'id',
        'user__username',
        'user__email',
        'description',
        'payment_id',
        'withdrawal_request_id'
    ]

    readonly_fields = [
        'id',
        'user',
        'transaction_type',
        'amount_usd',
        'balance_after',
        'payment_id',
        'withdrawal_request_id',
        'description',
        'metadata',
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('Transaction Information', {
            'fields': (
                'id',
                'user',
                'transaction_type',
                'amount_usd',
                'balance_after',
                'description'
            )
        }),
        ('References', {
            'fields': (
                'payment_id',
                'withdrawal_request_id'
            )
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    # Display methods
    @display(description="ID")
    def transaction_id_display(self, obj):
        """Transaction ID display."""
        return StatusBadge.create(
            text=str(obj.id)[:8] + "...",
            variant="info"
        )

    @display(description="User")
    def user_display(self, obj):
        """User display."""
        return self.display_user_simple(obj, 'user')

    @display(description="Type", label=True)
    def type_display(self, obj):
        """Transaction type display."""
        type_mappings = {
            'deposit': 'success',
            'withdrawal': 'warning',
            'payment': 'primary',
            'refund': 'info',
            'fee': 'secondary',
            'bonus': 'success',
            'adjustment': 'secondary'
        }

        from django_cfg.modules.django_admin import StatusBadgeConfig

        config = StatusBadgeConfig(
            custom_mappings=type_mappings,
            show_icons=True
        )

        return self.display_status_auto(
            type('obj', (), {'status': obj.transaction_type})(),
            'status',
            config
        )

    @display(description="Amount")
    def amount_display(self, obj):
        """Amount display with sign."""
        return self.display_money_amount(
            obj,
            'amount_usd',
            MoneyDisplayConfig(currency="USD", show_sign=True)
        )

    @display(description="Balance After")
    def balance_after_display(self, obj):
        """Balance after transaction."""
        return self.display_money_amount(
            obj,
            'balance_after',
            MoneyDisplayConfig(currency="USD", show_sign=False)
        )

    @display(description="Created")
    def created_display(self, obj):
        """Created time display."""
        return self.display_datetime_compact(obj, 'created_at')

    def has_add_permission(self, request):
        """Disable manual transaction creation (use managers instead)."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable transaction deletion (immutable records)."""
        return False
