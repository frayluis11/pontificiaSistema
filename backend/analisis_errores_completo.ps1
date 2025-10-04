# Script para análisis completo de errores en código, Docker y dependencias
Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Host "          ANÁLISIS COMPLETO DE ERRORES - SISTEMA PONTIFICIA         " -ForegroundColor Yellow  
Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Host ""

# Arrays de servicios y puertos
$services = @("auth", "users", "asistencia", "documentos", "pagos", "reportes", "auditoria", "gateway")
$servicePorts = @(3001, 3002, 3003, 3004, 3005, 3006, 3007, 8000)

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
        Write-Host "✅ Dockerfile encontrado: $service" -ForegroundColor Green
        
        # Verificar contenido básico
        $content = Get-Content $dockerFile -Raw
        if ($content -match "FROM python") {
            Write-Host "   ✅ Base image Python correcta" -ForegroundColor Green
        } else {
            Write-Host "   ❌ ERROR: Base image no válida" -ForegroundColor Red
            $erroresDocker++
        }
        
        if ($content -match "COPY requirements.txt") {
            Write-Host "   ✅ Copia requirements.txt" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  WARNING: No copia requirements.txt explícitamente" -ForegroundColor Yellow
        }
        
        if ($content -match "EXPOSE") {
            Write-Host "   ✅ Puerto expuesto correctamente" -ForegroundColor Green
        } else {
            Write-Host "   ❌ ERROR: Puerto no expuesto" -ForegroundColor Red
            $erroresDocker++
        }
    } else {
        Write-Host "❌ ERROR: Dockerfile faltante en $service" -ForegroundColor Red
        $erroresDocker++
    }
}

Write-Host ""
Write-Host "2. VERIFICANDO REQUIREMENTS.TXT..." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Gray

foreach ($service in $services) {
    $reqFile = "$service/requirements.txt"
    if (Test-Path $reqFile) {
        Write-Host "✅ Requirements.txt encontrado: $service" -ForegroundColor Green
        
        $content = Get-Content $reqFile -Raw
        
        # Verificar Django
        if ($content -match "Django==") {
            Write-Host "   ✅ Django version especificada" -ForegroundColor Green
        } else {
            Write-Host "   ❌ ERROR: Django no especificado" -ForegroundColor Red
            $erroresDependencias++
        }
        
        # Verificar DRF
        if ($content -match "djangorestframework==") {
            Write-Host "   ✅ Django REST Framework especificado" -ForegroundColor Green
        } else {
            Write-Host "   ❌ ERROR: DRF no especificado" -ForegroundColor Red
            $erroresDependencias++
        }
        
        # Verificar problema mysqlclient
        if ($content -match "mysqlclient") {
            Write-Host "   ⚠️  WARNING: mysqlclient presente (problemas de compilación)" -ForegroundColor Yellow
            Write-Host "       RECOMENDACIÓN: Usar PyMySQL en su lugar" -ForegroundColor Magenta
        }
        
    } else {
        Write-Host "❌ ERROR: requirements.txt faltante en $service" -ForegroundColor Red
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
        Write-Host "   ✅ manage.py presente" -ForegroundColor Green
    } else {
        Write-Host "   ❌ ERROR: manage.py faltante" -ForegroundColor Red
        $erroresCriticos++
    }
    
    # Verificar settings.py  
    $settingsPattern = "$service/*_service/settings.py"
    $settingsFiles = Get-ChildItem -Path $settingsPattern -ErrorAction SilentlyContinue
    if ($settingsFiles.Count -gt 0) {
        Write-Host "   ✅ settings.py presente" -ForegroundColor Green
        
        # Verificar configuración PyMySQL
        $settingsContent = Get-Content $settingsFiles[0].FullName -Raw
        if ($settingsContent -match "import pymysql") {
            Write-Host "   ✅ PyMySQL configurado correctamente" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  WARNING: PyMySQL no configurado" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ❌ ERROR: settings.py faltante" -ForegroundColor Red
        $erroresCriticos++
    }
    
    # Verificar urls.py
    $urlsPattern = "$service/*_service/urls.py"
    $urlsFiles = Get-ChildItem -Path $urlsPattern -ErrorAction SilentlyContinue
    if ($urlsFiles.Count -gt 0) {
        Write-Host "   ✅ urls.py presente" -ForegroundColor Green
    } else {
        Write-Host "   ❌ ERROR: urls.py faltante" -ForegroundColor Red
        $erroresCriticos++
    }
}

Write-Host ""
Write-Host "4. VERIFICANDO DOCKER-COMPOSE..." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Gray

$dockerComposeFile = "docker-compose.yml"
if (Test-Path $dockerComposeFile) {
    Write-Host "✅ docker-compose.yml encontrado" -ForegroundColor Green
    
    $composeContent = Get-Content $dockerComposeFile -Raw
    
    # Verificar servicios MySQL
    $mysqlCount = ($composeContent | Select-String "mysql_" -AllMatches).Matches.Count
    Write-Host "   ✅ Servicios MySQL configurados: $mysqlCount" -ForegroundColor Green
    
    # Verificar Redis
    if ($composeContent -match "redis:") {
        Write-Host "   ✅ Redis configurado" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  WARNING: Redis no configurado" -ForegroundColor Yellow
    }
    
    # Verificar network
    if ($composeContent -match "networks:") {
        Write-Host "   ✅ Redes Docker configuradas" -ForegroundColor Green
    } else {
        Write-Host "   ❌ ERROR: Redes Docker no configuradas" -ForegroundColor Red
        $erroresDocker++
    }
    
} else {
    Write-Host "❌ ERROR: docker-compose.yml faltante" -ForegroundColor Red
    $erroresDocker++
}

Write-Host ""
Write-Host "5. VERIFICANDO ESTRUCTURA DE DIRECTORIOS..." -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Gray

foreach ($service in $services) {
    if (Test-Path $service) {
        Write-Host "✅ Directorio $service existe" -ForegroundColor Green
        
        # Verificar venv
        if (Test-Path "$service/venv") {
            Write-Host "   ✅ Virtual environment presente" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  WARNING: Virtual environment faltante" -ForegroundColor Yellow
        }
        
        # Verificar app directory
        $appDirs = Get-ChildItem -Path "$service" -Directory | Where-Object { $_.Name.EndsWith("_app") }
        if ($appDirs.Count -gt 0) {
            Write-Host "   ✅ Directorio de aplicación presente: $($appDirs[0].Name)" -ForegroundColor Green
        } else {
            Write-Host "   ❌ ERROR: Directorio de aplicación faltante" -ForegroundColor Red
            $erroresCriticos++
        }
        
    } else {
        Write-Host "❌ ERROR: Directorio $service faltante" -ForegroundColor Red
        $erroresCriticos++
    }
}

# Calcular totales
$totalErrores = $erroresCriticos + $erroresDocker + $erroresDependencias

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Host "                            RESUMEN FINAL                           " -ForegroundColor Yellow
Write-Host "=====================================================================" -ForegroundColor Yellow

Write-Host "📊 ESTADÍSTICAS DE ERRORES:" -ForegroundColor White
Write-Host "   🔴 Errores Críticos: $erroresCriticos" -ForegroundColor Red
Write-Host "   🐳 Errores Docker: $erroresDocker" -ForegroundColor Blue  
Write-Host "   📦 Errores Dependencias: $erroresDependencias" -ForegroundColor Magenta
Write-Host "   📈 TOTAL ERRORES: $totalErrores" -ForegroundColor Yellow

Write-Host ""
if ($totalErrores -eq 0) {
    Write-Host "🎉 ¡EXCELENTE! No se encontraron errores críticos." -ForegroundColor Green
} elseif ($totalErrores -le 5) {
    Write-Host "✅ Estado: BUENO - Pocos errores encontrados" -ForegroundColor Green
} elseif ($totalErrores -le 10) {
    Write-Host "⚠️  Estado: REGULAR - Errores moderados encontrados" -ForegroundColor Yellow
} else {
    Write-Host "❌ Estado: CRÍTICO - Muchos errores encontrados" -ForegroundColor Red
}

Write-Host ""
Write-Host "🔧 PRÓXIMOS PASOS RECOMENDADOS:" -ForegroundColor Cyan
Write-Host "   1. Resolver errores críticos primero" -ForegroundColor White
Write-Host "   2. Corregir configuraciones Docker" -ForegroundColor White
Write-Host "   3. Actualizar dependencias problemáticas" -ForegroundColor White
Write-Host "   4. Ejecutar tests de funcionalidad" -ForegroundColor White

Write-Host ""
Write-Host "Análisis completado: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray