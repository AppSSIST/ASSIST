#!/usr/bin/env python
"""Test script to verify day mapping fix"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from hello.models import Faculty, Schedule
from hello.views import _build_schedule_context

# Get a faculty member with schedules
faculty = Faculty.objects.filter(schedules__isnull=False).first()

if not faculty:
    print("No faculty with schedules found")
    exit(1)

print(f"Testing with faculty: {faculty.first_name} {faculty.last_name}")
print("=" * 60)

# Get raw schedules
schedules = Schedule.objects.filter(faculty=faculty).order_by('day', 'start_time')
print("\nDatabase schedules:")
for s in schedules[:5]:
    day_name = dict(Schedule.DAY_CHOICES)[s.day]
    print(f"  {day_name:10} {s.start_time}-{s.end_time}: {s.course.course_code}")

# Get context
context = _build_schedule_context(faculty)
table_rows = context['table_rows']

print("\n\nSchedules in table (checking for courses):")
print("TIME      | MON | TUE | WED | THU | FRI | SAT")
print("-" * 50)

day_names = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
for row in table_rows:
    time = row['time_label']
    cells_display = []
    for i, cell in enumerate(row['cells']):
        if cell == 'skip':
            cells_display.append('    ')
        elif cell is None:
            cells_display.append('    ')
        elif isinstance(cell, dict):
            code = cell['course_code'][:3]
            cells_display.append(f"{code:4}")
        else:
            cells_display.append('????')
    
    if any(c.strip() for c in cells_display):  # Only show rows with courses
        print(f"{time:9} | {' | '.join(cells_display)}")

print("\n✓ If courses appear on their correct days, the fix worked!")
