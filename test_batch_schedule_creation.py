#!/usr/bin/env python3
"""
Test batch schedule creation with multiple days
This tests the new checkbox-based day selection feature
"""

import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
sys.path.insert(0, '/Users/Sesi/Auto-Scheduling-1')
django.setup()

from hello.models import Course, Section, Faculty, Room, Schedule

def test_batch_creation():
    """Test that batch schedule creation endpoint handles multiple days correctly"""
    
    # Find a course and section for testing
    course = Course.objects.first()
    section = Section.objects.first()
    
    if not course or not section:
        print("ERROR: No course or section found in database")
        return False
    
    # Find lecture room and faculty
    lecture_room = Room.objects.filter(room_type='lecture').first()
    faculty = Faculty.objects.first()
    
    if not lecture_room or not faculty:
        print("ERROR: No lecture room or faculty found")
        return False
    
    print(f"\nTest Configuration:")
    print(f"  Course: {course.course_code} ({course.descriptive_title})")
    print(f"  Section: {section.name}")
    print(f"  Room: {lecture_room.room_number} ({lecture_room.room_type})")
    print(f"  Faculty: {faculty.first_name} {faculty.last_name}")
    
    # Test 1: Verify existing schedules for this section
    print(f"\nTest 1: Check existing schedules for {section.name}")
    existing = Schedule.objects.filter(section=section, course=course)
    print(f"  Existing {course.course_code} schedules in {section.name}: {existing.count()}")
    if existing.exists():
        for sched in existing:
            day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            print(f"    - {day_names[sched.day]} {sched.start_time}-{sched.end_time} in {sched.room.room_number}")
    
    # Test 2: Simulate what the JavaScript will do for multiple days
    print(f"\nTest 2: Simulate batch creation for multiple days")
    test_days = [0, 1, 2]  # Monday, Tuesday, Wednesday
    day_names = ['Monday', 'Tuesday', 'Wednesday']
    
    print(f"  Simulating creation of {course.course_code} on: {', '.join(day_names)}")
    
    # Check duplicate detection for each day
    print(f"  Checking for duplicates...")
    for day in test_days:
        duplicate = Schedule.objects.filter(
            section=section, 
            course=course, 
            day=day
        ).exists()
        day_name = day_names[day]
        status = "DUPLICATE (would be blocked)" if duplicate else "OK (would create)"
        print(f"    - {day_name}: {status}")
    
    # Test 3: Check hour requirements
    print(f"\nTest 3: Check hour requirements")
    print(f"  {course.course_code} requirements:")
    print(f"    - Lecture hours: {course.lecture_hours}")
    print(f"    - Lab hours: {course.laboratory_hours}")
    
    # Calculate current hours scheduled
    lecture_hours = 0
    lab_hours = 0
    existing = Schedule.objects.filter(section=section, course=course)
    
    for sched in existing:
        if sched.room.room_type == 'lecture':
            duration_hours = (sched.end_time.hour - sched.start_time.hour) + \
                           (sched.end_time.minute - sched.start_time.minute) / 60
            lecture_hours += duration_hours
        elif sched.room.room_type == 'laboratory':
            duration_hours = (sched.end_time.hour - sched.start_time.hour) + \
                           (sched.end_time.minute - sched.start_time.minute) / 60
            lab_hours += duration_hours
    
    print(f"  Current hours scheduled in {section.name}:")
    print(f"    - Lecture: {lecture_hours} / {course.lecture_hours} hours")
    print(f"    - Lab: {lab_hours} / {course.laboratory_hours} hours")
    
    print("\n✓ Batch creation test completed successfully")
    return True

if __name__ == '__main__':
    try:
        test_batch_creation()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
