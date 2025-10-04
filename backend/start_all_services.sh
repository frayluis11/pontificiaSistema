#!/bin/bash

echo "🚀 Starting All Microservices - Sistema Pontificia"

# Crear redes y volúmenes si no existen
echo "📦 Setting up Docker networks and volumes..."
docker network create pontificia_network 2>/dev/null || echo "Network already exists"

# Detener servicios existentes si los hay
echo "🛑 Stopping existing services..."
docker-compose down 2>/dev/null || echo "No services to stop"

# Construir todas las imágenes
echo "🏗️ Building all microservices..."
docker-compose build

# Iniciar todas las bases de datos primero
echo "🗄️ Starting all MySQL databases..."
docker-compose up -d mysql_auth mysql_users mysql_asistencia mysql_documentos mysql_pagos mysql_reportes mysql_auditoria redis

# Esperar que las bases de datos estén listas
echo "⏳ Waiting for databases to be healthy..."
sleep 30

# Iniciar todos los microservicios
echo "🚀 Starting all microservices..."
docker-compose up -d

# Mostrar estado
echo "📊 Service Status:"
docker-compose ps

echo "✅ All services started successfully!"
echo "🌐 Gateway available at: http://localhost:8000"
echo "🔐 Auth Service: http://localhost:3001"  
echo "👥 Users Service: http://localhost:3002"
echo "🕒 Asistencia Service: http://localhost:3003"
echo "📄 Documentos Service: http://localhost:3004"
echo "💰 Pagos Service: http://localhost:3005"
echo "📊 Reportes Service: http://localhost:3006"
echo "🔍 Auditoría Service: http://localhost:3007"