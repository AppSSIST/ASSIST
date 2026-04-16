#!/usr/bin/env python
"""Debug script to show ALL table rows including empty ones"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

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
print(f"Total rows in table_rows: {len(table_rows)}")
print("=" * 70)

day_names = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']

# Show first 10 rows
print("\nFirst 10 rows:")
for i, row in enumerate(table_rows[:10]):
    time_label = row['time_label']
    time_cell = row.get('time_cell')
    cells = row['cells']
    
    # Count what types of cells
    skip_count = sum(1 for c in cells if c == 'skip')
    course_count = sum(1 for c in cells if c and isinstance(c, dict))
    empty_count = sum(1 for c in cells if c is None)
    
    time_cell_info = f"rowspan={time_cell['rowspan']}" if time_cell else "None"
    
    print(f"\n[{i:2d}] {time_label:9} | time_cell={time_cell_info:10} | {skip_count} skip, {course_count} courses, {empty_count} empty")
    
    if course_count > 0:
        for day_idx, cell in enumerate(cells):
            if isinstance(cell, dict):
                print(f"       {day_names[day_idx]}: {cell.get('course_code')} (rowspan={cell.get('rowspan')})")

print("\n" + "=" * 70)
print("Looking for rows with time_cell=None (covered by rowspan):")
print("=" * 70)

for i, row in enumerate(table_rows):
    if row.get('time_cell') is None:
        print(f"[{i:2d}] {row['time_label']:9} - time_cell is None")
