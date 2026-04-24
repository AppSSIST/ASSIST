#!/usr/bin/env python
"""Test /api/schedules/ with real database data"""
import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

# Create test client
client = APIClient()

# Get admin user
admin_user = User.objects.get_or_create(
    username='admin',
    defaults={
        'is_staff': True,
        'is_superuser': True,
        'email': 'admin@test.com'
    }
)[0]

# Generate JWT token
refresh = RefreshToken.for_user(admin_user)
access_token = str(refresh.access_token)
client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

# Real test data from database
test_data = {
    'course_id': 70,
    'section_id': 17,
    'faculty_id': 21,
    'room_id': 31,
    'day': 0,
    'start_time': '08:00',
    'end_time': '09:30'
}

print("Testing /api/schedules/ POST endpoint with real data\n")
print(f"Request Data: {json.dumps(test_data, indent=2)}\n")

response = client.post('/api/schedules/', test_data, format='json')

print(f"Status Code: {response.status_code}")
print(f"Response:\n{json.dumps(response.json(), indent=2)}\n")

if response.status_code == 404:
    print("❌ Got 404 - Restart Django development server!")
elif response.status_code == 201:
    print("✅ Schedule created successfully!")
elif response.status_code == 400:
    print("⚠ Validation error (check response above)")
    print("   This is normal - could be time conflict or validation issues")
else:
    print(f"Status: {response.status_code}")
