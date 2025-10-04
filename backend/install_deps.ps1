# Script para instalar dependencias en todos los servicios
Write-Host "=== INSTALACION COMPLETA DE DEPENDENCIAS ===" -ForegroundColor Green

$services = @("auth", "users", "asistencia", "documentos", "pagos", "reportes", "auditoria", "gateway")

foreach ($service in $services) {
    Write-Host "`nInstalando dependencias para: $($service.ToUpper())" -ForegroundColor Cyan
    
    $servicePath = "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\$service"
    
    if (!(Test-Path $servicePath)) {
        Write-Host "ERROR: Directorio no encontrado" -ForegroundColor Red
        continue
    }
    
    Set-Location $servicePath
    
    # Verificar venv
    if (!(Test-Path "venv\Scripts\python.exe")) {
        Write-Host "Creando entorno virtual..." -ForegroundColor Yellow
        python -m venv venv
        Start-Sleep -Seconds 2
    }
    
    # Instalar dependencias básicas
    Write-Host "Instalando dependencias básicas..." -ForegroundColor Yellow
    
    $deps = @(
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
    
    # Instalar cada dependencia
    foreach ($dep in $deps) {
        try {
            & "venv\Scripts\pip.exe" install $dep --quiet --disable-pip-version-check
        } catch {
            Write-Host "Error instalando $dep" -ForegroundColor Red
        }
    }
    
    # Dependencias específicas
    switch ($service) {
        "reportes" {
            Write-Host "Instalando deps de reportes..." -ForegroundColor Yellow
            & "venv\Scripts\pip.exe" install pandas openpyxl matplotlib reportlab --quiet --disable-pip-version-check
        }
        "pagos" {
            Write-Host "Instalando deps de pagos..." -ForegroundColor Yellow  
            & "venv\Scripts\pip.exe" install stripe --quiet --disable-pip-version-check
        }
    }
    
    # Verificar instalación básica
    try {
        $result = & "venv\Scripts\python.exe" -c "import django, rest_framework; print('OK')" 2>$null
        if ($result -eq "OK") {
            Write-Host "EXITO: $service instalado correctamente" -ForegroundColor Green
        } else {
            Write-Host "ERROR: Problemas con $service" -ForegroundColor Red
        }
    } catch {
        Write-Host "ERROR: No se puede verificar $service" -ForegroundColor Red
    }
}

Write-Host "`nINSTALACION COMPLETADA" -ForegroundColor Green