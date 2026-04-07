# Render Deployment Guide

## Prerequisites
- Render account (free at render.com)
- Your project pushed to GitHub (or GitLab)
- Python 3.11+

## Step-by-Step Deployment

### 1. **Prepare Your Repository**
```bash
git add .
git commit -m "Add Render deployment configuration"
git push
```

Files added:
- `render.yaml` - Render deployment configuration
- `Procfile` - Process definition for Render
- `dj-database-url` - Added to requirements.txt

### 2. **Create Render Account & Connect Git**
1. Go to https://dashboard.render.com
2. Sign up (free tier available)
3. Click "New +" and select "Web Service"
4. Connect your GitHub repository
5. Select the branch (main/master)

### 3. **Configure the Web Service**

**Basic Settings:**
- Name: `auto-scheduling`
- Environment: `Python 3`
- Region: Oregon (or closest to you)
- Plan: Free tier (or upgrade as needed)

**Build & Deploy:**
- Build Command: `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
- Start Command: `gunicorn ASSIST.wsgi:application`

### 4. **Set Environment Variables**

In Render dashboard, go to **Environment** tab and add:

```
SECRET_KEY=<generate-a-random-secret-key>
DEBUG=False
ALLOWED_HOSTS=auto-scheduling-5.onrender.com,auto-scheduling.onrender.com
DATABASE_URL=<Render will provide this if using PostgreSQL>
```

### 5. **Add PostgreSQL Database (Optional)**

If you want persistent data on Render:
1. Click "New +" → "PostgreSQL"
2. Name: `auto-scheduling-db`
3. PostgreSQL Version: 16
4. Plan: Free
5. Render will auto-populate `DATABASE_URL`

### 6. **Deploy!**

1. Click "Create Web Service"
2. Render automatically builds and deploys
3. Wait for "Your service is live" message
4. Visit your URL: `https://auto-scheduling-5.onrender.com`

---

## After Deployment

### Create Admin User
```bash
# Via Render shell (in dashboard):
python manage.py createsuperuser

# Then visit: https://your-app.onrender.com/admin
```

### View Logs
Render dashboard → Logs tab shows real-time output

### Test the App
1. Visit homepage
2. Test schedule generation
3. Check admin panel

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **500 Error** | Check logs in Render dashboard. Likely `SECRET_KEY` not set. |
| **Static files not loading** | Run: `python manage.py collectstatic --noinput` |
| **Database connection failed** | Verify `DATABASE_URL` env var is set correctly |
| **Import errors** | Ensure all packages in `requirements.txt` are installed |

---

## Database Migration Notes

**First Deploy (SQLite locally → PostgreSQL on Render):**
1. Create new PostgreSQL database on Render
2. Set `DATABASE_URL` env variable
3. Render will auto-run migrations via build command
4. Your data will start fresh (normal for first deploy)

**Subsequent Deploys:**
- Migrations run automatically on each deploy
- Your PostgreSQL data persists

---

## Cost Breakdown (Free Tier)

- Web Service: **Free** ✅
- Database (PostgreSQL): **Free** ✅
- Storage: 0.5 GB (included) ✅
- Monthly limit: Generous free tier

*Upgrade anytime if needed for better performance/storage*

---

## Next Steps

1. Push code with deployment files
2. Create Render account
3. Connect GitHub repository
4. Configure environment variables
5. Deploy and test

Questions? Check [Render Docs](https://render.com/docs)
