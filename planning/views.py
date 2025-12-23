from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Reservation
from fleet.models import Aircraft
from members.models import Member
import json
from datetime import datetime
from django.utils import timezone
from .services import check_reservation_compliance

@login_required
def calendar_view(request):
    """Affiche le calendrier principal"""
    aircrafts = Aircraft.objects.filter(status__in=['AVAILABLE', 'MAINTENANCE'])
    return render(request, 'planning/calendrier.html', {'aircrafts': aircrafts})

def events_api(request):
    """Renvoie les réservations au format JSON pour FullCalendar"""
    reservations = Reservation.objects.all()
    events = []
    
    colors = {
        'F-GABC': '#3b82f6', 
        'F-HJOY': '#10b981', 
        'F-PLOP': '#ef4444', 
        'F-BXTD': '#f59e0b', 
    }

    for resa in reservations:
        color = colors.get(resa.aircraft.registration, '#6b7280')
        events.append({
            'title': f"{resa.user.last_name} - {resa.aircraft.registration}",
            'start': resa.start_time.isoformat(),
            'end': resa.end_time.isoformat(),
            'backgroundColor': color,
            'borderColor': color,
            'extendedProps': {
                'aircraft': resa.aircraft.registration,
                'pilot': f"{resa.user.first_name} {resa.user.last_name}"
            }
        })
    
    return JsonResponse(events, safe=False)

@csrf_exempt
@login_required
@require_POST
def create_reservation(request):
    try:
        data = json.loads(request.body)
        aircraft_id = data.get('aircraft')
        start_str = data.get('start')
        end_str = data.get('end')
        
        # Validations basiques
        if not all([aircraft_id, start_str, end_str]):
            return JsonResponse({'success': False, 'error': 'Données manquantes'})
            
        aircraft = Aircraft.objects.get(id=aircraft_id)
        start_time = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
        
        # --- NOUVEAU : Compliance Check ---
        is_compliant, error_msg = check_reservation_compliance(request.user, aircraft, start_time)
        if not is_compliant:
            return JsonResponse({'success': False, 'error': f"REFUSÉ : {error_msg}"})
        # ----------------------------------

        end_time = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
        
        # Logic 1: Solde positif ? (Déjà couvert par services.py mais double check ok)
        # try:
        #     member = request.user.member_profile
        #     if member.account_balance <= 0:
        #          return JsonResponse({'success': False, 'error': 'Solde insuffisant pour réserver.'})
        # except Member.DoesNotExist:
        #      return JsonResponse({'success': False, 'error': 'Profil pilote introuvable.'})

        # Logic 2: Dispo machine ? (Collision naive)
        overlapping = Reservation.objects.filter(
            aircraft=aircraft,
            start_time__lt=end_time, 
            end_time__gt=start_time
        ).exists()
        
        if overlapping:
            return JsonResponse({'success': False, 'error': 'Avion déjà réservé sur ce créneau.'})

        # Création
        Reservation.objects.create(
            user=request.user,
            aircraft=aircraft,
            start_time=start_time,
            end_time=end_time,
            title=f"Vol {request.user.last_name}"
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
