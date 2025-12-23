import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aeroclub_project.settings')
django.setup()

from django.contrib.auth.models import User
from members.models import Member
from datetime import date, timedelta

def fix_admin_profile():
    try:
        # Récupérer l'utilisateur admin (superuser)
        # On suppose qu'il s'appelle 'admin' ou le premier superuser trouvé
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if not admin_user:
            print("Aucun superutilisateur trouvé.")
            return

        print(f"Superutilisateur trouvé : {admin_user.username}")

        # Créer ou récupérer le profil membre
        member, created = Member.objects.get_or_create(user=admin_user)
        
        # Mettre à jour les champs pour qu'il soit 'valide' pour voler
        member.phone = "0600000000"
        member.account_balance = 500.00 # Solde positif pour réserver !
        
        # Validités dans le futur
        future_date = date.today() + timedelta(days=365)
        member.medical_validity = future_date
        member.license_validity = future_date
        
        member.save()
        
        if created:
            print(f"Profil Membre créé pour {admin_user.username} !")
        else:
            print(f"Profil Membre mis à jour pour {admin_user.username} (Solde=500€, Validités=OK).")

    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    fix_admin_profile()
