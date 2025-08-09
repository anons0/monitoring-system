@echo off
echo Starting Monitoring System Development Environment
echo ================================================

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Change to backend directory and run migrations
cd backend
echo Running Django migrations...
python manage.py migrate

REM Start the development server with Daphne
echo Starting Daphne server on port 8000...
echo Server will be available at: http://localhost:8000
echo Press Ctrl+C to stop the server
daphne -p 8000 project.asgi:application

pause
