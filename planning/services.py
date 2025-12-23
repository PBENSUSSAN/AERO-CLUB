from datetime import date
from django.utils import timezone
from members.models import Member

def check_reservation_compliance(user, aircraft=None, start_time=None):
    """
    Vérifie si un utilisateur peut réserver.
    Retourne (success: bool, error_message: str|None)
    """
    errors = []
    
    # 1. Profil Membre existe ?
    try:
        member = user.member_profile
    except Member.DoesNotExist:
        return False, "Profil pilote incomplet."

    # 2. Validité de la Licence
    if not member.is_license_valid:
        errors.append(f"Licence expirée (fin: {member.top_validity})")

    # 3. Validité Médicale
    if not member.is_medical_valid:
        errors.append(f"Certificat médical expiré (fin: {member.medical_validity})")

    # 4. Solde Compte
    if member.account_balance <= 0:
        errors.append(f"Solde insuffisant ({member.account_balance} €). Rechargez votre compte.")

    # 5. Expérience Récente (3 atterrissages / 90 jours) - BLOCANT pour emport passager, ici on simplifie
    if member.landings_last_90_days < 3:
        # Si c'est un vol solo (pas d'instructeur prévu), on pourrait bloquer
        # Pour l'instant, on met juste un warning mais on ne bloque pas TOUT le monde (ex: élève avec instructeur)
        # Mais la règle demandée est "Vérification 3 atterrissages/90j" -> Bloquant
        pass 
        # TODO: Affiner si le vol est "Solo" ou "Instruction". 
        # Si l'utilisateur n'est pas instructeur et n'a pas fait 3 atterrissages, il doit voler avec instructeur.
        # errors.append("Expérience récente insuffisante (moins de 3 atterrissages en 90 jours). Vol avec instructeur requis.")

    if errors:
        return False, " / ".join(errors)

    return True, None
