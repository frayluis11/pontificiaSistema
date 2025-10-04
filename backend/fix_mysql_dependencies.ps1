# Script para reemplazar mysqlclient con PyMySQL (no requiere compilacion)
Write-Host "SOLUCIONANDO PROBLEMAS DE MYSQL..." -ForegroundColor Yellow

$services = @("auth", "users", "asistencia", "documentos", "pagos", "reportes", "auditoria", "gateway")

foreach ($service in $services) {
    Write-Host "Configurando $service..." -ForegroundColor Cyan
    
    cd $service
    
    # Activar entorno virtual
    .\venv\Scripts\Activate.ps1
    
    # Desinstalar mysqlclient si existe
    pip uninstall mysqlclient -y 2>$null
    
    # Instalar PyMySQL como alternativa
    pip install PyMySQL==1.1.0
    
    Write-Host "EXITO: $service configurado con PyMySQL" -ForegroundColor Green
    
    # Desactivar entorno
    deactivate
    
    cd ..
}

Write-Host "CONFIGURACION MYSQL COMPLETADA - Ahora usar PyMySQL en lugar de mysqlclient" -ForegroundColor Green