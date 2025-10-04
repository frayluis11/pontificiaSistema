# Script para probar cada servicio individualmente
Write-Host "=== PRUEBA INDIVIDUAL DE SERVICIOS ===" -ForegroundColor Green

$services = @(
    @{Name="auth"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\auth"; Port="3001"; DBPort="3307"; DBName="auth_db"},
    @{Name="users"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\users"; Port="3002"; DBPort="3308"; DBName="users_db"},
    @{Name="asistencia"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\asistencia"; Port="3003"; DBPort="3309"; DBName="asistencia_db"},
    @{Name="pagos"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\pagos"; Port="3005"; DBPort="3311"; DBName="pagos_db"},
    @{Name="reportes"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\reportes"; Port="3006"; DBPort="3312"; DBName="reportes_db"},
    @{Name="gateway"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\gateway"; Port="8000"; DBPort="3313"; DBName="gateway_db"}
)

foreach ($service in $services) {
    Write-Host "`n" + "="*50 -ForegroundColor Cyan
    Write-Host "PROBANDO: $($service.Name.ToUpper())" -ForegroundColor Cyan
    Write-Host "="*50 -ForegroundColor Cyan
    
    # Cambiar al directorio del servicio
    Set-Location $service.Path
    
    # Configurar variables de entorno
    $env:DB_HOST = "localhost"
    $env:DB_PORT = $service.DBPort
    $env:DB_NAME = $service.DBName
    $env:DB_USER = "root"
    $env:DB_PASSWORD = "root"
    
    Write-Host "Directorio: $($service.Path)" -ForegroundColor Yellow
    Write-Host "Puerto: $($service.Port)" -ForegroundColor Yellow
    Write-Host "Base de datos: localhost:$($service.DBPort)/$($service.DBName)" -ForegroundColor Yellow
    
    # Verificar archivos esenciales
    if (!(Test-Path "manage.py")) {
        Write-Host "ERROR: No se encuentra manage.py" -ForegroundColor Red
        continue
    }
    
    if (!(Test-Path "venv\Scripts\python.exe")) {
        Write-Host "ERROR: No hay entorno virtual" -ForegroundColor Red
        continue
    }
    
    # Probar comandos Django básicos
    Write-Host "`nProbando comandos Django..." -ForegroundColor Yellow
    
    try {
        # Probar importaciones básicas
        Write-Host "  - Verificando importaciones..." -ForegroundColor Gray
        $result = & "venv\Scripts\python.exe" -c "import django; print('Django OK')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✅ Django importado correctamente" -ForegroundColor Green
        } else {
            Write-Host "    ❌ Error importando Django" -ForegroundColor Red
            continue
        }
        
        # Probar configuración de settings
        Write-Host "  - Verificando configuración..." -ForegroundColor Gray
        $result = & "venv\Scripts\python.exe" -c "import os; os.environ['DJANGO_SETTINGS_MODULE'] = '$($service.Name)_service.settings'; import django; django.setup(); print('Settings OK')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✅ Settings configurado correctamente" -ForegroundColor Green
        } else {
            Write-Host "    ❌ Error en configuración de settings" -ForegroundColor Red
            continue
        }
        
        # Intentar iniciar el servidor (solo por 5 segundos)
        Write-Host "  - Intentando iniciar servidor..." -ForegroundColor Gray
        $serverProcess = Start-Process -FilePath "venv\Scripts\python.exe" -ArgumentList "manage.py", "runserver", "127.0.0.1:$($service.Port)" -PassThru -WindowStyle Hidden
        
        Start-Sleep -Seconds 5
        
        # Verificar si el servidor responde
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$($service.Port)/" -TimeoutSec 3 -ErrorAction Stop
            Write-Host "    ✅ Servidor iniciado y respondiendo (Status: $($response.StatusCode))" -ForegroundColor Green
            
            # Mostrar un poco del contenido
            if ($response.Content.Length -lt 300) {
                Write-Host "    Respuesta: $($response.Content)" -ForegroundColor Gray
            }
            
        } catch {
            if ($_.Exception.Message -like "*404*") {
                Write-Host "    ⚠️ Servidor iniciado pero sin ruta raíz (404)" -ForegroundColor Yellow
            } else {
                Write-Host "    ❌ Servidor no responde: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        # Detener el proceso del servidor
        if ($serverProcess -and !$serverProcess.HasExited) {
            $serverProcess.Kill()
            Write-Host "    Servidor detenido" -ForegroundColor Gray
        }
        
    } catch {
        Write-Host "    ❌ Error general: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Limpiar variables de entorno
    Remove-Item Env:DB_HOST -ErrorAction SilentlyContinue
    Remove-Item Env:DB_PORT -ErrorAction SilentlyContinue
    Remove-Item Env:DB_NAME -ErrorAction SilentlyContinue
    Remove-Item Env:DB_USER -ErrorAction SilentlyContinue
    Remove-Item Env:DB_PASSWORD -ErrorAction SilentlyContinue
}

Write-Host "`n" + "="*60 -ForegroundColor Green
Write-Host "PRUEBA COMPLETADA" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Green