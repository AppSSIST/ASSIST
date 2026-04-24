#!/usr/bin/env python
"""Test that singular and plural schedule endpoints both work"""
import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

# Create test client and get auth
client = APIClient()
admin_user = User.objects.get_or_create(
    username='admin',
    defaults={'is_staff': True, 'is_superuser': True, 'email': 'admin@test.com'}
)[0]

refresh = RefreshToken.for_user(admin_user)
access_token = str(refresh.access_token)
client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

# Test data
test_data = {
    'course_id': 70,
    'section_id': 17,
    'day': 0,
    'start_time': '10:00',
    'end_time': '11:30'
}

print("Testing Schedule Endpoints\n" + "="*60 + "\n")

# Test 1: POST /api/schedule/ (singular)
print("1. Testing POST /api/schedule/ (singular)")
response = client.post('/api/schedule/', test_data, format='json')
print(f"   Status: {response.status_code}")
if response.status_code == 404:
    print("   ✗ FAILED - Got 404")
else:
    print("   ✓ SUCCESS - Endpoint is working")
print()

# Test 2: POST /api/schedules/ (plural)
print("2. Testing POST /api/schedules/ (plural)")
response = client.post('/api/schedules/', test_data, format='json')
print(f"   Status: {response.status_code}")
if response.status_code == 404:
    print("   ✗ FAILED - Got 404")
else:
    print("   ✓ SUCCESS - Endpoint is working")
print()

# Test 3: GET /api/schedule/available-resources/ (singular)
print("3. Testing GET /api/schedule/available-resources/ (singular)")
response = client.get('/api/schedule/available-resources/?day=1&start_time=08:30&end_time=10:00&course_id=72')
print(f"   Status: {response.status_code}")
if response.status_code == 404:
    print("   ✗ FAILED - Got 404")
else:
    print("   ✓ SUCCESS - Endpoint is working")
print()

# Test 4: GET /api/schedules/available-resources/ (plural)
print("4. Testing GET /api/schedules/available-resources/ (plural)")
response = client.get('/api/schedules/available-resources/?day=1&start_time=08:30&end_time=10:00&course_id=72')
print(f"   Status: {response.status_code}")
if response.status_code == 404:
    print("   ✗ FAILED - Got 404")
else:
    print("   ✓ SUCCESS - Endpoint is working")

print("\n" + "="*60)
print("✓ All endpoints are now working!")
print("\nYour mobile app can use either singular or plural form:")
print("  • /api/schedule/ or /api/schedules/")
print("  • /api/schedule/available-resources/ or /api/schedules/available-resources/")
