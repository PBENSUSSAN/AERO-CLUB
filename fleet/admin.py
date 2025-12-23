from django.contrib import admin
from django.utils.html import format_html
from .models import Aircraft, MaintenanceDeadline, Flight, MaintenanceLog


class MaintenanceDeadlineInline(admin.TabularInline):
    model = MaintenanceDeadline
    extra = 0
    fields = ['deadline_type', 'title', 'due_at_date', 'due_at_hours', 'priority', 'is_completed']
    readonly_fields = ['is_completed']


class MaintenanceLogInline(admin.TabularInline):
    model = MaintenanceLog
    extra = 0
    fields = ['date', 'work_type', 'workshop', 'description', 'cost']
    readonly_fields = ['date', 'work_type', 'workshop', 'description', 'cost']


@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = [
        'registration', 'model_name', 'status_badge', 'current_hours',
        'engine_hours_remaining_display', 'hourly_rate', 'cdn_status', 'insurance_status'
    ]
    list_filter = ['status', 'category', 'fuel_type', 'has_gps', 'has_autopilot']
    search_fields = ['registration', 'model_name', 'manufacturer', 'serial_number']
    inlines = [MaintenanceDeadlineInline, MaintenanceLogInline]
    readonly_fields = ['engine_hours_remaining', 'engine_life_percentage', 'is_airworthy', 'has_overdue_maintenance']

    fieldsets = (
        ('Identification', {
            'fields': ('registration', 'model_name', 'manufacturer', 'serial_number', 'year_of_manufacture', 'category', 'image')
        }),
        ('Configuration', {
            'fields': (
                'num_seats',
                ('fuel_type', 'fuel_capacity', 'usable_fuel', 'fuel_consumption'),
                'oil_capacity',
            )
        }),
        ('Performances', {
            'fields': (('cruise_speed', 'max_range'), ('mtow', 'empty_weight')),
            'classes': ('collapse',)
        }),
        ('Documents legaux', {
            'fields': (
                ('cdn_number', 'cdn_issue_date', 'cdn_expiry_date'), 'cdn_scan',
                'registration_certificate_date', 'registration_certificate_scan',
                ('radio_license_number', 'radio_license_expiry'),
                ('insurance_company', 'insurance_policy_number', 'insurance_expiry'), 'insurance_scan',
                'flight_manual_scan',
            )
        }),
        ('Compteurs cellule', {
            'fields': ('current_hours', 'cycles_count')
        }),
        ('Moteur', {
            'fields': (
                ('engine_model', 'engine_serial'),
                ('engine_hours', 'engine_tbo', 'engine_tsoh'),
                ('engine_hours_remaining', 'engine_life_percentage'),
                'engine_overhaul_date',
            )
        }),
        ('Helice', {
            'fields': (('propeller_model', 'propeller_serial'), ('propeller_hours', 'propeller_tbo')),
            'classes': ('collapse',)
        }),
        ('Equipements', {
            'fields': (
                ('has_gps', 'gps_model'),
                ('has_autopilot', 'has_efis'),
                ('has_transponder', 'transponder_mode', 'has_adsb'),
                ('has_vor', 'has_ils', 'has_dme', 'has_adf'),
                'equipment_notes',
            ),
            'classes': ('collapse',)
        }),
        ('Tarification', {
            'fields': ('hourly_rate', 'hourly_rate_instruction', 'instruction_fee')
        }),
        ('Statut', {
            'fields': ('status', 'is_airworthy', 'has_overdue_maintenance', 'is_club_owned', 'owner_name', 'notes')
        }),
    )

    def status_badge(self, obj):
        colors = {
            'AVAILABLE': 'green',
            'MAINTENANCE': 'orange',
            'GROUNDED': 'red',
            'RESERVED': 'blue',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Statut'

    def engine_hours_remaining_display(self, obj):
        remaining = obj.engine_hours_remaining
        if remaining < 50:
            color = 'red'
        elif remaining < 100:
            color = 'orange'
        else:
            color = 'green'
        return format_html('<span style="color: {};">{:.0f}h</span>', color, remaining)
    engine_hours_remaining_display.short_description = 'Avant TBO'

    def cdn_status(self, obj):
        if obj.is_cdn_valid:
            return format_html('<span style="color: green;">OK</span>')
        return format_html('<span style="color: red;">EXPIRE</span>')
    cdn_status.short_description = 'CDN'

    def insurance_status(self, obj):
        if obj.is_insurance_valid:
            return format_html('<span style="color: green;">OK</span>')
        return format_html('<span style="color: red;">EXPIRE</span>')
    insurance_status.short_description = 'Assur.'


@admin.register(MaintenanceDeadline)
class MaintenanceDeadlineAdmin(admin.ModelAdmin):
    list_display = [
        'aircraft', 'deadline_type', 'title', 'due_at_date', 'due_at_hours',
        'priority_badge', 'status_display', 'days_remaining', 'hours_remaining'
    ]
    list_filter = ['aircraft', 'deadline_type', 'priority', 'is_completed']
    search_fields = ['title', 'aircraft__registration', 'reference']

    fieldsets = (
        ('Echeance', {
            'fields': ('aircraft', 'deadline_type', 'title', 'priority')
        }),
        ('Butees', {
            'fields': (('due_at_date', 'due_at_hours'), ('tolerance_days', 'tolerance_hours'))
        }),
        ('Details', {
            'fields': ('reference', 'description', 'estimated_cost')
        }),
        ('Realisation', {
            'fields': ('is_completed', 'completion_date', 'completion_hours', 'completed_by', 'completion_notes')
        }),
    )

    def priority_badge(self, obj):
        colors = {
            'LOW': '#3498db',
            'MEDIUM': '#f39c12',
            'HIGH': '#e74c3c',
            'CRITICAL': '#8e44ad',
        }
        color = colors.get(obj.priority, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Priorite'

    def status_display(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: green;">Effectuee</span>')
        if obj.is_overdue():
            return format_html('<span style="color: red; font-weight: bold;">DEPASSEE</span>')
        if obj.is_approaching():
            return format_html('<span style="color: orange;">Approche</span>')
        return format_html('<span style="color: green;">OK</span>')
    status_display.short_description = 'Statut'


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'aircraft', 'pilot', 'flight_type', 'departure_airport',
        'arrival_airport', 'duration', 'landings_count', 'cost'
    ]
    list_filter = ['aircraft', 'flight_type', 'date', 'pilot']
    search_fields = ['aircraft__registration', 'pilot__username', 'pilot__last_name', 'departure_airport', 'arrival_airport']
    date_hierarchy = 'date'
    readonly_fields = ['duration', 'cost', 'signature_date']

    fieldsets = (
        ('Vol', {
            'fields': ('aircraft', 'pilot', 'copilot', 'date', 'flight_type')
        }),
        ('Itineraire', {
            'fields': ('departure_airport', 'arrival_airport', 'route')
        }),
        ('Compteurs', {
            'fields': (('hour_meter_start', 'hour_meter_end'), 'duration')
        }),
        ('Horaires', {
            'fields': (('block_off', 'takeoff_time'), ('landing_time', 'block_on'))
        }),
        ('Atterrissages', {
            'fields': (('landings_count', 'landings_day', 'landings_night'), 'passengers_count')
        }),
        ('Carburant & Huile', {
            'fields': (('fuel_on_departure', 'fuel_on_arrival', 'fuel_added'), 'oil_added')
        }),
        ('Observations techniques', {
            'fields': ('complaints', 'complaint_resolved', 'resolution_notes')
        }),
        ('Facturation', {
            'fields': ('cost',)
        }),
        ('Signature', {
            'fields': ('pilot_signature', 'signature_date'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ['date', 'aircraft', 'work_type', 'workshop', 'cost', 'approved_by']
    list_filter = ['aircraft', 'work_type', 'date']
    search_fields = ['aircraft__registration', 'workshop', 'description']
    date_hierarchy = 'date'

    fieldsets = (
        ('Intervention', {
            'fields': ('aircraft', 'related_deadline', 'work_type', 'date', 'hours_at_work')
        }),
        ('Details', {
            'fields': ('workshop', 'description', 'parts_replaced')
        }),
        ('Facturation', {
            'fields': ('cost', 'invoice_number', 'invoice_scan')
        }),
        ('Approbation', {
            'fields': ('approved_by', 'approval_reference')
        }),
    )
