# Debugging Course Hour Tracking Issue

## Summary
The course hour validation warnings are not appearing when schedules exceed requirements, and completed courses are still appearing in the course select dropdown.

## Root Cause Investigation
I've added comprehensive debug logging to identify what's happening. Here's how to run the test:

## Steps to Debug

### 1. Open Browser DevTools
- Open the schedule admin page in your browser
- Press `F12` or `Ctrl+Shift+I` to open Developer Tools
- Go to the **Console** tab

### 2. Create a Test Schedule with Chemistry

**Test Scenario from User Report:**
- Select a section 
- Select Chemistry course (or any course with lecture_hours and laboratory_hours > 0)
- Select a lecture room (or any room with room_type='lecture')
- Set time from 1:00 PM to 3:00 PM (2 hours)
- **Expected:** Warning should appear if remaining lecture hours < 2

### 3. Watch Console Output

Look for these debug messages in this order:

```
DEBUG loadScheduleView: {sectionId: X, sectionName: "Y"}
  Stored currentSchedules: [...]
```

**Check 1: currentSchedules Data**
Look at the array and verify EACH schedule object has:
- ✅ `course_id`: should be a number
- ✅ `section_id`: should match the selected section
- ✅ `room_type`: should be either "lecture", "laboratory", or null if TBA
- ✅ `duration`: should be a number (in minutes)

**If room_type is null for all schedules:** This is the problem! Old schedules created before the room_type field was added don't have this data.

---

```
DEBUG filterCourses called with: course_select
  Section selected: {sectionId: X, ...}
  Checking course Chemistry (123):
    Hours: lecture=3/0, lab=2/0
    isComplete = (3===0 || 0>=3) && (2===0 || 0>=2) = false
    SHOWING
```

**Check 2: getCourseHoursInSection Data**
Inside `getCourseHoursInSection()` logs, you should see:
- Each existing schedule being checked
- For Chemistry courses, you should see lines like:
  ```
  MATCHED! room_type: "lecture" duration: 3600
  Added to lecture: 1 total lecture: 1
  ```

If you see `WARNING: room_type is neither lecture nor laboratory: null`, that confirms schedules have null room_type.

---

```
DEBUG validateCourseRoomMatch called
  Values: {lectureHours: 3, labHours: 2, roomType: "lecture", sectionId: X, courseId: 123}
  Times: {startTime: "13:00", endTime: "15:00"}
  Duration in hours: 2
  Lecture validation: required=3, used=0, remaining=3, duration=2
```

**Check 3: Validation Logic**
- `required=3` (from course data attribute)
- `used=0` (should accumulate from existing schedules)
- `remaining=3` (= required - used)
- `duration=2` (from selected time slot)

If `used` is always 0, it means `getCourseHoursInSection()` returned `{ lecture: 0, lab: 0 }` because:
1. No schedules match the course_id
2. No schedules have matching section_id
3. All schedules have `room_type: null` so the if conditions don't trigger

---

## What to Report

After running this test, take a screenshot of the console output and note:

1. **Does currentSchedules have room_type values?**
   - YES: room_type is "lecture", "laboratory" 
   - NO: room_type is null
   - MIXED: some have values, some are null

2. **Does the "used" hours accumulate?**
   - YES: used increases as you view different schedules
   - NO: used is always 0

3. **Does the warning appear?**
   - YES: Yellow warning box shows
   - NO: No warning even when duration > remaining

## Likely Fix Needed

If `room_type` is null for existing schedules:

**Option 1 (Quick):** Delete all test schedules and create new ones - they should get room_type from the room assignment.

**Option 2 (Proper):** Regenerate the schedule data to populate room_type from the Room model for each schedule's room.

---

## Expected Behavior After Fix

1. ✅ When Chemistry is selected with a Lecture room, "used" hours should show accumulated lecture time
2. ✅ Warning should appear if you try to add more hours than remaining
3. ✅ Course should be hidden from dropdown once all hours are scheduled
4. ✅ Completing a course (Mon-Sat, 5-7 total hours exceeding requirement) should hide it from dropdown

---

Let me know what the console shows!
