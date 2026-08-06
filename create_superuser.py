"""Auto-create superuser during deployment if none exists."""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'soloNest.settings')
django.setup()

from core.models import User

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
