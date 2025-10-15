"""
Payment Admin interface for Payments v2.0.

Clean, modern payment management using Unfold Admin.
"""

from django.contrib import admin
from django.utils import timezone
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

from ..models import Payment
from .filters import PaymentAmountFilter, PaymentStatusFilter, RecentActivityFilter

logger = get_logger("payment_admin")


@admin.register(Payment)
class PaymentAdmin(OptimizedModelAdmin, DisplayMixin, ModelAdmin):
    """
    Payment admin for Payments v2.0.

    Features:
    - Clean display utilities with no HTML duplication
    - Automatic query optimization
    - NowPayments-specific UI
    - Polling-based status management
    """

    # Performance optimization
    select_related_fields = ['user', 'currency']
    annotations = {}

    # List configuration
    list_display = [
        'payment_id_display',
        'user_display',
        'amount_display',
        'currency_display',
        'status_display',
        'status_changed_display',
        'created_display'
    ]

    list_filter = [
        PaymentStatusFilter,
        PaymentAmountFilter,
        RecentActivityFilter,
        'currency',
        'created_at',
        'status_changed_at',
    ]

    search_fields = [
        'internal_payment_id',
        'provider_payment_id',
        'transaction_hash',
        'user__username',
        'user__email',
        'pay_address'
    ]

    readonly_fields = [
        'id',
        'internal_payment_id',
        'provider_payment_id',
        'created_at',
        'updated_at',
        'status_changed_at',
        'completed_at',
        'payment_details_display',
        'qr_code_display'
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'id',
                'internal_payment_id',
                'user',
                'status',
                'description'
            )
        }),
        ('Payment Details', {
            'fields': (
                'amount_usd',
                'currency',
                'pay_amount',
                'actual_amount',
                'actual_amount_usd'
            )
        }),
        ('Provider Information', {
            'fields': (
                'provider',
                'provider_payment_id',
                'pay_address',
                'payment_url'
            )
        }),
        ('Blockchain Information', {
            'fields': (
                'transaction_hash',
                'confirmations_count'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'status_changed_at',
                'completed_at',
                'expires_at'
            ),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': (
                'provider_data',
                'payment_details_display',
                'qr_code_display'
            ),
            'classes': ('collapse',)
        })
    )

    # Register actions
    actions = ['mark_as_completed', 'mark_as_failed', 'cancel_payments']

    # Display methods using utilities
    @display(description="Payment ID")
    def payment_id_display(self, obj):
        """Payment ID display with badge."""
        return StatusBadge.create(
            text=obj.internal_payment_id[:16] + "...",
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
        """Status display with payment-specific colors."""
        # Payment v2.0 status mappings
        payment_status_mappings = {
            'pending': 'warning',
            'confirming': 'info',
            'confirmed': 'primary',
            'completed': 'success',
            'partially_paid': 'warning',
            'failed': 'danger',
            'cancelled': 'secondary',
            'expired': 'danger'
        }

        config = StatusBadgeConfig(
            custom_mappings=payment_status_mappings,
            show_icons=True
        )

        return self.display_status_auto(obj, 'status', config)

    @display(description="Created")
    def created_display(self, obj):
        """Created time display."""
        return self.display_datetime_relative(
            obj,
            'created_at',
            DateTimeDisplayConfig(show_relative=True, show_seconds=False)
        )

    @display(description="Status Changed")
    def status_changed_display(self, obj):
        """Status changed time display."""
        if not obj.status_changed_at:
            return "-"
        return self.display_datetime_relative(
            obj,
            'status_changed_at',
            DateTimeDisplayConfig(show_relative=True, show_seconds=False)
        )

    # Readonly field displays
    def payment_details_display(self, obj):
        """Detailed payment information for detail view."""
        if not obj.pk:
            return "Save to see details"

        from django_cfg.modules.django_admin.utils.displays import MoneyDisplay

        # Calculate age
        age = timezone.now() - obj.created_at
        age_text = f"{age.days} days, {age.seconds // 3600} hours"

        # Build details HTML
        details = []

        # Basic info
        details.append(f"<strong>Internal ID:</strong> {obj.internal_payment_id}")
        details.append(f"<strong>Age:</strong> {age_text}")

        # Provider info
        if obj.provider_payment_id:
            details.append(f"<strong>Provider Payment ID:</strong> {obj.provider_payment_id}")

        # Transaction details
        if obj.transaction_hash:
            explorer_link = obj.get_explorer_link()
            if explorer_link:
                details.append(f"<strong>Transaction:</strong> <a href='{explorer_link}' target='_blank'>{obj.transaction_hash[:16]}...</a>")
            else:
                details.append(f"<strong>Transaction Hash:</strong> {obj.transaction_hash}")

        if obj.confirmations_count > 0:
            details.append(f"<strong>Confirmations:</strong> {obj.confirmations_count}")

        if obj.pay_address:
            details.append(f"<strong>Pay Address:</strong> <code>{obj.pay_address}</code>")

        if obj.pay_amount:
            details.append(f"<strong>Pay Amount:</strong> {obj.pay_amount:.8f} {obj.currency.token}")

        if obj.actual_amount:
            details.append(f"<strong>Actual Amount:</strong> {obj.actual_amount:.8f} {obj.currency.token}")

        # URLs
        if obj.payment_url:
            details.append(f"<strong>Payment URL:</strong> <a href='{obj.payment_url}' target='_blank'>Open</a>")

        # Expiration
        if obj.expires_at:
            if obj.is_expired:
                details.append(f"<strong>Expired:</strong> <span style='color:red;'>Yes ({obj.expires_at})</span>")
            else:
                details.append(f"<strong>Expires At:</strong> {obj.expires_at}")

        # Description
        if obj.description:
            details.append(f"<strong>Description:</strong> {obj.description}")

        return format_html("<br>".join(details))

    payment_details_display.short_description = "Payment Details"

    def qr_code_display(self, obj):
        """QR code display for payment address."""
        if not obj.pay_address:
            return "No payment address"

        qr_url = obj.get_qr_code_url(size=200)
        if qr_url:
            return format_html(
                '<img src="{}" alt="QR Code" style="max-width:200px;"><br>'
                '<small>Scan to pay: <code>{}</code></small>',
                qr_url,
                obj.pay_address
            )
        return f"Address: {obj.pay_address}"

    qr_code_display.short_description = "QR Code"

    # Actions
    @action(description="Mark as completed", variant=ActionVariant.SUCCESS)
    def mark_as_completed(self, request, queryset):
        """Mark selected payments as completed."""
        updated = 0
        for payment in queryset.filter(status__in=['pending', 'confirming', 'confirmed']):
            success = Payment.objects.update_payment_status(
                payment,
                'completed'
            )
            if success:
                updated += 1

        self.message_user(
            request,
            f"Successfully marked {updated} payment(s) as completed.",
            level='SUCCESS'
        )

    @action(description="Mark as failed", variant=ActionVariant.DANGER)
    def mark_as_failed(self, request, queryset):
        """Mark selected payments as failed."""
        updated = 0
        for payment in queryset.filter(status__in=['pending', 'confirming', 'confirmed']):
            success = Payment.objects.update_payment_status(
                payment,
                'failed'
            )
            if success:
                updated += 1

        self.message_user(
            request,
            f"Successfully marked {updated} payment(s) as failed.",
            level='WARNING'
        )

    @action(description="Cancel payments", variant=ActionVariant.WARNING)
    def cancel_payments(self, request, queryset):
        """Cancel selected payments."""
        updated = 0
        for payment in queryset.filter(status__in=['pending', 'confirming']):
            success = Payment.objects.update_payment_status(
                payment,
                'cancelled'
            )
            if success:
                updated += 1

        self.message_user(
            request,
            f"Successfully cancelled {updated} payment(s).",
            level='WARNING'
        )
