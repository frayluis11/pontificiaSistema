# Script correcto para configurar PyMySQL en todos los services
Write-Host "CONFIGURANDO PYMYSQL EN SETTINGS..." -ForegroundColor Yellow

$services = @(
    @{name="auth"; path="auth\auth_service\settings.py"},
    @{name="users"; path="users\users_service\settings.py"},
    @{name="asistencia"; path="asistencia\asistencia_service\settings.py"},
    @{name="documentos"; path="documentos\documentos_service\settings.py"},
    @{name="pagos"; path="pagos\pagos_service\settings.py"},
    @{name="reportes"; path="reportes\reportes_service\settings.py"},
    @{name="auditoria"; path="auditoria\auditoria_service\settings.py"},
    @{name="gateway"; path="gateway\gateway_service\settings.py"}
)

foreach ($service in $services) {
    Write-Host "Configurando settings.py de $($service.name)..." -ForegroundColor Cyan
    
    $settingsPath = $service.path
    
    if (Test-Path $settingsPath) {
        # Leer contenido actual
        $content = Get-Content $settingsPath -Raw -Encoding UTF8
        
        # Si no tiene configuracion PyMySQL, agregarla al inicio
        if ($content -notmatch "import pymysql") {
            $newContent = @"
import pymysql
pymysql.install_as_MySQLdb()

$content
"@
            Set-Content -Path $settingsPath -Value $newContent -Encoding UTF8
            Write-Host "EXITO: $($service.name) configurado para PyMySQL" -ForegroundColor Green
        } else {
            Write-Host "INFO: $($service.name) ya tiene PyMySQL configurado" -ForegroundColor Yellow
        }
    } else {
        Write-Host "ERROR: No se encontro settings.py en $settingsPath" -ForegroundColor Red
    }
}

Write-Host "CONFIGURACION PYMYSQL COMPLETADA" -ForegroundColor Green