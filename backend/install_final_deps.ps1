# Script para instalar las ultimas dependencias faltantes
Write-Host "INSTALANDO DEPENDENCIAS FINALES FALTANTES..." -ForegroundColor Yellow

$finalFixes = @(
    @{service="pagos"; packages=@("reportlab")},
    @{service="reportes"; packages=@("seaborn", "matplotlib", "numpy")},
    @{service="auditoria"; packages=@("reportlab")},
    @{service="gateway"; packages=@("django-ratelimit")}
)

foreach ($fix in $finalFixes) {
    Write-Host ""
    Write-Host "=== INSTALANDO DEPS FINALES EN $($fix.service) ===" -ForegroundColor Cyan
    
    cd $fix.service
    
    # Activar entorno virtual
    .\venv\Scripts\Activate.ps1
    
    # Instalar paquetes faltantes
    foreach ($package in $fix.packages) {
        Write-Host "Instalando $package..." -ForegroundColor Yellow
        pip install $package
    }
    
    Write-Host "EXITO: Dependencias finales de $($fix.service) instaladas" -ForegroundColor Green
    
    # Desactivar entorno
    deactivate
    
    cd ..
}

Write-Host ""
Write-Host "TODAS LAS DEPENDENCIAS FINALES INSTALADAS!" -ForegroundColor Green