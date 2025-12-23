from django.contrib import admin
from django.utils.html import format_html
from .models import Alert, AlertConfiguration


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['severity_badge', 'title', 'user', 'alert_type', 'status', 'expires_at', 'created_at']
    list_filter = ['severity', 'alert_type', 'status', 'created_at']
    search_fields = ['title', 'message', 'user__username', 'user__last_name']
    readonly_fields = ['created_at', 'acknowledged_at', 'resolved_at', 'unique_key']
    ordering = ['-created_at']

    fieldsets = (
        ('Alerte', {
            'fields': ('alert_type', 'severity', 'status', 'title', 'message')
        }),
        ('Destinataire', {
            'fields': ('user', 'related_aircraft')
        }),
        ('Dates', {
            'fields': ('expires_at', 'created_at', 'acknowledged_at', 'resolved_at')
        }),
        ('Notification', {
            'fields': ('email_sent', 'email_sent_at')
        }),
        ('Technique', {
            'fields': ('unique_key',),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_acknowledged', 'mark_resolved']

    def severity_badge(self, obj):
        colors = {
            'INFO': '#3498db',
            'WARNING': '#f39c12',
            'CRITICAL': '#e74c3c',
            'BLOCKING': '#8e44ad',
        }
        color = colors.get(obj.severity, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_severity_display()
        )
    severity_badge.short_description = 'Sévérité'
    severity_badge.admin_order_field = 'severity'

    def mark_acknowledged(self, request, queryset):
        for alert in queryset:
            alert.acknowledge()
        self.message_user(request, f"{queryset.count()} alerte(s) marquée(s) comme prise(s) en compte.")
    mark_acknowledged.short_description = "Marquer comme pris en compte"

    def mark_resolved(self, request, queryset):
        for alert in queryset:
            alert.resolve()
        self.message_user(request, f"{queryset.count()} alerte(s) marquée(s) comme résolue(s).")
    mark_resolved.short_description = "Marquer comme résolue"


@admin.register(AlertConfiguration)
class AlertConfigurationAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'days_info', 'days_warning', 'days_critical', 'block_on_expiry', 'send_email', 'is_active']
    list_editable = ['days_info', 'days_warning', 'days_critical', 'block_on_expiry', 'send_email', 'is_active']
