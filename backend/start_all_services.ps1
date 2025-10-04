# Script para iniciar todos los microservicios del Sistema Pontificia
Write-Host "=== Iniciando todos los microservicios ===" -ForegroundColor Green

# Configuración de puertos y servicios
$services = @(
    @{Name="auth"; Port="3001"; DBPort="3307"; DBName="auth_db"},
    @{Name="users"; Port="3002"; DBPort="3308"; DBName="users_db"},
    @{Name="asistencia"; Port="3003"; DBPort="3309"; DBName="asistencia_db"},
    @{Name="documentos"; Port="3004"; DBPort="3310"; DBName="documentos_db"},
    @{Name="pagos"; Port="3005"; DBPort="3311"; DBName="pagos_db"},
    @{Name="reportes"; Port="3006"; DBPort="3312"; DBName="reportes_db"},
    @{Name="auditoria"; Port="3007"; DBPort="3312"; DBName="auditoria_db"},
    @{Name="gateway"; Port="8000"; DBPort="3313"; DBName="gateway_db"}
)

# Función para instalar dependencias básicas
function Install-Dependencies {
    param($ServicePath)
    
    Write-Host "Instalando dependencias para $ServicePath..." -ForegroundColor Yellow
    
    if (!(Test-Path "$ServicePath\venv")) {
        python -m venv "$ServicePath\venv"
    }
    
    & "$ServicePath\venv\Scripts\activate.ps1"
    pip install django djangorestframework mysqlclient django-cors-headers python-decouple djangorestframework-simplejwt drf-spectacular pillow 2>$null
    deactivate
}

# Función para aplicar migraciones
function Apply-Migrations {
    param($ServicePath, $DBHost, $DBPort, $DBName)
    
    Write-Host "Aplicando migraciones para $ServicePath..." -ForegroundColor Yellow
    
    $env:DB_HOST = $DBHost
    $env:DB_PORT = $DBPort
    $env:DB_NAME = $DBName
    $env:DB_USER = "root"
    $env:DB_PASSWORD = "root"
    
    & "$ServicePath\venv\Scripts\activate.ps1"
    python "$ServicePath\manage.py" makemigrations 2>$null
    python "$ServicePath\manage.py" migrate 2>$null
    deactivate
    
    # Limpiar variables de entorno
    Remove-Item Env:DB_HOST -ErrorAction SilentlyContinue
    Remove-Item Env:DB_PORT -ErrorAction SilentlyContinue
    Remove-Item Env:DB_NAME -ErrorAction SilentlyContinue
    Remove-Item Env:DB_USER -ErrorAction SilentlyContinue
    Remove-Item Env:DB_PASSWORD -ErrorAction SilentlyContinue
}

# Función para iniciar un servicio
function Start-Service {
    param($ServicePath, $Port, $DBHost, $DBPort, $DBName, $ServiceName)
    
    Write-Host "Iniciando servicio $ServiceName en puerto $Port..." -ForegroundColor Green
    
    $env:DB_HOST = $DBHost
    $env:DB_PORT = $DBPort
    $env:DB_NAME = $DBName
    $env:DB_USER = "root"
    $env:DB_PASSWORD = "root"
    
    # Iniciar el servicio en background
    Start-Process powershell -ArgumentList "-Command", "cd '$ServicePath'; venv\Scripts\activate; `$env:DB_HOST='$DBHost'; `$env:DB_PORT='$DBPort'; `$env:DB_NAME='$DBName'; `$env:DB_USER='root'; `$env:DB_PASSWORD='root'; python manage.py runserver 0.0.0.0:$Port" -WindowStyle Minimized
    
    Start-Sleep -Seconds 2
}

# Procesar cada microservicio
foreach ($service in $services) {
    $servicePath = ""
    
    # Determinar el path del servicio
    switch ($service.Name) {
        "auth" { $servicePath = "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\auth" }
        "users" { $servicePath = "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\users" }
        "asistencia" { $servicePath = "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\asistencia" }
        "documentos" { $servicePath = "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\documentos" }
        "pagos" { $servicePath = "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\pagos" }
        "reportes" { $servicePath = "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\reportes" }
        "auditoria" { $servicePath = "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\auditoria" }
        "gateway" { $servicePath = "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\gateway" }
    }
    
    if (Test-Path $servicePath) {
        Write-Host "`n--- Procesando servicio: $($service.Name) ---" -ForegroundColor Cyan
        
        # Instalar dependencias si no existe venv o está incompleto
        if (!(Test-Path "$servicePath\venv") -or !(Test-Path "$servicePath\venv\Scripts\python.exe")) {
            Install-Dependencies -ServicePath $servicePath
        }
        
        # Aplicar migraciones
        Apply-Migrations -ServicePath $servicePath -DBHost "localhost" -DBPort $service.DBPort -DBName $service.DBName
        
        # Iniciar servicio
        Start-Service -ServicePath $servicePath -Port $service.Port -DBHost "localhost" -DBPort $service.DBPort -DBName $service.DBName -ServiceName $service.Name
        
        Write-Host "Servicio $($service.Name) iniciado en http://localhost:$($service.Port)" -ForegroundColor Green
    } else {
        Write-Host "ADVERTENCIA: No se encontró el directorio $servicePath" -ForegroundColor Red
    }
}

Write-Host "`n=== RESUMEN DE SERVICIOS ===" -ForegroundColor Green
Write-Host "Auth Service:        http://localhost:3001" -ForegroundColor White
Write-Host "Users Service:       http://localhost:3002" -ForegroundColor White
Write-Host "Asistencia Service:  http://localhost:3003" -ForegroundColor White
Write-Host "Documentos Service:  http://localhost:3004" -ForegroundColor White
Write-Host "Pagos Service:       http://localhost:3005" -ForegroundColor White
Write-Host "Reportes Service:    http://localhost:3006" -ForegroundColor White
Write-Host "Auditoria Service:   http://localhost:3007" -ForegroundColor White
Write-Host "Gateway Service:     http://localhost:8000" -ForegroundColor White
Write-Host "`nTodos los servicios se están ejecutando. Presiona Ctrl+C para detener." -ForegroundColor Yellow

# Mantener el script ejecutándose para monitorear
Write-Host "Presiona cualquier tecla para salir..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")