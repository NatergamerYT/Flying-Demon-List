# Game Leaderboard

A Flask-based web application for submitting and tracking game level completions with YouTube proof videos.

## Features

- **User Registration & Authentication**: Secure account creation and login
- **Claim Submission**: Submit level completion claims with YouTube proof links
- **Community Voting**: Vote on approved claims to determine rankings
- **Dynamic Leaderboard**: Top 50 ranked claims with embedded YouTube videos
- **Points System**: Earn points based on ranking (51 - rank formula)
- **Admin Dashboard**: Review and approve/reject user submissions
- **User Profiles**: View all claims and total points for any user

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Database**: PostgreSQL
- **Frontend**: Bootstrap 5, Jinja2 templates
- **Security**: CSRF protection, password hashing, session management

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- PostgreSQL database

### 2. Clone and Setup

```bash
cd c:\git\Leaderboard
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Configure Database

Create a PostgreSQL database:
```sql
CREATE DATABASE leaderboard_dev;
```

Create a `.env` file (copy from `.env.example`):
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-random-secret-key-here
DEV_DATABASE_URL=postgresql://username:password@localhost/leaderboard_dev
```

### 4. Initialize Database

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 5. Create Admin User

```bash
flask create-admin
```

### 6. Seed Levels (Optional)

```bash
flask seed-levels
```

### 7. Run the Application

```bash
flask run
```

Visit http://localhost:5000

## Deployment notes

- Recommended start command (Render / production):

```
flask db upgrade && gunicorn run:app
```

- You can also use the included `bin/start.sh` which runs migrations then starts Gunicorn.

- To auto-create an admin on first startup, set the following environment variables in your host:

```
AUTO_CREATE_ADMIN=1
ADMIN_USERNAME=NaterGamer
ADMIN_EMAIL=natergamer@example.com
ADMIN_PASSWORD=Nc522774
```

This will create the admin only if no admin user exists.

## Project Structure

```
c:\git\Leaderboard\
├── app/                    # Application package
│   ├── auth/              # Authentication routes
│   ├── main/              # Main pages
│   ├── claims/            # Claim submission & voting
│   ├── users/             # User profiles
│   ├── admin/             # Admin dashboard
│   ├── templates/         # HTML templates
│   ├── static/            # CSS, JS files
│   └── models.py          # Database models
├── migrations/            # Database migrations
├── config.py              # Configuration
├── run.py                 # Application entry point
└── requirements.txt       # Python dependencies
```

## Usage

### For Users
1. Register an account
2. Submit claims for levels you've beaten with YouTube proof links
3. Vote on other users' approved claims
4. View your profile to see your total points

### For Admins
1. Login with admin credentials
2. Review pending claims
3. Approve or reject submissions
4. Manage game levels

## Security Features

- Password hashing (bcrypt via werkzeug)
- CSRF protection on all forms
- Session security (HttpOnly, SameSite cookies)
- SQL injection prevention (SQLAlchemy ORM)
- Input validation (WTForms)
- XSS prevention (Jinja2 auto-escaping)

## License

This project is open source and available for educational purposes.
