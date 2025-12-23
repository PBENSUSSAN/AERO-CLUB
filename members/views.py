from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Member
from finance.models import Transaction

@login_required
def profile_view(request):
    """Tableau de bord du pilote"""
    # Si le user n'a pas de profil membre (cas admin pur), on gère l'erreur ou on crée
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        # Fallback pour admin ou user sans profil
        member = None

    transactions = request.user.transactions.all()[:10] # 10 dernières opérations

    return render(request, 'membres/profil.html', {
        'member': member,
        'transactions': transactions
    })

@login_required
def documents_view(request):
    """Gestion des documents (Upload)"""
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        # On pourrait rediriger ou créer
        return render(request, 'membres/profil.html', {'error': 'Profil non trouvé'})

    if request.method == 'POST':
        # 1. Upload Fichiers
        if request.FILES.get('license_scan'):
            member.license_scan = request.FILES['license_scan']
        if request.FILES.get('medical_scan'):
            member.medical_scan = request.FILES['medical_scan']
            
        # 2. Mise à jour dates (si modifiées)
        if request.POST.get('top_validity'):
            member.top_validity = request.POST.get('top_validity')
        if request.POST.get('medical_validity'):
            member.medical_validity = request.POST.get('medical_validity')
            
        member.save()
        
        # Feedback (idéalement avec messages framework, ici simple redirect)
        return render(request, 'membres/documents.html', {'member': member, 'success': True})

    return render(request, 'membres/documents.html', {'member': member})
