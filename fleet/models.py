from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import date


class Aircraft(models.Model):
    """
    Fiche aeronef complete conforme EASA Part-M.
    """
    STATUS_CHOICES = [
        ('AVAILABLE', 'Disponible'),
        ('MAINTENANCE', 'En Maintenance'),
        ('GROUNDED', 'Cloue au sol (Panne)'),
        ('RESERVED', 'Reserve (Admin)'),
    ]

    FUEL_TYPES = [
        ('100LL', '100LL (Avgas)'),
        ('UL91', 'UL91 (Sans plomb)'),
        ('JETA1', 'JET-A1 (Kerosene)'),
        ('MOGAS', 'Mogas (Auto)'),
    ]

    AIRCRAFT_CATEGORIES = [
        ('SEP', 'Monomoteur Piston'),
        ('MEP', 'Multimoteur Piston'),
        ('SET', 'Monomoteur Turboprop'),
        ('MET', 'Multimoteur Turboprop'),
        ('ULM', 'ULM'),
    ]

    # ========== IDENTIFICATION ==========
    registration = models.CharField("Immatriculation", max_length=10, unique=True)
    model_name = models.CharField("Modele", max_length=50)
    manufacturer = models.CharField("Constructeur", max_length=50, blank=True)
    serial_number = models.CharField("Numero de serie", max_length=50, blank=True)
    year_of_manufacture = models.PositiveIntegerField("Annee construction", null=True, blank=True)
    category = models.CharField("Categorie", max_length=10, choices=AIRCRAFT_CATEGORIES, default='SEP')

    # ========== CONFIGURATION ==========
    num_seats = models.PositiveSmallIntegerField("Nombre de places", default=4)
    fuel_type = models.CharField("Type carburant", max_length=10, choices=FUEL_TYPES, default='100LL')
    fuel_capacity = models.DecimalField("Capacite carburant (L)", max_digits=6, decimal_places=1, default=0)
    usable_fuel = models.DecimalField("Carburant utilisable (L)", max_digits=6, decimal_places=1, default=0)
    fuel_consumption = models.DecimalField("Consommation horaire (L/h)", max_digits=5, decimal_places=1, default=0)
    oil_capacity = models.DecimalField("Capacite huile (L)", max_digits=4, decimal_places=1, default=0)

    # ========== PERFORMANCES ==========
    cruise_speed = models.PositiveIntegerField("Vitesse croisiere (kt)", null=True, blank=True)
    max_range = models.PositiveIntegerField("Distance franchissable (NM)", null=True, blank=True)
    mtow = models.PositiveIntegerField("Masse max decollage (kg)", null=True, blank=True)
    empty_weight = models.PositiveIntegerField("Masse a vide (kg)", null=True, blank=True)

    # ========== DOCUMENTS LEGAUX (Part-M) ==========
    # CDN - Certificat de Navigabilite
    cdn_number = models.CharField("Numero CDN", max_length=50, blank=True)
    cdn_issue_date = models.DateField("Date emission CDN", null=True, blank=True)
    cdn_expiry_date = models.DateField("Date expiration CDN", null=True, blank=True)
    cdn_scan = models.FileField("Scan CDN", upload_to='fleet/documents/', blank=True, null=True)

    # Certificat d'Immatriculation
    registration_certificate_date = models.DateField("Date certificat immat.", null=True, blank=True)
    registration_certificate_scan = models.FileField("Scan certificat immat.", upload_to='fleet/documents/', blank=True, null=True)

    # Licence de station d'aeronef (radio)
    radio_license_number = models.CharField("Numero licence radio", max_length=50, blank=True)
    radio_license_expiry = models.DateField("Expiration licence radio", null=True, blank=True)

    # Assurance
    insurance_company = models.CharField("Compagnie assurance", max_length=100, blank=True)
    insurance_policy_number = models.CharField("Numero police", max_length=50, blank=True)
    insurance_expiry = models.DateField("Expiration assurance", null=True, blank=True)
    insurance_scan = models.FileField("Scan assurance", upload_to='fleet/documents/', blank=True, null=True)

    # Manuel de vol
    flight_manual_scan = models.FileField("Manuel de vol (PDF)", upload_to='fleet/manuals/', blank=True, null=True)

    # ========== SUIVI TECHNIQUE (COMPTEURS) ==========
    # Cellule
    current_hours = models.DecimalField("Heures cellule", max_digits=10, decimal_places=2, default=0.00)
    cycles_count = models.PositiveIntegerField("Cycles cellule", default=0, help_text="Nombre de vols")

    # Moteur
    engine_model = models.CharField("Modele moteur", max_length=50, blank=True)
    engine_serial = models.CharField("N. serie moteur", max_length=50, blank=True)
    engine_hours = models.DecimalField("Heures moteur", max_digits=10, decimal_places=2, default=0.00)
    engine_tbo = models.PositiveIntegerField("TBO moteur (h)", default=2000, help_text="Time Before Overhaul")
    engine_tsoh = models.DecimalField("Heures depuis revision (TSOH)", max_digits=10, decimal_places=2, default=0.00)
    engine_overhaul_date = models.DateField("Date derniere revision moteur", null=True, blank=True)

    # Helice
    propeller_model = models.CharField("Modele helice", max_length=50, blank=True)
    propeller_serial = models.CharField("N. serie helice", max_length=50, blank=True)
    propeller_hours = models.DecimalField("Heures helice", max_digits=10, decimal_places=2, default=0.00)
    propeller_tbo = models.PositiveIntegerField("TBO helice (h)", null=True, blank=True)

    # ========== EQUIPEMENTS ==========
    has_gps = models.BooleanField("GPS", default=False)
    gps_model = models.CharField("Modele GPS", max_length=50, blank=True)
    has_autopilot = models.BooleanField("Pilote automatique", default=False)
    has_transponder = models.BooleanField("Transpondeur", default=True)
    transponder_mode = models.CharField("Mode transpondeur", max_length=20, default="Mode S")
    has_adsb = models.BooleanField("ADS-B Out", default=False)
    has_efis = models.BooleanField("EFIS/Glass cockpit", default=False)
    has_vor = models.BooleanField("VOR", default=True)
    has_ils = models.BooleanField("ILS", default=False)
    has_dme = models.BooleanField("DME", default=False)
    has_adf = models.BooleanField("ADF", default=False)
    equipment_notes = models.TextField("Notes equipements", blank=True)

    # ========== TARIFICATION ==========
    hourly_rate = models.DecimalField("Tarif horaire solo (Euros)", max_digits=6, decimal_places=2)
    hourly_rate_instruction = models.DecimalField(
        "Tarif horaire instruction (Euros)",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Tarif avec instructeur (hors frais FI)"
    )
    instruction_fee = models.DecimalField(
        "Frais instruction/heure (Euros)",
        max_digits=5,
        decimal_places=2,
        default=50.00
    )

    # ========== STATUT & META ==========
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    image = models.ImageField("Photo", upload_to='fleet/photos/', blank=True, null=True)
    notes = models.TextField("Notes", blank=True)
    is_club_owned = models.BooleanField("Propriete du club", default=True)
    owner_name = models.CharField("Proprietaire", max_length=100, blank=True, help_text="Si non club")

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Aeronef"
        verbose_name_plural = "Aeronefs"
        ordering = ['registration']

    def __str__(self):
        return f"{self.registration} - {self.model_name}"

    # ========== PROPRIETES CALCULEES ==========
    @property
    def engine_hours_remaining(self):
        """Heures restantes avant TBO moteur."""
        return self.engine_tbo - self.engine_tsoh

    @property
    def engine_life_percentage(self):
        """Pourcentage de vie moteur utilisee."""
        if self.engine_tbo == 0:
            return 0
        return round((self.engine_tsoh / self.engine_tbo) * 100, 1)

    @property
    def is_cdn_valid(self):
        """Verifie si le CDN est valide."""
        if not self.cdn_expiry_date:
            return False
        return self.cdn_expiry_date >= date.today()

    @property
    def is_insurance_valid(self):
        """Verifie si l'assurance est valide."""
        if not self.insurance_expiry:
            return False
        return self.insurance_expiry >= date.today()

    @property
    def is_airworthy(self):
        """Verifie si l'avion est en etat de navigabilite."""
        return (
            self.status == 'AVAILABLE' and
            self.is_cdn_valid and
            self.is_insurance_valid and
            not self.has_overdue_maintenance
        )

    @property
    def has_overdue_maintenance(self):
        """Verifie si une echeance de maintenance est depassee."""
        for deadline in self.deadlines.all():
            if deadline.is_overdue():
                return True
        return False

    @property
    def next_maintenance(self):
        """Retourne la prochaine echeance de maintenance."""
        upcoming = []
        today = date.today()

        for deadline in self.deadlines.all():
            if deadline.due_at_date and deadline.due_at_date >= today:
                upcoming.append((deadline.due_at_date, deadline))
            if deadline.due_at_hours and deadline.due_at_hours >= self.current_hours:
                # Estimer la date basee sur l'usage moyen
                upcoming.append((None, deadline))

        if upcoming:
            # Retourner celle avec la date la plus proche
            dated = [u for u in upcoming if u[0]]
            if dated:
                return min(dated, key=lambda x: x[0])[1]
            return upcoming[0][1]
        return None


class Flight(models.Model):
    """
    Carnet de route electronique (Tech Log).
    Conforme aux exigences reglementaires.
    """
    FLIGHT_TYPES = [
        ('LOCAL', 'Local'),
        ('NAV', 'Navigation'),
        ('INSTRUCTION', 'Instruction'),
        ('CHECK', 'Controle'),
        ('EXAM', 'Examen'),
        ('FERRY', 'Convoyage'),
        ('MAINTENANCE', 'Vol maintenance'),
    ]

    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='flights')
    pilot = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flights')

    # Second pilote / Instructeur
    copilot = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='flights_as_copilot',
        verbose_name="Second pilote/Instructeur"
    )

    date = models.DateField(default=timezone.now)
    flight_type = models.CharField("Type de vol", max_length=20, choices=FLIGHT_TYPES, default='LOCAL')

    # Aerodromes
    departure_airport = models.CharField("Aerodrome depart", max_length=10, default="LFNE")
    arrival_airport = models.CharField("Aerodrome arrivee", max_length=10, default="LFNE")
    route = models.CharField("Route/Escales", max_length=200, blank=True)

    # Compteurs (Horametre)
    hour_meter_start = models.DecimalField("Compteur Depart", max_digits=10, decimal_places=2)
    hour_meter_end = models.DecimalField("Compteur Arrivee", max_digits=10, decimal_places=2)

    # Horaires (Tech Log)
    block_off = models.TimeField("Bloc Depart", null=True, blank=True)
    takeoff_time = models.TimeField("Decollage", null=True, blank=True)
    landing_time = models.TimeField("Atterrissage", null=True, blank=True)
    block_on = models.TimeField("Bloc Arrivee", null=True, blank=True)

    # Atterrissages
    landings_count = models.PositiveIntegerField("Nb Atterrissages", default=1)
    landings_day = models.PositiveIntegerField("Atterrissages jour", default=1)
    landings_night = models.PositiveIntegerField("Atterrissages nuit", default=0)

    # Carburant & Huile
    fuel_on_departure = models.DecimalField("Carburant depart (L)", max_digits=6, decimal_places=1, null=True, blank=True)
    fuel_on_arrival = models.DecimalField("Carburant arrivee (L)", max_digits=6, decimal_places=1, null=True, blank=True)
    fuel_added = models.DecimalField("Essence Ajoutee (L)", max_digits=6, decimal_places=2, default=0.00)
    oil_added = models.DecimalField("Huile Ajoutee (L)", max_digits=4, decimal_places=2, default=0.00)

    # Observations techniques
    complaints = models.TextField("Observations Techniques (Squawks)", blank=True)
    complaint_resolved = models.BooleanField("Squawk resolu", default=True)
    resolution_notes = models.TextField("Notes resolution", blank=True)

    # Nombre de passagers
    passengers_count = models.PositiveSmallIntegerField("Passagers", default=0)

    # Calculs automatiques
    duration = models.DecimalField("Duree (h)", max_digits=5, decimal_places=2, editable=False)
    cost = models.DecimalField("Cout (Euros)", max_digits=8, decimal_places=2, editable=False)

    # Signature electronique
    pilot_signature = models.BooleanField("Signe par pilote", default=True)
    signature_date = models.DateTimeField("Date signature", auto_now_add=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def save(self, *args, **kwargs):
        # 1. Calcul Duree (Centesimal)
        start = Decimal(str(self.hour_meter_start))
        end = Decimal(str(self.hour_meter_end))
        self.duration = end - start

        # 2. Calcul Cout
        if self.flight_type == 'INSTRUCTION' and self.aircraft.hourly_rate_instruction:
            base_rate = self.aircraft.hourly_rate_instruction
        else:
            base_rate = self.aircraft.hourly_rate

        self.cost = self.duration * base_rate

        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # 3. Debit automatique de la transaction
            from finance.models import Transaction
            Transaction.objects.create(
                user=self.pilot,
                amount=self.cost,
                type='DEBIT',
                description=f"Vol {self.aircraft.registration} ({self.duration}h) - {self.get_flight_type_display()}"
            )

            # 4. Mise a jour des compteurs avion
            self.aircraft.current_hours = self.hour_meter_end
            self.aircraft.engine_hours = self.hour_meter_end
            self.aircraft.engine_tsoh = Decimal(str(self.aircraft.engine_tsoh)) + self.duration
            self.aircraft.propeller_hours = self.hour_meter_end
            self.aircraft.cycles_count += self.landings_count
            self.aircraft.save()

    def __str__(self):
        return f"Vol {self.aircraft.registration} - {self.pilot.username} ({self.date})"

    class Meta:
        verbose_name = "Vol Realise"
        verbose_name_plural = "Vols Realises"
        ordering = ['-date', '-created_at']


class MaintenanceDeadline(models.Model):
    """
    Butees de maintenance (Part-M).
    Ex: Visite 50h, Visite annuelle, CDN, etc.
    """
    DEADLINE_TYPES = [
        ('50H', 'Visite 50 heures'),
        ('100H', 'Visite 100 heures'),
        ('ANNUAL', 'Visite annuelle'),
        ('CDN', 'Renouvellement CDN'),
        ('ENGINE', 'Revision moteur'),
        ('PROPELLER', 'Revision helice'),
        ('AD', 'Consigne de navigabilite (AD)'),
        ('SB', 'Service Bulletin'),
        ('OTHER', 'Autre'),
    ]

    PRIORITY_LEVELS = [
        ('LOW', 'Basse'),
        ('MEDIUM', 'Moyenne'),
        ('HIGH', 'Haute'),
        ('CRITICAL', 'Critique'),
    ]

    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='deadlines')
    deadline_type = models.CharField("Type echeance", max_length=20, choices=DEADLINE_TYPES, default='OTHER')
    title = models.CharField("Titre", max_length=100)
    priority = models.CharField("Priorite", max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')

    # Butees
    due_at_hours = models.DecimalField("Butee Horaire", max_digits=10, decimal_places=2, null=True, blank=True)
    due_at_date = models.DateField("Butee Calendaire", null=True, blank=True)

    # Tolerances
    tolerance_hours = models.DecimalField(
        "Tolerance horaire",
        max_digits=5,
        decimal_places=1,
        default=0,
        help_text="Heures de tolerance apres butee"
    )
    tolerance_days = models.PositiveIntegerField(
        "Tolerance jours",
        default=0,
        help_text="Jours de tolerance apres butee"
    )

    # Reference documentaire
    reference = models.CharField("Reference (AD/SB)", max_length=100, blank=True)

    description = models.TextField("Description/Notes", blank=True)
    estimated_cost = models.DecimalField("Cout estime (Euros)", max_digits=10, decimal_places=2, null=True, blank=True)

    # Statut
    is_completed = models.BooleanField("Effectuee", default=False)
    completion_date = models.DateField("Date realisation", null=True, blank=True)
    completion_hours = models.DecimalField("Heures a la realisation", max_digits=10, decimal_places=2, null=True, blank=True)
    completion_notes = models.TextField("Notes realisation", blank=True)
    completed_by = models.CharField("Realise par (atelier)", max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        verbose_name = "Echeance Maintenance"
        verbose_name_plural = "Echeances Maintenance"
        ordering = ['due_at_date', 'due_at_hours']

    def __str__(self):
        return f"{self.title} - {self.aircraft.registration}"

    def is_overdue(self):
        """Verifie si l'echeance est depassee."""
        if self.is_completed:
            return False

        today = date.today()

        if self.due_at_date:
            if self.due_at_date < today:
                return True

        if self.due_at_hours:
            if self.due_at_hours < self.aircraft.current_hours:
                return True

        return False

    def is_approaching(self, hours_margin=10, days_margin=30):
        """Verifie si l'echeance approche."""
        if self.is_completed or self.is_overdue():
            return False

        today = date.today()

        if self.due_at_date:
            days_remaining = (self.due_at_date - today).days
            if days_remaining <= days_margin:
                return True

        if self.due_at_hours:
            hours_remaining = float(self.due_at_hours - self.aircraft.current_hours)
            if hours_remaining <= hours_margin:
                return True

        return False

    @property
    def hours_remaining(self):
        """Heures restantes avant butee."""
        if not self.due_at_hours:
            return None
        return float(self.due_at_hours - self.aircraft.current_hours)

    @property
    def days_remaining(self):
        """Jours restants avant butee."""
        if not self.due_at_date:
            return None
        return (self.due_at_date - date.today()).days


class MaintenanceLog(models.Model):
    """
    Journal de maintenance (historique des travaux).
    """
    WORK_TYPES = [
        ('SCHEDULED', 'Maintenance programmee'),
        ('UNSCHEDULED', 'Maintenance non programmee'),
        ('REPAIR', 'Reparation'),
        ('MODIFICATION', 'Modification'),
        ('INSPECTION', 'Inspection'),
    ]

    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE, related_name='maintenance_logs')
    related_deadline = models.ForeignKey(
        MaintenanceDeadline,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs'
    )

    work_type = models.CharField("Type travaux", max_length=20, choices=WORK_TYPES)
    date = models.DateField("Date travaux")
    hours_at_work = models.DecimalField("Heures cellule", max_digits=10, decimal_places=2)

    workshop = models.CharField("Atelier/Mecanicien", max_length=100)
    description = models.TextField("Description travaux")
    parts_replaced = models.TextField("Pieces remplacees", blank=True)

    cost = models.DecimalField("Cout (Euros)", max_digits=10, decimal_places=2, null=True, blank=True)
    invoice_number = models.CharField("N. facture", max_length=50, blank=True)
    invoice_scan = models.FileField("Scan facture", upload_to='fleet/invoices/', blank=True, null=True)

    # Approbation
    approved_by = models.CharField("Approuve par (APRS)", max_length=100, blank=True)
    approval_reference = models.CharField("Reference approbation", max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        verbose_name = "Intervention maintenance"
        verbose_name_plural = "Journal de maintenance"
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - {self.aircraft.registration} - {self.get_work_type_display()}"
