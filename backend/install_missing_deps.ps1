# Script para instalar dependencias faltantes especificas
Write-Host "INSTALANDO DEPENDENCIAS FALTANTES IDENTIFICADAS..." -ForegroundColor Yellow

# Problemas identificados:
# - pkg_resources (setuptools) en asistencia, documentos, pagos, gateway
# - celery en reportes  
# - django_filters en auditoria

$fixes = @(
    @{service="asistencia"; packages=@("setuptools")},
    @{service="documentos"; packages=@("setuptools")},
    @{service="pagos"; packages=@("setuptools")},
    @{service="gateway"; packages=@("setuptools")},
    @{service="reportes"; packages=@("celery", "redis")},
    @{service="auditoria"; packages=@("django-filter")}
)

foreach ($fix in $fixes) {
    Write-Host ""
    Write-Host "=== REPARANDO $($fix.service) ===" -ForegroundColor Cyan
    
    cd $fix.service
    
    # Activar entorno virtual
    .\venv\Scripts\Activate.ps1
    
    # Instalar paquetes faltantes
    foreach ($package in $fix.packages) {
        Write-Host "Instalando $package..." -ForegroundColor Yellow
        pip install $package
    }
    
    Write-Host "EXITO: $($fix.service) reparado" -ForegroundColor Green
    
    # Desactivar entorno
    deactivate
    
    cd ..
}

Write-Host ""
Write-Host "TODAS LAS DEPENDENCIAS FALTANTES INSTALADAS" -ForegroundColor Green