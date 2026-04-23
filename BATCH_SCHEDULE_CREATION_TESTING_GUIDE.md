# Batch Schedule Creation - Quick Testing Guide

## How to Test in Your Browser

### Step 1: Navigate to Schedule Admin
1. Go to http://localhost:8000/admin/schedule/view/3
2. Click the blue "Create Schedule" button
3. You should see **6 checkboxes** instead of a dropdown: Monday through Saturday

### Step 2: Test Single Day (Existing Behavior)
1. Select: CHM 001, Room 311, Faculty, Start Time: 13:00, End Time: 14:00
2. Check **only Monday**
3. Click Submit
4. ✓ Should succeed if no Monday schedule exists for CHM 001
5. ✓ Should show "Schedule created successfully!" message

### Step 3: Test Multiple Days (New Feature!)
1. Click "Create Schedule" again
2. Select: CHM 001, Room 311, Faculty, Start Time: 14:00, End Time: 15:00
3. Check **Tuesday, Wednesday, Thursday** (3 days)
4. Click Submit
5. ✓ Should create CHM 001 at 14:00-15:00 for all 3 days
6. ✓ Message should say "Schedule created successfully for CHM 001 on Tuesday, Wednesday, Thursday!"

### Step 4: Test Duplicate Detection (Per Day)
1. Click "Create Schedule" again
2. Select: CHM 001, Room 311, Faculty, Start Time: 15:00, End Time: 16:00
3. Check **Monday, Tuesday, Friday** (Monday was scheduled in Step 2; Tue/Wed/Thu in Step 3)
4. Click Submit
5. ✓ Should show error: "CHM 001 is already scheduled on Monday. Cannot have multiple sessions on the same day."
6. ✓ Modal should stay open, no schedules created

### Step 5: Test Partial Success
1. Click "Create Schedule" again
2. Select: CHM 001, Room 311, Faculty, Start Time: 16:00, End Time: 17:00
3. Check **Wednesday, Friday, Saturday**
   - Wednesday: Already has 07:30-09:00 and 14:00-15:00
   - Friday: Already has 07:30-10:30 and 14:00-15:00
   - Saturday: Empty
4. Click Submit
5. ✓ Should show yellow warning: "Schedule created for CHM 001 on Saturday. Failed days: Wednesday (already scheduled), Friday (already scheduled)"
6. ✓ Schedule view should reload with Saturday's new schedule

### Step 6: Test No Days Selected (Validation)
1. Click "Create Schedule" again
2. Select: CHM 001, Room 311, Faculty, Start Time: 17:00, End Time: 18:00
3. **Don't check any days**
4. Click Submit
5. ✓ Should show error: "Please select at least one day."
6. ✓ No schedule created

### Step 7: Test All Days Selection
1. Click "Create Schedule" again
2. Select: CHM 001, Room 311, Faculty, Start Time: 11:00, End Time: 12:00
3. **Check all 6 days** (Mon-Sat)
4. Click Submit
5. Should get errors for days that already have CHM 001 schedules
6. ✓ Days without conflicts should be created successfully

### Step 8: Test Different Course
1. Click "Create Schedule" again
2. Select: **MTH 001** (or any other course), Room 311, Faculty, Start Time: 09:00, End Time: 10:00
3. Check **Monday, Wednesday, Friday** (likely empty for new course)
4. Click Submit
5. ✓ Should successfully create MTH 001 for Mon, Wed, Fri
6. ✓ Message confirms: "Schedule created successfully for MTH 001 on Monday, Wednesday, Friday!"

## Verifying in Browser Console

Open DevTools (F12 or Right-click → Inspect) and go to **Console** tab:

### When creating schedule with selected days:
```
DEBUG submitCreateSchedule: selectedDays = [0, 1, 2]  ← Shows selected days
DEBUG handleBatchScheduleResults: results = {
    success: ["Monday", "Tuesday", "Wednesday"],
    failed: []
}
```

### If some days fail:
```
DEBUG handleBatchScheduleResults: results = {
    success: ["Monday", "Friday"],
    failed: [
        {day: "Wednesday", error: "CHM 001 is already scheduled on Wednesday"},
        {day: "Thursday", error: "Room is already booked at that time"}
    ]
}
```

## Expected Visual Changes

### Before (Dropdown)
```
Day ▼
[Select a day...]
[Monday        ]
[Tuesday       ]
...
```

### After (Checkboxes - 3-column Grid)
```
Days (Select one or more)
☐ Monday    ☐ Tuesday   ☐ Wednesday
☐ Thursday  ☐ Friday    ☐ Saturday
```

### On Mobile (<600px - 2-column Grid)
```
Days (Select one or more)
☐ Monday    ☐ Tuesday
☐ Wednesday ☐ Thursday
☐ Friday    ☐ Saturday
```

## Quick Edge Cases to Test

### Time Validation Still Works
- Select days but leave end time blank → Error: "Please fill in all fields"
- Select days with time range > 9:30 PM → Error: "Time outside allowed range"

### Hour Limit Validation Still Works
- If CHM 001 needs 3 hours lecture total
- Already scheduled: 1.5 hours (Mon) + 2 hours (Wed) = 3.5 hours
- Try to add any more lecture → Error: "Exceeds required hours"

### Room Type Filtering Still Works
- Select "Lab" room
- Try to add course that needs lecture hours only
- Should succeed (lab hours = 0)

### Faculty/Instructor Filtering Still Works
- Select faculty with conflicts
- All days still show available times
- Backend rejects if there's actually a conflict

## Common Issues & Solutions

### Issue: Checkboxes don't appear
**Solution:** Hard refresh browser (Ctrl+F5) to clear CSS cache

### Issue: Selecting multiple days shows error
**Solution:** Check browser console (F12) for JavaScript errors
- Look for red error messages
- Check that all fields are filled before submitting

### Issue: One day failed but others succeeded
**Solution:** This is expected! The warning message shows which days failed
- Click "Create Schedule" again if you want to retry the failed days
- Or modify the time and try again

### Issue: Edit mode has dropdown (not checkboxes)
**Solution:** This is by design! Edit mode intentionally stays as dropdown
- Edit is typically 1-to-1 (edit one schedule at a time)
- Create is 1-to-many (create same schedule across multiple days)

## Performance Notes

- Creating 6 schedules simultaneously takes ~3-5 seconds total
- API calls happen sequentially (one per day)
- Browser stays responsive during batch creation
- Page reloads automatically when done

## Rollback Plan (If Needed)

If you encounter issues and want to revert to single-day dropdown:

1. Replace `<div class="day-checkboxes">` section in schedule.html with original `<select>` dropdown
2. Change JavaScript `submitCreateSchedule()` back to getting single day value
3. Restart Django server

But the feature should be stable! All existing validations still apply.
