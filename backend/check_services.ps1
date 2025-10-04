# Script para probar todos los servicios del sistema pontificia
Write-Host "🔍 PROBANDO SERVICIOS DEL SISTEMA PONTIFICIA" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

# Función para probar un servicio
function Test-Service {
    param($serviceName, $port, $endpoint = "/")
    
    $url = "http://localhost:$port$endpoint"
    
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 3 -ErrorAction Stop
        Write-Host "✅ $serviceName (Puerto $port) - FUNCIONANDO" -ForegroundColor Green
        
        # Mostrar información adicional si es necesario
        if ($response.StatusCode -eq 200) {
            Write-Host "   Status: $($response.StatusCode) OK" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "❌ $serviceName (Puerto $port) - NO RESPONDE" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
    }
    Write-Host ""
}

# Función para probar endpoints específicos
function Test-ApiEndpoints {
    param($serviceName, $port)
    
    Write-Host "🔧 Probando endpoints de $serviceName:" -ForegroundColor Yellow
    
    # Endpoints comunes de Django REST
    $endpoints = @("/api/", "/admin/", "/health/")
    
    foreach ($endpoint in $endpoints) {
        $url = "http://localhost:$port$endpoint"
        try {
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 2 -ErrorAction Stop
            $response = Invoke-WebRequest -Uri $url -TimeoutSec 2 -ErrorAction Stop
            Write-Host "   ✅ $endpoint - OK ($($response.StatusCode))" -ForegroundColor Green
        }
        catch {
            Write-Host "   ❌ $endpoint - No disponible" -ForegroundColor Gray
        }
    }
    Write-Host ""
}

Write-Host "📊 ESTADO DE LOS SERVICIOS:" -ForegroundColor Yellow
Write-Host "=============================" -ForegroundColor Yellow

# Probar servicios básicos
Test-Service "Auth Service" 3001
Test-Service "Users Service" 3002
Test-Service "Asistencia Service" 3003
Test-Service "Documentos Service" 3004
Test-Service "Pagos Service" 3005
Test-Service "Reportes Service" 3006
Test-Service "Auditoria Service" 3007
Test-Service "Gateway Service" 8000

Write-Host "🧪 PRUEBAS DETALLADAS DE ENDPOINTS:" -ForegroundColor Magenta
Write-Host "====================================" -ForegroundColor Magenta

# Probar endpoints específicos para algunos servicios
Test-ApiEndpoints "Gateway" 8000
Test-ApiEndpoints "Auth" 3001
Test-ApiEndpoints "Users" 3002

Write-Host "✨ PRUEBAS COMPLETADAS" -ForegroundColor Green