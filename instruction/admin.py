from django.contrib import admin
from .models import Lesson

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('date', 'student', 'instructor', 'title', 'grade')
    list_filter = ('instructor', 'grade', 'date')
    search_fields = ('student__last_name', 'student__first_name', 'comments')
    autocomplete_fields = ['student', 'instructor', 'flight']
