#!/bin/bash

echo "🚀 Starting Auth Service..."

# Navigate to application directory
cd /app

# Run migrations (Django will wait for DB automatically)
echo "🔄 Running database migrations..."
python manage.py migrate --no-input

# Start Django development server
echo "🌐 Starting Auth Service on port 8000..."
python manage.py runserver 0.0.0.0:8000
