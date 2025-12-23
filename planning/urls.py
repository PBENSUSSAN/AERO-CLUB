from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('api/events/', views.events_api, name='api_events'),
    path('api/create/', views.create_reservation, name='api_create_reservation'),
]
