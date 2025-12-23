from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Avg
from .models import (
    Lesson, TrainingPhase, TrainingExercise,
    StudentProgression, ExerciseProgress, LessonExerciseEvaluation
)
from members.models import Member


@login_required
def my_progression(request):
    """Vue Eleve : Voir son livret de progression complet"""
    lessons = Lesson.objects.filter(student=request.user).order_by('-date')

    # Recuperer ou creer la progression de l'eleve
    progression = None
    exercise_progress = []
    phases_progress = []

    try:
        progression = request.user.training_progression
        exercise_progress = ExerciseProgress.objects.filter(
            student_progression=progression
        ).select_related('exercise', 'exercise__phase').order_by(
            'exercise__phase__order', 'exercise__order'
        )

        # Calculer la progression par phase
        for phase in TrainingPhase.objects.all().order_by('order'):
            exercises = TrainingExercise.objects.filter(phase=phase)
            total = exercises.count()
            acquired = ExerciseProgress.objects.filter(
                student_progression=progression,
                exercise__phase=phase,
                level__in=['A', '+']
            ).count()
            in_progress = ExerciseProgress.objects.filter(
                student_progression=progression,
                exercise__phase=phase,
                level__in=['P', 'E']
            ).count()

            phases_progress.append({
                'phase': phase,
                'total': total,
                'acquired': acquired,
                'in_progress': in_progress,
                'percentage': int((acquired / total * 100) if total > 0 else 0)
            })

    except StudentProgression.DoesNotExist:
        pass

    # Statistiques
    total_lessons = lessons.count()
    avg_grade = lessons.aggregate(avg=Avg('grade'))['avg'] or 0

    return render(request, 'instruction/progression.html', {
        'lessons': lessons[:20],
        'total_lessons': total_lessons,
        'avg_grade': round(avg_grade, 1),
        'progression': progression,
        'exercise_progress': exercise_progress,
        'phases_progress': phases_progress,
        'all_phases': TrainingPhase.objects.all().order_by('order'),
    })


@login_required
def student_progression_detail(request, student_id):
    """Vue Instructeur : Voir la progression d'un eleve"""
    if not hasattr(request.user, 'member_profile') or not request.user.member_profile.is_instructor:
        messages.error(request, "Acces reserve aux instructeurs.")
        return redirect('home')

    student = get_object_or_404(User, pk=student_id)
    lessons = Lesson.objects.filter(student=student).order_by('-date')

    # Progression
    progression = None
    exercise_progress = []
    phases_progress = []

    try:
        progression = student.training_progression
    except StudentProgression.DoesNotExist:
        # Creer automatiquement la progression
        progression = StudentProgression.objects.create(
            student=student,
            primary_instructor=request.user
        )

    exercise_progress = ExerciseProgress.objects.filter(
        student_progression=progression
    ).select_related('exercise', 'exercise__phase').order_by(
        'exercise__phase__order', 'exercise__order'
    )

    # Calculer la progression par phase
    for phase in TrainingPhase.objects.all().order_by('order'):
        exercises = TrainingExercise.objects.filter(phase=phase)
        total = exercises.count()
        acquired = ExerciseProgress.objects.filter(
            student_progression=progression,
            exercise__phase=phase,
            level__in=['A', '+']
        ).count()
        in_progress = ExerciseProgress.objects.filter(
            student_progression=progression,
            exercise__phase=phase,
            level__in=['P', 'E']
        ).count()

        phases_progress.append({
            'phase': phase,
            'total': total,
            'acquired': acquired,
            'in_progress': in_progress,
            'percentage': int((acquired / total * 100) if total > 0 else 0)
        })

    return render(request, 'instruction/student_progression.html', {
        'student': student,
        'lessons': lessons[:20],
        'progression': progression,
        'exercise_progress': exercise_progress,
        'phases_progress': phases_progress,
        'all_phases': TrainingPhase.objects.all().order_by('order'),
    })


@login_required
def instructor_dashboard(request):
    """Vue Instructeur : Liste des eleves et saisie"""
    if not hasattr(request.user, 'member_profile') or not request.user.member_profile.is_instructor:
        messages.error(request, "Acces reserve aux instructeurs.")
        return redirect('home')

    # Recuperer tous les eleves actifs
    students = User.objects.filter(
        member_profile__is_student=True
    ).select_related('member_profile')

    # Eleves avec leur progression
    students_with_progress = []
    for student in students:
        try:
            prog = student.training_progression
            students_with_progress.append({
                'user': student,
                'progression': prog,
                'hours': prog.total_hours if prog else 0
            })
        except StudentProgression.DoesNotExist:
            students_with_progress.append({
                'user': student,
                'progression': None,
                'hours': 0
            })

    # Dernieres lecons donnees par cet instructeur
    my_lessons = Lesson.objects.filter(instructor=request.user).select_related(
        'student', 'phase'
    ).order_by('-date')[:10]

    # Statistiques
    stats = {
        'total_students': len(students_with_progress),
        'active_students': StudentProgression.objects.filter(
            is_active=True,
            primary_instructor=request.user
        ).count(),
        'total_lessons': Lesson.objects.filter(instructor=request.user).count(),
    }

    return render(request, 'instruction/instructor_dashboard.html', {
        'students': students_with_progress,
        'my_lessons': my_lessons,
        'stats': stats,
        'phases': TrainingPhase.objects.all().order_by('order'),
    })


@login_required
def log_lesson(request, student_id):
    """Formulaire instructeur pour noter une lecon"""
    if not hasattr(request.user, 'member_profile') or not request.user.member_profile.is_instructor:
        return redirect('home')

    student = get_object_or_404(User, pk=student_id)
    phases = TrainingPhase.objects.all().order_by('order')
    exercises = TrainingExercise.objects.all().select_related('phase').order_by('phase__order', 'order')

    # Recuperer ou creer la progression de l'eleve
    try:
        progression = student.training_progression
    except StudentProgression.DoesNotExist:
        progression = StudentProgression.objects.create(
            student=student,
            primary_instructor=request.user
        )

    if request.method == 'POST':
        title = request.POST.get('title')
        comments = request.POST.get('comments')
        next_steps = request.POST.get('next_steps', '')
        grade = request.POST.get('grade', 3)
        lesson_type = request.POST.get('lesson_type', 'INSTRUCTION')
        phase_id = request.POST.get('phase')
        weather = request.POST.get('weather', '')
        wind = request.POST.get('wind', '')
        objectives = request.POST.get('objectives', '')
        briefing_content = request.POST.get('briefing_content', '')
        strong_points = request.POST.get('strong_points', '')
        areas_to_improve = request.POST.get('areas_to_improve', '')
        solo_authorized = request.POST.get('solo_authorized') == 'on'
        solo_notes = request.POST.get('solo_authorization_notes', '')

        phase = None
        if phase_id:
            phase = TrainingPhase.objects.filter(pk=phase_id).first()

        lesson = Lesson.objects.create(
            instructor=request.user,
            student=student,
            title=title,
            comments=comments,
            next_steps=next_steps,
            grade=grade,
            lesson_type=lesson_type,
            phase=phase,
            weather=weather,
            wind=wind,
            objectives=objectives,
            briefing_content=briefing_content,
            strong_points=strong_points,
            areas_to_improve=areas_to_improve,
            solo_authorized=solo_authorized,
            solo_authorization_notes=solo_notes
        )

        # Traiter les exercices pratiques
        exercise_ids = request.POST.getlist('exercises')
        if exercise_ids:
            lesson.exercises_practiced.set(exercise_ids)

        # Traiter les evaluations d'exercices
        for key, value in request.POST.items():
            if key.startswith('level_'):
                ex_id = key.replace('level_', '')
                if value and value != '-':
                    try:
                        exercise = TrainingExercise.objects.get(pk=ex_id)
                        # Niveau avant
                        level_before = '-'
                        try:
                            ep = ExerciseProgress.objects.get(
                                student_progression=progression,
                                exercise=exercise
                            )
                            level_before = ep.level
                        except ExerciseProgress.DoesNotExist:
                            pass

                        # Creer l'evaluation
                        LessonExerciseEvaluation.objects.create(
                            lesson=lesson,
                            exercise=exercise,
                            level_before=level_before,
                            level_after=value,
                            notes=request.POST.get(f'note_{ex_id}', '')
                        )
                    except TrainingExercise.DoesNotExist:
                        pass

        messages.success(request, f"Lecon enregistree pour {student.last_name} !")
        return redirect('instructor_dashboard')

    # Recuperer les niveaux actuels de l'eleve
    current_levels = {}
    for ep in ExerciseProgress.objects.filter(student_progression=progression):
        current_levels[ep.exercise_id] = ep.level

    return render(request, 'instruction/log_lesson.html', {
        'student': student,
        'phases': phases,
        'exercises': exercises,
        'current_levels': current_levels,
        'progression': progression,
    })


@login_required
def training_program(request):
    """Vue du programme de formation complet"""
    phases = TrainingPhase.objects.all().prefetch_related('exercises').order_by('order')

    return render(request, 'instruction/training_program.html', {
        'phases': phases,
    })


@login_required
def update_exercise_level(request, student_id, exercise_id):
    """Mettre a jour le niveau d'un exercice (AJAX ou POST)"""
    if not hasattr(request.user, 'member_profile') or not request.user.member_profile.is_instructor:
        return redirect('home')

    if request.method == 'POST':
        student = get_object_or_404(User, pk=student_id)
        exercise = get_object_or_404(TrainingExercise, pk=exercise_id)
        new_level = request.POST.get('level', '-')

        try:
            progression = student.training_progression
        except StudentProgression.DoesNotExist:
            progression = StudentProgression.objects.create(
                student=student,
                primary_instructor=request.user
            )

        ep, created = ExerciseProgress.objects.update_or_create(
            student_progression=progression,
            exercise=exercise,
            defaults={
                'level': new_level,
                'last_practiced': request.POST.get('date') or None
            }
        )

        messages.success(request, f"Niveau mis a jour: {exercise.code} -> {new_level}")

    return redirect('student_progression', student_id=student_id)
