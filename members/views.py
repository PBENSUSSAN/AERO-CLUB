from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Member, MemberDocument
import qrcode
from io import BytesIO
import base64
import json


@login_required
def profile_view(request):
    """Tableau de bord du pilote"""
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        member = None

    transactions = request.user.transactions.all()[:10]

    # Documents recents
    documents = []
    if member:
        documents = member.documents.filter(is_current=True).order_by('document_type')

    return render(request, 'members/profile.html', {
        'member': member,
        'transactions': transactions,
        'documents': documents,
    })


@login_required
def documents_view(request):
    """Gestion des documents (Upload)"""
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        messages.error(request, "Profil membre non trouve.")
        return redirect('home')

    # Documents actuels par type
    current_documents = {}
    for doc in member.documents.filter(is_current=True):
        current_documents[doc.document_type] = doc

    # Historique complet
    all_documents = member.documents.all().order_by('-upload_date')[:20]

    return render(request, 'members/documents.html', {
        'member': member,
        'current_documents': current_documents,
        'all_documents': all_documents,
        'document_types': MemberDocument.DOCUMENT_TYPES,
    })


@login_required
def upload_document(request):
    """Upload d'un nouveau document"""
    if request.method != 'POST':
        return redirect('documents')

    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        messages.error(request, "Profil membre non trouve.")
        return redirect('home')

    document_type = request.POST.get('document_type')
    title = request.POST.get('title', '')
    file = request.FILES.get('file')
    issue_date = request.POST.get('issue_date') or None
    expiry_date = request.POST.get('expiry_date') or None

    if not file:
        messages.error(request, "Veuillez selectionner un fichier.")
        return redirect('documents')

    if not document_type:
        messages.error(request, "Veuillez selectionner un type de document.")
        return redirect('documents')

    # Generer un titre par defaut si non fourni
    if not title:
        for code, label in MemberDocument.DOCUMENT_TYPES:
            if code == document_type:
                title = label
                break

    # Creer le document
    doc = MemberDocument.objects.create(
        member=member,
        document_type=document_type,
        title=title,
        file=file,
        issue_date=issue_date,
        expiry_date=expiry_date,
        status='PENDING',
        is_current=True,
    )

    # Mettre a jour les dates sur le profil membre si pertinent
    if expiry_date:
        if document_type == 'MEDICAL':
            member.medical_validity = expiry_date
            member.save()
        elif document_type == 'FFA':
            member.ffa_subscription_validity = expiry_date
            member.save()
        elif document_type == 'INSURANCE':
            member.insurance_validity = expiry_date
            member.save()
        elif document_type == 'CLUB':
            member.club_subscription_validity = expiry_date
            member.save()

    messages.success(request, f"Document '{title}' uploade avec succes. En attente de validation.")
    return redirect('documents')


@login_required
def delete_document(request, document_id):
    """Supprimer un document (seulement si PENDING)"""
    try:
        member = request.user.member_profile
        doc = get_object_or_404(MemberDocument, pk=document_id, member=member)

        if doc.status == 'PENDING':
            doc.delete()
            messages.success(request, "Document supprime.")
        else:
            messages.error(request, "Impossible de supprimer un document valide.")
    except Member.DoesNotExist:
        messages.error(request, "Profil membre non trouve.")

    return redirect('documents')


@login_required
def document_status_api(request):
    """API JSON pour verifier le statut des documents"""
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        return JsonResponse({'error': 'Member not found'}, status=404)

    documents = []
    for doc in member.documents.filter(is_current=True):
        documents.append({
            'type': doc.document_type,
            'type_display': doc.get_document_type_display(),
            'title': doc.title,
            'status': doc.status,
            'expiry_date': doc.expiry_date.isoformat() if doc.expiry_date else None,
            'is_expired': doc.is_expired,
            'days_until_expiry': doc.days_until_expiry,
        })

    return JsonResponse({
        'member': member.full_name,
        'documents': documents,
        'can_fly': member.can_fly_solo,
    })


@login_required
def member_qrcode(request):
    """Genere un QR code pour identification rapide du membre."""
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        return HttpResponse("Profil non trouve", status=404)

    # Donnees a encoder dans le QR code
    qr_data = {
        'id': member.id,
        'member_number': member.member_number or '',
        'name': member.full_name,
        'license': member.license_type,
        'can_fly': member.can_fly_solo,
        'medical_valid': member.is_medical_valid,
        'sep_valid': member.is_sep_valid,
    }

    # Generer le QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Retourner l'image
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return HttpResponse(buffer.getvalue(), content_type='image/png')


@login_required
def member_card(request):
    """Affiche la carte de membre avec QR code."""
    try:
        member = request.user.member_profile
    except Member.DoesNotExist:
        messages.error(request, "Profil membre non trouve.")
        return redirect('home')

    # Generer le QR code en base64 pour inclusion dans le HTML
    qr_data = {
        'id': member.id,
        'member_number': member.member_number or '',
        'name': member.full_name,
    }

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=2,
    )
    qr.add_data(json.dumps(qr_data))
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render(request, 'members/card.html', {
        'member': member,
        'qr_base64': qr_base64,
    })


def scan_member(request, member_id):
    """API pour scanner un membre (verification rapide)."""
    try:
        member = Member.objects.get(pk=member_id)
    except Member.DoesNotExist:
        return JsonResponse({'error': 'Membre non trouve'}, status=404)

    return JsonResponse({
        'success': True,
        'member': {
            'id': member.id,
            'name': member.full_name,
            'member_number': member.member_number,
            'license_type': member.license_type,
            'can_fly_solo': member.can_fly_solo,
            'can_carry_passengers': member.can_carry_passengers,
            'medical_valid': member.is_medical_valid,
            'medical_expiry': member.medical_validity.isoformat() if member.medical_validity else None,
            'sep_valid': member.is_sep_valid,
            'sep_expiry': member.sep_validity.isoformat() if member.sep_validity else None,
            'landings_90_days': member.landings_last_90_days,
            'account_balance': float(member.account_balance),
            'qualifications': member.qualifications_list,
        },
        'warnings': get_member_warnings(member),
    })


def get_member_warnings(member):
    """Genere les avertissements pour un membre."""
    warnings = []

    if not member.is_medical_valid:
        warnings.append({'type': 'error', 'message': 'Medical expire ou manquant'})

    if not member.is_sep_valid:
        warnings.append({'type': 'error', 'message': 'Qualification SEP expiree'})

    if member.landings_last_90_days < 3:
        warnings.append({
            'type': 'warning',
            'message': f'Seulement {member.landings_last_90_days} atterrissages en 90 jours (3 requis)'
        })

    if member.account_balance <= 0:
        warnings.append({'type': 'error', 'message': 'Solde compte insuffisant'})
    elif member.account_balance < 100:
        warnings.append({'type': 'warning', 'message': f'Solde faible: {member.account_balance} EUR'})

    if not member.is_club_subscription_valid:
        warnings.append({'type': 'warning', 'message': 'Cotisation club expiree'})

    if not member.is_ffa_valid:
        warnings.append({'type': 'warning', 'message': 'Licence FFA expiree'})

    return warnings
