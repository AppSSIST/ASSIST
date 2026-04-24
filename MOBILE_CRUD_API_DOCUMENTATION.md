# Mobile CRUD API Documentation

## Overview
Complete CRUD (Create, Read, Update, Delete) API endpoints for the Auto-Scheduling mobile application. All endpoints require JWT authentication.

---

## Authentication
All endpoints (except GET list endpoints) require:
- **Header**: `Authorization: Bearer <JWT_TOKEN>`
- **Token Endpoint**: `POST /api/auth/token/`

---

## Faculty API Endpoints

### Edit Faculty
**Endpoint**: `PUT /api/faculty/<faculty_id>/`
**Authentication**: Required
**Description**: Update faculty member details

**Request Body**:
```json
{
  "first_name": "John",
  "middle_name": "David",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "gender": "M",
  "professional_title": "Dr.",
  "employment_status": "full_time",
  "highest_degree": "Master's Degree",
  "prc_licensed": true,
  "specialization": "software_dev"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Faculty updated successfully",
  "faculty_id": 1
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Email already registered to another faculty member"
}
```

---

### Delete Faculty
**Endpoint**: `DELETE /api/faculty/<faculty_id>/`
**Authentication**: Required
**Description**: Delete faculty member and all associated user accounts

**Success Response** (204 No Content):
```json
{
  "success": true,
  "message": "Faculty deleted successfully"
}
```

**Notes**:
- Automatically unassigns faculty from all schedules (preserves schedule records)
- Deletes all User accounts with matching email address
- Logs all activity

---

## Course API Endpoints

### Edit Course
**Endpoint**: `PUT /api/courses/<course_id>/edit/`
**Authentication**: Required
**Description**: Update course details

**Request Body**:
```json
{
  "curriculum_id": 1,
  "course_code": "CS101",
  "descriptive_title": "Introduction to Computer Science",
  "laboratory_hours": 2,
  "lecture_hours": 3,
  "credit_units": 4,
  "year_level": 1,
  "semester": 1
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Course updated successfully",
  "course_id": 1
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Course code already exists in this curriculum"
}
```

---

### Delete Course
**Endpoint**: `DELETE /api/courses/<course_id>/edit/`
**Authentication**: Required
**Description**: Delete course (only if no schedules exist)

**Success Response** (204 No Content):
```json
{
  "success": true,
  "message": "Course deleted successfully"
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": "Cannot delete course with existing schedules"
}
```

---

## Room API Endpoints

### Edit Room
**Endpoint**: `PUT /api/rooms/<room_id>/`
**Authentication**: Required
**Description**: Update room details

**Request Body**:
```json
{
  "name": "Room 101",
  "room_number": "101",
  "capacity": 50,
  "campus": "casal",
  "room_type": "lecture"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Room updated successfully",
  "room_id": 1
}
```

---

### Delete Room
**Endpoint**: `DELETE /api/rooms/<room_id>/`
**Authentication**: Required
**Description**: Delete room

**Success Response** (204 No Content):
```json
{
  "success": true,
  "message": "Room deleted successfully"
}
```

---

## Section API Endpoints

### Edit Section
**Endpoint**: `PUT /api/sections/<section_id>/`
**Authentication**: Required
**Description**: Update section details

**Request Body**:
```json
{
  "name": "CPE11S1",
  "year_level": 1,
  "semester": 1,
  "max_students": 40,
  "status": "complete"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Section updated successfully",
  "section_id": 1
}
```

**Validation Rules**:
- Section name must follow format: `CPE[year][semester]S[number]` (e.g., CPE11S1)
- Year and semester in name must match selected values

---

### Delete Section
**Endpoint**: `DELETE /api/sections/<section_id>/`
**Authentication**: Required
**Description**: Delete section and all associated schedules

**Success Response** (204 No Content):
```json
{
  "success": true,
  "message": "Section deleted successfully"
}
```

**Notes**:
- Automatically deletes all schedules for this section

---

## Schedule API Endpoints

### Add Schedule
**Endpoint**: `POST /api/schedules/`
**Authentication**: Required
**Description**: Create new schedule

**Request Body**:
```json
{
  "course_id": 1,
  "section_id": 1,
  "faculty_id": 1,
  "room_id": 1,
  "day": 0,
  "start_time": "08:00",
  "end_time": "09:30"
}
```

**Success Response** (201 Created):
```json
{
  "success": true,
  "message": "Schedule created successfully",
  "schedule_id": 1
}
```

**Validation Rules**:
- Times must be within 07:30 - 21:30
- No faculty time conflicts on same day
- No section time conflicts on same day
- No room time conflicts on same day
- Course year/semester must match section year/semester
- Course curriculum must match section curriculum

---

### Edit Schedule
**Endpoint**: `PUT /api/schedules/<schedule_id>/`
**Authentication**: Required
**Description**: Update schedule details

**Request Body**:
```json
{
  "course_id": 1,
  "section_id": 1,
  "faculty_id": 1,
  "room_id": 1,
  "day": 0,
  "start_time": "08:00",
  "end_time": "09:30"
}
```

**Success Response** (200 OK):
```json
{
  "success": true,
  "message": "Schedule updated successfully",
  "schedule_id": 1
}
```

---

### Delete Schedule
**Endpoint**: `DELETE /api/schedules/<schedule_id>/`
**Authentication**: Required
**Description**: Delete schedule

**Success Response** (204 No Content):
```json
{
  "success": true,
  "message": "Schedule deleted successfully"
}
```

---

## Day Codes
Day values use integer codes:
- 0 = Monday
- 1 = Tuesday
- 2 = Wednesday
- 3 = Thursday
- 4 = Friday
- 5 = Saturday

---

## Employment Status Codes
- `full_time` = Full-Time
- `part_time` = Part-Time
- `contractual` = Contractual

---

## Room Type Codes
- `lecture` = Lecture
- `laboratory` = Laboratory

---

## Section Status Codes
- `complete` = Complete Schedule
- `incomplete` = No Schedule Yet

---

## Error Codes

| HTTP Status | Description |
|---|---|
| 200 | Successful PUT request |
| 201 | Successful POST (creation) |
| 204 | Successful DELETE (no content) |
| 400 | Bad Request (validation error) |
| 404 | Resource not found |
| 500 | Internal server error |

---

## Activity Logging
All CRUD operations are automatically logged with:
- User performing the action
- Action type (create, edit, delete)
- Entity type and name
- Timestamp

---

## Example Usage

### Create Faculty Account
1. First, add faculty via `POST /api/faculty/add/`
2. Faculty receives email with password reset link
3. Faculty sets password and can login

### Update Faculty
```bash
curl -X PUT http://localhost:8000/api/faculty/1/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "email": "jane.doe@example.com",
    "employment_status": "part_time"
  }'
```

### Delete Faculty
```bash
curl -X DELETE http://localhost:8000/api/faculty/1/ \
  -H "Authorization: Bearer <TOKEN>"
```

---

## Notes for Mobile App Developers

1. **Token Management**: Store and refresh JWT tokens securely
2. **Error Handling**: Check both response status codes and `success` field
3. **Validation**: Client-side validation should match server-side rules
4. **Time Format**: Use 24-hour format (HH:MM)
5. **Permissions**: Ensure user has admin permissions for all CRUD operations
6. **Cascade Operations**: 
   - Deleting section cascades to schedules
   - Deleting faculty unassigns from schedules but preserves schedules
   - Deleting course requires no active schedules

---

## Implemented Routes (hello/urls.py)

```python
# Mobile CRUD API endpoints for Faculty
path('api/faculty/<int:faculty_id>/', views.api_edit_delete_faculty)

# Mobile CRUD API endpoints for Course
path('api/courses/<int:course_id>/edit/', views.api_edit_delete_course)

# Mobile CRUD API endpoints for Room
path('api/rooms/<int:room_id>/', views.api_edit_delete_room)

# Mobile CRUD API endpoints for Section
path('api/sections/<int:section_id>/', views.api_edit_delete_section)

# Mobile CRUD API endpoints for Schedule
path('api/schedules/<int:schedule_id>/', views.api_edit_delete_schedule)
```

---

## Implementation Summary

### Endpoints Created: 10
- Faculty: Edit (PUT), Delete (DELETE)
- Course: Edit (PUT), Delete (DELETE)
- Room: Edit (PUT), Delete (DELETE)
- Section: Edit (PUT), Delete (DELETE)
- Schedule: Add (POST), Edit (PUT), Delete (DELETE)

### Features
✅ Complete CRUD operations for all entities
✅ JWT authentication on all endpoints
✅ Comprehensive error handling and validation
✅ Activity logging for all operations
✅ Cascade deletion handling (sections → schedules)
✅ Email validation and uniqueness checks
✅ Time conflict detection and prevention
✅ Curriculum and year/semester validation

---

**Last Updated**: 2024
**Status**: Complete and Ready for Mobile Integration
