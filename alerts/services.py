"""
Service de génération et gestion des alertes automatiques.
À exécuter périodiquement (via Celery, cron, ou commande Django).
"""
from datetime import date, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings

from .models import Alert, AlertConfiguration
from members.models import Member
from fleet.models import Aircraft, MaintenanceDeadline


# Seuils par défaut si pas de configuration
DEFAULT_THRESHOLDS = {
    'days_info': 60,
    'days_warning': 30,
    'days_critical': 7,
}


def get_severity_for_days(days_remaining, config=None):
    """Détermine la sévérité en fonction du nombre de jours restants."""
    if config:
        thresholds = {
            'days_info': config.days_info,
            'days_warning': config.days_warning,
            'days_critical': config.days_critical,
        }
    else:
        thresholds = DEFAULT_THRESHOLDS

    if days_remaining <= 0:
        return 'BLOCKING'
    elif days_remaining <= thresholds['days_critical']:
        return 'CRITICAL'
    elif days_remaining <= thresholds['days_warning']:
        return 'WARNING'
    elif days_remaining <= thresholds['days_info']:
        return 'INFO'
    return None  # Pas encore d'alerte nécessaire


def create_or_update_alert(unique_key, **kwargs):
    """
    Crée une alerte ou met à jour une existante.
    Évite les doublons grâce à unique_key.
    """
    alert, created = Alert.objects.update_or_create(
        unique_key=unique_key,
        defaults=kwargs
    )
    return alert, created


def check_member_medical_alerts():
    """
    Vérifie les certificats médicaux de tous les membres.
    Génère des alertes INFO/WARNING/CRITICAL/BLOCKING selon les échéances.
    """
    today = date.today()
    config = AlertConfiguration.objects.filter(alert_type='MEDICAL', is_active=True).first()

    # Récupérer les seuils
    days_info = config.days_info if config else DEFAULT_THRESHOLDS['days_info']

    # Membres avec médical expirant dans les X jours
    threshold_date = today + timedelta(days=days_info)

    members = Member.objects.filter(
        Q(medical_validity__isnull=False) &
        Q(medical_validity__lte=threshold_date)
    ).select_related('user')

    alerts_created = 0
    for member in members:
        days_remaining = (member.medical_validity - today).days
        severity = get_severity_for_days(days_remaining, config)

        if severity:
            unique_key = f"medical_{member.user.id}_{member.medical_validity.strftime('%Y-%m')}"

            if days_remaining <= 0:
                title = f"Certificat médical EXPIRÉ"
                message = f"Votre certificat médical a expiré le {member.medical_validity.strftime('%d/%m/%Y')}. Vous ne pouvez plus voler tant qu'il n'est pas renouvelé."
            else:
                title = f"Certificat médical expire dans {days_remaining} jour(s)"
                message = f"Votre certificat médical expire le {member.medical_validity.strftime('%d/%m/%Y')}. Pensez à prendre rendez-vous avec un médecin agréé."

            alert, created = create_or_update_alert(
                unique_key=unique_key,
                user=member.user,
                alert_type='MEDICAL',
                severity=severity,
                title=title,
                message=message,
                expires_at=member.medical_validity,
                status='ACTIVE' if severity in ['CRITICAL', 'BLOCKING'] else 'ACTIVE',
            )
            if created:
                alerts_created += 1

    return alerts_created


def check_member_license_alerts():
    """
    Vérifie les licences/qualifications de tous les membres.
    """
    today = date.today()
    config = AlertConfiguration.objects.filter(alert_type='LICENSE', is_active=True).first()
    days_info = config.days_info if config else DEFAULT_THRESHOLDS['days_info']

    threshold_date = today + timedelta(days=days_info)

    members = Member.objects.filter(
        Q(top_validity__isnull=False) &
        Q(top_validity__lte=threshold_date)
    ).select_related('user')

    alerts_created = 0
    for member in members:
        days_remaining = (member.top_validity - today).days
        severity = get_severity_for_days(days_remaining, config)

        if severity:
            unique_key = f"license_{member.user.id}_{member.top_validity.strftime('%Y-%m')}"

            if days_remaining <= 0:
                title = f"Licence/SEP EXPIRÉE"
                message = f"Votre licence a expiré le {member.top_validity.strftime('%d/%m/%Y')}. Contactez un instructeur pour un vol de prorogation."
            else:
                title = f"Licence expire dans {days_remaining} jour(s)"
                message = f"Votre licence expire le {member.top_validity.strftime('%d/%m/%Y')}. Planifiez un vol de prorogation avec un instructeur."

            alert, created = create_or_update_alert(
                unique_key=unique_key,
                user=member.user,
                alert_type='LICENSE',
                severity=severity,
                title=title,
                message=message,
                expires_at=member.top_validity,
            )
            if created:
                alerts_created += 1

    return alerts_created


def check_member_experience_alerts():
    """
    Vérifie l'expérience récente (3 atterrissages en 90 jours).
    """
    today = date.today()

    members = Member.objects.filter(
        is_instructor=False  # Les instructeurs sont exemptés de cette règle simplifiée
    ).select_related('user')

    alerts_created = 0
    for member in members:
        landings = member.landings_last_90_days

        if landings < 3:
            unique_key = f"experience_{member.user.id}_{today.strftime('%Y-%m')}"

            if landings == 0:
                severity = 'CRITICAL'
                title = "Aucun atterrissage depuis 90 jours"
                message = "Vous n'avez effectué aucun atterrissage depuis plus de 90 jours. Un vol avec instructeur est obligatoire avant de voler solo ou d'emporter des passagers."
            else:
                severity = 'WARNING'
                title = f"Expérience récente insuffisante ({landings}/3 atterrissages)"
                message = f"Vous n'avez que {landings} atterrissage(s) sur les 90 derniers jours. Minimum 3 requis pour emporter des passagers (FCL.060)."

            alert, created = create_or_update_alert(
                unique_key=unique_key,
                user=member.user,
                alert_type='EXPERIENCE',
                severity=severity,
                title=title,
                message=message,
            )
            if created:
                alerts_created += 1

    return alerts_created


def check_member_balance_alerts():
    """
    Vérifie les soldes de compte des membres.
    """
    # Seuils de solde
    LOW_BALANCE_WARNING = 100  # €
    LOW_BALANCE_CRITICAL = 50  # €

    members = Member.objects.filter(
        account_balance__lte=LOW_BALANCE_WARNING
    ).select_related('user')

    alerts_created = 0
    for member in members:
        balance = float(member.account_balance)

        if balance <= 0:
            severity = 'BLOCKING'
            title = "Solde insuffisant - Réservations bloquées"
            message = f"Votre solde est de {balance:.2f} €. Rechargez votre compte pour pouvoir réserver."
        elif balance <= LOW_BALANCE_CRITICAL:
            severity = 'CRITICAL'
            title = f"Solde très bas : {balance:.2f} €"
            message = f"Votre solde est de {balance:.2f} €. Pensez à recharger votre compte."
        else:
            severity = 'WARNING'
            title = f"Solde bas : {balance:.2f} €"
            message = f"Votre solde est de {balance:.2f} €. Rechargez votre compte pour éviter toute interruption."

        unique_key = f"balance_{member.user.id}_{severity}"

        alert, created = create_or_update_alert(
            unique_key=unique_key,
            user=member.user,
            alert_type='BALANCE',
            severity=severity,
            title=title,
            message=message,
        )
        if created:
            alerts_created += 1

    return alerts_created


def check_aircraft_maintenance_alerts():
    """
    Vérifie les échéances de maintenance des avions.
    """
    today = date.today()
    config = AlertConfiguration.objects.filter(alert_type='MAINTENANCE', is_active=True).first()

    alerts_created = 0

    for deadline in MaintenanceDeadline.objects.select_related('aircraft').all():
        aircraft = deadline.aircraft
        severity = None
        days_remaining = None
        hours_remaining = None

        # Vérification butée calendaire
        if deadline.due_at_date:
            days_remaining = (deadline.due_at_date - today).days
            severity = get_severity_for_days(days_remaining, config)

        # Vérification butée horaire
        if deadline.due_at_hours:
            hours_remaining = float(deadline.due_at_hours - aircraft.current_hours)

            # Convertir en "équivalent jours" pour la sévérité (10h de vol = ~7 jours en moyenne)
            if hours_remaining <= 0:
                severity = 'BLOCKING'
            elif hours_remaining <= 5:
                severity = 'CRITICAL' if severity != 'BLOCKING' else severity
            elif hours_remaining <= 10:
                severity = 'WARNING' if severity not in ['BLOCKING', 'CRITICAL'] else severity
            elif hours_remaining <= 20:
                severity = 'INFO' if severity is None else severity

        if severity:
            unique_key = f"maintenance_{aircraft.id}_{deadline.id}"

            # Construire le message
            parts = []
            if days_remaining is not None:
                if days_remaining <= 0:
                    parts.append(f"Butée calendaire dépassée de {-days_remaining} jour(s)")
                else:
                    parts.append(f"{days_remaining} jour(s) avant butée calendaire ({deadline.due_at_date.strftime('%d/%m/%Y')})")

            if hours_remaining is not None:
                if hours_remaining <= 0:
                    parts.append(f"Butée horaire dépassée de {-hours_remaining:.1f}h")
                else:
                    parts.append(f"{hours_remaining:.1f}h avant butée horaire ({deadline.due_at_hours}h)")

            if severity == 'BLOCKING':
                title = f"⛔ {aircraft.registration} - {deadline.title} - BLOQUÉ"
            else:
                title = f"{aircraft.registration} - {deadline.title}"

            message = f"Échéance maintenance '{deadline.title}' pour {aircraft.registration}.\n" + "\n".join(parts)
            if deadline.description:
                message += f"\n\nNotes: {deadline.description}"

            alert, created = create_or_update_alert(
                unique_key=unique_key,
                alert_type='MAINTENANCE',
                severity=severity,
                title=title,
                message=message,
                related_aircraft=aircraft,
                expires_at=deadline.due_at_date,
            )
            if created:
                alerts_created += 1

    return alerts_created


def run_all_checks():
    """
    Exécute toutes les vérifications d'alertes.
    À appeler quotidiennement.
    """
    results = {
        'medical': check_member_medical_alerts(),
        'license': check_member_license_alerts(),
        'experience': check_member_experience_alerts(),
        'balance': check_member_balance_alerts(),
        'maintenance': check_aircraft_maintenance_alerts(),
    }

    total = sum(results.values())
    return total, results


def resolve_outdated_alerts():
    """
    Résout automatiquement les alertes qui ne sont plus pertinentes.
    Ex: médical renouvelé, solde rechargé, etc.
    """
    today = date.today()
    resolved_count = 0

    # Alertes médicales pour membres avec médical valide
    for alert in Alert.objects.filter(alert_type='MEDICAL', status='ACTIVE'):
        if alert.user:
            try:
                member = alert.user.member_profile
                if member.medical_validity and member.medical_validity > today:
                    alert.resolve()
                    resolved_count += 1
            except Member.DoesNotExist:
                pass

    # Alertes licence pour membres avec licence valide
    for alert in Alert.objects.filter(alert_type='LICENSE', status='ACTIVE'):
        if alert.user:
            try:
                member = alert.user.member_profile
                if member.top_validity and member.top_validity > today:
                    alert.resolve()
                    resolved_count += 1
            except Member.DoesNotExist:
                pass

    # Alertes solde pour membres avec solde positif
    for alert in Alert.objects.filter(alert_type='BALANCE', status='ACTIVE'):
        if alert.user:
            try:
                member = alert.user.member_profile
                if member.account_balance > 100:  # Seuil de résolution
                    alert.resolve()
                    resolved_count += 1
            except Member.DoesNotExist:
                pass

    # Alertes expérience pour membres avec 3+ atterrissages
    for alert in Alert.objects.filter(alert_type='EXPERIENCE', status='ACTIVE'):
        if alert.user:
            try:
                member = alert.user.member_profile
                if member.landings_last_90_days >= 3:
                    alert.resolve()
                    resolved_count += 1
            except Member.DoesNotExist:
                pass

    return resolved_count


def get_user_active_alerts(user):
    """
    Récupère les alertes actives pour un utilisateur.
    """
    return Alert.objects.filter(
        Q(user=user) | Q(user__isnull=True),  # Alertes perso + alertes globales
        status='ACTIVE'
    ).order_by('-severity', '-created_at')


def get_blocking_alerts(user):
    """
    Récupère uniquement les alertes bloquantes pour un utilisateur.
    """
    return Alert.objects.filter(
        user=user,
        severity='BLOCKING',
        status='ACTIVE'
    )


def has_blocking_alerts(user):
    """
    Vérifie si l'utilisateur a des alertes bloquantes.
    """
    return get_blocking_alerts(user).exists()
