#!/usr/bin/env python
"""Check database for test data"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from hello.models import Course, Section, Faculty, Room

print("Database Content Check:\n")

courses = Course.objects.first()
if courses:
    print(f"✓ Course found: ID={courses.id}, Code={courses.course_code}")
else:
    print("✗ No courses in database")

sections = Section.objects.first()
if sections:
    print(f"✓ Section found: ID={sections.id}, Name={sections.name}")
else:
    print("✗ No sections in database")

faculty = Faculty.objects.first()
if faculty:
    print(f"✓ Faculty found: ID={faculty.id}, Name={faculty.first_name} {faculty.last_name}")
else:
    print("✗ No faculty in database")

rooms = Room.objects.first()
if rooms:
    print(f"✓ Room found: ID={rooms.id}, Name={rooms.name}")
else:
    print("✗ No rooms in database")

print("\n" + "="*60)
if all([courses, sections]):
    print("✓ You have sufficient data to test the /api/schedules/ endpoint")
    print(f"\nSample POST request payload:")
    print(f"{{")
    print(f'    "course_id": {courses.id},')
    print(f'    "section_id": {sections.id},')
    if faculty:
        print(f'    "faculty_id": {faculty.id},')
    if rooms:
        print(f'    "room_id": {rooms.id},')
    print(f'    "day": 0,')
    print(f'    "start_time": "08:00",')
    print(f'    "end_time": "09:30"')
    print(f"}}")
else:
    print("✗ Missing required data - create courses and sections first")
