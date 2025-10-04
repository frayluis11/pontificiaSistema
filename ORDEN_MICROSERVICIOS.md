# 🚀 ORDEN DE EJECUCIÓN DE MICROSERVICIOS - SISTEMA PONTIFICIA

## 📋 **ORDEN RECOMENDADO DE INICIO**

### 🏗️ **FASE 1: INFRAESTRUCTURA (Primero)**
```powershell
# 1. Iniciar bases de datos
cd ../infra
docker-compose up -d
# Esperar 30-45 segundos para inicialización completa
```

### 🔐 **FASE 2: SERVICIOS CORE (Segundo)**
```powershell
cd ../backend

# 2. AUTH SERVICE (Puerto 3001) - PRIMERO SIEMPRE
cd auth
python manage.py runserver 3001
# Esperar 10-15 segundos

# 3. USERS SERVICE (Puerto 3002) - Depende de AUTH
cd ../users  
python manage.py runserver 3002
# Esperar 10-15 segundos
```

### 🔧 **FASE 3: SERVICIOS DE NEGOCIO (Tercero)**
```powershell
# 4. ASISTENCIA SERVICE (Puerto 3003)
cd ../asistencia
python manage.py runserver 3003
# Esperar 10-15 segundos

# 5. DOCUMENTOS SERVICE (Puerto 3004)
cd ../documentos
python manage.py runserver 3004
# Esperar 10-15 segundos

# 6. PAGOS SERVICE (Puerto 3005)
cd ../pagos
python manage.py runserver 3005
# Esperar 10-15 segundos
```

### 📊 **FASE 4: SERVICIOS DE SOPORTE (Cuarto)**
```powershell
# 7. REPORTES SERVICE (Puerto 3006) - Necesita datos de otros servicios
cd ../reportes
python manage.py runserver 3006
# Esperar 10-15 segundos

# 8. AUDITORIA SERVICE (Puerto 3007) - Monitorea todos los servicios
cd ../auditoria
python manage.py runserver 3007
# Esperar 10-15 segundos
```

### 🌐 **FASE 5: GATEWAY (Último)**
```powershell
# 9. GATEWAY (Puerto 8000) - ÚLTIMO SIEMPRE
cd ../gateway
python manage.py runserver 8000
# Esperar 15-20 segundos
```

---

## 🔗 **EXPLICACIÓN DE DEPENDENCIAS**

### 🏛️ **Arquitectura de Dependencias:**
```
                    🗄️ BASES DE DATOS
                           ↓
                    🔐 AUTH SERVICE (3001)
                           ↓
                    👥 USERS SERVICE (3002)
                           ↓
         ┌─────────────────┼─────────────────┐
         ↓                 ↓                 ↓
   📋 ASISTENCIA      📄 DOCUMENTOS      💰 PAGOS
     (3003)            (3004)            (3005)
         ↓                 ↓                 ↓
         └─────────────────┼─────────────────┘
                           ↓
                    📊 REPORTES (3006)
                           ↓
                    🔍 AUDITORIA (3007)
                           ↓
                    🌐 GATEWAY (8000)
```

### 🎯 **¿POR QUÉ ESTE ORDEN?**

1. **🔐 AUTH PRIMERO**: Todos los demás servicios necesitan autenticación JWT
2. **👥 USERS SEGUNDO**: Gestiona perfiles y validaciones de usuarios
3. **📋📄💰 SERVICIOS DE NEGOCIO**: Operan independientemente entre sí
4. **📊 REPORTES**: Necesita datos de asistencia, documentos y pagos
5. **🔍 AUDITORIA**: Monitorea y registra actividad de todos los servicios
6. **🌐 GATEWAY ÚLTIMO**: Enruta peticiones a todos los servicios ya iniciados

---

## ⚡ **SCRIPT AUTOMATIZADO**

### 📋 **Script PowerShell Completo:**
```powershell
# Script para iniciar sistema completo en orden correcto
Write-Host "🚀 INICIANDO SISTEMA PONTIFICIA EN ORDEN CORRECTO" -ForegroundColor Green

# Fase 1: Infraestructura
Write-Host "🗄️ FASE 1: Iniciando bases de datos..." -ForegroundColor Yellow
Set-Location "../infra"
docker-compose up -d
Start-Sleep -Seconds 45

# Fase 2: Servicios Core
Write-Host "🔐 FASE 2: Iniciando servicios core..." -ForegroundColor Yellow
Set-Location "../backend"

Write-Host "Iniciando AUTH..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'auth'; python manage.py runserver 3001" -WindowStyle Minimized
Start-Sleep -Seconds 15

Write-Host "Iniciando USERS..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'users'; python manage.py runserver 3002" -WindowStyle Minimized
Start-Sleep -Seconds 15

# Fase 3: Servicios de Negocio
Write-Host "🔧 FASE 3: Iniciando servicios de negocio..." -ForegroundColor Yellow

Write-Host "Iniciando ASISTENCIA..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'asistencia'; python manage.py runserver 3003" -WindowStyle Minimized
Start-Sleep -Seconds 15

Write-Host "Iniciando DOCUMENTOS..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'documentos'; python manage.py runserver 3004" -WindowStyle Minimized
Start-Sleep -Seconds 15

Write-Host "Iniciando PAGOS..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'pagos'; python manage.py runserver 3005" -WindowStyle Minimized
Start-Sleep -Seconds 15

# Fase 4: Servicios de Soporte
Write-Host "📊 FASE 4: Iniciando servicios de soporte..." -ForegroundColor Yellow

Write-Host "Iniciando REPORTES..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'reportes'; python manage.py runserver 3006" -WindowStyle Minimized
Start-Sleep -Seconds 15

Write-Host "Iniciando AUDITORIA..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'auditoria'; python manage.py runserver 3007" -WindowStyle Minimized
Start-Sleep -Seconds 15

# Fase 5: Gateway
Write-Host "🌐 FASE 5: Iniciando gateway..." -ForegroundColor Yellow
Write-Host "Iniciando GATEWAY..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'gateway'; python manage.py runserver 8000" -WindowStyle Minimized
Start-Sleep -Seconds 20

Write-Host "✅ SISTEMA INICIADO COMPLETAMENTE" -ForegroundColor Green
Write-Host "Esperando estabilización final..." -ForegroundColor Cyan
Start-Sleep -Seconds 30
```

---

## 🚨 **ERRORES COMUNES Y SOLUCIONES**

### ❌ **Si un servicio no inicia:**
1. **Verificar que el anterior** esté funcionando
2. **Instalar dependencias faltantes** (cryptography, etc.)
3. **Ejecutar migraciones** si es necesario
4. **Verificar conexión a base de datos**

### ✅ **Orden de verificación:**
```powershell
# Verificar en orden
curl http://localhost:3001  # AUTH
curl http://localhost:3002  # USERS  
curl http://localhost:3003  # ASISTENCIA
curl http://localhost:3004  # DOCUMENTOS
curl http://localhost:3005  # PAGOS
curl http://localhost:3006  # REPORTES
curl http://localhost:3007  # AUDITORIA
curl http://localhost:8000  # GATEWAY
```

---

## 🎯 **RESUMEN**

**⚡ ORDEN CRÍTICO:**
1. 🗄️ **Bases de datos** (infra)
2. 🔐 **AUTH** (3001)
3. 👥 **USERS** (3002)
4. 📋📄💰 **Servicios de negocio** (3003-3005)
5. 📊 **REPORTES** (3006)
6. 🔍 **AUDITORIA** (3007)
7. 🌐 **GATEWAY** (8000)

**⏰ TIEMPOS RECOMENDADOS:**
- Bases de datos: **45 segundos**
- Cada servicio: **15 segundos**
- Gateway: **20 segundos**
- Estabilización final: **30 segundos**

¡Este orden asegura que las dependencias se resuelvan correctamente! 🚀