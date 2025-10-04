# Script para iniciar AUTH service
Set-Location "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\auth"
$env:DB_HOST="localhost"
$env:DB_PORT="3307"
$env:DJANGO_SETTINGS_MODULE="auth_service.settings"

# Activar entorno virtual
& ".\venv\Scripts\Activate.ps1"

# Ejecutar servicio
python manage.py runserver 3001
