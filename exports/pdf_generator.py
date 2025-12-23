"""
Generateur de documents PDF pour l'aeroclub.
Utilise ReportLab pour la generation.
"""
from io import BytesIO
from datetime import date, datetime
from decimal import Decimal

from django.http import HttpResponse
from django.db.models import Sum

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas


# ============================================================
# STYLES
# ============================================================

def get_styles():
    """Retourne les styles personnalises pour les documents."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='TitleMain',
        parent=styles['Title'],
        fontSize=18,
        spaceAfter=20,
        textColor=colors.HexColor('#1a365d'),
    ))

    styles.add(ParagraphStyle(
        name='Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#4a5568'),
        spaceAfter=10,
    ))

    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2d3748'),
        spaceBefore=15,
        spaceAfter=10,
        borderPadding=5,
    ))

    styles.add(ParagraphStyle(
        name='TableHeader',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.white,
        alignment=TA_CENTER,
    ))

    styles.add(ParagraphStyle(
        name='TableCell',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_LEFT,
    ))

    styles.add(ParagraphStyle(
        name='Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#718096'),
        alignment=TA_CENTER,
    ))

    return styles


def get_table_style():
    """Style de base pour les tableaux."""
    return TableStyle([
        # En-tete
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),

        # Corps
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),

        # Grille
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Alternance couleurs
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
    ])


# ============================================================
# RELEVE DE COMPTE PILOTE
# ============================================================

def generate_account_statement(member, start_date=None, end_date=None):
    """
    Genere un releve de compte PDF pour un membre.

    Args:
        member: Instance de Member
        start_date: Date de debut (optionnel)
        end_date: Date de fin (optionnel)

    Returns:
        HttpResponse avec le PDF
    """
    from finance.models import Transaction

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = get_styles()
    elements = []

    # Filtrer les transactions
    transactions = Transaction.objects.filter(user=member.user).order_by('-date')
    if start_date:
        transactions = transactions.filter(date__gte=start_date)
    if end_date:
        transactions = transactions.filter(date__lte=end_date)

    # En-tete
    elements.append(Paragraph("AEROCLUB", styles['TitleMain']))
    elements.append(Paragraph("Releve de compte pilote", styles['Subtitle']))
    elements.append(Spacer(1, 10*mm))

    # Informations membre
    info_data = [
        ['Nom:', f"{member.user.first_name} {member.user.last_name}"],
        ['N. Adherent:', member.member_number or '-'],
        ['N. Licence:', member.license_number or '-'],
        ['Date edition:', datetime.now().strftime('%d/%m/%Y %H:%M')],
    ]

    if start_date or end_date:
        period = ""
        if start_date:
            period += f"Du {start_date.strftime('%d/%m/%Y')}"
        if end_date:
            period += f" au {end_date.strftime('%d/%m/%Y')}"
        info_data.append(['Periode:', period])

    info_table = Table(info_data, colWidths=[3*cm, 8*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10*mm))

    # Solde actuel
    balance_color = colors.HexColor('#38a169') if member.account_balance >= 0 else colors.HexColor('#e53e3e')
    elements.append(Paragraph(
        f"<b>Solde actuel: {member.account_balance:.2f} EUR</b>",
        ParagraphStyle('Balance', parent=styles['Normal'], fontSize=14, textColor=balance_color)
    ))
    elements.append(Spacer(1, 10*mm))

    # Tableau des transactions
    elements.append(Paragraph("Historique des mouvements", styles['SectionTitle']))

    if transactions.exists():
        table_data = [['Date', 'Libelle', 'Debit', 'Credit', 'Solde']]

        # Calculer le solde cumule
        running_balance = member.account_balance
        rows = []
        for tx in transactions:
            if tx.type == 'DEBIT':
                running_balance += tx.amount
            else:
                running_balance -= tx.amount

        # Remettre dans l'ordre chronologique pour le calcul
        running_balance = member.account_balance
        for tx in reversed(list(transactions)):
            if tx.type == 'CREDIT':
                running_balance -= tx.amount

        # Construire le tableau
        current_balance = running_balance
        for tx in transactions.order_by('date'):
            if tx.type == 'CREDIT':
                debit = ''
                credit = f"{tx.amount:.2f}"
                current_balance += tx.amount
            else:
                debit = f"{tx.amount:.2f}"
                credit = ''
                current_balance -= tx.amount

            table_data.append([
                tx.date.strftime('%d/%m/%Y'),
                tx.description[:40] + '...' if len(tx.description) > 40 else tx.description,
                debit,
                credit,
                f"{current_balance:.2f}",
            ])

        table = Table(table_data, colWidths=[2.5*cm, 8*cm, 2*cm, 2*cm, 2.5*cm])
        style = get_table_style()
        # Alignement des montants a droite
        style.add('ALIGN', (2, 0), (-1, -1), 'RIGHT')
        table.setStyle(style)
        elements.append(table)

        # Totaux
        elements.append(Spacer(1, 5*mm))
        total_credits = transactions.filter(type='CREDIT').aggregate(Sum('amount'))['amount__sum'] or 0
        total_debits = transactions.filter(type='DEBIT').aggregate(Sum('amount'))['amount__sum'] or 0

        totals_data = [
            ['Total credits:', f"+{total_credits:.2f} EUR"],
            ['Total debits:', f"-{total_debits:.2f} EUR"],
            ['Nombre de mouvements:', str(transactions.count())],
        ]
        totals_table = Table(totals_data, colWidths=[4*cm, 4*cm])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        elements.append(totals_table)
    else:
        elements.append(Paragraph("Aucune transaction sur cette periode.", styles['Normal']))

    # Pied de page
    elements.append(Spacer(1, 20*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e0')))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph(
        f"Document genere automatiquement le {datetime.now().strftime('%d/%m/%Y a %H:%M')}",
        styles['Footer']
    ))
    elements.append(Paragraph("Aeroclub - Aerodrome de Salon-Eyguieres (LFNE)", styles['Footer']))

    doc.build(elements)

    # Creer la reponse HTTP
    buffer.seek(0)
    filename = f"releve_compte_{member.user.username}_{date.today().strftime('%Y%m%d')}.pdf"

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


# ============================================================
# CARNET DE ROUTE (TECH LOG)
# ============================================================

def generate_flight_log(aircraft, start_date=None, end_date=None):
    """
    Genere un carnet de route PDF pour un aeronef.

    Args:
        aircraft: Instance de Aircraft
        start_date: Date de debut (optionnel)
        end_date: Date de fin (optionnel)

    Returns:
        HttpResponse avec le PDF
    """
    from fleet.models import Flight

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1*cm,
        leftMargin=1*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm,
    )

    styles = get_styles()
    elements = []

    # Filtrer les vols
    flights = Flight.objects.filter(aircraft=aircraft).order_by('-date')
    if start_date:
        flights = flights.filter(date__gte=start_date)
    if end_date:
        flights = flights.filter(date__lte=end_date)

    # En-tete
    elements.append(Paragraph("CARNET DE ROUTE", styles['TitleMain']))
    elements.append(Paragraph(f"{aircraft.registration} - {aircraft.model_name}", styles['Subtitle']))
    elements.append(Spacer(1, 8*mm))

    # Informations aeronef
    info_data = [
        ['Immatriculation:', aircraft.registration, 'Modele:', aircraft.model_name],
        ['N. Serie:', aircraft.serial_number or '-', 'Constructeur:', aircraft.manufacturer or '-'],
        ['Heures cellule:', f"{aircraft.current_hours:.2f}h", 'Cycles:', str(aircraft.cycles_count)],
        ['Date edition:', datetime.now().strftime('%d/%m/%Y'), '', ''],
    ]

    info_table = Table(info_data, colWidths=[3*cm, 4.5*cm, 3*cm, 4.5*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))

    # Tableau des vols
    elements.append(Paragraph("Historique des vols", styles['SectionTitle']))

    if flights.exists():
        table_data = [[
            'Date', 'Pilote', 'Dep', 'Arr',
            'Cpt Dep', 'Cpt Arr', 'Duree',
            'Att.', 'Ess.', 'Observations'
        ]]

        for flight in flights.order_by('date'):
            pilot_name = f"{flight.pilot.last_name[:10]}"

            table_data.append([
                flight.date.strftime('%d/%m'),
                pilot_name,
                flight.departure_airport,
                flight.arrival_airport,
                f"{flight.hour_meter_start:.2f}",
                f"{flight.hour_meter_end:.2f}",
                f"{flight.duration:.2f}",
                str(flight.landings_count),
                f"{flight.fuel_added:.0f}L" if flight.fuel_added else '-',
                (flight.complaints[:20] + '...') if flight.complaints and len(flight.complaints) > 20 else (flight.complaints or '-'),
            ])

        table = Table(
            table_data,
            colWidths=[1.5*cm, 2*cm, 1.2*cm, 1.2*cm, 1.5*cm, 1.5*cm, 1.3*cm, 1*cm, 1.3*cm, 4*cm]
        )
        style = get_table_style()
        style.add('FONTSIZE', (0, 0), (-1, -1), 7)
        table.setStyle(style)
        elements.append(table)

        # Statistiques
        elements.append(Spacer(1, 8*mm))
        total_hours = flights.aggregate(Sum('duration'))['duration__sum'] or 0
        total_landings = flights.aggregate(Sum('landings_count'))['landings_count__sum'] or 0
        total_fuel = flights.aggregate(Sum('fuel_added'))['fuel_added__sum'] or 0

        stats_data = [
            ['Nombre de vols:', str(flights.count()), 'Heures totales:', f"{total_hours:.2f}h"],
            ['Atterrissages:', str(total_landings), 'Carburant:', f"{total_fuel:.0f}L"],
        ]

        stats_table = Table(stats_data, colWidths=[3*cm, 3*cm, 3*cm, 3*cm])
        stats_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#edf2f7')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(stats_table)
    else:
        elements.append(Paragraph("Aucun vol enregistre sur cette periode.", styles['Normal']))

    # Pied de page
    elements.append(Spacer(1, 15*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e0')))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph(
        f"Carnet de route - {aircraft.registration} - Edite le {datetime.now().strftime('%d/%m/%Y')}",
        styles['Footer']
    ))

    doc.build(elements)

    buffer.seek(0)
    filename = f"carnet_route_{aircraft.registration}_{date.today().strftime('%Y%m%d')}.pdf"

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


# ============================================================
# FACTURE / RECU
# ============================================================

def generate_invoice(transaction):
    """
    Genere une facture/recu PDF pour une transaction.

    Args:
        transaction: Instance de Transaction

    Returns:
        HttpResponse avec le PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = get_styles()
    elements = []

    # En-tete
    elements.append(Paragraph("AEROCLUB", styles['TitleMain']))
    elements.append(Paragraph("Aerodrome de Salon-Eyguieres (LFNE)", styles['Subtitle']))
    elements.append(Spacer(1, 15*mm))

    # Type de document
    doc_type = "RECU DE CREDIT" if transaction.type == 'CREDIT' else "FACTURE"
    elements.append(Paragraph(doc_type, ParagraphStyle(
        'DocType', parent=styles['Normal'], fontSize=16,
        alignment=TA_CENTER, textColor=colors.HexColor('#2d3748')
    )))
    elements.append(Spacer(1, 10*mm))

    # Informations
    try:
        member = transaction.user.member_profile
        member_info = f"{member.user.first_name} {member.user.last_name}"
        member_number = member.member_number or '-'
    except:
        member_info = transaction.user.username
        member_number = '-'

    info_data = [
        ['N. Document:', f"{transaction.id:06d}"],
        ['Date:', transaction.date.strftime('%d/%m/%Y %H:%M')],
        ['Membre:', member_info],
        ['N. Adherent:', member_number],
    ]

    info_table = Table(info_data, colWidths=[4*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 15*mm))

    # Detail
    elements.append(Paragraph("Detail", styles['SectionTitle']))

    detail_data = [
        ['Description', 'Montant'],
        [transaction.description, f"{transaction.amount:.2f} EUR"],
    ]

    detail_table = Table(detail_data, colWidths=[12*cm, 4*cm])
    style = get_table_style()
    style.add('ALIGN', (1, 0), (1, -1), 'RIGHT')
    detail_table.setStyle(style)
    elements.append(detail_table)
    elements.append(Spacer(1, 5*mm))

    # Total
    total_style = ParagraphStyle(
        'Total', parent=styles['Normal'], fontSize=14,
        alignment=TA_RIGHT, textColor=colors.HexColor('#2d3748')
    )
    sign = "+" if transaction.type == 'CREDIT' else "-"
    elements.append(Paragraph(
        f"<b>TOTAL: {sign}{transaction.amount:.2f} EUR</b>",
        total_style
    ))

    # Pied de page
    elements.append(Spacer(1, 30*mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e0')))
    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph(
        "Document genere automatiquement - Conserver pour vos archives",
        styles['Footer']
    ))
    elements.append(Paragraph("Aeroclub - contact@aeroclub.fr", styles['Footer']))

    doc.build(elements)

    buffer.seek(0)
    doc_prefix = "recu" if transaction.type == 'CREDIT' else "facture"
    filename = f"{doc_prefix}_{transaction.id:06d}.pdf"

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response
