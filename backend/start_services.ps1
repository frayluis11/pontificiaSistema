# Script para iniciar todos los microservicios del sistema pontificia
Write-Host "🚀 INICIANDO SISTEMA DE MICROSERVICIOS PONTIFICIA" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Función para iniciar un servicio
function Start-Service {
    param($serviceName, $port, $path)
    
    Write-Host "🔄 Iniciando $serviceName en puerto $port..." -ForegroundColor Yellow
    
    # Cambiar al directorio del servicio
    Set-Location $path
    
    # Iniciar el servicio en background
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "python manage.py runserver $port"
    
    Write-Host "✅ $serviceName iniciado en http://localhost:$port" -ForegroundColor Green
    Start-Sleep -Seconds 2
}

# Directorio base
$baseDir = "c:\Users\Fray Luis\Desktop\sistemaPontificia\backend"

# Iniciar servicios
Start-Service "Auth Service" 3001 "$baseDir\auth"
Start-Service "Users Service" 3002 "$baseDir\users"  
Start-Service "Asistencia Service" 3003 "$baseDir\asistencia"
Start-Service "Documentos Service" 3004 "$baseDir\documentos"
Start-Service "Pagos Service" 3005 "$baseDir\pagos"
Start-Service "Reportes Service" 3006 "$baseDir\reportes"
Start-Service "Auditoria Service" 3007 "$baseDir\auditoria"
Start-Service "Gateway Service" 8000 "$baseDir\gateway"

Write-Host ""
Write-Host "🎉 TODOS LOS SERVICIOS INICIADOS" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "📋 Servicios disponibles:"
Write-Host "   • Auth: http://localhost:3001"
Write-Host "   • Users: http://localhost:3002"
Write-Host "   • Asistencia: http://localhost:3003"
Write-Host "   • Documentos: http://localhost:3004"
Write-Host "   • Pagos: http://localhost:3005"
Write-Host "   • Reportes: http://localhost:3006"
Write-Host "   • Auditoria: http://localhost:3007"
Write-Host "   • Gateway: http://localhost:8000"
Write-Host ""
Write-Host "🔍 Para verificar el estado, ejecuta: .\test_services.ps1"