# Microservicio de Pagos - Sistema Pontificia

Sistema de gestión de pagos, planillas y adelantos para el sistema de la Universidad Pontificia.

## 🏗️ Arquitectura

El microservicio está construido usando patrones de diseño empresariales:

- **Repository Pattern**: Para abstracción de datos
- **Strategy Pattern**: Para cálculos de descuentos y bonificaciones  
- **Service Layer**: Para lógica de negocio
- **Factory Pattern**: Para creación de estrategias de cálculo

## 📋 Funcionalidades

### ✅ Gestión de Pagos
- Cálculo automático de pagos con descuentos y bonificaciones
- Estados: CALCULADO → APROBADO → PAGADO → ANULADO
- Validaciones de negocio y auditoría completa

### ✅ Planillas de Pagos
- Generación automática de planillas mensuales
- Aprobación y procesamiento por lotes
- Exportación a Excel para reportes

### ✅ Boletas de Pago
- Generación individual o masiva de boletas
- Exportación a PDF con formato profesional
- Envío automático por email

### ✅ Adelantos de Sueldo
- Solicitud y aprobación de adelantos
- Flujo completo: PENDIENTE → APROBADO/RECHAZADO → PAGADO
- Validaciones de montos y fechas límite

### ✅ Sistema de Descuentos y Bonificaciones
- Descuentos obligatorios (EsSalud, ONP, etc.)
- Bonificaciones configurables
- Cálculo automático por porcentaje o monto fijo

## 🔧 Tecnologías

- **Django 4.2.7**: Framework web
- **Django REST Framework**: APIs REST
- **MySQL**: Base de datos (puerto 3311)
- **ReportLab**: Generación de PDFs
- **openpyxl**: Reportes Excel
- **Celery**: Tareas asíncronas

## 📡 API Endpoints

### 🔐 Autenticación
Todos los endpoints requieren autenticación JWT.

### 💰 Pagos
```
GET    /api/v1/pagos/                    # Listar pagos
POST   /api/v1/pagos/                    # Crear pago
GET    /api/v1/pagos/{id}/               # Obtener pago
PUT    /api/v1/pagos/{id}/               # Actualizar pago
PATCH  /api/v1/pagos/{id}/               # Actualizar parcial
DELETE /api/v1/pagos/{id}/               # Eliminar pago
POST   /api/v1/pagos/{id}/aprobar/       # Aprobar pago
POST   /api/v1/pagos/{id}/marcar_pagado/ # Marcar como pagado
POST   /api/v1/pagos/{id}/anular/        # Anular pago
GET    /api/v1/pagos/estadisticas/       # Estadísticas
GET    /api/v1/pagos/por_trabajador/     # Pagos por trabajador
```

### 📋 Planillas
```
GET    /api/v1/planillas/                     # Listar planillas
POST   /api/v1/planillas/                     # Crear planilla
GET    /api/v1/planillas/{id}/                # Obtener planilla
PUT    /api/v1/planillas/{id}/                # Actualizar planilla
PATCH  /api/v1/planillas/{id}/                # Actualizar parcial
DELETE /api/v1/planillas/{id}/                # Eliminar planilla
POST   /api/v1/planillas/generar_planilla/    # Generar planilla completa
POST   /api/v1/planillas/{id}/aprobar/        # Aprobar planilla
GET    /api/v1/planillas/{id}/pagos/          # Pagos de planilla
GET    /api/v1/planillas/{id}/exportar_excel/ # Exportar Excel
GET    /api/v1/planillas/estadisticas_anuales/ # Estadísticas anuales
```

### 🧾 Boletas
```
GET    /api/v1/boletas/                   # Listar boletas
POST   /api/v1/boletas/                   # Crear boleta
GET    /api/v1/boletas/{id}/              # Obtener boleta
PUT    /api/v1/boletas/{id}/              # Actualizar boleta
PATCH  /api/v1/boletas/{id}/              # Actualizar parcial
DELETE /api/v1/boletas/{id}/              # Eliminar boleta
POST   /api/v1/boletas/generar_boleta/    # Generar boleta individual
GET    /api/v1/boletas/{id}/descargar_pdf/ # Descargar PDF
POST   /api/v1/boletas/{id}/enviar_email/ # Enviar por email
POST   /api/v1/boletas/generar_masivo/    # Generar boletas masivas
```

### 💸 Adelantos
```
GET    /api/v1/adelantos/                # Listar adelantos
POST   /api/v1/adelantos/                # Crear adelanto
GET    /api/v1/adelantos/{id}/           # Obtener adelanto
PUT    /api/v1/adelantos/{id}/           # Actualizar adelanto
PATCH  /api/v1/adelantos/{id}/           # Actualizar parcial
DELETE /api/v1/adelantos/{id}/           # Eliminar adelanto
POST   /api/v1/adelantos/{id}/aprobar/   # Aprobar adelanto
POST   /api/v1/adelantos/{id}/rechazar/  # Rechazar adelanto
POST   /api/v1/adelantos/{id}/marcar_pagado/ # Marcar como pagado
GET    /api/v1/adelantos/por_trabajador/ # Adelantos por trabajador
GET    /api/v1/adelantos/estadisticas/   # Estadísticas
```

### ⚙️ Configuración
```
GET    /api/v1/descuentos/     # Gestión de descuentos
GET    /api/v1/bonificaciones/ # Gestión de bonificaciones
```

## 🔍 Filtros y Búsqueda

### Filtros Comunes
- `?search=texto` - Búsqueda por nombre, documento
- `?ordering=campo` - Ordenación ascendente
- `?ordering=-campo` - Ordenación descendente
- `?page=1&page_size=20` - Paginación

### Filtros Específicos

#### Pagos
```
?estado=CALCULADO,APROBADO,PAGADO,ANULADO
?planilla__año=2024
?planilla__mes=1
?trabajador_id=123
?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
?monto_min=1000&monto_max=5000
```

#### Planillas
```
?año=2024
?mes=1
?procesada=true
?aprobada=true
```

#### Adelantos
```
?estado=PENDIENTE,APROBADO,RECHAZADO,PAGADO
?trabajador_id=123
?solo_pendientes=true
?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
```

## 📊 Modelos de Datos

### Pago
```python
- id: UUID
- trabajador_id: String
- trabajador_nombre: String  
- trabajador_documento: String
- planilla: ForeignKey
- monto_bruto: Decimal
- monto_descuentos: Decimal (calculado)
- monto_bonificaciones: Decimal (calculado)
- monto_neto: Decimal (calculado)
- estado: Choice (CALCULADO, APROBADO, PAGADO, ANULADO)
- fecha_calculo: DateTime
- fecha_aprobacion: DateTime
- fecha_pago: DateTime
```

### Planilla  
```python
- id: UUID
- nombre: String
- año: Integer
- mes: Integer  
- procesada: Boolean
- aprobada: Boolean
- fecha_procesamiento: DateTime
- fecha_aprobacion: DateTime
- total_pagos: Integer (calculado)
- total_monto: Decimal (calculado)
```

### Boleta
```python
- id: UUID
- pago: OneToOne
- fecha_generacion: DateTime
- archivo_pdf: BinaryField
```

### Adelanto
```python
- id: UUID
- trabajador_id: String
- trabajador_nombre: String
- trabajador_documento: String  
- monto: Decimal
- motivo: Text
- estado: Choice (PENDIENTE, APROBADO, RECHAZADO, PAGADO)
- fecha_solicitud: DateTime
- fecha_limite_pago: Date
- fecha_aprobacion: DateTime
- fecha_pago: DateTime
- observaciones: Text
```

### Descuento
```python
- id: UUID
- nombre: String
- descripcion: Text
- tipo: Choice (PORCENTAJE, MONTO_FIJO)
- porcentaje: Decimal
- monto_fijo: Decimal
- obligatorio: Boolean
```

### Bonificacion
```python
- id: UUID  
- nombre: String
- descripcion: Text
- tipo: Choice (PORCENTAJE, MONTO_FIJO)
- porcentaje: Decimal
- monto_fijo: Decimal
- imponible: Boolean
```

## 🚀 Instalación y Configuración

### 1. Clonar y preparar entorno
```bash
cd backend/pagos
pip install -r requirements.txt
```

### 2. Configurar base de datos
```bash
# Asegurarse que MySQL esté corriendo en puerto 3311
# Crear base de datos 'pagos_db'

python manage.py makemigrations
python manage.py migrate
```

### 3. Crear superusuario
```bash
python manage.py createsuperuser
```

### 4. Ejecutar servidor
```bash
python manage.py runserver 0.0.0.0:3005
```

## 🧪 Testing

```bash
# Ejecutar todas las pruebas
python manage.py test

# Ejecutar pruebas específicas
python manage.py test pagos_app.tests.test_models
python manage.py test pagos_app.tests.test_services  
python manage.py test pagos_app.tests.test_api
```

## 📈 Monitoreo

### Logs
Los logs se configuran en `settings.py`:
- INFO: Operaciones normales
- WARNING: Validaciones fallidas
- ERROR: Errores de sistema
- DEBUG: Información detallada

### Métricas
- Número de pagos procesados
- Tiempo promedio de cálculo
- Errores por endpoint
- Uso de memoria y CPU

## 🔒 Seguridad

- Autenticación JWT requerida
- Validación de permisos por endpoint
- Sanitización de inputs
- Logs de auditoría
- Encriptación de datos sensibles

## 🐳 Docker

```dockerfile
# El Dockerfile está configurado para:
FROM python:3.11-slim
EXPOSE 3005
WORKDIR /app
# Instalación automática de dependencias
# Configuración de MySQL
# Variables de entorno
```

## 📚 Dependencias Principales

```txt
Django==4.2.7
djangorestframework==3.14.0
mysqlclient==2.2.0
python-decouple==3.8
reportlab==4.0.7
openpyxl==3.1.2
celery==5.3.4
redis==5.0.1
```

## 🤝 Contribución

1. Fork del repositorio
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto es parte del Sistema Pontificia y está bajo licencia privada.

## 👥 Equipo

- **Desarrollador Principal**: [Tu nombre]
- **Arquitecto de Software**: [Nombre]
- **QA/Testing**: [Nombre]

## 📞 Soporte

Para reportar problemas o solicitar funcionalidades:
- Email: soporte@pontificia.edu.pe
- Issues: GitHub Issues
- Documentación: Wiki del repositorio

---

**Estado**: ✅ **COMPLETADO** - Microservicio listo para producción

**Última actualización**: Diciembre 2024