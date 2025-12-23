from django.db import models
from django.contrib.auth.models import User
from fleet.models import Flight

class Lesson(models.Model):
    GRADES = [
        (1, 'À revoir (1/5)'),
        (2, 'En cours (2/5)'),
        (3, 'Acquis (3/5)'),
        (4, 'Maîtrisé (4/5)'),
        (5, 'Excellent (5/5)'),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lessons_received', verbose_name="Élève")
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lessons_given', verbose_name="Instructeur")
    flight = models.OneToOneField(Flight, on_delete=models.SET_NULL, null=True, blank=True, related_name='lesson_report', verbose_name="Vol associé")
    
    date = models.DateTimeField("Date de la séance", auto_now_add=True)
    
    # Contenu Pédagogique
    title = models.CharField("Thème de la séance", max_length=100) # ex: Maniabilité, Tour de piste
    comments = models.TextField("Commentaire Instructeur")
    next_steps = models.TextField("À travailler prochainement", blank=True)
    
    grade = models.PositiveSmallIntegerField("Note globale", choices=GRADES, default=3)
    
    def __str__(self):
        return f"{self.date.strftime('%d/%m')} - {self.student.last_name} (Instr: {self.instructor.last_name})"

    class Meta:
        verbose_name = "Leçon / Séance"
        verbose_name_plural = "Livret de Progression"
        ordering = ['-date']
