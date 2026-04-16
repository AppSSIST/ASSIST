#!/usr/bin/env python
"""Debug script to show the actual table rows"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from django.template.loader import render_to_string
from hello.models import Faculty
from hello.views import _build_schedule_context

# Get test faculty
faculty = Faculty.objects.filter(schedules__isnull=False).first()
if not faculty:
    print("No faculty found")
    exit(1)

context = _build_schedule_context(faculty)
table_rows = context['table_rows']

print("=" * 70)
print("Table rows structure from context")
print("=" * 70)

day_names = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

for row in table_rows:
    time_label = row['time_label']
    cells = row['cells']
    
    # Check if this row has any courses
    has_course = False
    for day_idx, cell in enumerate(cells):
        if cell and cell != 'skip' and isinstance(cell, dict):
            has_course = True
            break
    
    if has_course:
        print(f"\nTime: {time_label}")
        print(f"  Time (raw): {row['time']}")
        print(f"  Cells: {len(cells)}")
        
        for day_idx, cell in enumerate(cells):
            if cell == 'skip':
                print(f"    [{day_names[day_idx]}]: SKIP (covered by rowspan)")
            elif cell is None:
                print(f"    [{day_names[day_idx]}]: empty")
            elif isinstance(cell, dict):
                code = cell.get('course_code')
                rowspan = cell.get('rowspan')
                print(f"    [{day_names[day_idx]}]: {code} (rowspan={rowspan})")
            else:
                print(f"    [{day_names[day_idx]}]: {cell}")
