#!/bin/bash

echo "Starting Monitoring System Development Environment"
echo "================================================"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Change to backend directory and run migrations
cd backend
echo "Running Django migrations..."
python manage.py migrate

# Start the development server with Daphne
echo "Starting Daphne server on port 8000..."
echo "Server will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
daphne -p 8000 project.asgi:application
