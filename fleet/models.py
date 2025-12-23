from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal

class Aircraft(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Disponible'),
        ('MAINTENANCE', 'En Maintenance'),
        ('GROUNDED', 'Cloué au sol (Panne)'),
    ]

    registration = models.CharField("Immatriculation", max_length=10, unique=True) # ex: F-GABC
    model_name = models.CharField("Modèle", max_length=50) # ex: DR400-120
    image = models.ImageField("Photo", upload_to='aircrafts/', blank=True, null=True)
    
    # Tarification
    hourly_rate = models.DecimalField("Tarif Horaire (€)", max_digits=6, decimal_places=2, help_text="Coût à l'heure de vol")
    
    # Suivi technique (Compteurs)
    current_hours = models.DecimalField("Heures Totales (Cellule)", max_digits=10, decimal_places=2, default=0.00)
    
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    
    def __str__(self):
        return f"{self.registration} - {self.model_name}"

    class Meta:
        verbose_name = "Avion"
        verbose_name_plural = "Avions"

class Flight(models.Model):
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='flights')
    pilot = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flights')
    date = models.DateField(default=timezone.now)
    
    # Compteurs (Horamètre)
    hour_meter_start = models.DecimalField("Compteur Départ", max_digits=10, decimal_places=2)
    hour_meter_end = models.DecimalField("Compteur Arrivée", max_digits=10, decimal_places=2)
    
    # Carnet de Route (Tech Log)
    block_off = models.TimeField("Bloc Départ", null=True, blank=True)
    takeoff_time = models.TimeField("Décollage", null=True, blank=True)
    landing_time = models.TimeField("Atterrissage", null=True, blank=True)
    block_on = models.TimeField("Bloc Arrivée", null=True, blank=True)
    
    landings_count = models.IntegerField("Nb Atterrissages", default=1)
    
    fuel_added = models.DecimalField("Essence Ajoutée (L)", max_digits=6, decimal_places=2, default=0.00)
    oil_added = models.DecimalField("Huile Ajoutée (L)", max_digits=4, decimal_places=2, default=0.00)
    
    complaints = models.TextField("Observations Techniques (Squawks)", blank=True)
    
    duration = models.DecimalField("Durée (h)", max_digits=5, decimal_places=2, editable=False)
    cost = models.DecimalField("Coût (€)", max_digits=8, decimal_places=2, editable=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 1. Calcul Durée (Centimal)
        # Gestion si passé en float
        start = Decimal(str(self.hour_meter_start))
        end = Decimal(str(self.hour_meter_end))
        self.duration = end - start
        
        # 2. Calcul Coût
        self.cost = self.duration * self.aircraft.hourly_rate
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # 3. Débit automatique de la transaction
            from finance.models import Transaction
            Transaction.objects.create(
                user=self.pilot,
                amount=self.cost,
                type='DEBIT',
                description=f"Vol {self.aircraft.registration} ({self.duration}h)"
            )
            
            # 4. Mise à jour de l'avion
            self.aircraft.current_hours = self.hour_meter_end
            self.aircraft.save()

    def __str__(self):
        return f"Vol {self.aircraft.registration} - {self.pilot.username} ({self.date})"
        
    class Meta:
        verbose_name = "Vol Réalisé"
        verbose_name_plural = "Vols Réalisés"
        ordering = ['-date', '-created_at']

class MaintenanceDeadline(models.Model):
    """Butées de maintenance (ex: Prochaine 50h à 1240h ou au 12/12/2025)"""
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='deadlines')
    title = models.CharField("Type d'échéance", max_length=100) # ex: Visite 50h
    
    due_at_hours = models.DecimalField("Butée Horaire", max_digits=10, decimal_places=2, null=True, blank=True)
    due_at_date = models.DateField("Butée Calendaire", null=True, blank=True)
    
    description = models.TextField("Notes", blank=True)

    def is_overdue(self):
        # Vérification simple (à affiner avec la logique métier plus tard)
        if self.due_at_date and self.due_at_date < timezone.now().date():
            return True
        if self.due_at_hours and self.due_at_hours < self.aircraft.current_hours:
            return True
        return False

    def __str__(self):
        return f"{self.title} pour {self.aircraft.registration}"

    class Meta:
        verbose_name = "Échéance Maintenance"
        verbose_name_plural = "Échéances Maintenance"
