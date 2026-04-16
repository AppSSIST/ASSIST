#!/usr/bin/env python
"""Debug script to check what's being passed to the template"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from hello.models import Schedule, Faculty
from hello.views import _build_schedule_context

# Get test faculty
faculty = Faculty.objects.filter(schedules__isnull=False).first()
if not faculty:
    print("No faculty found")
    exit(1)

context = _build_schedule_context(faculty)
table_rows = context['table_rows']

print("=" * 70)
print("Checking rowspan values in context")
print("=" * 70)

day_names = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

for row in table_rows:
    time_label = row['time_label']
    cells = row['cells']
    
    for day_idx, cell in enumerate(cells):
        if cell and cell != 'skip' and isinstance(cell, dict):
            code = cell.get('course_code', '???')
            rowspan = cell.get('rowspan', '?')
            day_name = day_names[day_idx]
            
            print(f"\n{time_label:9} | {day_name} | {code:10}")
            print(f"  rowspan: {rowspan}")
            
            # Calculate what the end time should be
            time_parts = row['time'].split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            # Each slot is 30 minutes
            end_minute = minute + (rowspan * 30)
            end_hour = hour
            while end_minute >= 60:
                end_minute -= 60
                end_hour += 1
            
            print(f"  Displays: {row['time_label']} - {end_hour:02d}:{end_minute:02d}")
