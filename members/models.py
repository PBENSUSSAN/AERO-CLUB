from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta


class Member(models.Model):
    """
    Profil pilote complet conforme aux standards EASA/DGAC/FFA.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member_profile')

    # ========== INFORMATIONS PERSONNELLES ==========
    phone_number = models.CharField("Telephone", max_length=20, blank=True)
    emergency_contact = models.CharField("Contact urgence", max_length=100, blank=True)
    emergency_phone = models.CharField("Tel. urgence", max_length=20, blank=True)
    birth_date = models.DateField("Date de naissance", null=True, blank=True)
    birth_place = models.CharField("Lieu de naissance", max_length=100, blank=True)
    nationality = models.CharField("Nationalite", max_length=50, default="Francaise")
    address = models.TextField("Adresse", blank=True)
    city = models.CharField("Ville", max_length=100, blank=True)
    postal_code = models.CharField("Code postal", max_length=10, blank=True)
    photo = models.ImageField("Photo identite", upload_to='members/photos/', blank=True, null=True)

    # ========== INFORMATIONS AEROCLUB ==========
    member_number = models.CharField("N. Adherent Club", max_length=20, blank=True, unique=True, null=True)
    join_date = models.DateField("Date adhesion", null=True, blank=True)
    ffa_number = models.CharField("N. Licence FFA", max_length=50, blank=True)

    # ========== LICENCE PILOTE (EASA Part-FCL) ==========
    LICENSE_TYPES = [
        ('NONE', 'Aucune licence'),
        ('LAPL', 'LAPL(A) - Light Aircraft Pilot Licence'),
        ('PPL', 'PPL(A) - Private Pilot Licence'),
        ('CPL', 'CPL(A) - Commercial Pilot Licence'),
        ('ATPL', 'ATPL(A) - Airline Transport Pilot Licence'),
        ('ULM', 'Brevet ULM'),
        ('BB', 'Brevet de Base (ancien)'),
    ]

    license_type = models.CharField(
        "Type de licence",
        max_length=10,
        choices=LICENSE_TYPES,
        default='NONE'
    )
    license_number = models.CharField("Numero de Licence", max_length=50, blank=True)
    license_issue_date = models.DateField("Date obtention licence", null=True, blank=True)
    license_authority = models.CharField("Autorite delivrance", max_length=50, default="DGAC France")
    license_scan = models.FileField("Scan Licence", upload_to='members/licenses/', blank=True, null=True)

    # ========== QUALIFICATIONS / RATINGS ==========
    # SEP - Single Engine Piston (Land)
    has_sep = models.BooleanField("SEP(Land) - Monomoteur", default=False)
    sep_validity = models.DateField("Validite SEP", null=True, blank=True)

    # MEP - Multi Engine Piston
    has_mep = models.BooleanField("MEP(Land) - Multimoteur", default=False)
    mep_validity = models.DateField("Validite MEP", null=True, blank=True)

    # IR - Instrument Rating
    has_ir = models.BooleanField("IR - Vol aux instruments", default=False)
    ir_validity = models.DateField("Validite IR", null=True, blank=True)

    # Night Rating
    has_night = models.BooleanField("Qualification Nuit", default=False)
    night_validity = models.DateField("Validite Nuit", null=True, blank=True)

    # Mountain Rating
    has_mountain = models.BooleanField("Qualification Montagne", default=False)
    mountain_wheels = models.BooleanField("Montagne Roues", default=False)
    mountain_skis = models.BooleanField("Montagne Skis", default=False)

    # Aerobatics
    has_aerobatics = models.BooleanField("Qualification Voltige", default=False)

    # Towing
    has_towing = models.BooleanField("Remorquage planeurs", default=False)

    # FI - Flight Instructor
    has_fi = models.BooleanField("FI(A) - Instructeur Vol", default=False)
    fi_validity = models.DateField("Validite FI", null=True, blank=True)

    # FE - Flight Examiner
    has_fe = models.BooleanField("FE(A) - Examinateur", default=False)

    # ========== CERTIFICAT MEDICAL ==========
    MEDICAL_CLASSES = [
        ('NONE', 'Aucun'),
        ('LAPL', 'Medical LAPL'),
        ('CLASS2', 'Classe 2'),
        ('CLASS1', 'Classe 1'),
    ]

    medical_class = models.CharField(
        "Classe medicale",
        max_length=10,
        choices=MEDICAL_CLASSES,
        default='NONE'
    )
    medical_validity = models.DateField("Validite Medicale", null=True, blank=True)
    medical_restrictions = models.TextField("Restrictions medicales", blank=True)
    medical_scan = models.FileField("Scan Medical", upload_to='members/medical/', blank=True, null=True)

    # ========== RADIOTELEPHONIE ==========
    has_radio_certificate = models.BooleanField("Certificat Radiotelephonie", default=False)
    radio_certificate_number = models.CharField("N. Certificat Radio", max_length=50, blank=True)
    radio_certificate_date = models.DateField("Date certificat radio", null=True, blank=True)
    has_english_level = models.BooleanField("Niveau Anglais OACI", default=False)
    english_level = models.PositiveSmallIntegerField("Niveau Anglais (1-6)", null=True, blank=True)
    english_validity = models.DateField("Validite Anglais", null=True, blank=True)

    # ========== COTISATIONS ==========
    club_subscription_validity = models.DateField("Validite cotisation club", null=True, blank=True)
    ffa_subscription_validity = models.DateField("Validite licence FFA", null=True, blank=True)
    insurance_validity = models.DateField("Validite assurance RC", null=True, blank=True)

    # ========== EXPERIENCE ==========
    total_flight_hours = models.DecimalField(
        "Heures totales",
        max_digits=7,
        decimal_places=1,
        default=0,
        help_text="Heures de vol totales declarees"
    )
    solo_date = models.DateField("Date premier solo", null=True, blank=True)
    license_date = models.DateField("Date obtention brevet", null=True, blank=True)

    # ========== COMPTE & STATUT ==========
    account_balance = models.DecimalField("Solde Compte (Euros)", max_digits=10, decimal_places=2, default=0.00)
    is_instructor = models.BooleanField("Est Instructeur", default=False)
    is_student = models.BooleanField("Est Eleve", default=False)
    is_active = models.BooleanField("Membre actif", default=True)

    # ========== NOTES ==========
    notes = models.TextField("Notes internes", blank=True)

    class Meta:
        verbose_name = "Membre"
        verbose_name_plural = "Membres"
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f"{self.user.last_name} {self.user.first_name} ({self.user.username})"

    # ========== PROPRIETES CALCULEES ==========
    @property
    def last_flight_date(self):
        last_flight = self.user.flights.order_by('-date').first()
        return last_flight.date if last_flight else None

    @property
    def landings_last_90_days(self):
        from django.db.models import Sum
        cutoff = date.today() - timedelta(days=90)
        total = self.user.flights.filter(date__gte=cutoff).aggregate(Sum('landings_count'))['landings_count__sum']
        return total or 0

    @property
    def hours_last_12_months(self):
        from django.db.models import Sum
        cutoff = date.today() - timedelta(days=365)
        total = self.user.flights.filter(date__gte=cutoff).aggregate(Sum('duration'))['duration__sum']
        return total or 0

    @property
    def is_medical_valid(self):
        if not self.medical_validity:
            return False
        return self.medical_validity >= date.today()

    @property
    def is_license_valid(self):
        """Verifie si la licence de base est valide."""
        if self.license_type == 'NONE':
            return False
        return True  # La licence elle-meme n'expire pas

    @property
    def is_sep_valid(self):
        """Verifie si la qualification SEP est valide."""
        if not self.has_sep or not self.sep_validity:
            return False
        return self.sep_validity >= date.today()

    @property
    def is_club_subscription_valid(self):
        if not self.club_subscription_validity:
            return False
        return self.club_subscription_validity >= date.today()

    @property
    def is_ffa_valid(self):
        if not self.ffa_subscription_validity:
            return False
        return self.ffa_subscription_validity >= date.today()

    @property
    def can_fly_solo(self):
        """Verifie si le pilote peut voler seul."""
        return (
            self.is_medical_valid and
            self.is_sep_valid and
            self.is_club_subscription_valid and
            self.account_balance > 0 and
            self.landings_last_90_days >= 3
        )

    @property
    def can_carry_passengers(self):
        """Verifie si le pilote peut emporter des passagers (FCL.060)."""
        return self.can_fly_solo and self.landings_last_90_days >= 3

    @property
    def needs_instructor_flight(self):
        """Verifie si un vol avec instructeur est requis (< 3 atterrissages)."""
        return self.landings_last_90_days < 3

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @property
    def qualifications_list(self):
        """Retourne la liste des qualifications actives."""
        quals = []
        if self.has_sep:
            quals.append('SEP')
        if self.has_mep:
            quals.append('MEP')
        if self.has_ir:
            quals.append('IR')
        if self.has_night:
            quals.append('Nuit')
        if self.has_mountain:
            quals.append('Montagne')
        if self.has_aerobatics:
            quals.append('Voltige')
        if self.has_towing:
            quals.append('Remorquage')
        if self.has_fi:
            quals.append('FI')
        if self.has_fe:
            quals.append('FE')
        return quals


class QualificationType(models.Model):
    """
    Types de qualifications sur types d'avions specifiques.
    Ex: Lacher sur DR400, Lacher sur PA28, etc.
    """
    aircraft_type = models.CharField("Type avion", max_length=50)
    description = models.CharField("Description", max_length=200, blank=True)
    requires_instructor_checkout = models.BooleanField("Necessite lacher instructeur", default=True)
    min_hours_required = models.PositiveIntegerField("Heures min requises", default=0)

    class Meta:
        verbose_name = "Type de qualification"
        verbose_name_plural = "Types de qualifications"

    def __str__(self):
        return self.aircraft_type


class MemberTypeQualification(models.Model):
    """
    Qualifications d'un membre sur un type d'avion specifique.
    """
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='type_qualifications')
    qualification_type = models.ForeignKey(QualificationType, on_delete=models.CASCADE)
    granted_date = models.DateField("Date du lacher")
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_qualifications',
        verbose_name="Instructeur"
    )
    notes = models.TextField("Remarques", blank=True)
    is_active = models.BooleanField("Active", default=True)

    class Meta:
        verbose_name = "Qualification type"
        verbose_name_plural = "Qualifications types"
        unique_together = ['member', 'qualification_type']

    def __str__(self):
        return f"{self.member.user.last_name} - {self.qualification_type}"
