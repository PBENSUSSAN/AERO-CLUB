from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from fleet.models import Aircraft
from django.utils import timezone


class Reservation(models.Model):
    """
    Reservation d'un avion avec verification des conditions de vol.
    """
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('CONFIRMED', 'Confirmee'),
        ('CANCELLED', 'Annulee'),
        ('COMPLETED', 'Terminee'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='reservations')

    start_time = models.DateTimeField("Debut")
    end_time = models.DateTimeField("Fin")

    title = models.CharField("Objet du vol", max_length=100, default="Vol local")
    destination = models.CharField("Destination", max_length=100, blank=True)
    is_instruction = models.BooleanField("Instruction", default=False)
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instructed_flights'
    )
    passengers_count = models.PositiveSmallIntegerField("Nombre de passagers", default=0)

    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default='CONFIRMED')

    # Verification des conditions
    eligibility_checked = models.BooleanField("Eligibilite verifiee", default=False)
    eligibility_warnings = models.TextField("Avertissements eligibilite", blank=True)
    force_allowed = models.BooleanField(
        "Autorise malgre avertissements",
        default=False,
        help_text="Cocher si un responsable autorise malgre les restrictions"
    )
    force_allowed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='authorized_reservations',
        verbose_name="Autorise par"
    )

    notes = models.TextField("Notes", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.aircraft} ({self.start_time.strftime('%d/%m %H:%M')})"

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        ordering = ['-start_time']

    def clean(self):
        """Valide la reservation et verifie l'eligibilite du pilote."""
        errors = []

        # Verifier que l'heure de fin est apres l'heure de debut
        if self.start_time and self.end_time:
            if self.end_time <= self.start_time:
                errors.append("L'heure de fin doit etre apres l'heure de debut.")

        # Verifier les chevauchements
        if self.start_time and self.end_time and self.aircraft_id:
            overlapping = Reservation.objects.filter(
                aircraft=self.aircraft,
                status__in=['PENDING', 'CONFIRMED'],
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            ).exclude(pk=self.pk)

            if overlapping.exists():
                errors.append("Cet avion est deja reserve sur ce creneau.")

        if errors:
            raise ValidationError(errors)

    def check_pilot_eligibility(self):
        """
        Verifie l'eligibilite du pilote a voler.
        Retourne (can_fly, warnings, blockers)
        """
        warnings = []
        blockers = []

        try:
            member = self.user.member_profile
        except:
            blockers.append("Profil membre non trouve")
            return False, warnings, blockers

        # Verifications bloquantes
        if not member.is_medical_valid:
            blockers.append("Medical expire ou non renseigne")

        if not member.is_sep_valid and not self.is_instruction:
            blockers.append("Qualification SEP expiree")

        if member.account_balance <= 0:
            blockers.append(f"Solde compte insuffisant ({member.account_balance} EUR)")

        # Vol avec passagers : verification 3 atterrissages / 90 jours
        if self.passengers_count > 0 and not self.is_instruction:
            if member.landings_last_90_days < 3:
                blockers.append(
                    f"Experience recente insuffisante pour emport passagers "
                    f"({member.landings_last_90_days}/3 atterrissages en 90j)"
                )

        # Vol solo sans les 3 atterrissages : warning mais pas bloquant
        if member.landings_last_90_days < 3 and not self.is_instruction:
            if not blockers:  # Si pas deja bloque
                warnings.append(
                    f"Seulement {member.landings_last_90_days} atterrissages en 90 jours. "
                    f"Vol avec instructeur recommande."
                )

        # Verifications non bloquantes (warnings)
        if not member.is_club_subscription_valid:
            warnings.append("Cotisation club expiree")

        if not member.is_ffa_valid:
            warnings.append("Licence FFA expiree")

        if member.account_balance < 100:
            warnings.append(f"Solde compte faible ({member.account_balance} EUR)")

        # Verifier l'avion
        try:
            aircraft = self.aircraft
            if not aircraft.is_airworthy:
                blockers.append("Avion non navigable")
            if aircraft.has_overdue_maintenance:
                warnings.append("Maintenance en retard sur cet avion")
        except:
            pass

        can_fly = len(blockers) == 0
        return can_fly, warnings, blockers

    def save(self, *args, **kwargs):
        # Verifier l'eligibilite avant sauvegarde
        can_fly, warnings, blockers = self.check_pilot_eligibility()

        self.eligibility_checked = True
        all_issues = blockers + warnings
        self.eligibility_warnings = "\n".join(all_issues) if all_issues else ""

        # Si bloque et pas force, lever une erreur
        if not can_fly and not self.force_allowed:
            if not self.is_instruction:  # L'instruction passe toujours
                raise ValidationError(
                    f"Reservation impossible: {'; '.join(blockers)}"
                )

        super().save(*args, **kwargs)
