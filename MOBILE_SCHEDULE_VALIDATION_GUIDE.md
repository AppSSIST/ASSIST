# Mobile App Schedule Validation Guide

## Overview
Apply the same course hour tracking and validation logic from the web admin interface to your mobile app. This guide shows how to implement client-side validation for adding/editing schedules with lecture vs laboratory hour differentiation.

---

## Architecture

### Data Flow
```
Mobile App UI
    ↓
Fetch metadata (courses, sections, rooms, faculty)
    ↓
Client-side validation (JavaScript/Kotlin logic)
    ↓
POST to /admin/schedule/add/ or /admin/schedule/edit/
    ↓
Server validation
    ↓
Success/Error response
```

---

## API Endpoints

### 1. Get Section with Courses & Schedule Data
```http
GET /admin/section/{section_id}/schedule-data/
Authorization: Bearer {access_token}
```

**Response:**
```json
{
  "success": true,
  "schedules": [
    {
      "id": 1,
      "course_id": 45,
      "section_id": 6,
      "day": 0,
      "start_time": "13:00",
      "end_time": "15:00",
      "duration": 7200,
      "room_type": "lecture",
      "course_code": "CHM101",
      "course_title": "Chemistry I",
      "faculty": "Dr. Smith",
      "room": "A-311"
    }
  ],
  "courses": [
    {
      "course_code": "CHM101",
      "descriptive_title": "Chemistry I",
      "lecture_hours": 3,
      "laboratory_hours": 2,
      "credit_units": 4,
      "faculty": "Dr. Smith, Dr. Johnson"
    }
  ],
  "section_info": {
    "name": "BS Chemistry 1-1",
    "year_level": 1,
    "semester": 1,
    "curriculum": "BS Chemistry"
  }
}
```

### 2. Create Schedule
```http
POST /admin/schedule/add/
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer {access_token}

course={course_id}&section={section_id}&room={room_id}&faculty={faculty_id}&day={day}&start_time={HH:MM}&end_time={HH:MM}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Schedule created successfully"
}
```

**Error Response (400):**
```json
{
  "success": false,
  "errors": [
    "This would add 4hrs of lecture, but only 3hrs is remaining..."
  ]
}
```

### 3. Edit Schedule
```http
POST /admin/schedule/edit/{schedule_id}/
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer {access_token}

course={course_id}&section={section_id}&room={room_id}&faculty={faculty_id}&day={day}&start_time={HH:MM}&end_time={HH:MM}
```

---

## Client-Side Validation Logic

### Core Functions to Implement

#### 1. Calculate Course Hours Used (Excluding Current Schedule)
```javascript
// For Java/Kotlin, translate this to your language
function getCourseHoursInSectionExcluding(
  courseId, 
  sectionId, 
  excludeScheduleId, 
  schedulesList
) {
  let lectureHours = 0;
  let labHours = 0;
  
  schedulesList.forEach(schedule => {
    // Skip the schedule being edited
    if (schedule.id === excludeScheduleId) {
      return;
    }
    
    if (schedule.course_id === courseId && schedule.section_id === sectionId) {
      const durationHours = schedule.duration / 3600; // Convert seconds to hours
      
      if (schedule.room_type === 'lecture') {
        lectureHours += durationHours;
      } else if (schedule.room_type === 'laboratory') {
        labHours += durationHours;
      }
    }
  });
  
  return { lecture: lectureHours, lab: labHours };
}
```

#### 2. Validate Schedule Duration Against Requirements
```javascript
function validateScheduleHours(
  courseId,
  sectionId,
  newDurationHours,
  roomType,
  coursesList,
  schedulesList,
  excludeScheduleId = null
) {
  // Find course requirements
  const course = coursesList.find(c => c.id === courseId);
  if (!course) {
    return { valid: false, error: "Course not found" };
  }
  
  const lectureRequired = course.lecture_hours || 0;
  const labRequired = course.laboratory_hours || 0;
  
  // Get existing hours (excluding current schedule if editing)
  const existingHours = getCourseHoursInSectionExcluding(
    courseId,
    sectionId,
    excludeScheduleId,
    schedulesList
  );
  
  // Check if this new schedule would exceed requirements
  if (roomType === 'lecture') {
    const newTotal = existingHours.lecture + newDurationHours;
    
    if (lectureRequired > 0 && newTotal > lectureRequired) {
      return {
        valid: false,
        error: `Would use ${newTotal.toFixed(1)}hrs of lecture, but ${course.course_code} requires only ${lectureRequired}hrs.`
      };
    }
  } else if (roomType === 'laboratory') {
    const newTotal = existingHours.lab + newDurationHours;
    
    if (labRequired > 0 && newTotal > labRequired) {
      return {
        valid: false,
        error: `Would use ${newTotal.toFixed(1)}hrs of lab, but ${course.course_code} requires only ${labRequired}hrs.`
      };
    }
  }
  
  return { valid: true };
}
```

#### 3. Calculate Duration from Times
```javascript
function calculateDurationInHours(startTime, endTime) {
  // Format: "HH:MM" (24-hour format)
  const [startHour, startMin] = startTime.split(':').map(Number);
  const [endHour, endMin] = endTime.split(':').map(Number);
  
  const startTotalMin = startHour * 60 + startMin;
  const endTotalMin = endHour * 60 + endMin;
  
  const durationMin = endTotalMin - startTotalMin;
  return durationMin / 60; // Convert to hours (decimal)
}
```

#### 4. Check for Duplicate Course on Same Day
```javascript
function isDuplicateCourseOnDay(
  courseId,
  sectionId,
  dayIndex,
  schedulesList,
  excludeScheduleId = null
) {
  return schedulesList.some(schedule => 
    schedule.course_id === courseId &&
    schedule.section_id === sectionId &&
    schedule.day === dayIndex &&
    schedule.id !== excludeScheduleId
  );
}
```

---

## Implementation Examples

### Kotlin (Android) - Create Schedule

```kotlin
import okhttp3.*
import org.json.JSONObject
import java.io.IOException

class ScheduleManager(private val token: String, private val baseUrl: String) {
    
    private val client = OkHttpClient()
    
    fun createSchedule(
        courseId: Int,
        sectionId: Int,
        roomId: Int?,
        facultyId: Int?,
        day: Int,
        startTime: String,
        endTime: String,
        courses: List<Course>,
        schedules: List<Schedule>
    ): Result {
        
        // Step 1: Find the course
        val course = courses.find { it.id == courseId }
            ?: return Result.Error("Course not found")
        
        // Step 2: Find the room to get room_type
        val room = findRoomById(roomId)
        val roomType = room?.room_type ?: "lecture"
        
        // Step 3: Check for duplicate course on same day
        if (isDuplicateCourseOnDay(courseId, sectionId, day, schedules)) {
            return Result.Error(
                "${course.course_code} is already scheduled on ${getDayName(day)}"
            )
        }
        
        // Step 4: Validate schedule duration
        val duration = calculateDurationInHours(startTime, endTime)
        val validation = validateScheduleHours(
            courseId, sectionId, duration, roomType, courses, schedules
        )
        if (!validation.valid) {
            return Result.Error(validation.error)
        }
        
        // Step 5: Validate time range (7:30 AM - 9:30 PM)
        val timeValidation = validateTimeRange(startTime, endTime)
        if (!timeValidation.valid) {
            return Result.Error(timeValidation.error)
        }
        
        // Step 6: Send to server
        return sendCreateScheduleRequest(
            courseId, sectionId, roomId, facultyId, day, startTime, endTime
        )
    }
    
    private fun sendCreateScheduleRequest(
        courseId: Int,
        sectionId: Int,
        roomId: Int?,
        facultyId: Int?,
        day: Int,
        startTime: String,
        endTime: String
    ): Result {
        val body = FormBody.Builder()
            .add("course", courseId.toString())
            .add("section", sectionId.toString())
            .add("day", day.toString())
            .add("start_time", startTime)
            .add("end_time", endTime)
            .apply {
                if (roomId != null) add("room", roomId.toString())
                if (facultyId != null) add("faculty", facultyId.toString())
            }
            .build()
        
        val request = Request.Builder()
            .url("$baseUrl/admin/schedule/add/")
            .addHeader("Authorization", "Bearer $token")
            .post(body)
            .build()
        
        return try {
            val response = client.newCall(request).execute()
            val responseBody = response.body?.string() ?: "{}"
            val json = JSONObject(responseBody)
            
            if (json.getBoolean("success")) {
                Result.Success("Schedule created successfully")
            } else {
                val errors = json.getJSONArray("errors")
                val errorMsg = errors.getString(0)
                Result.Error(errorMsg)
            }
        } catch (e: IOException) {
            Result.Error("Network error: ${e.message}")
        }
    }
    
    private fun calculateDurationInHours(startTime: String, endTime: String): Double {
        val (startHour, startMin) = startTime.split(":").map { it.toInt() }
        val (endHour, endMin) = endTime.split(":").map { it.toInt() }
        
        val startTotalMin = startHour * 60 + startMin
        val endTotalMin = endHour * 60 + endMin
        
        return (endTotalMin - startTotalMin) / 60.0
    }
    
    private fun isDuplicateCourseOnDay(
        courseId: Int,
        sectionId: Int,
        dayIndex: Int,
        schedules: List<Schedule>
    ): Boolean {
        return schedules.any { schedule ->
            schedule.course_id == courseId &&
            schedule.section_id == sectionId &&
            schedule.day == dayIndex
        }
    }
    
    private fun validateTimeRange(startTime: String, endTime: String): ValidationResult {
        fun timeToMinutes(time: String): Int {
            val (h, m) = time.split(":").map { it.toInt() }
            return h * 60 + m
        }
        
        val minAllowed = 7 * 60 + 30 // 7:30 AM
        val maxAllowed = 21 * 60 + 30 // 9:30 PM
        
        val startMin = timeToMinutes(startTime)
        val endMin = timeToMinutes(endTime)
        
        return when {
            startMin < minAllowed || endMin > maxAllowed ->
                ValidationResult(false, "Times must be between 7:30 AM and 9:30 PM")
            endMin <= startMin ->
                ValidationResult(false, "End time must be after start time")
            else -> ValidationResult(true, "")
        }
    }
}

// Data classes
sealed class Result {
    data class Success(val message: String) : Result()
    data class Error(val message: String) : Result()
}

data class ValidationResult(val valid: Boolean, val error: String)

data class Course(
    val id: Int,
    val course_code: String,
    val descriptive_title: String,
    val lecture_hours: Int,
    val laboratory_hours: Int
)

data class Schedule(
    val id: Int,
    val course_id: Int,
    val section_id: Int,
    val day: Int,
    val start_time: String,
    val end_time: String,
    val duration: Int,
    val room_type: String
)
```

### Swift (iOS) - Create Schedule

```swift
import Foundation

class ScheduleManager {
    let token: String
    let baseUrl: String
    
    init(token: String, baseUrl: String) {
        self.token = token
        self.baseUrl = baseUrl
    }
    
    func createSchedule(
        courseId: Int,
        sectionId: Int,
        roomId: Int?,
        facultyId: Int?,
        day: Int,
        startTime: String,
        endTime: String,
        courses: [Course],
        schedules: [Schedule]
    ) async -> Result<String, ScheduleError> {
        
        // Step 1: Find the course
        guard let course = courses.first(where: { $0.id == courseId }) else {
            return .failure(.courseNotFound)
        }
        
        // Step 2: Find the room
        let room = findRoomById(roomId)
        let roomType = room?.room_type ?? "lecture"
        
        // Step 3: Check for duplicate
        if isDuplicateCourseOnDay(courseId, sectionId, day, schedules) {
            return .failure(.duplicateCourse(course.course_code, getDayName(day)))
        }
        
        // Step 4: Validate hours
        let duration = calculateDurationInHours(startTime, endTime)
        let validation = validateScheduleHours(
            courseId, sectionId, duration, roomType, courses, schedules
        )
        if !validation.valid {
            return .failure(.hoursExceeded(validation.error))
        }
        
        // Step 5: Validate time range
        let timeValidation = validateTimeRange(startTime, endTime)
        if !timeValidation.valid {
            return .failure(.invalidTimeRange(timeValidation.error))
        }
        
        // Step 6: Send to server
        return await sendCreateScheduleRequest(
            courseId, sectionId, roomId, facultyId, day, startTime, endTime
        )
    }
    
    private func calculateDurationInHours(_ startTime: String, _ endTime: String) -> Double {
        let components = startTime.split(separator: ":").compactMap { Int($0) }
        let endComponents = endTime.split(separator: ":").compactMap { Int($0) }
        
        guard components.count == 2, endComponents.count == 2 else { return 0 }
        
        let startMin = components[0] * 60 + components[1]
        let endMin = endComponents[0] * 60 + endComponents[1]
        
        return Double(endMin - startMin) / 60.0
    }
    
    private func validateTimeRange(_ startTime: String, _ endTime: String) -> (valid: Bool, error: String) {
        let minAllowed = 7 * 60 + 30 // 7:30 AM
        let maxAllowed = 21 * 60 + 30 // 9:30 PM
        
        let startComponents = startTime.split(separator: ":").compactMap { Int($0) }
        let endComponents = endTime.split(separator: ":").compactMap { Int($0) }
        
        guard startComponents.count == 2, endComponents.count == 2 else {
            return (false, "Invalid time format")
        }
        
        let startMin = startComponents[0] * 60 + startComponents[1]
        let endMin = endComponents[0] * 60 + endComponents[1]
        
        if startMin < minAllowed || endMin > maxAllowed {
            return (false, "Times must be between 7:30 AM and 9:30 PM")
        }
        
        if endMin <= startMin {
            return (false, "End time must be after start time")
        }
        
        return (true, "")
    }
}

// Data structures
enum Result<Success, Failure: Error> {
    case success(Success)
    case failure(Failure)
}

enum ScheduleError: Error {
    case courseNotFound
    case duplicateCourse(String, String)
    case hoursExceeded(String)
    case invalidTimeRange(String)
    case networkError(String)
}

struct Course: Codable {
    let id: Int
    let course_code: String
    let descriptive_title: String
    let lecture_hours: Int
    let laboratory_hours: Int
}

struct Schedule: Codable {
    let id: Int
    let course_id: Int
    let section_id: Int
    let day: Int
    let start_time: String
    let end_time: String
    let duration: Int
    let room_type: String
}
```

---

## Step-by-Step Implementation Guide

### 1. **Fetch Section Data on Load**
```
GET /admin/section/{sectionId}/schedule-data/
```
- Parse response to get:
  - Current schedules (with room_type)
  - Available courses with lecture_hours & laboratory_hours
  - Section metadata

### 2. **Display Course Selection UI**
- Show only courses matching section criteria (curriculum, year level, semester)
- Hide courses that already have all hours scheduled
- Show real-time progress: "Used: 1.5/3 hrs lecture, 0/2 hrs lab"

### 3. **On Room Selection**
- Display the room type (lecture/laboratory)
- Show which hours will be used: lecture or lab

### 4. **On Time Selection**
- Calculate duration
- Show warning if it would exceed remaining hours
- Disable submit button if validation fails

### 5. **Before Submission**
- Run all 4 validations:
  1. Duplicate course on same day?
  2. Hours would exceed requirement?
  3. Time range valid (7:30 AM - 9:30 PM)?
  4. End time after start time?
  
- Only send POST if all pass

### 6. **Handle Server Response**
- Success: Reload schedules, show confirmation
- Error: Display the error message to user

---

## Key Differences from Web Implementation

| Aspect | Web | Mobile |
|--------|-----|--------|
| **Validation Trigger** | Real-time on field changes | Before submission |
| **Room Type Access** | HTML data attributes | API response `room_type` field |
| **State Management** | DOM/JavaScript objects | App state/viewmodel |
| **Error Display** | Modal warning divs | Toast/Dialog/Alert |
| **Time Picker** | Custom scroll wheel | Native date/time picker |
| **Hour Calculation** | Division by 60 (seconds→minutes→hours) | Same: duration / 3600 |

---

## Testing Checklist

- [ ] Create schedule with valid hours
- [ ] Attempt to exceed lecture hours → blocked
- [ ] Attempt to exceed lab hours → blocked
- [ ] Create duplicate course on same day → blocked
- [ ] Times outside 7:30 AM - 9:30 PM → blocked
- [ ] Edit schedule to exceed hours → blocked
- [ ] After completion, course disappears from dropdown
- [ ] Course hours show as "Complete" or similar

---

## API Response Examples

### Successful Creation
```json
HTTP 200 OK
{
  "success": true,
  "message": "Schedule created successfully"
}
```

### Validation Failure
```json
HTTP 400 Bad Request
{
  "success": false,
  "errors": [
    "This would add 4hrs of lecture, but only 3hrs is remaining. Chemistry requires 3hrs total."
  ]
}
```

### Duplicate Course Error
```json
HTTP 400 Bad Request
{
  "success": false,
  "errors": [
    "CHM101 is already scheduled on Monday. A course cannot have multiple sessions on the same day."
  ]
}
```

---

## Summary

The mobile app should:

1. **Fetch** course requirements and existing schedules from `/admin/section/{id}/schedule-data/`
2. **Calculate** total lecture vs lab hours per course
3. **Validate** before allowing submission:
   - No duplicate courses per day
   - No exceeding lecture hour requirements
   - No exceeding lab hour requirements
   - Times within 7:30 AM - 9:30 PM
4. **Display** warnings to users
5. **Submit** only valid schedules to `/admin/schedule/add/` or `/admin/schedule/edit/`

This mirrors the web interface logic exactly, ensuring consistency across platforms.
