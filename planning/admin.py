from django.contrib import admin
from .models import Reservation

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('user', 'aircraft', 'start_time', 'end_time', 'is_instruction')
    list_filter = ('aircraft', 'start_time', 'is_instruction')
    search_fields = ('user__username', 'user__last_name', 'aircraft__registration')
