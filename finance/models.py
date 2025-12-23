from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('CREDIT', 'Crédit (Versement)'),
        ('DEBIT', 'Débit (Vol/Achat)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField("Montant (€)", max_digits=10, decimal_places=2) # Toujours positif
    type = models.CharField("Type", max_length=10, choices=TRANSACTION_TYPES)
    description = models.CharField("Libellé", max_length=200)
    date = models.DateTimeField("Date", default=timezone.now)
    
    # Lien optionnel vers un vol ou un avion (pour traçabilité)
    # flight = models.ForeignKey('fleet.Flight', ...) # À venir

    def save(self, *args, **kwargs):
        # Mise à jour automatique du solde du membre
        super().save(*args, **kwargs)
        member = self.user.member_profile
        if self.type == 'CREDIT':
            member.account_balance += self.amount
        else:
            member.account_balance -= self.amount
        member.save()

    def __str__(self):
        sign = "+" if self.type == 'CREDIT' else "-"
        return f"{self.date.strftime('%d/%m/%Y')} - {self.user.username} : {sign}{self.amount}€ ({self.description})"

    class Meta:
        verbose_name = "Écriture Comptable"
        verbose_name_plural = "Écritures Comptables"
        ordering = ['-date']
