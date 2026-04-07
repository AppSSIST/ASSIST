# Complete Step-by-Step Render Deployment Guide

## PHASE 1: Prepare Your Local Project (5 minutes)

### Step 1: Verify files exist
Make sure these files are in your project root:
- `requirements.txt` ✅
- `manage.py` ✅
- `Procfile` ✅ (already created)
- `render.yaml` ✅ (already created)

### Step 2: Add missing dependency
Run in PowerShell (in your project folder):
```powershell
# Activate virtual environment
& .\.venv-1\Scripts\Activate.ps1

# Add dj-database-url if not already there
pip install dj-database-url
pip freeze | findstr dj-database-url
```

Expected output: `dj-database-url==2.1.0`

### Step 3: Update requirements.txt
```powershell
pip freeze > requirements.txt
```

This ensures all packages are listed.

### Step 4: Commit and push to GitHub
```powershell
git add .
git commit -m "Add Render deployment files"
git push origin main
```

Wait for completion message: "Everything up-to-date"

---

## PHASE 2: Set Up Render (15 minutes)

### Step 5: Create Render Account (if you don't have one)
1. Go to https://dashboard.render.com
2. Click "Sign Up"
3. Choose GitHub login (easier!)
4. Authorize GitHub access

### Step 6: Create a New Web Service
1. In Render dashboard, click **"+ New"** (top right)
2. Select **"Web Service"**
3. Click **"Connect a repository"**
4. Find and select your GitHub repository
5. Click **"Connect"**

### Step 7: Configure the Web Service

**Fill in these fields:**

| Field | Value |
|-------|-------|
| **Name** | `auto-scheduling` |
| **Environment** | `Python 3` |
| **Region** | `Oregon` (or closest to you) |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput` |
| **Start Command** | `gunicorn ASSIST.wsgi:application` |
| **Plan** | `Free` |

Click **"Create Web Service"**

### Step 8: Add Environment Variables (IMPORTANT!)

1. In your Web Service dashboard, go to **"Environment"** tab
2. Click **"Add Environment Variable"** for each:

**Add these variables:**

| Key | Value | Example |
|-----|-------|---------|
| `DEBUG` | `False` | (type exactly: False) |
| `ALLOWED_HOSTS` | Your Render URL | `auto-scheduling.onrender.com` |
| `SECRET_KEY` | Random string | (see next step) |

### Step 9: Generate SECRET_KEY
Run in PowerShell:
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output (long random string), then:
1. In Render Environment tab, add variable:
   - Key: `SECRET_KEY`
   - Value: Paste your generated key

2. Click **"Save"**

### Step 10: Add PostgreSQL Database

1. Click **"+ New"** (in Render dashboard)
2. Select **"PostgreSQL"**
3. Fill in:
   - Name: `auto-scheduling-db`
   - PostgreSQL Version: `16`
   - Region: `Oregon` (same as web service)
   - Plan: `Free`
4. Click **"Create Database"**

5. **Copy the Internal Connection String:**
   - Go to your new database
   - Under "Connections", copy the "Internal Database URL"
   - Format: `postgresql://user:password@localhost/dbname`

6. **Add to Web Service:**
   - Go back to your Web Service
   - Environment tab → Add variable:
     - Key: `DATABASE_URL`
     - Value: Paste the connection string
   - Click **"Save"**

---

## PHASE 3: Trigger Deployment (2 minutes)

### Step 11: Start the Deploy
1. Return to your **Web Service** page
2. Look for the **"Deploy"** button (top right)
3. Click **"Deploy latest commit"**

You should see:
```
Building...
Creating build for main branch...
Running build command...
```

### Step 12: Monitor the Build
1. Watch the **"Logs"** tab (bottom half of screen)
2. You should see:
   - ✅ `Installing dependencies...`
   - ✅ `Running migrations...`
   - ✅ `Collecting static files...`
   - ✅ `Service is live`

**Wait time:** 3-5 minutes for first deploy

### Step 13: Check if Deployment Succeeded
1. When you see **"Your service is live"** in logs
2. Your URL will appear at top: `https://auto-scheduling.onrender.com`
3. Click the URL to visit your app!

---

## PHASE 4: Post-Deployment Setup (5 minutes)

### Step 14: Create Django Admin User
1. In Render dashboard, go to your **Web Service**
2. Click **"Shell"** tab (next to Logs)
3. Run this command:
```bash
python manage.py createsuperuser
```

4. Follow prompts:
   - Username: `admin`
   - Email: `your@email.com`
   - Password: (create a strong one)
   - Confirm: (repeat password)

### Step 15: Test the App
1. Visit your app: `https://auto-scheduling.onrender.com`
2. Should see your homepage
3. Visit `/admin` to test login with your admin account
4. Test schedule generation feature

---

## ✅ Success Checklist

- [ ] Files (Procfile, render.yaml, requirements.txt) pushed to GitHub
- [ ] Web Service created on Render
- [ ] Environment variables set (DEBUG, ALLOWED_HOSTS, SECRET_KEY, DATABASE_URL)
- [ ] PostgreSQL database added
- [ ] Build completed successfully
- [ ] Admin user created
- [ ] App accessible at your Render URL
- [ ] Admin panel works (/admin)

---

## 🔧 Troubleshooting

### Build fails with "gunicorn not found"
- Check requirements.txt has `gunicorn==23.0.0`
- Run: `pip install -r requirements.txt` locally
- Push to GitHub again

### 500 Error on app
**Check logs for the exact error:**
1. Go to Render dashboard
2. Click "Logs" tab
3. Search for "ERROR"
4. Most common: Missing environment variables

### App says "Connection refused" for database
- Verify `DATABASE_URL` is set in Environment
- Copy FULL connection string from your PostgreSQL service
- Make sure it's the "Internal" URL not "External"

### Static files (CSS/images) not loading
- This usually means `collectstatic` failed
- Check logs for static file errors
- Run locally: `python manage.py collectstatic --noinput`

### Admin panel gives 403 Forbidden
- CSRF token issue: Make sure `ALLOWED_HOSTS` includes your Render URL
- Clear browser cookies and try again

---

## 📊 What Happens During Deploy

```
1. GitHub Push
   ↓
2. Render detects change
   ↓
3. Installs Python packages (from requirements.txt)
   ↓
4. Runs migrations (updates database schema)
   ↓
5. Collects static files (CSS/JS)
   ↓
6. Starts gunicorn web server
   ↓
7. App is LIVE! 🚀
```

---

## 💡 Tips

- **First deploy takes 3-5 minutes** - subsequent deploys are faster
- **Free tier limitations:** App sleeps after 15 min inactivity (wakes up on first request)
- **Logs are your friend** - always check them if something breaks
- **Upgrades anytime** - can upgrade to paid plan for always-on service
