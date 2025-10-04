# Script mejorado para iniciar todos los microservicios con diagnósticos
Write-Host "=== DIAGNÓSTICO Y INICIO DE MICROSERVICIOS ===" -ForegroundColor Cyan

# Función para verificar conexión a base de datos
function Test-DatabaseConnection {
    param($Host, $Port, $Database, $User, $Password)
    
    try {
        # Intentar conexión básica con MySQL
        $connectionString = "Server=$Host;Port=$Port;Database=$Database;Uid=$User;Pwd=$Password;"
        Write-Host "    🔍 Probando conexión a: $Host:$Port/$Database" -ForegroundColor Yellow
        
        # Usar netstat para verificar si el puerto está abierto
        $portOpen = (Test-NetConnection -ComputerName $Host -Port $Port -WarningAction SilentlyContinue).TcpTestSucceeded
        if ($portOpen) {
            Write-Host "    ✅ Puerto $Port disponible" -ForegroundColor Green
            return $true
        } else {
            Write-Host "    ❌ Puerto $Port no disponible" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "    ❌ Error de conexión: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Función para verificar dependencias Python
function Test-PythonDependencies {
    param($ServicePath, $ServiceName)
    
    Write-Host "    🔍 Verificando dependencias de $ServiceName..." -ForegroundColor Yellow
    
    if (!(Test-Path "$ServicePath\venv\Scripts\python.exe")) {
        Write-Host "    ❌ No hay entorno virtual" -ForegroundColor Red
        return $false
    }
    
    try {
        # Probar importaciones básicas
        $testCommand = "$ServicePath\venv\Scripts\python.exe -c 'import django, rest_framework, mysqlclient; print(\"OK\")'"
        $result = Invoke-Expression $testCommand 2>$null
        if ($result -eq "OK") {
            Write-Host "    ✅ Dependencias correctas" -ForegroundColor Green
            return $true
        } else {
            Write-Host "    ❌ Faltan dependencias" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "    ❌ Error verificando dependencias: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Función para verificar configuración Django
function Test-DjangoConfig {
    param($ServicePath, $ServiceName, $DBHost, $DBPort, $DBName)
    
    Write-Host "    🔍 Verificando configuración Django de $ServiceName..." -ForegroundColor Yellow
    
    $env:DB_HOST = $DBHost
    $env:DB_PORT = $DBPort
    $env:DB_NAME = $DBName
    $env:DB_USER = "root"
    $env:DB_PASSWORD = "root"
    
    try {
        $checkCommand = "cd '$ServicePath'; venv\Scripts\python.exe manage.py check --deploy"
        $result = Invoke-Expression $checkCommand 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✅ Configuración Django válida" -ForegroundColor Green
            $canStart = $true
        } else {
            Write-Host "    ⚠️ Advertencias en configuración Django" -ForegroundColor Yellow
            $canStart = $true  # Podemos intentar arrancar aunque haya advertencias
        }
    } catch {
        Write-Host "    ❌ Error en configuración Django" -ForegroundColor Red
        $canStart = $false
    }
    
    # Limpiar variables de entorno
    Remove-Item Env:DB_HOST -ErrorAction SilentlyContinue
    Remove-Item Env:DB_PORT -ErrorAction SilentlyContinue
    Remove-Item Env:DB_NAME -ErrorAction SilentlyContinue
    Remove-Item Env:DB_USER -ErrorAction SilentlyContinue
    Remove-Item Env:DB_PASSWORD -ErrorAction SilentlyContinue
    
    return $canStart
}

# Configuración de servicios
$services = @(
    @{Name="auth"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\auth"; Port="3001"; DBPort="3307"; DBName="auth_db"},
    @{Name="users"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\users"; Port="3002"; DBPort="3308"; DBName="users_db"},
    @{Name="asistencia"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\asistencia"; Port="3003"; DBPort="3309"; DBName="asistencia_db"},
    @{Name="documentos"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\documentos"; Port="3004"; DBPort="3310"; DBName="documentos_db"},
    @{Name="pagos"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\pagos"; Port="3005"; DBPort="3311"; DBName="pagos_db"},
    @{Name="reportes"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\reportes"; Port="3006"; DBPort="3312"; DBName="reportes_db"},
    @{Name="auditoria"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\auditoria"; Port="3007"; DBPort="3312"; DBName="auditoria_db"},
    @{Name="gateway"; Path="C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\gateway"; Port="8000"; DBPort="3313"; DBName="gateway_db"}
)

$workingServices = @()
$failedServices = @()

# Diagnóstico completo
foreach ($service in $services) {
    Write-Host "`n" + "="*60 -ForegroundColor Cyan
    Write-Host "🔧 DIAGNÓSTICO: $($service.Name.ToUpper())" -ForegroundColor Cyan
    Write-Host "="*60 -ForegroundColor Cyan
    
    $issues = @()
    $canStart = $true
    
    # 1. Verificar si el path existe
    if (!(Test-Path $service.Path)) {
        Write-Host "❌ Directorio no encontrado: $($service.Path)" -ForegroundColor Red
        $issues += "Directorio no encontrado"
        $canStart = $false
        continue
    }
    
    # 2. Verificar conexión a base de datos
    if (!(Test-DatabaseConnection -Host "localhost" -Port $service.DBPort -Database $service.DBName -User "root" -Password "root")) {
        $issues += "Conexión a base de datos"
        $canStart = $false
    }
    
    # 3. Verificar dependencias Python
    if (!(Test-PythonDependencies -ServicePath $service.Path -ServiceName $service.Name)) {
        $issues += "Dependencias Python"
        $canStart = $false
    }
    
    # 4. Verificar configuración Django
    if ($canStart -and !(Test-DjangoConfig -ServicePath $service.Path -ServiceName $service.Name -DBHost "localhost" -DBPort $service.DBPort -DBName $service.DBName)) {
        $issues += "Configuración Django"
        $canStart = $false
    }
    
    if ($canStart) {
        Write-Host "✅ $($service.Name) - LISTO PARA INICIAR" -ForegroundColor Green
        $workingServices += $service
    } else {
        Write-Host "❌ $($service.Name) - PROBLEMAS DETECTADOS: $($issues -join ', ')" -ForegroundColor Red
        $failedServices += @{Service=$service; Issues=$issues}
    }
}

# Resumen de diagnóstico
Write-Host "`n" + "="*80 -ForegroundColor Magenta
Write-Host "📊 RESUMEN DE DIAGNÓSTICO" -ForegroundColor Magenta
Write-Host "="*80 -ForegroundColor Magenta
Write-Host "✅ Servicios listos: $($workingServices.Count)" -ForegroundColor Green
Write-Host "❌ Servicios con problemas: $($failedServices.Count)" -ForegroundColor Red

if ($workingServices.Count -gt 0) {
    Write-Host "`n🚀 INICIANDO SERVICIOS FUNCIONALES..." -ForegroundColor Green
    
    foreach ($service in $workingServices) {
        Write-Host "`n▶️ Iniciando $($service.Name) en puerto $($service.Port)..." -ForegroundColor Yellow
        
        $startCommand = @"
cd '$($service.Path)'; 
`$env:DB_HOST = 'localhost'; 
`$env:DB_PORT = '$($service.DBPort)'; 
`$env:DB_NAME = '$($service.DBName)'; 
`$env:DB_USER = 'root'; 
`$env:DB_PASSWORD = 'root'; 
venv\Scripts\python.exe manage.py runserver 127.0.0.1:$($service.Port)
"@
        
        Start-Process powershell -ArgumentList "-Command", $startCommand -WindowStyle Minimized
        Start-Sleep -Seconds 3
        
        # Verificar que el servicio responda
        try {
            $testResponse = Invoke-WebRequest -Uri "http://127.0.0.1:$($service.Port)/" -TimeoutSec 5 -ErrorAction Stop
            Write-Host "    ✅ $($service.Name) respondiendo en puerto $($service.Port)" -ForegroundColor Green
        } catch {
            Write-Host "    ⚠️ $($service.Name) iniciado pero no responde aún" -ForegroundColor Yellow
        }
    }
}

if ($failedServices.Count -gt 0) {
    Write-Host "`n🔧 SERVICIOS QUE REQUIEREN REPARACIÓN:" -ForegroundColor Red
    foreach ($failed in $failedServices) {
        Write-Host "- $($failed.Service.Name): $($failed.Issues -join ', ')" -ForegroundColor Red
    }
}

Write-Host "`n🎯 PARA PROBAR LOS SERVICIOS:" -ForegroundColor Cyan
foreach ($service in $workingServices) {
    Write-Host "http://127.0.0.1:$($service.Port)/" -ForegroundColor White
}

Write-Host "`nPresiona cualquier tecla para salir..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")