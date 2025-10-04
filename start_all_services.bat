@echo off
echo ====================================
echo   SISTEMA PONTIFICIA - BACKEND
echo   Iniciando todos los microservicios
echo ====================================

echo.
echo [INFO] Configurando variables de entorno para desarrollo local...
set DB_HOST=localhost
set REDIS_HOST=localhost

echo.
echo [INFO] Iniciando servicio de Autenticacion (Puerto 3001)...
cd /d "%~dp0backend\auth"
call venv\Scripts\activate.bat
set DB_PORT=3307
start "AUTH SERVICE - Puerto 3001" python manage.py runserver 3001

echo.
echo [INFO] Iniciando servicio de Usuarios (Puerto 3002)...
cd /d "%~dp0backend\users"
call ..\auth\venv\Scripts\activate.bat
set DB_PORT=3308
start "USERS SERVICE - Puerto 3002" python manage.py runserver 3002

echo.
echo [INFO] Iniciando servicio de Asistencia (Puerto 3003)...
cd /d "%~dp0backend\asistencia"
call ..\auth\venv\Scripts\activate.bat
set DB_PORT=3309
start "ASISTENCIA SERVICE - Puerto 3003" python manage.py runserver 3003

echo.
echo [INFO] Iniciando servicio de Documentos (Puerto 3004)...
cd /d "%~dp0backend\documentos"
call ..\auth\venv\Scripts\activate.bat
set DB_PORT=3310
start "DOCUMENTOS SERVICE - Puerto 3004" python manage.py runserver 3004

echo.
echo [INFO] Iniciando servicio de Pagos (Puerto 3005)...
cd /d "%~dp0backend\pagos"
call ..\auth\venv\Scripts\activate.bat
set DB_PORT=3311
start "PAGOS SERVICE - Puerto 3005" python manage.py runserver 3005

echo.
echo [INFO] Iniciando servicio de Reportes (Puerto 3006)...
cd /d "%~dp0backend\reportes"
call ..\auth\venv\Scripts\activate.bat
set DB_PORT=3312
start "REPORTES SERVICE - Puerto 3006" python manage.py runserver 3006

echo.
echo [INFO] Iniciando servicio de Auditoria (Puerto 3007)...
cd /d "%~dp0backend\auditoria"
call ..\auth\venv\Scripts\activate.bat
set DB_PORT=3313
start "AUDITORIA SERVICE - Puerto 3007" python manage.py runserver 3007

echo.
echo [INFO] Iniciando Gateway (Puerto 8000)...
cd /d "%~dp0backend\gateway"
call ..\auth\venv\Scripts\activate.bat
start "GATEWAY SERVICE - Puerto 8000" python manage.py runserver 8000

echo.
echo ====================================
echo  TODOS LOS SERVICIOS INICIANDO...
echo ====================================
echo.
echo AUTH Service:      http://localhost:3001
echo USERS Service:     http://localhost:3002  
echo ASISTENCIA Service: http://localhost:3003
echo DOCUMENTOS Service: http://localhost:3004
echo PAGOS Service:     http://localhost:3005
echo REPORTES Service:  http://localhost:3006
echo AUDITORIA Service: http://localhost:3007
echo GATEWAY Service:   http://localhost:8000
echo.
echo Presiona cualquier tecla para cerrar este script...
pause > nul