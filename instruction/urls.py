from django.urls import path
from . import views

urlpatterns = [
    path('progression/', views.my_progression, name='my_progression'),
    path('instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('log-lesson/<int:student_id>/', views.log_lesson, name='log_lesson'),
]
