#!/bin/bash

# Pagos Service Entrypoint Script
echo "🚀 Starting Pagos Service..."

# Wait for database to be ready
echo "⏳ Waiting for MySQL Pagos database..."
while ! mysqladmin ping -h"mysql_pagos" -P3306 -u"root" -p"root" --silent; do
    sleep 1
done
echo "✅ MySQL Pagos database is ready!"

# Navigate to Django project directory
cd /app

# Run Django migrations
echo "🔄 Running Django migrations..."
python manage.py makemigrations
python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Creating superuser..."
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"

# Run seeds
echo "🌱 Running seeds..."
python manage.py seed_pagos

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn server
echo "🌐 Starting Gunicorn server on port 8005..."
exec gunicorn --bind 0.0.0.0:8005 --workers 3 core.wsgi:application