# Dockerfile para Auth Service - Sistema Pontificia
FROM python:3.11-slim

# Información del servicio
LABEL service="auth-service"
LABEL port="3001"

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SERVICE_NAME="Auth Service" \
    SERVICE_PORT=3001

# Crear usuario no-root
RUN groupadd -r django && useradd -r -g django django

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        pkg-config \
        default-libmysqlclient-dev \
        build-essential \
        curl \
        netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . /app/

# Crear directorios y permisos
RUN mkdir -p /app/logs /app/data \
    && chown -R django:django /app

# Exponer puerto
EXPOSE 3001

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]