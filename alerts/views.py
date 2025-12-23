from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Alert
from .services import get_user_active_alerts, run_all_checks, resolve_outdated_alerts


@login_required
def my_alerts(request):
    """Affiche les alertes de l'utilisateur connecté."""
    alerts = get_user_active_alerts(request.user)

    # Grouper par sévérité
    blocking = alerts.filter(severity='BLOCKING')
    critical = alerts.filter(severity='CRITICAL')
    warning = alerts.filter(severity='WARNING')
    info = alerts.filter(severity='INFO')

    context = {
        'blocking_alerts': blocking,
        'critical_alerts': critical,
        'warning_alerts': warning,
        'info_alerts': info,
        'total_count': alerts.count(),
    }
    return render(request, 'alerts/my_alerts.html', context)


@login_required
@require_POST
def acknowledge_alert(request, alert_id):
    """Marque une alerte comme prise en compte."""
    alert = get_object_or_404(Alert, id=alert_id, user=request.user)
    alert.acknowledge()
    messages.success(request, f"Alerte '{alert.title}' prise en compte.")
    return redirect('alerts:my_alerts')


@staff_member_required
def admin_dashboard(request):
    """Tableau de bord des alertes pour les administrateurs."""
    all_alerts = Alert.objects.filter(status='ACTIVE')

    # Statistiques
    stats = {
        'total': all_alerts.count(),
        'blocking': all_alerts.filter(severity='BLOCKING').count(),
        'critical': all_alerts.filter(severity='CRITICAL').count(),
        'warning': all_alerts.filter(severity='WARNING').count(),
        'info': all_alerts.filter(severity='INFO').count(),
    }

    # Alertes par type
    by_type = {
        'medical': all_alerts.filter(alert_type='MEDICAL'),
        'license': all_alerts.filter(alert_type='LICENSE'),
        'maintenance': all_alerts.filter(alert_type='MAINTENANCE'),
        'balance': all_alerts.filter(alert_type='BALANCE'),
        'experience': all_alerts.filter(alert_type='EXPERIENCE'),
    }

    context = {
        'stats': stats,
        'by_type': by_type,
        'recent_alerts': all_alerts.order_by('-created_at')[:20],
    }
    return render(request, 'alerts/admin_dashboard.html', context)


@staff_member_required
@require_POST
def run_checks(request):
    """Déclenche manuellement la vérification des alertes."""
    total, results = run_all_checks()
    resolved = resolve_outdated_alerts()

    messages.success(
        request,
        f"Vérification terminée : {total} nouvelle(s) alerte(s) créée(s), {resolved} alerte(s) résolue(s)."
    )
    return redirect('alerts:admin_dashboard')


@login_required
def alerts_api(request):
    """API JSON pour récupérer les alertes (HTMX, widgets, etc.)."""
    alerts = get_user_active_alerts(request.user)

    data = {
        'count': alerts.count(),
        'blocking_count': alerts.filter(severity='BLOCKING').count(),
        'alerts': [
            {
                'id': a.id,
                'type': a.alert_type,
                'severity': a.severity,
                'title': a.title,
                'message': a.message,
                'days_until_expiry': a.days_until_expiry,
            }
            for a in alerts[:10]  # Limiter à 10 pour le widget
        ]
    }
    return JsonResponse(data)
