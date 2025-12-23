import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aeroclub_project.settings')
django.setup()

from django.contrib.auth.models import User
from members.models import Member

def set_roles():
    try:
        # On cible le superuser (admin)
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            print("Admin introuvable.")
            return

        member = admin_user.member_profile
        
        # On active tout pour le test
        member.is_student = True
        member.is_instructor = True
        member.save()
        
        print(f"Rôles mis à jour pour {admin_user.username} : Élève=OUI, Instructeur=OUI")
        print("Les menus devraient apparaître.")

    except Exception as e:
        print(f"Erreur : {e}")

if __name__ == "__main__":
    set_roles()
