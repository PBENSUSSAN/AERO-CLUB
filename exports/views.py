"""
Vues pour l'export de documents PDF.
"""
from datetime import date, timedelta
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404

from members.models import Member
from fleet.models import Aircraft
from finance.models import Transaction
from .pdf_generator import (
    generate_account_statement,
    generate_flight_log,
    generate_invoice,
)


@login_required
def my_account_statement(request):
    """
    Telecharge le releve de compte de l'utilisateur connecte.
    Parametre optionnel: ?period=month|quarter|year|all
    """
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        raise Http404("Profil membre non trouve")

    # Gerer la periode
    period = request.GET.get('period', 'month')
    today = date.today()

    if period == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'quarter':
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_start_month, day=1)
        end_date = today
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:  # all
        start_date = None
        end_date = None

    return generate_account_statement(member, start_date, end_date)


@staff_member_required
def member_account_statement(request, member_id):
    """
    Telecharge le releve de compte d'un membre (admin).
    """
    member = get_object_or_404(Member, id=member_id)

    period = request.GET.get('period', 'all')
    today = date.today()

    if period == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'quarter':
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_start_month, day=1)
        end_date = today
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:
        start_date = None
        end_date = None

    return generate_account_statement(member, start_date, end_date)


@staff_member_required
def aircraft_flight_log(request, aircraft_id):
    """
    Telecharge le carnet de route d'un aeronef.
    Parametre optionnel: ?period=month|quarter|year|all
    """
    aircraft = get_object_or_404(Aircraft, id=aircraft_id)

    period = request.GET.get('period', 'month')
    today = date.today()

    if period == 'month':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'quarter':
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start_date = today.replace(month=quarter_start_month, day=1)
        end_date = today
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
        end_date = today
    else:
        start_date = None
        end_date = None

    return generate_flight_log(aircraft, start_date, end_date)


@login_required
def transaction_invoice(request, transaction_id):
    """
    Telecharge la facture/recu d'une transaction.
    L'utilisateur ne peut telecharger que ses propres transactions.
    """
    transaction = get_object_or_404(Transaction, id=transaction_id)

    # Verification des droits
    if transaction.user != request.user and not request.user.is_staff:
        raise Http404("Transaction non trouvee")

    return generate_invoice(transaction)


@staff_member_required
def all_transactions_pdf(request):
    """
    Liste de toutes les transactions (admin) - a implementer si necessaire.
    """
    # TODO: Implementer si besoin
    raise Http404("Non implemente")
