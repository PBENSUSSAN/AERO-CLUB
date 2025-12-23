from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Lesson
from members.models import Member

@login_required
def my_progression(request):
    """Vue Élève : Voir son livret"""
    lessons = Lesson.objects.filter(student=request.user)
    
    # Calcul statistiques rapides
    total_lessons = lessons.count()
    
    return render(request, 'instruction/progression.html', {
        'lessons': lessons,
        'total_lessons': total_lessons
    })

@login_required
def instructor_dashboard(request):
    """Vue Instructeur : Liste des élèves et saisie"""
    if not hasattr(request.user, 'member_profile') or not request.user.member_profile.is_instructor:
        messages.error(request, "Accès réservé aux instructeurs.")
        return redirect('home')

    # Récupérer tous les élèves (ceux qui ont is_student=True)
    students = User.objects.filter(member_profile__is_student=True)
    
    # Dernières leçons données par cet instructeur
    my_lessons = Lesson.objects.filter(instructor=request.user)[:10]

    return render(request, 'instruction/instructor_dashboard.html', {
        'students': students,
        'my_lessons': my_lessons
    })

@login_required
def log_lesson(request, student_id):
    """Formulaire instructeur pour noter une leçon"""
    if not hasattr(request.user, 'member_profile') or not request.user.member_profile.is_instructor:
         return redirect('home')
         
    student = User.objects.get(pk=student_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        comments = request.POST.get('comments')
        next_steps = request.POST.get('next_steps')
        grade = request.POST.get('grade')
        
        Lesson.objects.create(
            instructor=request.user,
            student=student,
            title=title,
            comments=comments,
            next_steps=next_steps,
            grade=grade
        )
        messages.success(request, f"Leçon enregistrée pour {student.last_name} !")
        return redirect('instructor_dashboard')

    return render(request, 'instruction/log_lesson.html', {'student': student})
