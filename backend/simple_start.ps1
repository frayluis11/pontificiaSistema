# Script simplificado para diagnosticar y iniciar microservicios
Write-Host "=== DIAGNOSTICO DE MICROSERVICIOS ===" -ForegroundColor Green

# Configuracion de servicios
$services = @(
    @{Name="auth"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\auth"; Port="3001"; DBPort="3307"; DBName="auth_db"},
    @{Name="users"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\users"; Port="3002"; DBPort="3308"; DBName="users_db"},
    @{Name="asistencia"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\asistencia"; Port="3003"; DBPort="3309"; DBName="asistencia_db"},
    @{Name="documentos"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\documentos"; Port="3004"; DBPort="3310"; DBName="documentos_db"},
    @{Name="pagos"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\pagos"; Port="3005"; DBPort="3311"; DBName="pagos_db"},
    @{Name="reportes"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\reportes"; Port="3006"; DBPort="3312"; DBName="reportes_db"},
    @{Name="auditoria"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\auditoria"; Port="3007"; DBPort="3312"; DBName="auditoria_db"},
    @{Name="gateway"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\gateway"; Port="8000"; DBPort="3313"; DBName="gateway_db"}
)

$workingServices = @()

# Diagnostico simple
foreach ($service in $services) {
    Write-Host "`nDiagnosticando: $($service.Name)" -ForegroundColor Yellow
    
    $canStart = $true
    $issues = @()
    
    # Verificar directorio
    if (!(Test-Path $service.Path)) {
        Write-Host "  ERROR: Directorio no encontrado" -ForegroundColor Red
        $canStart = $false
        continue
    }
    
    # Verificar venv
    if (!(Test-Path "$($service.Path)\venv\Scripts\python.exe")) {
        Write-Host "  ERROR: No hay entorno virtual" -ForegroundColor Red
        $canStart = $false
    }
    
    # Verificar manage.py
    if (!(Test-Path "$($service.Path)\manage.py")) {
        Write-Host "  ERROR: No se encuentra manage.py" -ForegroundColor Red
        $canStart = $false
    }
    
    # Verificar puerto de base de datos
    try {
        $connection = Test-NetConnection -ComputerName "localhost" -Port $service.DBPort -WarningAction SilentlyContinue
        if (!$connection.TcpTestSucceeded) {
            Write-Host "  ERROR: Puerto DB $($service.DBPort) no disponible" -ForegroundColor Red
            $canStart = $false
        }
    } catch {
        Write-Host "  ERROR: No se puede verificar puerto DB" -ForegroundColor Red
        $canStart = $false
    }
    
    if ($canStart) {
        Write-Host "  OK: $($service.Name) listo para iniciar" -ForegroundColor Green
        $workingServices += $service
    } else {
        Write-Host "  FALLO: $($service.Name) tiene problemas" -ForegroundColor Red
    }
}

Write-Host "`n=== RESUMEN ===" -ForegroundColor Cyan
Write-Host "Servicios listos: $($workingServices.Count)" -ForegroundColor Green
Write-Host "Servicios con problemas: $($services.Count - $workingServices.Count)" -ForegroundColor Red

if ($workingServices.Count -gt 0) {
    Write-Host "`nIniciando servicios funcionales..." -ForegroundColor Green
    
    foreach ($service in $workingServices) {
        Write-Host "Iniciando $($service.Name) en puerto $($service.Port)..."
        
        # Crear comando de inicio
        $cmd = "cd '$($service.Path)'; `$env:DB_HOST='localhost'; `$env:DB_PORT='$($service.DBPort)'; `$env:DB_NAME='$($service.DBName)'; `$env:DB_USER='root'; `$env:DB_PASSWORD='root'; venv\Scripts\python.exe manage.py runserver 127.0.0.1:$($service.Port)"
        
        # Iniciar en proceso separado
        Start-Process powershell -ArgumentList "-Command", $cmd -WindowStyle Minimized
        
        Start-Sleep -Seconds 2
    }
    
    # Esperar un poco y verificar
    Write-Host "`nEsperando que los servicios se inicien..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    Write-Host "`nVerificando servicios:" -ForegroundColor Cyan
    foreach ($service in $workingServices) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:$($service.Port)/" -TimeoutSec 3 -ErrorAction Stop
            Write-Host "  $($service.Name): FUNCIONANDO" -ForegroundColor Green
        } catch {
            Write-Host "  $($service.Name): No responde aun" -ForegroundColor Yellow
        }
    }
}

Write-Host "`nURLs para probar:" -ForegroundColor White
foreach ($service in $workingServices) {
    Write-Host "http://127.0.0.1:$($service.Port)/" -ForegroundColor Cyan
}