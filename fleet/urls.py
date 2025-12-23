from django.urls import path
from . import views

urlpatterns = [
    path('', views.fleet_list, name='fleet_list'),
    path('log-flight/<int:aircraft_id>/', views.log_flight, name='log_flight'),
    
    # Admin Dashboard
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/aircraft/add/', views.admin_aircraft_add, name='admin_aircraft_add'),
    path('admin/aircraft/<int:aircraft_id>/edit/', views.admin_aircraft_edit, name='admin_aircraft_edit'),
    path('admin/aircraft/<int:aircraft_id>/delete/', views.admin_aircraft_delete, name='admin_aircraft_delete'),
    path('admin/maintenance/', views.admin_maintenance, name='admin_maintenance'),
    path('admin/maintenance/add/<int:aircraft_id>/', views.admin_maintenance_add, name='admin_maintenance_add'),
]
