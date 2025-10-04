#!/bin/bash

# Script de inicio para API Gateway - Sistema Pontificia
# start_gateway.sh

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
GATEWAY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$GATEWAY_DIR/venv"
PYTHON_EXECUTABLE="$VENV_DIR/bin/python"
PIP_EXECUTABLE="$VENV_DIR/bin/pip"
MANAGE_PY="$GATEWAY_DIR/manage.py"
REQUIREMENTS_FILE="$GATEWAY_DIR/requirements.txt"
PORT=${GATEWAY_PORT:-8000}
HOST=${GATEWAY_HOST:-127.0.0.1}

echo -e "${BLUE}=== Sistema Pontificia - API Gateway Startup ===${NC}"
echo -e "${BLUE}Gateway Directory: $GATEWAY_DIR${NC}"
echo -e "${BLUE}Port: $PORT${NC}"
echo -e "${BLUE}Host: $HOST${NC}"
echo ""

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Verificar si estamos en el directorio correcto
if [ ! -f "$MANAGE_PY" ]; then
    error "manage.py not found. Make sure you're in the gateway directory."
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activar entorno virtual
log "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Actualizar pip
log "Updating pip..."
"$PIP_EXECUTABLE" install --upgrade pip

# Instalar dependencias
if [ -f "$REQUIREMENTS_FILE" ]; then
    log "Installing requirements..."
    "$PIP_EXECUTABLE" install -r "$REQUIREMENTS_FILE"
else
    warning "requirements.txt not found. Installing basic dependencies..."
    "$PIP_EXECUTABLE" install django djangorestframework drf-spectacular djangorestframework-simplejwt django-cors-headers django-ratelimit redis requests httpx
fi

# Verificar Redis
log "Checking Redis connection..."
if ! redis-cli ping > /dev/null 2>&1; then
    warning "Redis is not running. Some features may not work properly."
    warning "To start Redis: sudo systemctl start redis-server"
fi

# Ejecutar migraciones
log "Running database migrations..."
"$PYTHON_EXECUTABLE" "$MANAGE_PY" makemigrations --noinput
"$PYTHON_EXECUTABLE" "$MANAGE_PY" migrate --noinput

# Recoger archivos estáticos
log "Collecting static files..."
"$PYTHON_EXECUTABLE" "$MANAGE_PY" collectstatic --noinput --clear

# Verificar configuración
log "Checking Django configuration..."
"$PYTHON_EXECUTABLE" "$MANAGE_PY" check --deploy

# Función para manejar señales
cleanup() {
    log "Shutting down Gateway..."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Verificar conectividad a microservicios
log "Testing microservice connections..."
SERVICES=("auditoria:8001" "auth:8002" "users:8003" "academic:8004" "students:8005" "courses:8006" "reports:8007")

for service in "${SERVICES[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if nc -z localhost "$port" 2>/dev/null; then
        log "✓ $name service (port $port) is reachable"
    else
        warning "✗ $name service (port $port) is not reachable"
    fi
done

# Mostrar información del sistema
log "System Information:"
echo "  Python: $("$PYTHON_EXECUTABLE" --version)"
echo "  Django: $("$PYTHON_EXECUTABLE" -c "import django; print(django.get_version())")"
echo "  DRF: $("$PYTHON_EXECUTABLE" -c "import rest_framework; print(rest_framework.VERSION)" 2>/dev/null || echo 'Not installed')"

# Verificar archivo de configuración
if [ -f "$GATEWAY_DIR/gateway/settings.py" ]; then
    log "Configuration file found"
else
    error "Configuration file not found"
    exit 1
fi

# Mostrar URLs importantes
log "Important URLs:"
echo "  Gateway Root: http://$HOST:$PORT/"
echo "  Health Check: http://$HOST:$PORT/health/"
echo "  API Documentation: http://$HOST:$PORT/api/docs/"
echo "  Custom Docs: http://$HOST:$PORT/docs/"
echo "  Admin: http://$HOST:$PORT/admin/"

log "Starting Django development server..."
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Iniciar el servidor
"$PYTHON_EXECUTABLE" "$MANAGE_PY" runserver "$HOST:$PORT"