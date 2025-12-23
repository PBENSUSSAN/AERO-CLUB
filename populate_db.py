import os
import django
import random
from datetime import date, timedelta

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aeroclub_project.settings')
django.setup()

from django.contrib.auth.models import User
from members.models import Member
from fleet.models import Aircraft, MaintenanceDeadline

def create_fake_data():
    print("Début du peuplement de la base de données...")

    # 1. DELETE EXISTING DATA
    Member.objects.all().delete()
    Aircraft.objects.all().delete()
    User.objects.filter(is_superuser=False).delete()

    # 2. CREATE AIRCRAFTS
    aircrafts_data = [
        {"reg": "F-GABC", "model": "Robin DR400-120", "rate": 145.00, "hours": 2450.5},
        {"reg": "F-HJOY", "model": "Cessna 172 Skyhawk", "rate": 165.00, "hours": 4100.2},
        {"reg": "F-PLOP", "model": "Piper PA28", "rate": 155.00, "hours": 3200.0, "status": "MAINTENANCE"},
        {"reg": "F-BXTD", "model": "Cap 10 (Voltige)", "rate": 190.00, "hours": 1100.0},
    ]

    for data in aircrafts_data:
        ac = Aircraft.objects.create(
            registration=data["reg"],
            model_name=data["model"],
            hourly_rate=data["rate"],
            current_hours=data["hours"],
            status=data.get("status", "AVAILABLE")
        )
        print(f"Avion créé : {ac}")

        # Add maintenance deadline
        MaintenanceDeadline.objects.create(
            aircraft=ac,
            title="Visite 50h",
            due_at_hours=data["hours"] + 45, # Proche de l'échéance
            description="Vérification bougies et filtres."
        )

    # 3. CREATE MEMBERS
    users_data = [
        {"username": "jdupont", "first": "Jean", "last": "DUPONT", "license": "PPL-12345", "balance": 150.0},
        {"username": "mcurie", "first": "Marie", "last": "CURIE", "license": "PPL-67890", "balance": -50.0}, # Solde négatif
        {"username": "tpesquet", "first": "Thomas", "last": "PESQUET", "license": "ATPL-00001", "balance": 5000.0, "instructor": True},
    ]

    for data in users_data:
        u = User.objects.create_user(username=data["username"], email=f"{data['username']}@test.com", password="password123")
        u.first_name = data["first"]
        u.last_name = data["last"]
        u.save()

        Member.objects.create(
            user=u,
            license_number=data["license"],
            medical_validity=date.today() + timedelta(days=random.randint(30, 700)),
            top_validity=date.today() + timedelta(days=random.randint(100, 700)),
            account_balance=data["balance"],
            is_instructor=data.get("instructor", False),
            phone_number="0601020304"
        )
        print(f"Membre créé : {u.username}")

    print("Terminé ! Données fictives générées.")

if __name__ == "__main__":
    create_fake_data()
