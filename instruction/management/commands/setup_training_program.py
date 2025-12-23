"""
Commande pour initialiser le programme de formation PPL standard FFA.
Usage: python manage.py setup_training_program
"""
from django.core.management.base import BaseCommand
from instruction.models import TrainingPhase, TrainingExercise


class Command(BaseCommand):
    help = 'Initialise le programme de formation PPL standard FFA'

    def handle(self, *args, **options):
        self.stdout.write("Initialisation du programme de formation PPL FFA...")

        # ============================================================
        # PHASES DE FORMATION
        # ============================================================

        phases_data = [
            {
                'order': 1,
                'code': 'PH1',
                'name': 'Phase 1 - Decouverte',
                'description': 'Familiarisation avec l\'avion et les bases du pilotage',
                'target_hours': 5,
                'is_solo_allowed': False,
            },
            {
                'order': 2,
                'code': 'PH2',
                'name': 'Phase 2 - Maniabilite',
                'description': 'Maitrise du pilotage de base et des manoeuvres',
                'target_hours': 15,
                'is_solo_allowed': False,
            },
            {
                'order': 3,
                'code': 'PH3',
                'name': 'Phase 3 - Tours de piste',
                'description': 'Integration dans le circuit, decollages et atterrissages',
                'target_hours': 10,
                'is_solo_allowed': True,
            },
            {
                'order': 4,
                'code': 'PH4',
                'name': 'Phase 4 - Navigation',
                'description': 'Navigation VFR, voyages et radionavigation',
                'target_hours': 15,
                'is_solo_allowed': True,
            },
            {
                'order': 5,
                'code': 'PH5',
                'name': 'Phase 5 - Perfectionnement',
                'description': 'Perfectionnement et preparation examen',
                'target_hours': 10,
                'is_solo_allowed': True,
            },
        ]

        phases = {}
        for data in phases_data:
            phase, created = TrainingPhase.objects.update_or_create(
                code=data['code'],
                defaults=data
            )
            phases[data['code']] = phase
            status = "cree" if created else "mis a jour"
            self.stdout.write(f"  Phase {data['code']}: {status}")

        # ============================================================
        # EXERCICES DE FORMATION
        # ============================================================

        exercises_data = [
            # PHASE 1 - Decouverte
            {'phase': 'PH1', 'code': 'EX01', 'order': 1, 'name': 'Visite pre-vol et check-lists', 'is_mandatory': True},
            {'phase': 'PH1', 'code': 'EX02', 'order': 2, 'name': 'Installation a bord', 'is_mandatory': True},
            {'phase': 'PH1', 'code': 'EX03', 'order': 3, 'name': 'Mise en route et point fixe', 'is_mandatory': True},
            {'phase': 'PH1', 'code': 'EX04', 'order': 4, 'name': 'Roulage au sol', 'is_mandatory': True},
            {'phase': 'PH1', 'code': 'EX05', 'order': 5, 'name': 'Effets des commandes', 'is_mandatory': True},
            {'phase': 'PH1', 'code': 'EX06', 'order': 6, 'name': 'Vol rectiligne palier', 'is_mandatory': True},
            {'phase': 'PH1', 'code': 'EX07', 'order': 7, 'name': 'Montee et descente', 'is_mandatory': True},

            # PHASE 2 - Maniabilite
            {'phase': 'PH2', 'code': 'EX08', 'order': 1, 'name': 'Virages a moyenne inclinaison (30)', 'is_mandatory': True},
            {'phase': 'PH2', 'code': 'EX09', 'order': 2, 'name': 'Virages a grande inclinaison (45)', 'is_mandatory': True},
            {'phase': 'PH2', 'code': 'EX10', 'order': 3, 'name': 'Virages engages et desengagement', 'is_mandatory': True},
            {'phase': 'PH2', 'code': 'EX11', 'order': 4, 'name': 'Vol lent', 'is_mandatory': True},
            {'phase': 'PH2', 'code': 'EX12', 'order': 5, 'name': 'Decrochage en ligne droite', 'is_mandatory': True},
            {'phase': 'PH2', 'code': 'EX13', 'order': 6, 'name': 'Decrochage en virage', 'is_mandatory': True},
            {'phase': 'PH2', 'code': 'EX14', 'order': 7, 'name': 'Approche de decrochage', 'is_mandatory': True},
            {'phase': 'PH2', 'code': 'EX15', 'order': 8, 'name': 'Spirale', 'is_mandatory': True},
            {'phase': 'PH2', 'code': 'EX16', 'order': 9, 'name': 'Glissade', 'is_mandatory': False},
            {'phase': 'PH2', 'code': 'EX17', 'order': 10, 'name': 'Simulation panne moteur', 'is_mandatory': True},
            {'phase': 'PH2', 'code': 'EX18', 'order': 11, 'name': 'Atterrissage de precaution', 'is_mandatory': True},

            # PHASE 3 - Tours de piste
            {'phase': 'PH3', 'code': 'EX19', 'order': 1, 'name': 'Integration dans le circuit', 'is_mandatory': True},
            {'phase': 'PH3', 'code': 'EX20', 'order': 2, 'name': 'Decollage normal', 'is_mandatory': True},
            {'phase': 'PH3', 'code': 'EX21', 'order': 3, 'name': 'Decollage vent de travers', 'is_mandatory': True},
            {'phase': 'PH3', 'code': 'EX22', 'order': 4, 'name': 'Decollage piste courte', 'is_mandatory': False},
            {'phase': 'PH3', 'code': 'EX23', 'order': 5, 'name': 'Atterrissage normal', 'is_mandatory': True},
            {'phase': 'PH3', 'code': 'EX24', 'order': 6, 'name': 'Atterrissage vent de travers', 'is_mandatory': True},
            {'phase': 'PH3', 'code': 'EX25', 'order': 7, 'name': 'Atterrissage piste courte', 'is_mandatory': False},
            {'phase': 'PH3', 'code': 'EX26', 'order': 8, 'name': 'Atterrissage sans volets', 'is_mandatory': True},
            {'phase': 'PH3', 'code': 'EX27', 'order': 9, 'name': 'Remise de gaz', 'is_mandatory': True},
            {'phase': 'PH3', 'code': 'EX28', 'order': 10, 'name': 'Touch and go', 'is_mandatory': True},
            {'phase': 'PH3', 'code': 'EX29', 'order': 11, 'name': 'Encadrement piste', 'is_mandatory': True},
            {'phase': 'PH3', 'code': 'EX30', 'order': 12, 'name': 'Panne au decollage', 'is_mandatory': True},
            {'phase': 'PH3', 'code': 'SOLO1', 'order': 20, 'name': 'Premier solo', 'is_mandatory': True, 'is_solo_exercise': True},
            {'phase': 'PH3', 'code': 'SOLO2', 'order': 21, 'name': 'Solos locaux supervises', 'is_mandatory': True, 'is_solo_exercise': True},

            # PHASE 4 - Navigation
            {'phase': 'PH4', 'code': 'EX31', 'order': 1, 'name': 'Preparation navigation (log de nav)', 'is_mandatory': True},
            {'phase': 'PH4', 'code': 'EX32', 'order': 2, 'name': 'Lecture de carte', 'is_mandatory': True},
            {'phase': 'PH4', 'code': 'EX33', 'order': 3, 'name': 'Navigation a l\'estime', 'is_mandatory': True},
            {'phase': 'PH4', 'code': 'EX34', 'order': 4, 'name': 'Utilisation du VOR', 'is_mandatory': True},
            {'phase': 'PH4', 'code': 'EX35', 'order': 5, 'name': 'Utilisation du GPS', 'is_mandatory': False},
            {'phase': 'PH4', 'code': 'EX36', 'order': 6, 'name': 'Procedure radio (CTR, TMA)', 'is_mandatory': True},
            {'phase': 'PH4', 'code': 'EX37', 'order': 7, 'name': 'Integration terrain non connu', 'is_mandatory': True},
            {'phase': 'PH4', 'code': 'EX38', 'order': 8, 'name': 'Deroutement', 'is_mandatory': True},
            {'phase': 'PH4', 'code': 'EX39', 'order': 9, 'name': 'Navigation DC vers terrain exterieur', 'is_mandatory': True},
            {'phase': 'PH4', 'code': 'SOLO3', 'order': 20, 'name': 'Solo navigation supervise (150NM)', 'is_mandatory': True, 'is_solo_exercise': True},
            {'phase': 'PH4', 'code': 'SOLO4', 'order': 21, 'name': 'Solo navigation avec escales', 'is_mandatory': True, 'is_solo_exercise': True},

            # PHASE 5 - Perfectionnement
            {'phase': 'PH5', 'code': 'EX40', 'order': 1, 'name': 'Revision maniabilite', 'is_mandatory': True},
            {'phase': 'PH5', 'code': 'EX41', 'order': 2, 'name': 'Revision tours de piste', 'is_mandatory': True},
            {'phase': 'PH5', 'code': 'EX42', 'order': 3, 'name': 'Revision pannes', 'is_mandatory': True},
            {'phase': 'PH5', 'code': 'EX43', 'order': 4, 'name': 'Vol de synthese', 'is_mandatory': True},
            {'phase': 'PH5', 'code': 'EX44', 'order': 5, 'name': 'Navigation de preparation examen', 'is_mandatory': True},
            {'phase': 'PH5', 'code': 'EX45', 'order': 6, 'name': 'Test blanc (vol)', 'is_mandatory': True},
            {'phase': 'PH5', 'code': 'EXAM', 'order': 30, 'name': 'Examen pratique PPL', 'is_mandatory': True},
        ]

        for data in exercises_data:
            phase_code = data.pop('phase')
            phase = phases[phase_code]

            exercise, created = TrainingExercise.objects.update_or_create(
                phase=phase,
                code=data['code'],
                defaults=data
            )
            status = "cree" if created else "mis a jour"
            self.stdout.write(f"    Exercice {data['code']}: {status}")

        self.stdout.write(self.style.SUCCESS(
            f"\nProgramme de formation initialise:\n"
            f"  - {TrainingPhase.objects.count()} phases\n"
            f"  - {TrainingExercise.objects.count()} exercices"
        ))
