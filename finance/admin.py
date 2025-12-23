from django.contrib import admin
from .models import Transaction

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'amount', 'type', 'description')
    list_filter = ('type', 'date', 'user')
    search_fields = ('user__username', 'description')
