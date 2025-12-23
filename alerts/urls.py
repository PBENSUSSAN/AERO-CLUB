from django.urls import path
from . import views

app_name = 'alerts'

urlpatterns = [
    # Utilisateur
    path('', views.my_alerts, name='my_alerts'),
    path('acknowledge/<int:alert_id>/', views.acknowledge_alert, name='acknowledge'),
    path('api/', views.alerts_api, name='api'),

    # Administration
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/run-checks/', views.run_checks, name='run_checks'),
]
