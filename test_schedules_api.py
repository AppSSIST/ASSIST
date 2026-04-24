#!/usr/bin/env python
"""Test script for /api/schedules/ POST endpoint"""
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

# Get or create test admin user
admin_user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'is_staff': True,
        'is_superuser': True,
        'email': 'admin@test.com'
    }
)

# Generate JWT token for admin user
refresh = RefreshToken.for_user(admin_user)
access_token = str(refresh.access_token)

# Set authorization header
client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

print("Testing /api/schedules/ endpoint\n")
print(f"User: {admin_user.username}")
print(f"Token: {access_token[:50]}...\n")

# Test data (this will fail validation but should not return 404)
test_data = {
    'course_id': 1,
    'section_id': 1,
    'day': 0,
    'start_time': '08:00',
    'end_time': '09:30'
}

print(f"Sending POST request with data: {json.dumps(test_data, indent=2)}\n")

# Make POST request
response = client.post('/api/schedules/', test_data, format='json')

print(f"Status Code: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}\n")

if response.status_code == 404:
    print("❌ ERROR: Got 404 - URL routing issue detected!")
    print("Solution: Restart the Django development server")
else:
    print("✓ Endpoint is responding (status != 404)")
    if response.status_code in [201, 200]:
        print("✓ Schedule created successfully")
    else:
        print(f"  Note: Status {response.status_code} (expected 201/200 for success or 400 for validation error)")
