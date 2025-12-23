from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date

class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')
    
    # Informations Personnelles
    phone_number = models.CharField("Téléphone", max_length=20, blank=True)
    birth_date = models.DateField("Date de naissance", null=True, blank=True)
    address = models.TextField("Adresse", blank=True)
    
    # Informations Aéronautiques
    license_number = models.CharField("Numéro de Licence", max_length=50, blank=True)
    ffa_number = models.CharField("Numéro FFA", max_length=50, blank=True)
    
    # Validités (Dates d'expiration)
    medical_validity = models.DateField("Validité Médicale (Class 2/LAPL)", null=True, blank=True)
    medical_scan = models.FileField("Scan Médical", upload_to='members/medical/', blank=True, null=True)
    
    top_validity = models.DateField("Validité Licence (SEP)", null=True, blank=True)
    license_scan = models.FileField("Scan Licence", upload_to='members/licenses/', blank=True, null=True)
    
    # Expérience Récente
    @property
    def last_flight_date(self):
        last_flight = self.user.flights.order_by('-date').first()
        return last_flight.date if last_flight else None

    @property
    def landings_last_90_days(self):
        from datetime import timedelta
        from django.db.models import Sum
        cutoff = date.today() - timedelta(days=90)
        total = self.user.flights.filter(date__gte=cutoff).aggregate(Sum('landings_count'))['landings_count__sum']
        return total or 0
    
    # Soldes et Statut
    account_balance = models.DecimalField("Solde Compte (€)", max_digits=10, decimal_places=2, default=0.00)
    is_instructor = models.BooleanField("Est Instructeur", default=False)
    is_student = models.BooleanField("Est Élève", default=False)

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name} ({self.user.username})"

    @property
    def is_medical_valid(self):
        if not self.medical_validity:
            return False
        return self.medical_validity >= date.today()

    @property
    def is_license_valid(self):
        if not self.top_validity:
            return False
        return self.top_validity >= date.today()
        
    class Meta:
        verbose_name = "Membre"
        verbose_name_plural = "Membres"
