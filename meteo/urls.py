from django.urls import path
from . import views

urlpatterns = [
    path('', views.weather_dashboard, name='weather'),
    path('api/metar/<str:icao>/', views.metar_api, name='metar_api'),
    path('api/taf/<str:icao>/', views.taf_api, name='taf_api'),
    path('api/multi/', views.multi_airport_weather, name='multi_weather_api'),
    path('widget/', views.weather_widget, name='weather_widget'),
]
