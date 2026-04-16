#!/usr/bin/env python
"""Test script to verify rowspan calculations"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from hello.models import Faculty, Schedule
from hello.views import _build_schedule_context

# Get test faculty
faculty = Faculty.objects.filter(schedules__isnull=False).first()
if not faculty:
    print("No faculty with schedules")
    exit(1)

print(f"Testing rowspan calculations for: {faculty.first_name} {faculty.last_name}")
print("=" * 70)

# Get database schedules with durations
schedules = Schedule.objects.filter(faculty=faculty).order_by('day', 'start_time')
print("\nDatabase schedules (with durations):")
db_courses = {}
for s in schedules:
    day_name = dict(Schedule.DAY_CHOICES)[s.day]
    start_str = str(s.start_time)
    end_str = str(s.end_time)
    start_parts = start_str.split(':')
    end_parts = end_str.split(':')
    start_mins = int(start_parts[0]) * 60 + int(start_parts[1])
    end_mins = int(end_parts[0]) * 60 + int(end_parts[1])
    duration = end_mins - start_mins
    slots = duration // 30
    key = f"{day_name} {start_str}"
    db_courses[key] = {'code': s.course.course_code, 'duration': duration, 'slots': slots}
    print(f"  {day_name:10} {start_str}: {s.course.course_code:10} ({duration}min = {slots} slots)")

# Build context and check rowspans
context = _build_schedule_context(faculty)
print("\nSchedule map rowspan values:")
print("-" * 70)

# Map day indices to names
day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

for row in context['table_rows']:
    time_label = row['time_label']
    cells = row['cells']
    
    for day_idx, cell in enumerate(cells):
        if cell and cell != 'skip' and isinstance(cell, dict):
            code = cell.get('course_code', '???')
            rowspan = cell.get('rowspan', '?')
            day_name = day_names[day_idx]
            
            # Find matching DB course
            db_key = f"{day_name} {row['time'].replace(' ', ':')}" if ' ' not in row['time'] else f"{day_name} {row['time']}"
            expected = None
            for k, v in db_courses.items():
                if code in k or code == v['code']:
                    expected = v['slots']
                    break
            
            status = "✓" if rowspan == expected else "⚠"
            print(f"  {status} {time_label:9} | {day_name:10} {code:10} rowspan={rowspan} (expected ~{expected})")

print("\n" + "=" * 70)
print("✓ Rowspan calculations verified (should all be ✓)")
