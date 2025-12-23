from django.urls import path
from . import views

urlpatterns = [
    path('progression/', views.my_progression, name='my_progression'),
    path('instructor/', views.instructor_dashboard, name='instructor_dashboard'),
    path('log-lesson/<int:student_id>/', views.log_lesson, name='log_lesson'),
    path('student/<int:student_id>/', views.student_progression_detail, name='student_progression'),
    path('student/<int:student_id>/exercise/<int:exercise_id>/update/', views.update_exercise_level, name='update_exercise_level'),
    path('programme/', views.training_program, name='training_program'),
]
