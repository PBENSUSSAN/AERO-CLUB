from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.utils import timezone
from .models import Member, QualificationType, MemberTypeQualification, MemberDocument


class MemberInline(admin.StackedInline):
    model = Member
    can_delete = False
    verbose_name_plural = 'Profil Membre Aeroclub'
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('phone_number', 'birth_date', 'address', 'city', 'postal_code', 'photo')
        }),
        ('Contact urgence', {
            'fields': ('emergency_contact', 'emergency_phone'),
            'classes': ('collapse',)
        }),
        ('Aeroclub', {
            'fields': ('member_number', 'join_date', 'ffa_number', 'account_balance', 'is_instructor', 'is_student', 'is_active')
        }),
        ('Licence', {
            'fields': ('license_type', 'license_number', 'license_issue_date', 'license_scan')
        }),
        ('Qualifications', {
            'fields': ('has_sep', 'sep_validity', 'has_night', 'night_validity', 'has_fi', 'fi_validity'),
            'classes': ('collapse',)
        }),
        ('Medical', {
            'fields': ('medical_class', 'medical_validity', 'medical_restrictions', 'medical_scan')
        }),
        ('Cotisations', {
            'fields': ('club_subscription_validity', 'ffa_subscription_validity', 'insurance_validity'),
            'classes': ('collapse',)
        }),
    )


class UserAdmin(BaseUserAdmin):
    inlines = (MemberInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'get_balance', 'get_medical_status')

    def get_balance(self, obj):
        try:
            return f"{obj.member_profile.account_balance} EUR"
        except Member.DoesNotExist:
            return "-"
    get_balance.short_description = 'Solde'

    def get_medical_status(self, obj):
        try:
            if obj.member_profile.is_medical_valid:
                return format_html('<span style="color: green;">Valide</span>')
            return format_html('<span style="color: red;">Expire</span>')
        except Member.DoesNotExist:
            return "-"
    get_medical_status.short_description = 'Medical'


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'license_type', 'medical_status', 'sep_status', 'account_balance', 'is_instructor', 'is_active']
    list_filter = ['license_type', 'medical_class', 'is_instructor', 'is_student', 'is_active', 'has_sep', 'has_night']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'license_number', 'ffa_number']
    readonly_fields = ['full_name', 'qualifications_list', 'can_fly_solo', 'landings_last_90_days']

    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'full_name')
        }),
        ('Informations personnelles', {
            'fields': ('phone_number', 'birth_date', 'birth_place', 'nationality', 'address', 'city', 'postal_code', 'photo')
        }),
        ('Contact urgence', {
            'fields': ('emergency_contact', 'emergency_phone')
        }),
        ('Aeroclub', {
            'fields': ('member_number', 'join_date', 'ffa_number', 'is_instructor', 'is_student', 'is_active', 'notes')
        }),
        ('Licence pilote', {
            'fields': ('license_type', 'license_number', 'license_issue_date', 'license_authority', 'license_scan')
        }),
        ('Qualifications EASA', {
            'fields': (
                ('has_sep', 'sep_validity'),
                ('has_mep', 'mep_validity'),
                ('has_ir', 'ir_validity'),
                ('has_night', 'night_validity'),
                ('has_mountain', 'mountain_wheels', 'mountain_skis'),
                'has_aerobatics', 'has_towing',
                ('has_fi', 'fi_validity'),
                'has_fe',
                'qualifications_list',
            )
        }),
        ('Certificat medical', {
            'fields': ('medical_class', 'medical_validity', 'medical_restrictions', 'medical_scan')
        }),
        ('Radiotelephonie & Anglais', {
            'fields': (
                ('has_radio_certificate', 'radio_certificate_number', 'radio_certificate_date'),
                ('has_english_level', 'english_level', 'english_validity'),
            ),
            'classes': ('collapse',)
        }),
        ('Cotisations & Assurance', {
            'fields': ('club_subscription_validity', 'ffa_subscription_validity', 'insurance_validity')
        }),
        ('Experience', {
            'fields': ('total_flight_hours', 'solo_date', 'license_date', 'landings_last_90_days', 'can_fly_solo')
        }),
        ('Compte pilote', {
            'fields': ('account_balance',)
        }),
    )

    def medical_status(self, obj):
        if obj.is_medical_valid:
            return format_html('<span style="color: green; font-weight: bold;">OK</span>')
        return format_html('<span style="color: red; font-weight: bold;">EXPIRE</span>')
    medical_status.short_description = 'Medical'

    def sep_status(self, obj):
        if obj.is_sep_valid:
            return format_html('<span style="color: green;">Valide</span>')
        if obj.has_sep:
            return format_html('<span style="color: red;">Expire</span>')
        return '-'
    sep_status.short_description = 'SEP'


@admin.register(QualificationType)
class QualificationTypeAdmin(admin.ModelAdmin):
    list_display = ['aircraft_type', 'description', 'requires_instructor_checkout', 'min_hours_required']
    list_filter = ['requires_instructor_checkout']


@admin.register(MemberTypeQualification)
class MemberTypeQualificationAdmin(admin.ModelAdmin):
    list_display = ['member', 'qualification_type', 'granted_date', 'granted_by', 'is_active']
    list_filter = ['qualification_type', 'is_active', 'granted_date']
    search_fields = ['member__user__last_name', 'member__user__first_name']
    autocomplete_fields = ['member', 'granted_by']


class MemberDocumentInline(admin.TabularInline):
    model = MemberDocument
    extra = 0
    fields = ['document_type', 'title', 'file', 'expiry_date', 'status', 'is_current']
    readonly_fields = ['upload_date']
    ordering = ['-upload_date']


@admin.register(MemberDocument)
class MemberDocumentAdmin(admin.ModelAdmin):
    list_display = ['member', 'document_type', 'title', 'expiry_date', 'status_badge', 'is_current', 'upload_date']
    list_filter = ['document_type', 'status', 'is_current']
    search_fields = ['member__user__last_name', 'member__user__first_name', 'title']
    date_hierarchy = 'upload_date'
    autocomplete_fields = ['member', 'validated_by']
    readonly_fields = ['upload_date']
    actions = ['validate_documents', 'reject_documents']

    fieldsets = (
        ('Document', {
            'fields': ('member', 'document_type', 'title', 'file')
        }),
        ('Dates', {
            'fields': ('issue_date', 'expiry_date', 'upload_date')
        }),
        ('Validation', {
            'fields': ('status', 'validated_by', 'validation_date', 'rejection_reason')
        }),
        ('Options', {
            'fields': ('is_current', 'notes')
        }),
    )

    def status_badge(self, obj):
        colors = {
            'PENDING': 'orange',
            'VALID': 'green',
            'EXPIRED': 'red',
            'REJECTED': 'darkred',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'

    @admin.action(description="Valider les documents selectionnes")
    def validate_documents(self, request, queryset):
        count = queryset.update(
            status='VALID',
            validated_by=request.user,
            validation_date=timezone.now()
        )
        self.message_user(request, f"{count} document(s) valide(s).")

    @admin.action(description="Refuser les documents selectionnes")
    def reject_documents(self, request, queryset):
        count = queryset.update(status='REJECTED')
        self.message_user(request, f"{count} document(s) refuse(s).")
