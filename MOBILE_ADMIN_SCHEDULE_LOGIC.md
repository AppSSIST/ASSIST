# Mobile App: Admin Schedule Page Logic & Data Integration

**Status:** Real-time Synchronization with Website  
**Last Updated:** April 24, 2026  
**Version:** 1.0

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Data Model & Relationships](#data-model--relationships)
3. [Schedule Components](#schedule-components)
4. [Data Synchronization](#data-synchronization)
5. [Validation Rules](#validation-rules)
6. [API Integration](#api-integration)
7. [Mobile Display Logic](#mobile-display-logic)
8. [Real-World Examples](#real-world-examples)

---

## Overview

The Admin Schedule Page manages **class schedules** by connecting **4 core entities**:
- **Courses** (what is being taught)
- **Faculty** (who teaches)
- **Sections** (which class/group learns)
- **Rooms** (where the class meets)

Every entry is a **Schedule**, which links these four elements with **time and day information**.

### Key Principle
**The mobile app displays the SAME data from the website in real-time.** No separate mobile database exists—all changes made by admins on the website instantly appear in the mobile app.

---

## Data Model & Relationships

### 1. **COURSE** 📚
Represents a subject offered in the curriculum.

```
Course
├── course_code: String (e.g., "CSC101")
├── descriptive_title: String (e.g., "Introduction to Programming")
├── year_level: Integer (1, 2, 3, or 4)
├── semester: Integer (1st or 2nd)
├── lecture_hours: Integer (e.g., 3 hours/week)
├── laboratory_hours: Integer (e.g., 2 hours/week)
├── credit_units: Integer (e.g., 4 units)
├── curriculum: ForeignKey → Curriculum
├── color: String (Hex color for UI display, auto-assigned)
└── timestamps: created_at, updated_at
```

**Example:**
- **CSC101**: Introduction to Programming (Year 1, Sem 1, 3 lec + 2 lab = 5 credit units)

---

### 2. **FACULTY** 👨‍🏫
Represents a teacher/instructor.

```
Faculty
├── first_name: String
├── middle_name: String (optional)
├── last_name: String
├── email: String (unique)
├── gender: Char (M/F)
├── professional_title: String (e.g., "Dr.", "Engr.")
├── employment_status: String (Full-Time, Part-Time, Contractual)
├── specialization: String (e.g., "Software Development", "Cyber Security")
├── highest_degree: String (Bachelor's, Master's, Doctoral)
├── prc_licensed: Boolean (Professional licensing status)
├── department: String
└── profile_picture: Image (optional)
```

**Example:**
- **Dr. Juan Dela Cruz** (Full-Time, Software Development, Master's Degree, PRC Licensed)

---

### 3. **SECTION** 🏢
Represents a specific group/class within the curriculum.

```
Section
├── name: String (Format: CPE[Year][Semester]S[Number], e.g., "CPE11S1")
│   └── CPE11S1 = Computer Engineering, Year 1, Semester 1, Section 1
├── year_level: Integer (1, 2, 3, or 4)
├── semester: Integer (1st or 2nd)
├── curriculum: ForeignKey → Curriculum
├── max_students: Integer (default: 40)
├── status: String (complete, incomplete)
└── timestamps: created_at, updated_at
```

**Example:**
- **CPE11S1**: First-year Computer Engineering students, 1st semester, Section 1 (up to 40 students)

---

### 4. **ROOM** 🏛️
Represents a physical classroom where classes are held.

```
Room
├── name: String (e.g., "Computer Lab 1")
├── room_number: String (e.g., "301")
├── capacity: Integer (e.g., 40 students)
├── campus: String (Casal, Arlegui)
├── room_type: String (Lecture, Laboratory)
└── timestamps: created_at
```

**Example:**
- **Computer Lab 1** (Room 301, Arlegui Campus, Lab Room, Capacity: 30)

---

### 5. **SCHEDULE** ⏰ (The Hub)
Connects all four components with time and day information.

```
Schedule
├── course: ForeignKey → Course
├── section: ForeignKey → Section
├── faculty: ForeignKey → Faculty (nullable)
├── room: ForeignKey → Room (nullable)
├── day: Integer (0=Monday, 1=Tuesday, ..., 5=Saturday)
├── start_time: String (HH:MM format, e.g., "08:00")
├── end_time: String (HH:MM format, e.g., "10:00")
├── duration: Integer (calculated in minutes, e.g., 120)
└── timestamps: created_at
```

---

## Schedule Components

### What Does a Schedule Entry Represent?

**One Schedule = One Class Meeting**

Example Schedule Entry:
```
Monday, 08:00 AM - 10:00 AM
├── Course: CSC101 (Introduction to Programming)
├── Section: CPE11S1 (Year 1, Sem 1, Section 1)
├── Faculty: Dr. Juan Dela Cruz (Teaches it)
├── Room: Computer Lab 1 (Room 301, Arlegui Campus)
└── Duration: 120 minutes (2 hours)
```

### Time Window Rules ⚠️

**ALL schedules must fall within: 07:30 AM - 09:30 PM (21:30)**

- Classes cannot start before 7:30 AM
- Classes cannot end after 9:30 PM
- Mobile app should enforce this when displaying/validating times

---

## Data Synchronization

### How Mobile App Gets Data

The mobile app fetches data through **REST API endpoints** provided by the Django website backend:

#### 1. **Get All Schedules**
```
GET /api/schedules/
Authentication: Bearer {access_token}
```

**Response Format:**
```json
{
  "schedules": [
    {
      "id": 42,
      "day": 0,
      "start_time": "08:00",
      "end_time": "10:00",
      "duration": 120,
      "course": {
        "id": 5,
        "course_code": "CSC101",
        "descriptive_title": "Introduction to Programming",
        "year_level": 1,
        "semester": 1,
        "lecture_hours": 3,
        "laboratory_hours": 2,
        "credit_units": 4,
        "color": "#FF6B6B"
      },
      "section": {
        "id": 10,
        "name": "CPE11S1",
        "year_level": 1,
        "semester": 1,
        "max_students": 40,
        "status": "complete"
      },
      "faculty": {
        "id": 3,
        "first_name": "Juan",
        "last_name": "Dela Cruz",
        "email": "juan@university.edu",
        "professional_title": "Dr.",
        "specialization": "Software Development"
      },
      "room": {
        "id": 8,
        "name": "Computer Lab 1",
        "room_number": "301",
        "capacity": 30,
        "campus": "arlegui",
        "room_type": "laboratory"
      }
    }
  ]
}
```

#### 2. **Get Schedules for Specific Section**
```
GET /api/schedules/?section={section_id}
Authentication: Bearer {access_token}
```

#### 3. **Get Schedules for Specific Faculty**
```
GET /api/schedules/?faculty={faculty_id}
Authentication: Bearer {access_token}
```

#### 4. **Get Schedules by Day**
```
GET /api/schedules/?day={day_number}
Authentication: Bearer {access_token}
```

### Real-Time Updates

**When an admin makes changes on the website:**

1. **Changes are saved to the database**
2. **Mobile app fetches updated data** (either on-demand or via periodic sync)
3. **Display refreshes** showing the latest schedule

**⚠️ Important:** The mobile app is a READ-ONLY display of the website data. All edits happen on the website admin panel.

---

## Validation Rules

### Rules Enforced During Schedule Creation

#### Rule 1: Course-Section Matching
```
Schedule.course.year_level MUST EQUAL Schedule.section.year_level
Schedule.course.semester MUST EQUAL Schedule.section.semester
Schedule.course.curriculum MUST EQUAL Schedule.section.curriculum
```
❌ **Invalid:** Assigning a Year 2 course to a Year 1 section  
✅ **Valid:** Both course and section are Year 1, Semester 1

#### Rule 2: Time Window Constraint
```
start_time >= 07:30 AND end_time <= 21:30
```
❌ **Invalid:** 06:30 - 08:00 (starts before 7:30)  
✅ **Valid:** 08:00 - 10:00

#### Rule 3: No Section Time Conflicts
```
Same section cannot have two classes at overlapping times on the same day
```
❌ **Invalid:** 
  - Monday 08:00-10:00: CSC101 (CSC Section)
  - Monday 09:00-11:00: CSC102 (same CSC Section) ← CONFLICT

✅ **Valid:**
  - Monday 08:00-10:00: CSC101
  - Monday 10:30-12:30: CSC102 (30-min buffer)

#### Rule 4: No Faculty Time Conflicts
```
Same faculty cannot teach two classes at overlapping times on the same day
```
❌ **Invalid:**
  - Monday 08:00-10:00: Dr. Juan teaches CSC101
  - Monday 09:00-11:00: Dr. Juan teaches CSC102 ← CONFLICT (same faculty)

✅ **Valid:**
  - Monday 08:00-10:00: Dr. Juan teaches CSC101
  - Monday 10:30-12:30: Dr. Juan teaches CSC102

#### Rule 5: No Room Time Conflicts
```
Same room cannot host two classes at overlapping times on the same day
```
❌ **Invalid:**
  - Monday 08:00-10:00: Computer Lab 1 hosts CSC101
  - Monday 09:00-11:00: Computer Lab 1 hosts CSC102 ← CONFLICT

✅ **Valid:**
  - Monday 08:00-10:00: Computer Lab 1 hosts CSC101
  - Monday 10:30-12:30: Computer Lab 1 hosts CSC102

#### Rule 6: No Duplicate Course on Same Day per Section
```
Same section cannot have the same course scheduled twice on the same day
```
❌ **Invalid:**
  - Monday 08:00-10:00: CSC101 (CPE11S1)
  - Monday 14:00-16:00: CSC101 (CPE11S1) ← DUPLICATE on same day

✅ **Valid:**
  - Monday 08:00-10:00: CSC101 (CPE11S1)
  - Tuesday 08:00-10:00: CSC101 (CPE11S1) ← Different day

---

## API Integration

### Authentication
All API requests require a **JWT (JSON Web Token)**:

```
Header: Authorization: Bearer {access_token}
```

### Common API Endpoints for Mobile

#### Get All Schedules
```
GET /api/schedules/
GET /api/schedule/all/
```

#### Get Staff Schedule (Formatted HTML)
```
GET /api/schedule/staff/html/
Returns: Complete HTML page with CSS styling
```

#### Get Section Schedule
```
GET /api/section/{section_id}/schedule/
```

#### Get Faculty Schedule
```
GET /api/faculty/{faculty_id}/schedule/
```

#### Get Room Availability
```
GET /api/rooms/
GET /api/room/{room_id}/schedule/
```

### Error Handling

**When API calls fail, mobile app should:**

1. **Show cached data** (if previously loaded)
2. **Display error message** to user: "Unable to load schedules. Please check your connection."
3. **Provide retry button** to attempt reload
4. **Gracefully degrade** if no cached data exists

---

## Mobile Display Logic

### How to Display Schedules in Mobile App

#### 1. **Weekly Schedule View**
Display as a grid: Days × Time Slots

```
Example: CPE11S1 Weekly Schedule

        MON    TUE    WED    THU    FRI    SAT
07:30
08:00  CSC101
       Dr. Dela Cruz
       Lab 1
10:00
10:30
11:00  CSC102
       Dr. Garcia
       Room 305
13:00
14:00  CSC103
       Dr. Santos
       Lab 2
16:00
```

#### 2. **List View**
Display as a scrollable list sorted by day and time

```
MONDAY
├── 08:00 - 10:00: CSC101 - Introduction to Programming
│   Faculty: Dr. Juan Dela Cruz
│   Section: CPE11S1
│   Room: Computer Lab 1 (Arlegui, Capacity: 30)
│
└── 14:00 - 16:00: CSC103 - Database Systems
    Faculty: Dr. Maria Santos
    Section: CPE11S1
    Room: Lecture Room 305 (Casal, Capacity: 40)

TUESDAY
├── 09:00 - 11:00: CSC102 - Web Development
│   Faculty: Prof. Carlos Garcia
│   Section: CPE11S1
│   Room: Computer Lab 2 (Arlegui, Capacity: 30)
```

#### 3. **Section Filter**
Allow users to view schedules filtered by section

```
Select Section: [CPE11S1 ▼]
(Shows only schedules for CPE11S1)
```

#### 4. **Faculty View**
Show all classes taught by a specific faculty

```
Select Faculty: [Dr. Juan Dela Cruz ▼]
(Shows only schedules taught by Dr. Juan)
```

#### 5. **Room Availability View**
Show which rooms are available at specific times

```
Room: Computer Lab 1 (Arlegui)
Capacity: 30 | Type: Laboratory

Monday:
├── 08:00 - 10:00: OCCUPIED (CSC101)
├── 10:00 - 12:00: AVAILABLE
├── 12:00 - 14:00: AVAILABLE
├── 14:00 - 16:00: OCCUPIED (CSC103)
└── 16:00 - 21:30: AVAILABLE

Tuesday:
├── 09:00 - 11:00: OCCUPIED (CSC102)
├── 11:00 - 21:30: AVAILABLE
```

### Color Coding

**Each course has an auto-assigned color** (stored in `Course.color`)

- Use this color to visually differentiate courses in the schedule grid
- Makes it easier to spot the same course across different days/times
- Example:
  - CSC101 = Red (#FF6B6B)
  - CSC102 = Teal (#4ECDC4)
  - CSC103 = Blue (#45B7D1)

### Duration Calculation

**Duration is stored in minutes** and calculated as:

```
duration_minutes = (end_time_in_minutes) - (start_time_in_minutes)

Example:
start_time = "08:00" (480 minutes from midnight)
end_time = "10:00" (600 minutes from midnight)
duration = 600 - 480 = 120 minutes (2 hours)
```

---

## Real-World Examples

### Example 1: Complete Monday Schedule for CPE11S1

```
Section: CPE11S1 (Computer Engineering, Year 1, Semester 1)
Curriculum: BS Computer Engineering
Max Students: 40

MONDAY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

08:00 - 10:00 (120 minutes)
📚 CSC101 - Introduction to Programming
👨‍🏫 Dr. Juan Dela Cruz (Full-Time, Software Development)
🏛️ Computer Lab 1 (Room 301, Arlegui Campus, Capacity: 30)
📊 Lecture: 3hrs/week, Lab: 2hrs/week, 4 credit units
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

10:30 - 12:00 (90 minutes)
📚 MAT101 - Calculus I
👨‍🏫 Prof. Maria Garcia (Full-Time, Mathematics)
🏛️ Lecture Room 305 (Room 305, Casal Campus, Capacity: 40)
📊 Lecture: 4hrs/week, 3 credit units
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

14:00 - 16:00 (120 minutes)
📚 ENG101 - English Communication
👨‍🏫 Prof. Antonio Santos (Part-Time, English)
🏛️ Room 102 (Room 102, Casal Campus, Capacity: 40)
📊 Lecture: 3hrs/week, 3 credit units
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Example 2: Faculty Schedule (Dr. Juan Dela Cruz)

```
Faculty: Dr. Juan Dela Cruz
📋 Specialization: Software Development | 👔 Status: Full-Time
🎓 Degree: Master's | ✅ PRC Licensed: Yes
📧 juan@university.edu

MONDAY
├── 08:00 - 10:00: CSC101 (Computer Lab 1, CPE11S1)
└── 15:00 - 17:00: CSC201 (Computer Lab 2, CPE21S1)

TUESDAY
├── 09:00 - 11:00: CSC102 (Lecture Room 305, CPE11S1)
└── 13:00 - 15:00: CSC202 (Lecture Room 401, CPE21S1)

WEDNESDAY
└── 10:00 - 12:00: CSC103 (Computer Lab 1, CPE11S2)

THURSDAY
└── 14:00 - 16:00: CSC201 (Lecture Room 305, CPE21S1)

FRIDAY
└── 08:00 - 10:00: CSC101 (Computer Lab 2, CPE11S2)

SATURDAY
└── 09:00 - 11:00: CSC102 (Lecture Room 102, CPE11S3)

Total Weekly Hours: 14 hours (3+3+2+2+2+2)
Total Unique Courses: 4
Total Credit Units: 14
```

### Example 3: Room Utilization (Computer Lab 1)

```
Room: Computer Lab 1
Location: Arlegui Campus, Room #301
Type: Laboratory | Capacity: 30

MONDAY
├── 08:00 - 10:00: CSC101 (Dr. Juan Dela Cruz, CPE11S1)
├── 10:00 - 12:30: AVAILABLE
├── 12:30 - 14:30: CSC201 (Dr. Sarah Chen, CPE21S2)
└── 14:30 - 21:30: AVAILABLE

TUESDAY
├── 09:00 - 11:00: AVAILABLE
├── 11:00 - 13:00: CSC102 (Prof. Maria Garcia, CPE11S2)
├── 13:00 - 21:30: AVAILABLE

WEDNESDAY
├── 08:00 - 10:00: CSC103 (Dr. Juan Dela Cruz, CPE11S2)
├── 10:00 - 21:30: AVAILABLE

THURSDAY
├── 07:30 - 09:30: CSC101 (Dr. Carlos Lopez, CPE11S3)
├── 09:30 - 12:00: AVAILABLE
├── 12:00 - 14:00: CSC301 (Dr. Juan Dela Cruz, CPE31S1)
├── 14:00 - 21:30: AVAILABLE

FRIDAY
├── 08:00 - 10:00: CSC102 (Prof. Miguel Santos, CPE11S1)
├── 10:00 - 21:30: AVAILABLE

SATURDAY
├── 09:00 - 11:00: CSC201 (Dr. Maria Garcia, CPE21S3)
├── 11:00 - 21:30: AVAILABLE

Peak Hours: Monday 08:00-14:30 (High utilization)
Daily Utilization: ~45%
```

---

## Summary for Mobile Developers

### Key Points to Remember

1. **Data comes from the website** - Mobile is a synchronized display, not a standalone database
2. **One Schedule = One Class Meeting** with 4 connected entities (Course, Faculty, Section, Room)
3. **All times use 24-hour format** (HH:MM) and are bounded by 07:30 - 21:30
4. **Validation happens server-side** - Mobile app displays valid data only
5. **Color-coding helps users** - Each course has a unique auto-assigned color
6. **Filtering is essential** - Users need to filter by section, faculty, or room
7. **Display formats vary** - Grid, list, and individual views serve different needs
8. **No conflicts exist** - Time/resource conflicts are prevented at the API level

### Testing Checklist

- [ ] Load and display all schedules correctly
- [ ] Filter schedules by section, faculty, and room
- [ ] Display durations correctly in minutes
- [ ] Color-code courses based on `Course.color`
- [ ] Handle time display in 24-hour format (08:00, 14:30, etc.)
- [ ] Show faculty details (name, specialization, email)
- [ ] Display room details (name, capacity, campus, type)
- [ ] Handle missing optional data (faculty or room can be NULL)
- [ ] Implement error handling for API failures
- [ ] Cache data for offline viewing
- [ ] Refresh data periodically to stay in sync
- [ ] Validate time window constraints (07:30 - 21:30)

---

## Appendix: Field Reference

### Day Numbers
```
0 = Monday
1 = Tuesday
2 = Wednesday
3 = Thursday
4 = Friday
5 = Saturday
```

### Course Year Levels
```
1 = 1st Year
2 = 2nd Year
3 = 3rd Year
4 = 4th Year
```

### Course Semesters
```
1 = 1st Semester
2 = 2nd Semester
```

### Employment Status
```
full_time = Full-Time
part_time = Part-Time
contractual = Contractual
```

### Room Types
```
lecture = Lecture Room
laboratory = Laboratory
```

### Campus Options
```
casal = Casal Campus
arlegui = Arlegui Campus
```

### Section Status
```
complete = Schedule is fully planned
incomplete = Schedule not yet created
```

---

**End of Document**

Last Updated: April 24, 2026  
For questions or clarifications, refer to the main API documentation.
