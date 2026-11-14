"""Auto-create superuser and configure SocialApp/Site settings using environment variables."""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'soloNest.settings')
django.setup()

from core.models import User
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

# 1. Superuser Setup
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@solonest.com',
        password='Admin@1234',
        role='owner',
    )
    print(' Superuser "admin" created successfully!')
else:
    print('ℹ️ Superuser already exists, skipping.')

# 2. Site Configuration (fixes Google redirect URI domain mismatch)
try:
    site = Site.objects.get(id=1)
    site.domain = 'slolonest.onrender.com'
    site.name = 'SoloNest'
    site.save()
    print(' Site domain updated to slolonest.onrender.com')
except Site.DoesNotExist:
    site = Site.objects.create(id=1, domain='slolonest.onrender.com', name='SoloNest')
    print(' Site created successfully')

# 3. Google OAuth Setup — use settings.py APP block as the single source of truth.
#    Remove any stale DB SocialApps to prevent MultipleObjectsReturned errors.
try:
    existing_apps = SocialApp.objects.filter(provider='google')
    if existing_apps.exists():
        existing_apps.delete()
        print(' Cleared stale Google SocialApp entries from DB (settings.py APP block is used instead)')
except Exception as e:
    print(f'  Could not clear SocialApp entries: {e}')
