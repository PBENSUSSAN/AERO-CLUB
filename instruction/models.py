from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from fleet.models import Flight


# ============================================================
# PHASES DE FORMATION (Programme FFA/DGAC)
# ============================================================

class TrainingPhase(models.Model):
    """
    Phase de formation (ex: Phase 1 - Decouverte, Phase 2 - Maniabilite, etc.)
    Conforme au programme PPL FFA.
    """
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    code = models.CharField("Code", max_length=10, unique=True)  # ex: PH1, PH2
    name = models.CharField("Nom de la phase", max_length=100)
    description = models.TextField("Description", blank=True)
    target_hours = models.DecimalField(
        "Heures cibles",
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text="Nombre d'heures recommande pour cette phase"
    )
    is_solo_allowed = models.BooleanField("Solo autorise", default=False)

    class Meta:
        verbose_name = "Phase de formation"
        verbose_name_plural = "Phases de formation"
        ordering = ['order']

    def __str__(self):
        return f"{self.code} - {self.name}"


class TrainingExercise(models.Model):
    """
    Exercice standard du programme de formation.
    Ex: Vol rectiligne palier, Virage 30, Decrochage, etc.
    """
    COMPETENCY_LEVELS = [
        ('-', 'Non vu'),
        ('P', 'Presente'),
        ('E', 'En cours'),
        ('A', 'Acquis'),
        ('+', 'Maitrise'),
    ]

    phase = models.ForeignKey(TrainingPhase, on_delete=models.CASCADE, related_name='exercises')
    code = models.CharField("Code exercice", max_length=20)  # ex: EX01, EX02
    name = models.CharField("Nom de l'exercice", max_length=200)
    description = models.TextField("Description detaillee", blank=True)
    objectives = models.TextField("Objectifs pedagogiques", blank=True)
    order = models.PositiveSmallIntegerField("Ordre", default=0)
    is_mandatory = models.BooleanField("Obligatoire", default=True)
    is_solo_exercise = models.BooleanField("Exercice solo", default=False)

    class Meta:
        verbose_name = "Exercice de formation"
        verbose_name_plural = "Exercices de formation"
        ordering = ['phase__order', 'order']
        unique_together = ['phase', 'code']

    def __str__(self):
        return f"{self.code} - {self.name}"


# ============================================================
# PROGRESSION ELEVE
# ============================================================

class StudentProgression(models.Model):
    """
    Suivi de progression global d'un eleve.
    """
    student = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='training_progression',
        verbose_name="Eleve"
    )
    current_phase = models.ForeignKey(
        TrainingPhase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_students',
        verbose_name="Phase actuelle"
    )
    enrollment_date = models.DateField("Date inscription formation", default=timezone.now)
    target_license = models.CharField(
        "Objectif licence",
        max_length=20,
        choices=[
            ('LAPL', 'LAPL(A)'),
            ('PPL', 'PPL(A)'),
            ('CPL', 'CPL(A)'),
            ('BB', 'Brevet de Base'),
        ],
        default='PPL'
    )
    primary_instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_students',
        verbose_name="Instructeur principal"
    )

    # Jalons importants
    first_solo_date = models.DateField("Date premier solo", null=True, blank=True)
    first_solo_nav_date = models.DateField("Date premier solo nav", null=True, blank=True)
    theory_exam_date = models.DateField("Date examen theorique", null=True, blank=True)
    theory_exam_passed = models.BooleanField("Theorique reussi", default=False)
    practical_exam_date = models.DateField("Date examen pratique", null=True, blank=True)
    practical_exam_passed = models.BooleanField("Pratique reussi", default=False)
    license_obtained_date = models.DateField("Date obtention licence", null=True, blank=True)

    # Compteurs
    total_instruction_hours = models.DecimalField(
        "Heures DC",
        max_digits=6,
        decimal_places=1,
        default=0,
        help_text="Heures en double commande"
    )
    total_solo_hours = models.DecimalField(
        "Heures solo",
        max_digits=6,
        decimal_places=1,
        default=0
    )

    notes = models.TextField("Notes internes", blank=True)
    is_active = models.BooleanField("Formation active", default=True)

    class Meta:
        verbose_name = "Progression eleve"
        verbose_name_plural = "Progressions eleves"

    def __str__(self):
        return f"Progression {self.student.last_name} {self.student.first_name}"

    @property
    def total_hours(self):
        return self.total_instruction_hours + self.total_solo_hours

    @property
    def is_ready_for_solo(self):
        """Verifie si l'eleve peut etre lache solo."""
        # Verifier que les exercices obligatoires de base sont acquis
        required_exercises = ExerciseProgress.objects.filter(
            student_progression=self,
            exercise__is_mandatory=True,
            exercise__phase__is_solo_allowed=False,
        )
        return all(ep.level in ['A', '+'] for ep in required_exercises)


class ExerciseProgress(models.Model):
    """
    Niveau de competence d'un eleve sur un exercice specifique.
    """
    LEVELS = [
        ('-', 'Non vu'),
        ('P', 'Presente'),
        ('E', 'En cours d\'acquisition'),
        ('A', 'Acquis'),
        ('+', 'Maitrise / Expert'),
    ]

    student_progression = models.ForeignKey(
        StudentProgression,
        on_delete=models.CASCADE,
        related_name='exercise_progress'
    )
    exercise = models.ForeignKey(
        TrainingExercise,
        on_delete=models.CASCADE,
        related_name='student_progress'
    )
    level = models.CharField("Niveau", max_length=1, choices=LEVELS, default='-')
    last_practiced = models.DateField("Derniere pratique", null=True, blank=True)
    instructor_notes = models.TextField("Notes instructeur", blank=True)

    class Meta:
        verbose_name = "Progression exercice"
        verbose_name_plural = "Progressions exercices"
        unique_together = ['student_progression', 'exercise']

    def __str__(self):
        return f"{self.student_progression.student.last_name} - {self.exercise.code}: {self.level}"


# ============================================================
# LECONS / SEANCES
# ============================================================

class Lesson(models.Model):
    """
    Seance de formation (briefing + vol + debriefing).
    """
    GRADES = [
        (1, 'A revoir (1/5)'),
        (2, 'En cours (2/5)'),
        (3, 'Acquis (3/5)'),
        (4, 'Maitrise (4/5)'),
        (5, 'Excellent (5/5)'),
    ]

    LESSON_TYPES = [
        ('INSTRUCTION', 'Vol instruction DC'),
        ('SOLO_SUP', 'Solo supervise'),
        ('SOLO', 'Solo'),
        ('CHECK', 'Vol de controle'),
        ('BRIEFING', 'Briefing sol'),
        ('EXAM', 'Examen'),
    ]

    WEATHER_CONDITIONS = [
        ('CAVOK', 'CAVOK'),
        ('VFR', 'VFR'),
        ('MVFR', 'VFR marginal'),
        ('IFR', 'IFR'),
    ]

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lessons_received',
        verbose_name="Eleve"
    )
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lessons_given',
        verbose_name="Instructeur"
    )
    flight = models.OneToOneField(
        Flight,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lesson_report',
        verbose_name="Vol associe"
    )
    phase = models.ForeignKey(
        TrainingPhase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Phase"
    )

    date = models.DateTimeField("Date de la seance", default=timezone.now)
    lesson_type = models.CharField("Type", max_length=20, choices=LESSON_TYPES, default='INSTRUCTION')

    # Meteo
    weather = models.CharField("Conditions meteo", max_length=10, choices=WEATHER_CONDITIONS, blank=True)
    wind = models.CharField("Vent", max_length=50, blank=True, help_text="Ex: 180/15kt")

    # Contenu pedagogique
    title = models.CharField("Theme de la seance", max_length=100)
    briefing_content = models.TextField("Contenu briefing", blank=True)
    objectives = models.TextField("Objectifs de la seance", blank=True)

    # Exercices travailles
    exercises_practiced = models.ManyToManyField(
        TrainingExercise,
        blank=True,
        related_name='lessons',
        verbose_name="Exercices travailles"
    )

    # Evaluation
    strong_points = models.TextField("Points forts", blank=True)
    areas_to_improve = models.TextField("Points a ameliorer", blank=True)
    comments = models.TextField("Commentaire instructeur")
    next_steps = models.TextField("A travailler prochainement", blank=True)
    grade = models.PositiveSmallIntegerField("Note globale", choices=GRADES, default=3)

    # Autorisation
    solo_authorized = models.BooleanField("Solo autorise", default=False)
    solo_authorization_notes = models.TextField("Notes autorisation solo", blank=True)

    # Signature
    instructor_signature = models.BooleanField("Signe par instructeur", default=True)
    student_signature = models.BooleanField("Vu par eleve", default=False)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Lecon / Seance"
        verbose_name_plural = "Livret de progression"
        ordering = ['-date']

    def __str__(self):
        return f"{self.date.strftime('%d/%m/%Y')} - {self.student.last_name} ({self.title})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Mettre a jour la progression de l'eleve sur les exercices travailles
        if self.exercises_practiced.exists():
            try:
                progression = self.student.training_progression
                for exercise in self.exercises_practiced.all():
                    ep, created = ExerciseProgress.objects.get_or_create(
                        student_progression=progression,
                        exercise=exercise,
                        defaults={'level': 'P', 'last_practiced': self.date.date()}
                    )
                    if not created:
                        ep.last_practiced = self.date.date()
                        # Ne pas retrograder automatiquement
                        if ep.level == '-':
                            ep.level = 'P'
                        ep.save()
            except StudentProgression.DoesNotExist:
                pass


class LessonExerciseEvaluation(models.Model):
    """
    Evaluation detaillee d'un exercice lors d'une lecon.
    """
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='exercise_evaluations')
    exercise = models.ForeignKey(TrainingExercise, on_delete=models.CASCADE)
    level_before = models.CharField("Niveau avant", max_length=1, choices=ExerciseProgress.LEVELS, blank=True)
    level_after = models.CharField("Niveau apres", max_length=1, choices=ExerciseProgress.LEVELS)
    notes = models.TextField("Commentaires", blank=True)

    class Meta:
        verbose_name = "Evaluation exercice"
        verbose_name_plural = "Evaluations exercices"
        unique_together = ['lesson', 'exercise']

    def __str__(self):
        return f"{self.lesson} - {self.exercise.code}: {self.level_after}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Mettre a jour la progression globale de l'eleve
        try:
            progression = self.lesson.student.training_progression
            ep, created = ExerciseProgress.objects.get_or_create(
                student_progression=progression,
                exercise=self.exercise,
                defaults={'level': self.level_after, 'last_practiced': self.lesson.date.date()}
            )
            if not created:
                ep.level = self.level_after
                ep.last_practiced = self.lesson.date.date()
                ep.save()
        except StudentProgression.DoesNotExist:
            pass
