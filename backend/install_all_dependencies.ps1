# Script para instalar todas las dependencias requeridas en cada microservicio
Write-Host "=== INSTALACION COMPLETA DE DEPENDENCIAS ===" -ForegroundColor Green

$services = @("auth", "users", "asistencia", "documentos", "pagos", "reportes", "auditoria", "gateway")

foreach ($service in $services) {
    Write-Host "`n" + "="*60 -ForegroundColor Cyan
    Write-Host "📦 INSTALANDO DEPENDENCIAS: $($service.ToUpper())" -ForegroundColor Cyan
    Write-Host "="*60 -ForegroundColor Cyan
    
    $servicePath = "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\$service"
    
    if (!(Test-Path $servicePath)) {
        Write-Host "❌ Directorio no encontrado: $servicePath" -ForegroundColor Red
        continue
    }
    
    Set-Location $servicePath
    
    # Verificar si existe venv
    if (!(Test-Path "venv")) {
        Write-Host "🔧 Creando entorno virtual..." -ForegroundColor Yellow
        python -m venv venv
    }
    
    # Activar venv y actualizar pip
    Write-Host "🔄 Actualizando pip..." -ForegroundColor Yellow
    & "venv\Scripts\python.exe" -m pip install --upgrade pip
    
    # Instalar dependencias básicas para todos los servicios
    Write-Host "📦 Instalando dependencias básicas..." -ForegroundColor Yellow
    $basicDeps = @(
        "Django==4.2.7",
        "djangorestframework==3.14.0", 
        "djangorestframework-simplejwt==5.3.0",
        "mysqlclient==2.2.0",
        "django-cors-headers==4.3.1",
        "python-decouple==3.8",
        "drf-spectacular==0.26.5",
        "pillow==10.1.0",
        "django-extensions==3.2.3"
    )
    
    foreach ($dep in $basicDeps) {
        Write-Host "  - Instalando $dep" -ForegroundColor Gray
        & "venv\Scripts\pip.exe" install $dep --quiet
    }
    
    # Instalar desde requirements.txt si existe
    if (Test-Path "requirements.txt") {
        Write-Host "📋 Instalando desde requirements.txt..." -ForegroundColor Yellow
        & "venv\Scripts\pip.exe" install -r requirements.txt --quiet
    }
    
    # Dependencias específicas por servicio
    switch ($service) {
        "auth" {
            Write-Host "🔐 Instalando dependencias específicas de autenticación..." -ForegroundColor Yellow
            & "venv\Scripts\pip.exe" install celery==5.3.4 redis==5.0.1 --quiet
        }
        "documentos" {
            Write-Host "📄 Instalando dependencias específicas de documentos..." -ForegroundColor Yellow
            & "venv\Scripts\pip.exe" install celery==5.3.4 redis==5.0.1 --quiet
        }
        "reportes" {
            Write-Host "📊 Instalando dependencias específicas de reportes..." -ForegroundColor Yellow
            & "venv\Scripts\pip.exe" install pandas==2.1.3 openpyxl==3.1.2 matplotlib==3.8.2 reportlab==4.0.7 --quiet
        }
        "pagos" {
            Write-Host "💳 Instalando dependencias específicas de pagos..." -ForegroundColor Yellow
            & "venv\Scripts\pip.exe" install stripe==7.8.0 --quiet
        }
    }
    
    # Verificar instalación
    Write-Host "✅ Verificando instalación..." -ForegroundColor Green
    try {
        & "venv\Scripts\python.exe" -c "import django, rest_framework, mysqlclient; print('Dependencias básicas OK')"
        Write-Host "✅ $service: Dependencias instaladas correctamente" -ForegroundColor Green
    } catch {
        Write-Host "❌ $service: Error en las dependencias" -ForegroundColor Red
    }
    
    Write-Host "Completado: $service" -ForegroundColor Gray
}

Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "🎉 INSTALACION DE DEPENDENCIAS COMPLETADA" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green