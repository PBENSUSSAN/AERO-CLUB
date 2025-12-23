from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal
from .models import Transaction
from members.models import Member

def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def finance_dashboard(request):
    """Dashboard financier principal"""
    # Stats globales
    total_credits = Transaction.objects.filter(type='CREDIT').aggregate(Sum('amount'))['amount__sum'] or 0
    total_debits = Transaction.objects.filter(type='DEBIT').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Liste des pilotes avec leur solde
    pilots = Member.objects.select_related('user').order_by('user__last_name')
    
    # Dernières transactions
    recent_transactions = Transaction.objects.select_related('user').order_by('-date')[:20]
    
    context = {
        'total_credits': total_credits,
        'total_debits': total_debits,
        'balance': total_credits - total_debits,
        'pilots': pilots,
        'recent_transactions': recent_transactions,
        'pilots_count': pilots.count(),
    }
    return render(request, 'finance/admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def finance_transactions(request):
    """Liste complète des transactions"""
    transactions = Transaction.objects.select_related('user').order_by('-date')
    
    # Filtres optionnels
    user_filter = request.GET.get('user')
    type_filter = request.GET.get('type')
    
    if user_filter:
        transactions = transactions.filter(user_id=user_filter)
    if type_filter:
        transactions = transactions.filter(type=type_filter)
    
    users = User.objects.filter(member_profile__isnull=False).order_by('last_name')
    
    context = {
        'transactions': transactions,
        'users': users,
        'current_user_filter': user_filter,
        'current_type_filter': type_filter,
    }
    return render(request, 'finance/admin/transactions.html', context)

@login_required
@user_passes_test(is_admin)
def finance_credit_account(request, user_id=None):
    """Créditer le compte d'un pilote"""
    pilot = None
    if user_id:
        pilot = get_object_or_404(Member, user_id=user_id)
    
    if request.method == 'POST':
        try:
            target_user_id = request.POST.get('user_id')
            amount = Decimal(request.POST.get('amount', '0').replace(',', '.'))
            description = request.POST.get('description', 'Crédit compte')
            
            if amount <= 0:
                raise ValueError("Le montant doit être positif")
            
            target_user = User.objects.get(pk=target_user_id)
            
            Transaction.objects.create(
                user=target_user,
                amount=amount,
                type='CREDIT',
                description=description
            )
            
            messages.success(request, f"Compte de {target_user.get_full_name() or target_user.username} crédité de {amount}€")
            return redirect('finance_dashboard')
            
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
    
    pilots = Member.objects.select_related('user').order_by('user__last_name')
    
    return render(request, 'finance/admin/credit_form.html', {
        'pilot': pilot,
        'pilots': pilots,
    })

@login_required
@user_passes_test(is_admin)
def finance_pilot_detail(request, user_id):
    """Détail du compte d'un pilote"""
    pilot = get_object_or_404(Member, user_id=user_id)
    transactions = Transaction.objects.filter(user_id=user_id).order_by('-date')
    
    return render(request, 'finance/admin/pilot_detail.html', {
        'pilot': pilot,
        'transactions': transactions,
    })
