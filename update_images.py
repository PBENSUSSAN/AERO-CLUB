import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aeroclub_project.settings')
django.setup()

from fleet.models import Aircraft

def update_images():
    print("Mise à jour des images avions...")
    
    mapping = {
        'F-GABC': 'aircrafts/dr400.png',
        'F-HJOY': 'aircrafts/c172.png',
        'F-PLOP': 'aircrafts/pa28.png',
        'F-BXTD': 'aircrafts/cap10.png'
    }

    for reg, img_path in mapping.items():
        try:
            ac = Aircraft.objects.get(registration=reg)
            ac.image = img_path
            ac.save()
            print(f"{reg} : Image mise à jour ({img_path})")
        except Aircraft.DoesNotExist:
            print(f"{reg} : Introuvable")

if __name__ == "__main__":
    update_images()
