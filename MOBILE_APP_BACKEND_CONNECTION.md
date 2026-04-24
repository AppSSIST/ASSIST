# Mobile App Backend Configuration Guide

## Network Setup Summary

| Device | IP Address | Status |
|--------|-----------|--------|
| Backend (Your PC) | 10.201.37.25 | ✅ Ready |
| Mobile Phone | 192.168.1.17 | ✅ Connected |
| Network | 192.168.1.x | ✅ Local WiFi |

---

## Backend Configuration ✅ COMPLETE

Your Django backend has been configured to accept requests from:
- ✅ `10.201.37.25` (Backend IP)
- ✅ `192.168.1.17` (Phone IP)
- ✅ CORS enabled for cross-origin requests
- ✅ `corsheaders` middleware installed

### Changes Made:

1. **ALLOWED_HOSTS** updated in `ASSIST/settings.py`:
   ```python
   ALLOWED_HOSTS = [..., '10.201.37.25', '192.168.1.17']
   ```

2. **CORS Configuration** added:
   ```python
   CORS_ALLOWED_ORIGINS = [
       "http://192.168.1.17:*",  # Your phone
       "http://10.201.37.25:*",  # Backend
   ]
   CORS_ALLOW_CREDENTIALS = True
   ```

3. **Middleware** configured:
   - ✅ `corsheaders.middleware.CorsMiddleware` added
   - ✅ Installed `django-cors-headers` package

---

## Mobile App Configuration

### Base API URL

Use this URL in your mobile app configuration:

```
http://10.201.37.25:8000
```

### API Endpoints Available

| Endpoint | URL | Method |
|----------|-----|--------|
| Login | `/api/auth/token/` | POST |
| Get Courses | `/api/courses/` | GET |
| Get Sections | `/api/sections/` | GET |
| Get Faculty | `/api/faculty-list/` | GET |
| Get Rooms | `/api/rooms/` | GET |
| Get Available Resources | `/api/schedule/available-resources/` | GET |
| Create Schedule | `/api/schedule/` | POST |
| Get My Schedule | `/api/my-schedule/` | GET |

### Mobile App Setup Steps

#### 1. Update API Base URL (in your mobile app code)

**React Native / Flutter / etc:**

```javascript
// In your API configuration file
const API_BASE_URL = 'http://10.201.37.25:8000';

// Example: Making a login request
const login = async (username, password) => {
  const response = await fetch(`${API_BASE_URL}/api/auth/token/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password })
  });
  return response.json();
};
```

#### 2. Verify Phone is on Same WiFi Network

1. Go to phone Settings → WiFi
2. Verify connected to same network as your PC (same SSID)
3. Phone should be on `192.168.1.x` range

#### 3. Test Connection

Make a test request from your mobile app:

```bash
# From phone's mobile app (or via curl):
curl http://10.201.37.25:8000/api/curriculums/
```

---

## Starting the Backend Server

Make sure your Django server is running on the correct host and port:

```powershell
# Run on all network interfaces (allows phone connection)
python manage.py runserver 0.0.0.0:8000
```

Or if using a specific IP:

```powershell
python manage.py runserver 10.201.37.25:8000
```

---

## Troubleshooting

### Issue: "Connection Refused" or "Network Error"

**Solutions:**
1. Verify backend server is running: `python manage.py runserver 0.0.0.0:8000`
2. Check firewall isn't blocking port 8000
3. Verify phone and PC are on same WiFi network
4. Ping from phone to backend:
   ```
   ping 10.201.37.25
   ```

### Issue: 404 Not Found on Endpoints

1. Ensure Django server was restarted after URL changes
2. Check endpoint path is correct (see table above)
3. Verify you're using the correct HTTP method (GET/POST/PUT/DELETE)

### Issue: 403 Forbidden / CORS Error

1. Backend was already configured for CORS ✅
2. If still getting error, verify mobile app sends correct headers:
   ```
   Content-Type: application/json
   Accept: application/json
   ```

### Issue: Authentication Failed

1. Get JWT token first via `/api/auth/token/` endpoint
2. Use token in all subsequent requests:
   ```
   Authorization: Bearer <your-token-here>
   ```

---

## Example Mobile App Configuration

### API Service Class (Template)

```javascript
class APIService {
  constructor() {
    this.baseURL = 'http://10.201.37.25:8000';
    this.token = null;
  }

  async login(username, password) {
    const response = await fetch(`${this.baseURL}/api/auth/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const data = await response.json();
    this.token = data.access;  // Save JWT token
    return data;
  }

  async request(endpoint, method = 'GET', body = null) {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);

    const response = await fetch(`${this.baseURL}${endpoint}`, options);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.json();
  }

  getCourses() {
    return this.request('/api/courses/');
  }

  getSections() {
    return this.request('/api/sections/');
  }

  createSchedule(data) {
    return this.request('/api/schedule/', 'POST', data);
  }
}
```

---

## Network Diagram

```
Your PC (Backend)           Your Phone (Mobile App)
10.201.37.25:8000  ←——WiFi——→  192.168.1.17

Django Server Running         Mobile App
- API Endpoints               - Makes HTTP Requests
- Database                    - Displays Schedules
- Authentication              - JWT Token Storage
```

---

## Important Notes

1. **Local Network Only**: This configuration only works on your home/office WiFi
2. **Port 8000**: Make sure this port isn't blocked by firewall
3. **WiFi Requirement**: Both devices must be on same WiFi network
4. **Debug Mode**: Backend is running in DEBUG=True for development
5. **Database**: Uses SQLite (db.sqlite3) - synced on both systems

---

## Quick Reference Commands

### Start Backend Server:
```powershell
cd C:\Users\Sesi\Auto-Scheduling-1
python manage.py runserver 0.0.0.0:8000
```

### Check Backend is Accessible:
```bash
# From phone or another device:
curl http://10.201.37.25:8000/api/curriculums/
```

### View Logs:
```powershell
# Keep terminal open while server runs to see all requests
# Mobile app requests should appear here
```

---

**Last Updated**: April 24, 2026
**Status**: ✅ Ready for Mobile Connection
