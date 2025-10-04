# Script para ejecutar python manage.py check en todos los servicios
Write-Host "EJECUTANDO VERIFICACIONES DE CONFIGURACION..." -ForegroundColor Yellow

$services = @("auth", "users", "asistencia", "documentos", "pagos", "reportes", "auditoria", "gateway")

foreach ($service in $services) {
    Write-Host "`n=== VERIFICANDO $service ===" -ForegroundColor Cyan
    
    cd $service
    
    # Activar entorno virtual
    .\venv\Scripts\Activate.ps1
    
    # Ejecutar check de Django
    Write-Host "Ejecutando: python manage.py check" -ForegroundColor Yellow
    python manage.py check
    
    Write-Host "Estado de $service: VERIFICADO" -ForegroundColor Green
    
    # Desactivar entorno
    deactivate
    
    cd ..
}

Write-Host "`nVERIFICACIONES COMPLETADAS" -ForegroundColor Green