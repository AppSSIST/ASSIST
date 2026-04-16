#!/usr/bin/env python
"""Debug script to render HTML and check rowspan in output"""
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

# Render the template
html = render_to_string('hello/staff_schedule_print.html', context)

# Search for PE 001 in the HTML and show the relevant rows
import re

print("=" * 70)
print("Looking for PE 001 in rendered HTML")
print("=" * 70)

# Find tbody and extract rows
tbody_match = re.search(r'<tbody>(.*?)</tbody>', html, re.DOTALL)
if tbody_match:
    tbody = tbody_match.group(1)
    rows = re.findall(r'<tr>(.*?)</tr>', tbody, re.DOTALL)
    
    print(f"\nTotal rows in table: {len(rows)}\n")
    
    for i, row in enumerate(rows):
        # Extract time
        time_match = re.search(r'<td class="time-col">(.*?)</td>', row)
        time_val = time_match.group(1) if time_match else "NO TIME"
        
        # Look for PE 001
        if 'PE 001' in row:
            print(f"Row {i} (TIME: {time_val}):")
            print(f"  Found PE 001")
            # Get rowspan
            rowspan_match = re.search(r'rowspan="(\d+)"', row)
            rowspan = rowspan_match.group(1) if rowspan_match else "1"
            print(f"  Rowspan: {rowspan}")
else:
    print("Could not find tbody in HTML!")
