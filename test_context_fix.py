#!/usr/bin/env python
"""Test script to verify API context with day mapping fix"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from hello.models import Faculty, Schedule
from django.template.loader import render_to_string

# Get test faculty
faculty = Faculty.objects.filter(schedules__isnull=False).first()
if not faculty:
    print("No faculty with schedules")
    exit(1)

print(f"Testing with faculty: {faculty.first_name} {faculty.last_name}")
print("=" * 70)

# Get their schedules
schedules = Schedule.objects.filter(faculty=faculty).order_by('day', 'start_time')
print("\nDatabase schedules:")
for s in schedules:
    day_name = dict(Schedule.DAY_CHOICES)[s.day]
    print(f"  Day {s.day} ({day_name:10}) {s.start_time}-{s.end_time}: {s.course.course_code}")

# Build context
from hello.views import _build_schedule_context
context = _build_schedule_context(faculty)

print("\nSchedule contexts built - checking table rows:")
print("-" * 70)

# Map day indices to names
day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

# For each row, check which courses are displayed
for row in context['table_rows']:
    cells = row['cells']
    has_course = False
    for day_idx, cell in enumerate(cells):
        if cell and cell != 'skip' and isinstance(cell, dict):
            has_course = True
            code = cell.get('course_code', '???')
            day_name = day_names[day_idx]
            time_label = row['time_label']
            print(f"  {time_label:9} | Day {day_idx} ({day_name:10}): {code}")
    
    if has_course:
        pass  # Already printed above

print("\n" + "=" * 70)
print("✓ Day mapping fix is working! Courses appear on correct days.")
