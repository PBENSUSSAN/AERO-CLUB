from django.contrib import admin
from .models import (
    TrainingPhase, TrainingExercise, StudentProgression,
    ExerciseProgress, Lesson, LessonExerciseEvaluation
)


# ============================================================
# PROGRAMME DE FORMATION
# ============================================================

class TrainingExerciseInline(admin.TabularInline):
    model = TrainingExercise
    extra = 0
    fields = ['order', 'code', 'name', 'is_mandatory', 'is_solo_exercise']
    ordering = ['order']


@admin.register(TrainingPhase)
class TrainingPhaseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'order', 'target_hours', 'is_solo_allowed', 'exercise_count')
    list_editable = ('order', 'target_hours', 'is_solo_allowed')
    search_fields = ('code', 'name')
    ordering = ['order']
    inlines = [TrainingExerciseInline]

    def exercise_count(self, obj):
        return obj.exercises.count()
    exercise_count.short_description = "Nb exercices"


@admin.register(TrainingExercise)
class TrainingExerciseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'phase', 'order', 'is_mandatory', 'is_solo_exercise')
    list_filter = ('phase', 'is_mandatory', 'is_solo_exercise')
    search_fields = ('code', 'name', 'description')
    list_editable = ('order', 'is_mandatory', 'is_solo_exercise')
    ordering = ['phase__order', 'order']


# ============================================================
# PROGRESSION ELEVES
# ============================================================

class ExerciseProgressInline(admin.TabularInline):
    model = ExerciseProgress
    extra = 0
    fields = ['exercise', 'level', 'last_practiced', 'instructor_notes']
    readonly_fields = ['last_practiced']
    autocomplete_fields = ['exercise']
    ordering = ['exercise__phase__order', 'exercise__order']


@admin.register(StudentProgression)
class StudentProgressionAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'current_phase', 'target_license',
        'total_instruction_hours', 'total_solo_hours', 'total_hours',
        'first_solo_date', 'is_active'
    )
    list_filter = ('current_phase', 'target_license', 'is_active', 'theory_exam_passed', 'practical_exam_passed')
    search_fields = ('student__last_name', 'student__first_name', 'student__email', 'student__username')
    autocomplete_fields = ['student', 'primary_instructor', 'current_phase']
    readonly_fields = ['total_hours']
    inlines = [ExerciseProgressInline]

    fieldsets = (
        ('Eleve', {
            'fields': ('student', 'primary_instructor', 'target_license', 'is_active')
        }),
        ('Progression', {
            'fields': ('current_phase', 'enrollment_date')
        }),
        ('Heures de vol', {
            'fields': ('total_instruction_hours', 'total_solo_hours', 'total_hours')
        }),
        ('Jalons', {
            'fields': (
                'first_solo_date', 'first_solo_nav_date',
                ('theory_exam_date', 'theory_exam_passed'),
                ('practical_exam_date', 'practical_exam_passed'),
                'license_obtained_date'
            )
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

    def total_hours(self, obj):
        return obj.total_hours
    total_hours.short_description = "Total heures"


@admin.register(ExerciseProgress)
class ExerciseProgressAdmin(admin.ModelAdmin):
    list_display = ('student_progression', 'exercise', 'level', 'last_practiced')
    list_filter = ('level', 'exercise__phase')
    search_fields = (
        'student_progression__student__last_name',
        'student_progression__student__first_name',
        'exercise__code',
        'exercise__name'
    )
    autocomplete_fields = ['student_progression', 'exercise']


# ============================================================
# LECONS / SEANCES
# ============================================================

class LessonExerciseEvaluationInline(admin.TabularInline):
    model = LessonExerciseEvaluation
    extra = 1
    fields = ['exercise', 'level_before', 'level_after', 'notes']
    autocomplete_fields = ['exercise']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'student', 'instructor', 'lesson_type', 'phase',
        'title', 'grade', 'solo_authorized', 'instructor_signature', 'student_signature'
    )
    list_filter = ('lesson_type', 'phase', 'grade', 'solo_authorized', 'instructor', 'date')
    search_fields = ('student__last_name', 'student__first_name', 'title', 'comments', 'student__username')
    date_hierarchy = 'date'
    autocomplete_fields = ['student', 'instructor', 'flight', 'phase']
    filter_horizontal = ['exercises_practiced']
    inlines = [LessonExerciseEvaluationInline]

    fieldsets = (
        ('Informations generales', {
            'fields': ('date', 'lesson_type', 'student', 'instructor', 'flight', 'phase')
        }),
        ('Conditions', {
            'fields': ('weather', 'wind'),
            'classes': ('collapse',)
        }),
        ('Contenu pedagogique', {
            'fields': ('title', 'objectives', 'briefing_content', 'exercises_practiced')
        }),
        ('Evaluation', {
            'fields': ('strong_points', 'areas_to_improve', 'comments', 'next_steps', 'grade')
        }),
        ('Autorisation solo', {
            'fields': ('solo_authorized', 'solo_authorization_notes'),
            'classes': ('collapse',)
        }),
        ('Signatures', {
            'fields': ('instructor_signature', 'student_signature')
        }),
    )


@admin.register(LessonExerciseEvaluation)
class LessonExerciseEvaluationAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'exercise', 'level_before', 'level_after')
    list_filter = ('level_after', 'exercise__phase')
    autocomplete_fields = ['lesson', 'exercise']
