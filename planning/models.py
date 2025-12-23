from django.db import models
from django.contrib.auth.models import User
from fleet.models import Aircraft
from django.utils import timezone

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations')
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='reservations')
    
    start_time = models.DateTimeField("Début")
    end_time = models.DateTimeField("Fin")
    
    title = models.CharField("Objet du vol", max_length=100, default="Vol local")
    is_instruction = models.BooleanField("Instruction", default=False)
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='instructed_flights')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.aircraft} ({self.start_time.strftime('%d/%m %H:%M')})"

    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
