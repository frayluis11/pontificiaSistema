#!/bin/bash

# Gateway Service Entrypoint Script
echo "🚀 Starting API Gateway Service..."

# Wait for Redis to be ready
echo "⏳ Waiting for Redis..."
while ! redis-cli -h redis -p 6379 ping > /dev/null 2>&1; do
    sleep 1
done
echo "✅ Redis is ready!"

# Navigate to application directory
cd /app

# Run migrations
echo "� Running database migrations..."
python manage.py migrate --no-input

# Start Django development server (for testing)
echo "🌐 Starting Gateway on port 8000..."
python manage.py runserver 0.0.0.0:8000