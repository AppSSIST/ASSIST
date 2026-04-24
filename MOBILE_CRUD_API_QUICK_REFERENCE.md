# Mobile API CRUD Quick Reference

## Base URL
```
http://localhost:8000  (development)
https://your-domain.com  (production)
```

## Authentication Header
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

## Quick Reference Table

| Entity | Operation | Method | Endpoint | Status |
|--------|-----------|--------|----------|--------|
| Faculty | Create | POST | `/api/faculty/add/` | ✅ |
| Faculty | Read | GET | `/api/faculty-list/` | ✅ |
| Faculty | Update | PUT | `/api/faculty/<id>/` | ✅ NEW |
| Faculty | Delete | DELETE | `/api/faculty/<id>/` | ✅ NEW |
| Course | Create | POST | `/api/courses/add/` | ✅ |
| Course | Read | GET | `/api/courses/` | ✅ |
| Course | Update | PUT | `/api/courses/<id>/edit/` | ✅ NEW |
| Course | Delete | DELETE | `/api/courses/<id>/edit/` | ✅ NEW |
| Room | Create | POST | `/api/room/add/` | ✅ |
| Room | Read | GET | `/api/rooms/` | ✅ |
| Room | Update | PUT | `/api/rooms/<id>/` | ✅ NEW |
| Room | Delete | DELETE | `/api/rooms/<id>/` | ✅ NEW |
| Section | Create | POST | `/api/section/add/` | ✅ |
| Section | Read | GET | `/api/sections/` | ✅ |
| Section | Update | PUT | `/api/sections/<id>/` | ✅ NEW |
| Section | Delete | DELETE | `/api/sections/<id>/` | ✅ NEW |
| Schedule | Create | POST | `/api/schedules/` | ✅ |
| Schedule | Read | GET | `/api/schedules/` | ✅ |
| Schedule | Update | PUT | `/api/schedules/<id>/` | ✅ NEW |
| Schedule | Delete | DELETE | `/api/schedules/<id>/` | ✅ NEW |

---

## Example: Complete CRUD Flow

### 1. Add Faculty
```javascript
// POST /api/faculty/add/
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

// Response
{
  "success": true,
  "message": "Faculty invitation sent to john.doe@example.com",
  "faculty_id": 1
}
```

### 2. Get Faculty List
```javascript
// GET /api/faculty-list/

// Response
{
  "faculty": [
    {
      "id": 1,
      "name": "Doe, John David",
      "email": "john.doe@example.com",
      "employment_status": "full_time",
      "specialization": "software_dev"
    }
  ]
}
```

### 3. Update Faculty
```javascript
// PUT /api/faculty/1/
{
  "first_name": "Jane",
  "email": "jane.doe@example.com",
  "employment_status": "part_time"
}

// Response
{
  "success": true,
  "message": "Faculty updated successfully",
  "faculty_id": 1
}
```

### 4. Delete Faculty
```javascript
// DELETE /api/faculty/1/

// Response (204 No Content)
{
  "success": true,
  "message": "Faculty deleted successfully"
}
```

---

## Validation Rules Summary

### Faculty
- Email must be valid and unique
- Email format: user@domain.com
- All name fields required for creation
- Optional fields: middle_name, professional_title, specialization

### Course
- Course code must be unique per curriculum
- Year level: 1-4
- Semester: 1-2
- Hours (lecture/lab/credit) must be integers
- Cannot delete if schedules exist

### Room
- Capacity must be positive integer
- Campus: "casal" or "arlegui"
- Room type: "lecture" or "laboratory"

### Section
- Name format: CPE[year][semester]S[number]
  - Example: CPE11S1 (year 1, semester 1, section 1)
- Year level: 1-4
- Semester: 1-2
- Max students: positive integer
- Status: "complete" or "incomplete"

### Schedule
- Time window: 07:30 - 21:30
- Time format: HH:MM (24-hour)
- No overlapping times for:
  - Same faculty on same day
  - Same section on same day
  - Same room on same day
- Course year/semester must match section

---

## Common Error Responses

### 400 Bad Request - Validation Error
```json
{
  "success": false,
  "error": "Invalid email address format"
}
```

### 404 Not Found
```json
{
  "error": "Faculty not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Database connection error"
}
```

---

## HTTP Status Codes
- **200** - Successful GET/PUT ✅
- **201** - Successful POST (creation) ✅
- **204** - Successful DELETE (no response body) ✅
- **400** - Validation error ❌
- **404** - Resource not found ❌
- **500** - Server error ❌

---

## Implementation Checklist

- [ ] Add token-based authentication
- [ ] Implement JWT token storage securely
- [ ] Build create forms
- [ ] Build list/read views
- [ ] Build edit forms with pre-populated data
- [ ] Build delete confirmation dialogs
- [ ] Handle error messages gracefully
- [ ] Implement activity logging UI
- [ ] Test all CRUD operations
- [ ] Test validation error handling
- [ ] Test cascade deletions (section → schedules)
- [ ] Test email validations

---

## Testing Commands (cURL)

### Get Token
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password123"
  }'
```

### Create Faculty
```bash
curl -X POST http://localhost:8000/api/faculty/add/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
  }'
```

### Update Faculty
```bash
curl -X PUT http://localhost:8000/api/faculty/1/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane"
  }'
```

### Delete Faculty
```bash
curl -X DELETE http://localhost:8000/api/faculty/1/ \
  -H "Authorization: Bearer <TOKEN>"
```

---

## Notes

1. All edit operations accept partial data (only changed fields)
2. All delete operations remove associated records:
   - Delete section → removes all section schedules
   - Delete faculty → unassigns from schedules, deletes user account
3. Activity logging is automatic on all operations
4. Timestamps are ISO 8601 format
5. All IDs are positive integers

---

**Version**: 1.0
**Last Updated**: 2024
**Status**: Complete
