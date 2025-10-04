#!/bin/bash

# Documentos Service Entrypoint Script
echo "🚀 Starting Documentos Service..."

# Wait for database to be ready
echo "⏳ Waiting for MySQL Documentos database..."
while ! mysqladmin ping -h"mysql_documentos" -P3306 -u"root" -p"root" --silent; do
    sleep 1
done
echo "✅ MySQL Documentos database is ready!"

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
python manage.py seed_documentos

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn server
echo "🌐 Starting Gunicorn server on port 8004..."
exec gunicorn --bind 0.0.0.0:8004 --workers 3 core.wsgi:applicationz