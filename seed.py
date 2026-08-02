import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'soloNest.settings')
django.setup()
from core.models import User, Listing

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@solonest.test', 'admin12345')

owner, _ = User.objects.get_or_create(username='ravi_owner', defaults={'role':'owner','email':'ravi@test.com'})
owner.set_password('owner12345'); owner.role='owner'; owner.is_verified=True; owner.phone='9876543210'; owner.save()

guest, _ = User.objects.get_or_create(username='priya_guest', defaults={'role':'guest','email':'priya@test.com'})
guest.set_password('guest12345'); guest.role='guest'; guest.save()

Listing.objects.all().delete()

Listing.objects.create(
    owner=owner, title='Cozy private room near bus stand', city='Thanjavur', area='Medical College Road',
    address='12 Gandhi St', room_type='private', gender_preference='any', stay_type='both',
    price_per_day=250, price_per_month=5500, wifi=True, ac=False, attached_bathroom=True,
    food_included=True, is_verified=True, latitude=10.7905, longitude=79.1382
)
Listing.objects.create(
    owner=owner, title='Female-only shared room, walk to college', city='Thanjavur', area='SASTRA Road',
    address='45 Anna Nagar', room_type='shared', gender_preference='female', stay_type='monthly',
    price_per_month=4000, wifi=True, ac=False, attached_bathroom=False, food_included=False,
    latitude=10.7745, longitude=79.1467
)
Listing.objects.create(
    owner=owner, title='Guest house for interview candidates', city='Coimbatore', area='RS Puram',
    address='9 Race Course Rd', room_type='guesthouse', gender_preference='any', stay_type='short',
    price_per_day=350, wifi=True, ac=True, attached_bathroom=True, is_verified=True,
    latitude=11.0053, longitude=76.9661
)
Listing.objects.create(
    owner=owner, title='Budget room near Big Temple', city='Thanjavur', area='Big Temple Fort',
    address='3 Fort Rd', room_type='private', gender_preference='male', stay_type='short',
    price_per_day=200, wifi=True, ac=False, attached_bathroom=True,
    latitude=10.7828, longitude=79.1318
)
print('Seed complete. Login: admin/admin12345, ravi_owner/owner12345, priya_guest/guest12345')
