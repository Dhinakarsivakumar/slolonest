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
    print('✅ Superuser "admin" created successfully!')
else:
    print('ℹ️ Superuser already exists, skipping.')

# 2. Site Configuration (fixes Google redirect URI domain mismatch)
try:
    site = Site.objects.get(id=1)
    site.domain = 'slolonest.onrender.com'
    site.name = 'SoloNest'
    site.save()
    print('✅ Site domain updated to slolonest.onrender.com')
except Site.DoesNotExist:
    site = Site.objects.create(id=1, domain='slolonest.onrender.com', name='SoloNest')
    print('✅ Site created successfully')

# 3. Google OAuth Setup (loaded via env vars)
client_id = os.environ.get('GOOGLE_CLIENT_ID')
client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')

if client_id and client_secret:
    app, created = SocialApp.objects.get_or_create(
        provider='google',
        name='Google Login',
        defaults={
            'client_id': client_id,
            'secret': client_secret,
        }
    )

    if not created:
        app.client_id = client_id
        app.secret = client_secret
        app.save()
        print('🔄 Google SocialApp updated with latest keys')
    else:
        print('✅ Google SocialApp created successfully')

    # Link SocialApp to current Site
    if not app.sites.filter(id=site.id).exists():
        app.sites.add(site)
        print('✅ Google SocialApp linked to Site')
else:
    print('⚠️ GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set in environment variables. Skipping SocialApp configuration.')
