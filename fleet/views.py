from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Aircraft, Flight, MaintenanceDeadline
from decimal import Decimal

def is_admin(user):
    """Vérifie si l'utilisateur est staff ou superuser"""
    return user.is_staff or user.is_superuser

def fleet_list(request):
    """Affiche la liste des avions disponibles"""
    aircrafts = Aircraft.objects.all()
    return render(request, 'fleet/fleet_list.html', {'aircrafts': aircrafts})

@login_required
def log_flight(request, aircraft_id):
    """Enregistrement du Carnet de Route (Retour de vol)"""
    aircraft = get_object_or_404(Aircraft, pk=aircraft_id)
    
    if request.method == 'POST':
        try:
            # Récupération des données formulaire
            hour_start = Decimal(request.POST.get('hour_meter_start', '0').replace(',', '.').strip())
            hour_end = Decimal(request.POST.get('hour_meter_end', '0').replace(',', '.').strip())
            
            block_off = request.POST.get('block_off')
            block_on = request.POST.get('block_on')
            takeoff = request.POST.get('takeoff_time') # Optionnel selon formulaire
            landing = request.POST.get('landing_time') # Optionnel selon formulaire
            
            landings = int(request.POST.get('landings_count', 1))
            fuel = Decimal(request.POST.get('fuel_added', '0').replace(',', '.'))
            oil = Decimal(request.POST.get('oil_added', '0').replace(',', '.'))
            complaints = request.POST.get('complaints', '')

            if hour_end <= hour_start:
                 raise ValueError("Le compteur arrivée doit être supérieur au départ.")

            # Création du Vol
            flight = Flight.objects.create(
                aircraft=aircraft,
                pilot=request.user,
                hour_meter_start=hour_start,
                hour_meter_end=hour_end,
                block_off=block_off,
                block_on=block_on,
                takeoff_time=takeoff, # Si vide = None
                landing_time=landing, # Si vide = None
                landings_count=landings,
                fuel_added=fuel,
                oil_added=oil,
                complaints=complaints
            )
            
            # Gestion des pannes (Squawks)
            if complaints and len(complaints.strip()) > 3:
                # On pourrait changer le statut de l'avion ici
                # aircraft.status = 'MAINTENANCE' 
                # aircraft.save()
                messages.warning(request, "Observation enregistrée. L'atelier a été notifié.")

            messages.success(request, f"Vol enregistré ! Temps de vol: {flight.duration}h. Votre compte a été débité.")
            return redirect('profile') # Redirection vers profil
                
        except Exception as e:
            messages.error(request, f"Erreur lors de l'enregistrement : {e}")

    # Pré-remplissage
    current_meter = aircraft.current_hours
    
    return render(request, 'fleet/tech_log_form.html', {
        'aircraft': aircraft,
        'meter_start': current_meter,
        'today': timezone.now().date(),
    })

# =============================================================================
# ADMIN DASHBOARD
# =============================================================================

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Dashboard principal administrateur"""
    aircrafts = Aircraft.objects.all()
    
    # is_overdue() est une méthode, pas un champ - on filtre en Python
    all_deadlines = MaintenanceDeadline.objects.select_related('aircraft')
    maintenance_alerts = [d for d in all_deadlines if d.is_overdue()]
    
    context = {
        'aircrafts': aircrafts,
        'maintenance_alerts': maintenance_alerts,
        'total_aircrafts': aircrafts.count(),
        'active_aircrafts': aircrafts.filter(status='AVAILABLE').count(),
    }
    return render(request, 'fleet/admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def admin_aircraft_add(request):
    """Ajouter un nouvel avion"""
    if request.method == 'POST':
        try:
            aircraft = Aircraft.objects.create(
                registration=request.POST['registration'].upper(),
                model_name=request.POST['model_name'],
                status=request.POST.get('status', 'available'),
                current_hours=Decimal(request.POST.get('current_hours', '0').replace(',', '.')),
                hourly_rate=Decimal(request.POST.get('hourly_rate', '0').replace(',', '.')),
            )
            messages.success(request, f"Avion {aircraft.registration} ajouté avec succès !")
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
    
    return render(request, 'fleet/admin/aircraft_form.html', {'action': 'Ajouter'})

@login_required
@user_passes_test(is_admin)
def admin_aircraft_edit(request, aircraft_id):
    """Modifier un avion existant"""
    aircraft = get_object_or_404(Aircraft, pk=aircraft_id)
    
    if request.method == 'POST':
        try:
            aircraft.registration = request.POST['registration'].upper()
            aircraft.model_name = request.POST['model_name']
            aircraft.status = request.POST.get('status', 'available')
            aircraft.current_hours = Decimal(request.POST.get('current_hours', '0').replace(',', '.'))
            aircraft.hourly_rate = Decimal(request.POST.get('hourly_rate', '0').replace(',', '.'))
            aircraft.save()
            messages.success(request, f"Avion {aircraft.registration} modifié avec succès !")
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
    
    return render(request, 'fleet/admin/aircraft_form.html', {'aircraft': aircraft, 'action': 'Modifier'})

@login_required
@user_passes_test(is_admin)
def admin_aircraft_delete(request, aircraft_id):
    """Supprimer un avion"""
    aircraft = get_object_or_404(Aircraft, pk=aircraft_id)
    
    if request.method == 'POST':
        reg = aircraft.registration
        aircraft.delete()
        messages.success(request, f"Avion {reg} supprimé.")
        return redirect('admin_dashboard')
    
    return render(request, 'fleet/admin/aircraft_delete_confirm.html', {'aircraft': aircraft})

@login_required
@user_passes_test(is_admin)
def admin_maintenance(request):
    """Gestion de la maintenance"""
    deadlines = MaintenanceDeadline.objects.select_related('aircraft').order_by('due_at_date')
    
    return render(request, 'fleet/admin/maintenance.html', {'deadlines': deadlines})

@login_required
@user_passes_test(is_admin)
def admin_maintenance_add(request, aircraft_id):
    """Ajouter une échéance de maintenance"""
    aircraft = get_object_or_404(Aircraft, pk=aircraft_id)
    
    if request.method == 'POST':
        try:
            MaintenanceDeadline.objects.create(
                aircraft=aircraft,
                title=request.POST['title'],
                due_at_date=request.POST.get('due_at_date') or None,
                due_at_hours=Decimal(request.POST.get('due_at_hours', '0').replace(',', '.')) if request.POST.get('due_at_hours') else None,
            )
            messages.success(request, "Échéance ajoutée !")
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
    
    return render(request, 'fleet/admin/maintenance_form.html', {'aircraft': aircraft})
