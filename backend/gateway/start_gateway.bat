@echo off
REM Script de inicio para API Gateway - Sistema Pontificia (Windows)
REM start_gateway.bat

setlocal EnableDelayedExpansion

REM Configuración
set GATEWAY_DIR=%~dp0
set VENV_DIR=%GATEWAY_DIR%venv
set PYTHON_EXECUTABLE=%VENV_DIR%\Scripts\python.exe
set PIP_EXECUTABLE=%VENV_DIR%\Scripts\pip.exe
set MANAGE_PY=%GATEWAY_DIR%manage.py
set REQUIREMENTS_FILE=%GATEWAY_DIR%requirements.txt
if "%GATEWAY_PORT%"=="" set GATEWAY_PORT=8000
if "%GATEWAY_HOST%"=="" set GATEWAY_HOST=127.0.0.1

echo === Sistema Pontificia - API Gateway Startup ===
echo Gateway Directory: %GATEWAY_DIR%
echo Port: %GATEWAY_PORT%
echo Host: %GATEWAY_HOST%
echo.

REM Verificar si estamos en el directorio correcto
if not exist "%MANAGE_PY%" (
    echo [ERROR] manage.py not found. Make sure you're in the gateway directory.
    pause
    exit /b 1
)

REM Crear entorno virtual si no existe
if not exist "%VENV_DIR%" (
    echo [INFO] Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

REM Activar entorno virtual
echo [INFO] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

REM Actualizar pip
echo [INFO] Updating pip...
"%PIP_EXECUTABLE%" install --upgrade pip

REM Instalar dependencias
if exist "%REQUIREMENTS_FILE%" (
    echo [INFO] Installing requirements...
    "%PIP_EXECUTABLE%" install -r "%REQUIREMENTS_FILE%"
) else (
    echo [WARNING] requirements.txt not found. Installing basic dependencies...
    "%PIP_EXECUTABLE%" install django djangorestframework drf-spectacular djangorestframework-simplejwt django-cors-headers django-ratelimit redis requests httpx
)

REM Verificar Redis (opcional en Windows)
echo [INFO] Checking Redis connection...
redis-cli ping >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Redis is not running. Some features may not work properly.
    echo [WARNING] To start Redis on Windows, run: redis-server
)

REM Ejecutar migraciones
echo [INFO] Running database migrations...
"%PYTHON_EXECUTABLE%" "%MANAGE_PY%" makemigrations --noinput
"%PYTHON_EXECUTABLE%" "%MANAGE_PY%" migrate --noinput

REM Recoger archivos estáticos
echo [INFO] Collecting static files...
"%PYTHON_EXECUTABLE%" "%MANAGE_PY%" collectstatic --noinput --clear

REM Verificar configuración
echo [INFO] Checking Django configuration...
"%PYTHON_EXECUTABLE%" "%MANAGE_PY%" check

REM Verificar conectividad a microservicios
echo [INFO] Testing microservice connections...
set SERVICES=auditoria:8001 auth:8002 users:8003 academic:8004 students:8005 courses:8006 reports:8007

for %%s in (%SERVICES%) do (
    for /f "tokens=1,2 delims=:" %%a in ("%%s") do (
        netstat -an | find "127.0.0.1:%%b" >nul 2>&1
        if !errorlevel! equ 0 (
            echo   [OK] %%a service ^(port %%b^) is reachable
        ) else (
            echo   [WARNING] %%a service ^(port %%b^) is not reachable
        )
    )
)

REM Mostrar información del sistema
echo [INFO] System Information:
"%PYTHON_EXECUTABLE%" --version
"%PYTHON_EXECUTABLE%" -c "import django; print('  Django:', django.get_version())"
"%PYTHON_EXECUTABLE%" -c "import rest_framework; print('  DRF:', rest_framework.VERSION)" 2>nul || echo   DRF: Not installed

REM Verificar archivo de configuración
if exist "%GATEWAY_DIR%gateway\settings.py" (
    echo [INFO] Configuration file found
) else (
    echo [ERROR] Configuration file not found
    pause
    exit /b 1
)

REM Mostrar URLs importantes
echo [INFO] Important URLs:
echo   Gateway Root: http://%GATEWAY_HOST%:%GATEWAY_PORT%/
echo   Health Check: http://%GATEWAY_HOST%:%GATEWAY_PORT%/health/
echo   API Documentation: http://%GATEWAY_HOST%:%GATEWAY_PORT%/api/docs/
echo   Custom Docs: http://%GATEWAY_HOST%:%GATEWAY_PORT%/docs/
echo   Admin: http://%GATEWAY_HOST%:%GATEWAY_PORT%/admin/
echo.

echo [INFO] Starting Django development server...
echo Press Ctrl+C to stop the server
echo.

REM Iniciar el servidor
"%PYTHON_EXECUTABLE%" "%MANAGE_PY%" runserver %GATEWAY_HOST%:%GATEWAY_PORT%

pause