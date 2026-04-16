#!/usr/bin/env python
"""Debug script to check time slot calculation"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from hello.models import Schedule, Faculty

# Get test faculty
faculty = Faculty.objects.filter(schedules__isnull=False).first()
if not faculty:
    print("No faculty found")
    exit(1)

schedules = Schedule.objects.filter(faculty=faculty)
print("=" * 70)
print("Checking Schedule Time Calculations")
print("=" * 70)

for s in schedules:
    day_name = dict(Schedule.DAY_CHOICES)[s.day]
    start_str = str(s.start_time)
    end_str = str(s.end_time)
    
    # Parse times
    start_parts = start_str.split(':')
    end_parts = end_str.split(':')
    start_min = int(start_parts[0]) * 60 + int(start_parts[1])
    end_min = int(end_parts[0]) * 60 + int(end_parts[1])
    
    # Calculate index
    base_min = 7 * 60 + 30  # 450
    start_index = (start_min - base_min) // 30
    
    # Build time slots
    time_slots = ["07:30"]
    for hour in range(8, 22):
        for minute in ['00', '30']:
            if hour == 21 and minute == '30':
                break
            time_slots.append(f"{hour:02d}:{minute}")
    time_slots.append("21:30")
    
    print(f"\n{day_name} - {s.course.course_code}:")
    print(f"  Start Time (from DB): {start_str}")
    print(f"  Start Minutes: {start_min}")
    print(f"  Base Minutes (7:30 AM): {base_min}")
    print(f"  Difference: {start_min - base_min}")
    print(f"  Start Index: {start_index}")
    if 0 <= start_index < len(time_slots):
        print(f"  → Time Slot[{start_index}]: {time_slots[start_index]}")
        if start_index + 1 < len(time_slots):
            print(f"  → Time Slot[{start_index + 1}]: {time_slots[start_index + 1]}")
    else:
        print(f"  ⚠ INDEX OUT OF RANGE!")
    
    slots = (end_min - start_min) // 30
    print(f"  Duration: {end_min - start_min} mins = {slots} slots")

print("\n" + "=" * 70)
print("First 20 time slots for reference:")
time_slots = ["07:30"]
for hour in range(8, 22):
    for minute in ['00', '30']:
        if hour == 21 and minute == '30':
            break
        time_slots.append(f"{hour:02d}:{minute}")
time_slots.append("21:30")

for i, t in enumerate(time_slots[:20]):
    print(f"  [{i:2d}]: {t}")
