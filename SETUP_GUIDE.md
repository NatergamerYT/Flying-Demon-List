# Game Leaderboard - Setup Guide

Congratulations! Your Flask application is fully built. Follow these steps to get it running.

## Prerequisites

Before you begin, ensure you have:
- **Python 3.8+** installed
- **PostgreSQL** database server installed and running
- **Git** (optional, for version control)

## Step-by-Step Setup

### 1. Create Virtual Environment

Open PowerShell or Command Prompt and navigate to the project directory:

```bash
cd c:\git\Leaderboard
python -m venv venv
```

### 2. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

You should see `(venv)` in your command prompt.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask and extensions (SQLAlchemy, Login, Migrate, WTF)
- PostgreSQL driver (psycopg2-binary)
- Other dependencies

### 4. Set Up PostgreSQL Database

#### Option A: Using psql Command Line

```bash
psql -U postgres
CREATE DATABASE leaderboard_dev;
\q
```

#### Option B: Using pgAdmin

1. Open pgAdmin
2. Right-click "Databases" → Create → Database
3. Name it `leaderboard_dev`
4. Click "Save"

### 5. Create Environment Variables File

Create a `.env` file in the project root (`c:\git\Leaderboard\.env`):

```env
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-this-in-production
DEV_DATABASE_URL=postgresql://postgres:yourpassword@localhost/leaderboard_dev
```

**Important:** Replace `yourpassword` with your actual PostgreSQL password!

**To generate a secure SECRET_KEY**, run in Python:
```python
import secrets
print(secrets.token_hex(32))
```

### 6. Initialize Database Migrations

```bash
flask db init
```

This creates a `migrations/` folder.

### 7. Create Initial Migration

```bash
flask db migrate -m "Initial migration with User, Level, Claim, and Vote models"
```

This generates migration scripts based on your models.

### 8. Apply Migrations

```bash
flask db upgrade
```

This creates all the database tables.

### 9. Create Admin User

```bash
flask create-admin
```

You'll be prompted to enter:
- Username
- Email
- Password (minimum 8 characters)

### 10. (Optional) Seed Initial Levels

```bash
flask seed-levels
```

This adds 6 sample game levels to the database.

### 11. Run the Application

```bash
flask run
```

The application should start at: **http://127.0.0.1:5000**

## Verification Checklist

Test these features to ensure everything works:

### Authentication
- [ ] Register a new user account
- [ ] Log in with the new account
- [ ] Log out

### Claims
- [ ] Submit a claim with a YouTube link (as regular user)
- [ ] View "My Claims" page
- [ ] Check that claim shows as "PENDING"

### Admin Functions
- [ ] Log in as admin user
- [ ] View admin dashboard
- [ ] See pending claims
- [ ] Review and approve a claim
- [ ] Verify approved claim appears on leaderboard

### Voting & Ranking
- [ ] Vote on an approved claim (as different user, not claim owner)
- [ ] Verify vote count increases
- [ ] Click vote again to remove vote
- [ ] Check that rankings update correctly

### Leaderboard
- [ ] View leaderboard with approved claims
- [ ] Verify YouTube videos are embedded
- [ ] Filter leaderboard by level
- [ ] Check that only top 50 claims show

### User Profiles
- [ ] Click on a username to view profile
- [ ] Verify total points are calculated correctly
- [ ] See all user's claims with ranks and points

### Error Handling
- [ ] Try accessing `/admin/dashboard` as non-admin → Should get 403 error
- [ ] Visit a non-existent URL → Should get 404 error

## Common Issues & Solutions

### Issue: `ModuleNotFoundError: No module named 'flask'`
**Solution:** Make sure your virtual environment is activated. You should see `(venv)` in your prompt.

### Issue: `psycopg2.OperationalError: could not connect to server`
**Solution:**
- Ensure PostgreSQL is running
- Check your `DEV_DATABASE_URL` in `.env` has the correct password
- Verify the database `leaderboard_dev` exists

### Issue: `sqlalchemy.exc.ProgrammingError: relation "users" does not exist`
**Solution:** Run the migrations:
```bash
flask db upgrade
```

### Issue: Flask import errors
**Solution:** Make sure you're in the project root directory where `run.py` is located.

### Issue: Port 5000 already in use
**Solution:** Run on a different port:
```bash
flask run --port 5001
```

## Security Checklist

✅ **Already Implemented:**
- Password hashing with werkzeug (bcrypt)
- CSRF protection on all forms
- Session security (HttpOnly, SameSite cookies)
- SQL injection prevention (SQLAlchemy ORM)
- Input validation with WTForms
- XSS prevention (Jinja2 auto-escaping)
- Authorization decorators (@login_required, @admin_required)

⚠️ **For Production:**
- Set `FLASK_ENV=production` in `.env`
- Use a strong, random `SECRET_KEY`
- Enable HTTPS (`SESSION_COOKIE_SECURE = True` in production config)
- Use a production-grade database URL
- Set up proper logging and monitoring
- Consider rate limiting (Flask-Limiter)
- Set up email verification for new accounts

## Next Steps

### Add More Levels
1. Log in as admin
2. Go to Admin → Manage Levels
3. Add custom levels for your game

### Customize the Application
- Edit templates in `app/templates/` to change the UI
- Modify `app/static/css/custom.css` for custom styling
- Update `app/static/js/custom.js` for custom JavaScript

### Deploy to Production
- Use Gunicorn or uWSGI as WSGI server
- Set up Nginx as reverse proxy
- Use environment variables for sensitive config
- Set up automated backups for PostgreSQL database

## Project Structure Reference

```
c:\git\Leaderboard\
├── app\
│   ├── __init__.py              # Flask app factory
│   ├── models.py                # Database models
│   ├── auth\                    # Authentication
│   ├── main\                    # Main pages (home, leaderboard)
│   ├── claims\                  # Claim submission & voting
│   ├── users\                   # User profiles
│   ├── admin\                   # Admin dashboard
│   ├── templates\               # HTML templates
│   └── static\                  # CSS, JS
├── migrations\                  # Database migrations
├── config.py                    # Configuration
├── run.py                       # Application entry point
├── requirements.txt             # Dependencies
├── .env                         # Environment variables (create this)
├── .gitignore                   # Git ignore rules
├── README.md                    # Project overview
└── SETUP_GUIDE.md              # This file
```

## Support

If you encounter issues:
1. Check the error message carefully
2. Review the "Common Issues" section above
3. Ensure all dependencies are installed
4. Verify PostgreSQL is running and accessible

## Features Summary

✅ **Implemented:**
- User registration and authentication
- Level completion claim submission with YouTube proof
- Admin approval workflow for claims
- Community voting on approved claims
- Dynamic ranking system (top 50)
- Points calculation (51 - rank formula)
- User profiles with total points
- YouTube video embeds on leaderboard
- Responsive Bootstrap 5 UI
- Admin dashboard for managing claims and levels
- Level management (add/delete levels)
- Error handling (403, 404, 500 pages)

🎉 **Your application is ready to use!**
