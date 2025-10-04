# Script para análisis completo de errores en código, Docker y dependencias
Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Host "          ANÁLISIS COMPLETO DE ERRORES - SISTEMA PONTIFICIA         " -ForegroundColor Yellow  
Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Host ""

# Arrays de servicios y puertos
$services = @("auth", "users", "asistencia", "documentos", "pagos", "reportes", "auditoria", "gateway")

# Contadores de errores
$totalErrores = 0
$erroresCriticos = 0
$erroresDocker = 0
$erroresDependencias = 0

Write-Host "1. VERIFICANDO ARCHIVOS DOCKER..." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Gray

# Verificar Dockerfiles
foreach ($service in $services) {
    $dockerFile = "$service/Dockerfile"
    if (Test-Path $dockerFile) {
        Write-Host " $service - Dockerfile encontrado" -ForegroundColor Green
        
        # Verificar contenido básico
        $content = Get-Content $dockerFile -Raw
        if ($content -match "FROM python") {
            Write-Host "   Base image Python OK" -ForegroundColor Green
        } else {
            Write-Host "   ERROR: Base image no válida" -ForegroundColor Red
            $erroresDocker++
        }
    } else {
        Write-Host " $service - ERROR: Dockerfile faltante" -ForegroundColor Red
        $erroresDocker++
    }
}

Write-Host ""
Write-Host "2. VERIFICANDO REQUIREMENTS.TXT..." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Gray

foreach ($service in $services) {
    $reqFile = "$service/requirements.txt"
    if (Test-Path $reqFile) {
        Write-Host " $service - Requirements.txt encontrado" -ForegroundColor Green
        
        $content = Get-Content $reqFile -Raw
        
        # Verificar Django
        if ($content -match "Django==") {
            Write-Host "   Django OK" -ForegroundColor Green
        } else {
            Write-Host "   ERROR: Django no especificado" -ForegroundColor Red
            $erroresDependencias++
        }
        
        # Verificar problema mysqlclient
        if ($content -match "mysqlclient") {
            Write-Host "   WARNING: mysqlclient presente" -ForegroundColor Yellow
        }
        
    } else {
        Write-Host " $service - ERROR: requirements.txt faltante" -ForegroundColor Red
        $erroresDependencias++
    }
}

Write-Host ""
Write-Host "3. VERIFICANDO ARCHIVOS PYTHON CRÍTICOS..." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Gray

foreach ($service in $services) {
    Write-Host "Verificando $service..." -ForegroundColor White
    
    # Verificar manage.py
    $manageFile = "$service/manage.py"
    if (Test-Path $manageFile) {
        Write-Host "   manage.py presente" -ForegroundColor Green
    } else {
        Write-Host "   ERROR: manage.py faltante" -ForegroundColor Red
        $erroresCriticos++
    }
    
    # Verificar settings.py  
    $settingsPattern = "$service/*_service/settings.py"
    $settingsFiles = Get-ChildItem -Path $settingsPattern -ErrorAction SilentlyContinue
    if ($settingsFiles.Count -gt 0) {
        Write-Host "   settings.py presente" -ForegroundColor Green
    } else {
        Write-Host "   ERROR: settings.py faltante" -ForegroundColor Red
        $erroresCriticos++
    }
}

Write-Host ""
Write-Host "4. VERIFICANDO DOCKER-COMPOSE..." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Gray

$dockerComposeFile = "docker-compose.yml"
if (Test-Path $dockerComposeFile) {
    Write-Host " docker-compose.yml encontrado" -ForegroundColor Green
    
    $composeContent = Get-Content $dockerComposeFile -Raw
    
    # Verificar servicios MySQL
    if ($composeContent -match "mysql_") {
        Write-Host "   Servicios MySQL configurados" -ForegroundColor Green
    }
    
    # Verificar Redis
    if ($composeContent -match "redis:") {
        Write-Host "   Redis configurado" -ForegroundColor Green
    } else {
        Write-Host "   WARNING: Redis no configurado" -ForegroundColor Yellow
    }
    
} else {
    Write-Host " ERROR: docker-compose.yml faltante" -ForegroundColor Red
    $erroresDocker++
}

# Calcular totales
$totalErrores = $erroresCriticos + $erroresDocker + $erroresDependencias

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Host "                            RESUMEN FINAL                           " -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Yellow

Write-Host "ESTADÍSTICAS DE ERRORES:" -ForegroundColor White
Write-Host "   Errores Críticos: $erroresCriticos" -ForegroundColor Red
Write-Host "   Errores Docker: $erroresDocker" -ForegroundColor Blue  
Write-Host "   Errores Dependencias: $erroresDependencias" -ForegroundColor Magenta
Write-Host "   TOTAL ERRORES: $totalErrores" -ForegroundColor Yellow

Write-Host ""
if ($totalErrores -eq 0) {
    Write-Host "EXCELENTE! No se encontraron errores críticos." -ForegroundColor Green
} elseif ($totalErrores -le 5) {
    Write-Host "Estado: BUENO - Pocos errores encontrados" -ForegroundColor Green
} elseif ($totalErrores -le 10) {
    Write-Host "Estado: REGULAR - Errores moderados encontrados" -ForegroundColor Yellow
} else {
    Write-Host "Estado: CRÍTICO - Muchos errores encontrados" -ForegroundColor Red
}

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host ""
Write-Host "Análisis completado: $timestamp" -ForegroundColor Gray