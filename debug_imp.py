import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aeroclub_project.settings')
django.setup()

try:
    import finance.urls
    print("FINANCE URLS IMPORT OK")
except Exception as e:
    print(f"FINANCE URLS IMPORT ERROR: {e}")
