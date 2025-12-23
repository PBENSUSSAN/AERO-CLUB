from django.urls import path
from . import views

app_name = 'exports'

urlpatterns = [
    # Releves de compte
    path('account/me/', views.my_account_statement, name='my_account_statement'),
    path('account/<int:member_id>/', views.member_account_statement, name='member_account_statement'),

    # Carnet de route
    path('flight-log/<int:aircraft_id>/', views.aircraft_flight_log, name='aircraft_flight_log'),

    # Factures / Recus
    path('invoice/<int:transaction_id>/', views.transaction_invoice, name='transaction_invoice'),
]
