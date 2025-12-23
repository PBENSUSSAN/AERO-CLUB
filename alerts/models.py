from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Alert(models.Model):
    """
    Alertes générées automatiquement pour les expirations et échéances.
    """
    ALERT_TYPES = [
        ('MEDICAL', 'Certificat Médical'),
        ('LICENSE', 'Licence / Qualification'),
        ('CDN', 'Certificat de Navigabilité'),
        ('MAINTENANCE', 'Échéance Maintenance'),
        ('BALANCE', 'Solde Compte Bas'),
        ('EXPERIENCE', 'Expérience Récente'),
        ('INSURANCE', 'Assurance'),
        ('COTISATION', 'Cotisation Club'),
    ]

    SEVERITY_LEVELS = [
        ('INFO', 'Information'),
        ('WARNING', 'Avertissement'),
        ('CRITICAL', 'Critique'),
        ('BLOCKING', 'Bloquant'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ACKNOWLEDGED', 'Prise en compte'),
        ('RESOLVED', 'Résolue'),
        ('EXPIRED', 'Expirée'),
    ]

    # Destinataire (pilote ou null si alerte globale/flotte)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True,
        verbose_name="Membre concerné"
    )

    # Type et sévérité
    alert_type = models.CharField("Type d'alerte", max_length=20, choices=ALERT_TYPES)
    severity = models.CharField("Sévérité", max_length=20, choices=SEVERITY_LEVELS, default='WARNING')
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    # Contenu
    title = models.CharField("Titre", max_length=200)
    message = models.TextField("Message détaillé")

    # Dates
    created_at = models.DateTimeField("Créée le", auto_now_add=True)
    expires_at = models.DateField("Date d'expiration concernée", null=True, blank=True)
    acknowledged_at = models.DateTimeField("Prise en compte le", null=True, blank=True)
    resolved_at = models.DateTimeField("Résolue le", null=True, blank=True)

    # Référence optionnelle vers l'objet concerné
    related_aircraft = models.ForeignKey(
        'fleet.Aircraft',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alerts',
        verbose_name="Avion concerné"
    )

    # Éviter les doublons
    unique_key = models.CharField(
        "Clé unique",
        max_length=200,
        unique=True,
        help_text="Empêche la création de doublons (ex: medical_user_5_2025-06)"
    )

    # Notification envoyée ?
    email_sent = models.BooleanField("Email envoyé", default=False)
    email_sent_at = models.DateTimeField("Email envoyé le", null=True, blank=True)

    class Meta:
        verbose_name = "Alerte"
        verbose_name_plural = "Alertes"
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['alert_type', 'status']),
            models.Index(fields=['severity', 'status']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "Système"
        return f"[{self.get_severity_display()}] {self.title} - {user_str}"

    def acknowledge(self):
        """Marquer l'alerte comme prise en compte."""
        self.status = 'ACKNOWLEDGED'
        self.acknowledged_at = timezone.now()
        self.save()

    def resolve(self):
        """Marquer l'alerte comme résolue."""
        self.status = 'RESOLVED'
        self.resolved_at = timezone.now()
        self.save()

    @property
    def is_blocking(self):
        """Indique si cette alerte doit bloquer les réservations."""
        return self.severity == 'BLOCKING' and self.status == 'ACTIVE'

    @property
    def days_until_expiry(self):
        """Nombre de jours avant l'expiration."""
        if self.expires_at:
            delta = self.expires_at - timezone.now().date()
            return delta.days
        return None


class AlertConfiguration(models.Model):
    """
    Configuration des seuils d'alerte par type.
    Permet de personnaliser quand les alertes sont déclenchées.
    """
    alert_type = models.CharField(
        "Type d'alerte",
        max_length=20,
        choices=Alert.ALERT_TYPES,
        unique=True
    )

    # Seuils en jours avant expiration
    days_info = models.PositiveIntegerField(
        "Jours avant (Info)",
        default=60,
        help_text="Nombre de jours avant expiration pour alerte INFO"
    )
    days_warning = models.PositiveIntegerField(
        "Jours avant (Avertissement)",
        default=30,
        help_text="Nombre de jours avant expiration pour alerte WARNING"
    )
    days_critical = models.PositiveIntegerField(
        "Jours avant (Critique)",
        default=7,
        help_text="Nombre de jours avant expiration pour alerte CRITICAL"
    )

    # Blocage
    block_on_expiry = models.BooleanField(
        "Bloquer à expiration",
        default=True,
        help_text="Bloquer les réservations si expiré"
    )

    # Notifications
    send_email = models.BooleanField("Envoyer email", default=True)

    # Actif
    is_active = models.BooleanField("Actif", default=True)

    class Meta:
        verbose_name = "Configuration Alerte"
        verbose_name_plural = "Configurations Alertes"

    def __str__(self):
        return f"Config: {self.get_alert_type_display()}"
