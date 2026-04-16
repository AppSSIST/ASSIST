#!/usr/bin/env python
"""Test script to verify API endpoints work with day mapping fix"""
import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from hello.models import Faculty
from hello.views import staff_schedule_html

# Get a faculty member
faculty = Faculty.objects.filter(schedules__isnull=False).first()
if not faculty:
    print("No faculty with schedules")
    exit(1)

# Create a test user and token for authentication
user, _ = User.objects.get_or_create(username='test_api_user')
token, _ = Token.objects.get_or_create(user=user)

# Create a mock request
factory = RequestFactory()
request = factory.get('/api/schedule/staff/html/')
request.user = user

# Mock the token authentication
from rest_framework.test import force_authenticate
force_authenticate(request, user=user)

print(f"Testing API endpoint for faculty: {faculty.first_name} {faculty.last_name}")
print("=" * 60)

try:
    response = staff_schedule_html(request)
    html = response.content.decode('utf-8')
    
    # Check if HTML contains the faculty name
    if faculty.last_name.lower() in html.lower():
        print("✓ Faculty name found in HTML response")
    
    # Check if courses are in the HTML (look for course codes)
    courses = list(faculty.schedules.values_list('course__course_code', flat=True).distinct())
    found_courses = 0
    for course_code in courses[:3]:
        if course_code in html:
            print(f"✓ Course {course_code} found in HTML")
            found_courses += 1
    
    if found_courses > 0:
        print(f"\n✓ API endpoint is working correctly with {found_courses} courses found!")
    else:
        print("⚠ No courses found in HTML response")
        print(f"Expected to find: {courses}")
        
except Exception as e:
    print(f"✗ Error calling API endpoint: {e}")
    import traceback
    traceback.print_exc()
