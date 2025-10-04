# Script para configurar PyMySQL en todos los services
Write-Host "CONFIGURANDO PYMYSQL EN SETTINGS..." -ForegroundColor Yellow

$services = @("auth", "users", "asistencia", "documentos", "pagos", "reportes", "auditoria", "gateway")

foreach ($service in $services) {
    Write-Host "Configurando settings.py de $service..." -ForegroundColor Cyan
    
    $settingsPath = "$service\$service\settings.py"
    
    if (Test-Path $settingsPath) {
        # Leer contenido actual
        $content = Get-Content $settingsPath -Raw
        
        # Si no tiene configuracion PyMySQL, agregarla al inicio
        if ($content -notmatch "import pymysql") {
            $newContent = @"
import pymysql
pymysql.install_as_MySQLdb()

$content
"@
            Set-Content -Path $settingsPath -Value $newContent -Encoding UTF8
        }
        
        Write-Host "EXITO: $service configurado para PyMySQL" -ForegroundColor Green
    } else {
        Write-Host "WARNING: No se encontro settings.py en $settingsPath" -ForegroundColor Red
    }
}

Write-Host "CONFIGURACION PYMYSQL COMPLETADA" -ForegroundColor Green