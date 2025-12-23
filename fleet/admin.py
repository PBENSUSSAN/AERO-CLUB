from django.contrib import admin
from .models import Aircraft, MaintenanceDeadline, Flight

class MaintenanceDeadlineInline(admin.TabularInline):
    model = MaintenanceDeadline
    extra = 1

@admin.register(Aircraft)
class AircraftAdmin(admin.ModelAdmin):
    list_display = ('registration', 'model_name', 'status', 'current_hours', 'hourly_rate')
    list_filter = ('status', 'model_name')
    search_fields = ('registration', 'model_name')
    inlines = [MaintenanceDeadlineInline]

@admin.register(MaintenanceDeadline)
class MaintenanceDeadlineAdmin(admin.ModelAdmin):
    list_display = ('title', 'aircraft', 'due_at_date', 'due_at_hours', 'is_overdue')
    list_filter = ('aircraft',)

@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('date', 'aircraft', 'pilot', 'duration', 'cost')
    search_fields = ('aircraft__registration', 'pilot__username', 'pilot__last_name')
    list_filter = ('aircraft', 'date')
