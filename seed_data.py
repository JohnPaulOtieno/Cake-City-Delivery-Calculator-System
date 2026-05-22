import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cake_delivery.settings')
django.setup()

from django.contrib.auth.models import User
from stores.models import Store

# Set admin password
admin_user = User.objects.get(username='admin')
admin_user.set_password('admin123')
admin_user.save()
print(f"✓ Admin user password set to 'admin123'")

# Create 12 Nairobi stores with their coordinates
nairobi_stores = [
    {
        'name': 'City Center Branch',
        'latitude': -1.2921,
        'longitude': 36.8219,
        'address': '123 Kimathi Street, Nairobi City Center',
        'phone_number': '+254712345001'
    },
    {
        'name': 'Westlands Branch',
        'latitude': -1.2588,
        'longitude': 36.8010,
        'address': '456 Westlands Avenue, Westlands',
        'phone_number': '+254712345002'
    },
    {
        'name': 'Karen Branch',
        'latitude': -1.3156,
        'longitude': 36.6674,
        'address': '789 Karen Road, Karen',
        'phone_number': '+254712345003'
    },
    {
        'name': 'Nairobi South Branch',
        'latitude': -1.3446,
        'longitude': 36.8054,
        'address': '321 South C, South C Estate',
        'phone_number': '+254712345004'
    },
    {
        'name': 'Langata Branch',
        'latitude': -1.3554,
        'longitude': 36.7767,
        'address': '654 Langata Road, Langata',
        'phone_number': '+254712345005'
    },
    {
        'name': 'Kilimani Branch',
        'latitude': -1.2754,
        'longitude': 36.7947,
        'address': '987 Kilimani Lane, Kilimani',
        'phone_number': '+254712345006'
    },
    {
        'name': 'Parklands Branch',
        'latitude': -1.2396,
        'longitude': 36.8197,
        'address': '111 Parklands Drive, Parklands',
        'phone_number': '+254712345007'
    },
    {
        'name': 'Upper Hill Branch',
        'latitude': -1.3016,
        'longitude': 36.8357,
        'address': '222 Upper Hill Road, Upper Hill',
        'phone_number': '+254712345008'
    },
    {
        'name': 'Valley Road Branch',
        'latitude': -1.2768,
        'longitude': 36.7929,
        'address': '333 Valley Road, Valley Road',
        'phone_number': '+254712345009'
    },
    {
        'name': 'Muthaiga Branch',
        'latitude': -1.2315,
        'longitude': 36.8321,
        'address': '444 Muthaiga Road, Muthaiga',
        'phone_number': '+254712345010'
    },
    {
        'name': 'Runda Branch',
        'latitude': -1.2233,
        'longitude': 36.8515,
        'address': '555 Runda Drive, Runda',
        'phone_number': '+254712345011'
    },
    {
        'name': 'Kileleshwa Branch',
        'latitude': -1.2632,
        'longitude': 36.7863,
        'address': '666 Kileleshwa Road, Kileleshwa',
        'phone_number': '+254712345012'
    }
]

# Create stores
created_count = 0
for store_data in nairobi_stores:
    store, created = Store.objects.get_or_create(
        name=store_data['name'],
        defaults={
            'latitude': store_data['latitude'],
            'longitude': store_data['longitude'],
            'address': store_data['address'],
            'phone_number': store_data['phone_number'],
            'is_active': True
        }
    )
    if created:
        created_count += 1
        print(f"✓ Created: {store.name}")
    else:
        print(f"- Already exists: {store.name}")

print(f"\n✓ Total stores created: {created_count}")
print("\nSetup completed successfully!")
print("\nAdmin credentials:")
print("  Username: admin")
print("  Password: admin123")
print("\nYou can now log in to the admin panel at /admin/")
