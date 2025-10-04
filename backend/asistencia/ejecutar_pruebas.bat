@echo off
echo Activando entorno virtual y ejecutando pruebas...
cd /d "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\asistencia"
call "C:\Users\Fray Luis\Desktop\sistemaPontificia\backend\auth\venv\Scripts\activate.bat"
python test_completo.py
pause