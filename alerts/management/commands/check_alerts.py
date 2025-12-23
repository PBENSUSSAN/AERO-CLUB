"""
Commande Django pour verifier et generer les alertes.
Utilisation : python manage.py check_alerts

A planifier quotidiennement via cron ou Celery Beat.
"""
from django.core.management.base import BaseCommand
from alerts.services import run_all_checks, resolve_outdated_alerts


class Command(BaseCommand):
    help = 'Verifie toutes les echeances et genere les alertes appropriees'

    def add_arguments(self, parser):
        parser.add_argument(
            '--resolve',
            action='store_true',
            help='Resoudre egalement les alertes obsoletes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Afficher les details',
        )

    def handle(self, *args, **options):
        self.stdout.write("[*] Verification des alertes en cours...")

        total, results = run_all_checks()

        if options['verbose']:
            self.stdout.write(f"  - Certificats medicaux : {results['medical']} alerte(s)")
            self.stdout.write(f"  - Licences : {results['license']} alerte(s)")
            self.stdout.write(f"  - Experience recente : {results['experience']} alerte(s)")
            self.stdout.write(f"  - Soldes compte : {results['balance']} alerte(s)")
            self.stdout.write(f"  - Maintenance avions : {results['maintenance']} alerte(s)")

        self.stdout.write(
            self.style.SUCCESS(f"[OK] {total} nouvelle(s) alerte(s) creee(s)")
        )

        if options['resolve']:
            resolved = resolve_outdated_alerts()
            self.stdout.write(
                self.style.SUCCESS(f"[OK] {resolved} alerte(s) obsolete(s) resolue(s)")
            )

        self.stdout.write("Termine.")
