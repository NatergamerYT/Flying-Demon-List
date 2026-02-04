@echo off
echo ========================================
echo  Game Leaderboard - Quick Setup
echo ========================================
echo.

echo Step 1: Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo Make sure Python 3.8+ is installed
    pause
    exit /b 1
)
echo Virtual environment created successfully!
echo.

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo.

echo Step 3: Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully!
echo.

echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo NEXT STEPS:
echo 1. Create PostgreSQL database: CREATE DATABASE leaderboard_dev;
echo 2. Copy .env.example to .env and configure your database URL
echo 3. Run: flask db init
echo 4. Run: flask db migrate -m "Initial migration"
echo 5. Run: flask db upgrade
echo 6. Run: flask create-admin
echo 7. Run: flask seed-levels (optional)
echo 8. Run: flask run
echo.
echo For detailed instructions, see SETUP_GUIDE.md
echo.
pause
