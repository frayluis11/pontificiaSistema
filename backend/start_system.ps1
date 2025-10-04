# Script final para iniciar todos los microservicios funcionales
Write-Host "=== INICIANDO SISTEMA PONTIFICIA - TODOS LOS SERVICIOS ===" -ForegroundColor Green

# Detener procesos Python existentes
Get-Process -Name python* -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "Procesos Python anteriores detenidos" -ForegroundColor Yellow

$services = @(
    @{Name="auth"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\auth"; Port="3001"; DBPort="3307"; DBName="auth_db"},
    @{Name="users"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\users"; Port="3002"; DBPort="3308"; DBName="users_db"},
    @{Name="asistencia"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\asistencia"; Port="3003"; DBPort="3309"; DBName="asistencia_db"},
    @{Name="pagos"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\pagos"; Port="3005"; DBPort="3311"; DBName="pagos_db"},
    @{Name="reportes"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\reportes"; Port="3006"; DBPort="3312"; DBName="reportes_db"},
    @{Name="gateway"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\gateway"; Port="8000"; DBPort="3313"; DBName="gateway_db"}
)

$successfulServices = @()

# Iniciar cada servicio
foreach ($service in $services) {
    Write-Host "`nIniciando $($service.Name)..." -ForegroundColor Cyan
    
    # Comando para iniciar el servicio
    $startCommand = @"
cd '$($service.Path)'; 
`$env:DB_HOST = 'localhost'; 
`$env:DB_PORT = '$($service.DBPort)'; 
`$env:DB_NAME = '$($service.DBName)'; 
`$env:DB_USER = 'root'; 
`$env:DB_PASSWORD = 'root'; 
venv\Scripts\python.exe manage.py runserver 127.0.0.1:$($service.Port)
"@
    
    # Iniciar en proceso separado
    $process = Start-Process powershell -ArgumentList "-Command", $startCommand -PassThru -WindowStyle Minimized
    Start-Sleep -Seconds 3
    
    # Verificar que el servicio responda
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$($service.Port)/" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "  ✅ $($service.Name) - FUNCIONANDO (Puerto $($service.Port))" -ForegroundColor Green
        
        $successfulServices += @{
            Name = $service.Name
            Port = $service.Port
            Status = "Funcionando"
            Process = $process.Id
        }
        
    } catch {
        if ($_.Exception.Message -like "*404*") {
            Write-Host "  ⚠️ $($service.Name) - FUNCIONANDO con 404 (Puerto $($service.Port))" -ForegroundColor Yellow
            $successfulServices += @{
                Name = $service.Name
                Port = $service.Port
                Status = "Funcionando (404)"
                Process = $process.Id
            }
        } else {
            Write-Host "  ❌ $($service.Name) - NO RESPONDE: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

# Esperar un momento adicional para que se estabilicen
Write-Host "`nEsperando estabilización de servicios..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verificación final
Write-Host "`n" + "="*80 -ForegroundColor Green
Write-Host "🎯 VERIFICACIÓN FINAL DE SERVICIOS" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green

foreach ($service in $successfulServices) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:$($service.Port)/" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "✅ $($service.Name) (Puerto $($service.Port)) - ACTIVO" -ForegroundColor Green
        
        # Mostrar contenido si es JSON
        if ($response.Content -match '^\s*\{.*\}\s*$') {
            try {
                $jsonContent = $response.Content | ConvertFrom-Json
                if ($jsonContent.service) {
                    Write-Host "   Servicio: $($jsonContent.service)" -ForegroundColor Gray
                }
                if ($jsonContent.endpoints) {
                    Write-Host "   Endpoints disponibles:" -ForegroundColor Gray
                    foreach ($endpoint in $jsonContent.endpoints.PSObject.Properties) {
                        Write-Host "      - $($endpoint.Name): http://127.0.0.1:$($service.Port)$($endpoint.Value)" -ForegroundColor Cyan
                    }
                }
            } catch {
                Write-Host "   Respuesta recibida pero no es JSON válido" -ForegroundColor Gray
            }
        }
        }
        
    } catch {
        if ($_.Exception.Message -like "*404*") {
            Write-Host "⚠️ $($service.Name) (Puerto $($service.Port)) - FUNCIONANDO (sin ruta raíz)" -ForegroundColor Yellow
        } else {
            Write-Host "❌ $($service.Name) (Puerto $($service.Port)) - NO RESPONDE" -ForegroundColor Red
        }
    }
    Write-Host ""
}

# Resumen final
Write-Host "="*80 -ForegroundColor Magenta
Write-Host "📊 RESUMEN DEL SISTEMA PONTIFICIA" -ForegroundColor Magenta
Write-Host "="*80 -ForegroundColor Magenta
Write-Host "🟢 Servicios activos: $($successfulServices.Count)" -ForegroundColor Green
Write-Host "🔗 URLs principales:" -ForegroundColor White

foreach ($service in $successfulServices) {
    Write-Host "   http://127.0.0.1:$($service.Port)/ - $($service.Name)" -ForegroundColor Cyan
}

Write-Host "`n🚀 SISTEMA PONTIFICIA INICIADO EXITOSAMENTE" -ForegroundColor Green
Write-Host "📝 Para detener todos los servicios, usa: Get-Process -Name python* | Stop-Process -Force" -ForegroundColor Yellow
Write-Host "`nPresiona cualquier tecla para mantener los servicios ejecutándose..." -ForegroundColor White
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")