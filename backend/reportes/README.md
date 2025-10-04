# Microservicio de Reportes

Este microservicio maneja la generación, gestión y exportación de reportes del Sistema Pontificia. Está construido con Django 4.2.7, Django REST Framework, MySQL, y Celery para procesamiento asíncrono.

## 🏗️ Arquitectura

### Componentes Principales

- **Django 4.2.7**: Framework web principal
- **Django REST Framework**: API REST
- **MySQL**: Base de datos (puerto 3312)
- **Celery + Redis**: Procesamiento asíncrono
- **ReportLab**: Generación de PDFs
- **openpyxl**: Generación de Excel
- **matplotlib/seaborn**: Gráficos y visualizaciones

### Patrones de Diseño

- **Repository Pattern**: Abstracción de acceso a datos
- **Service Layer**: Lógica de negocio
- **DTO (Data Transfer Objects)**: Transferencia de datos
- **Factory Pattern**: Creación de reportes

## 🚀 Configuración y Instalación

### Prerrequisitos

- Python 3.9+
- MySQL 8.0+
- Redis 6.0+
- Node.js (opcional, para frontend)

### Instalación

1. **Clonar y configurar entorno**:
```bash
cd backend/reportes
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configurar base de datos MySQL**:
```sql
CREATE DATABASE reportes_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'reportes_user'@'localhost' IDENTIFIED BY 'reportes_password';
GRANT ALL PRIVILEGES ON reportes_db.* TO 'reportes_user'@'localhost';
FLUSH PRIVILEGES;
```

3. **Configurar variables de entorno**:
```bash
# .env
DEBUG=True
SECRET_KEY=tu-secret-key-aqui
DB_NAME=reportes_db
DB_USER=reportes_user
DB_PASSWORD=reportes_password
DB_HOST=localhost
DB_PORT=3312
REDIS_URL=redis://localhost:6379/0
```

4. **Ejecutar migraciones**:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

5. **Iniciar servicios**:
```bash
# Terminal 1: Django
python manage.py runserver 0.0.0.0:3006

# Terminal 2: Celery Worker
celery -A reportes_service worker -l info

# Terminal 3: Celery Beat (tareas programadas)
celery -A reportes_service beat -l info
```

## 📊 Modelos de Datos

### Reporte
```python
{
    "id": "uuid",
    "tipo": "ventas|usuarios|metricas|financiero|academico|asistencia|calificaciones|personalizado",
    "formato": "pdf|excel|csv",
    "estado": "pendiente|procesando|completado|error|expirado",
    "titulo": "string",
    "parametros": "json",
    "autor_id": "integer",
    "archivo": "file",
    "fecha_creacion": "datetime",
    "fecha_actualizacion": "datetime",
    "expires_at": "datetime"
}
```

### Métrica
```python
{
    "id": "integer",
    "nombre": "string",
    "valor": "float",
    "periodo": "diario|semanal|mensual|anual",
    "fecha_calculo": "datetime",
    "metadatos": "json",
    "activa": "boolean"
}
```

### ReporteMetrica
```python
{
    "reporte": "foreign_key",
    "metrica": "foreign_key",
    "incluida": "boolean"
}
```

## 🔌 API Endpoints

### Reportes

#### Generar Reporte
```http
POST /api/reportes/generar/
Content-Type: application/json

{
    "tipo": "ventas",
    "formato": "pdf",
    "titulo": "Reporte de Ventas Q1",
    "parametros": {
        "fecha_inicio": "2024-01-01",
        "fecha_fin": "2024-03-31",
        "incluir_graficos": true,
        "nivel_detalle": "detallado"
    },
    "asincrono": true,
    "notificar_completado": false
}
```

**Respuesta**:
```json
{
    "success": true,
    "message": "Reporte iniciado correctamente",
    "reporte_id": "550e8400-e29b-41d4-a716-446655440000",
    "estado": "pendiente",
    "url_seguimiento": "/api/reportes/550e8400-e29b-41d4-a716-446655440000/",
    "tiempo_estimado": 30
}
```

#### Listar Reportes
```http
GET /api/reportes/listar/?tipo=ventas&estado=completado&page=1&page_size=20
```

#### Obtener Estado de Reporte
```http
GET /api/reportes/550e8400-e29b-41d4-a716-446655440000/estado/
```

#### Descargar Reporte
```http
GET /api/reportes/550e8400-e29b-41d4-a716-446655440000/descargar/
```

### Métricas

#### Listar Métricas
```http
GET /api/metricas/?nombre=ventas&periodo=mensual
```

#### Exportar Métricas
```http
POST /api/metricas/exportar/
Content-Type: application/json

{
    "nombres": ["ventas_totales", "usuarios_activos"],
    "periodo": "mensual",
    "fecha_desde": "2024-01-01",
    "fecha_hasta": "2024-12-31",
    "formato": "excel",
    "incluir_graficos": true,
    "solo_activas": true
}
```

#### Resumen de Métricas
```http
GET /api/metricas/resumen/?periodo=mensual
```

### Estadísticas

#### Estadísticas de Reportes
```http
GET /api/estadisticas/
```

**Respuesta**:
```json
{
    "total_reportes": 150,
    "reportes_completados": 145,
    "reportes_pendientes": 3,
    "reportes_error": 2,
    "tiempo_promedio_procesamiento": 45.2,
    "porcentaje_completados": 96.67,
    "tipos_mas_solicitados": [
        {"tipo": "ventas", "cantidad": 45},
        {"tipo": "usuarios", "cantidad": 32}
    ],
    "formatos_preferidos": {
        "pdf": 85,
        "excel": 55,
        "csv": 10
    }
}
```

## 🔧 Servicios

### ReporteService

Maneja la lógica de negocio para reportes:

```python
from reportes_app.services import ReporteService

service = ReporteService()

# Generar reporte asíncrono
reporte = service.generar_reporte_async(
    tipo='ventas',
    formato='pdf',
    parametros={'fecha_inicio': '2024-01-01'},
    autor_id=user.id
)

# Generar reporte síncrono
reporte = service.generar_reporte_sync(
    tipo='usuarios',
    formato='excel',
    parametros={},
    autor_id=user.id
)
```

### MetricaService

Maneja métricas y cálculos:

```python
from reportes_app.services import MetricaService

service = MetricaService()

# Crear métrica
metrica = service.crear_metrica(
    nombre='ventas_mensuales',
    valor=15000.0,
    periodo='mensual'
)

# Calcular tendencia
tendencia = service.calcular_tendencia('ventas_mensuales', 'mensual')
```

## 📋 Tareas Asíncronas (Celery)

### Tareas Disponibles

- `procesar_reporte_async`: Procesa reportes de forma asíncrona
- `calcular_metricas_periodicas`: Calcula métricas del sistema
- `limpiar_reportes_expirados`: Limpia reportes expirados
- `generar_reporte_programado`: Genera reportes programados
- `exportar_metricas_async`: Exporta métricas de forma asíncrona

### Configuración de Tareas Periódicas

```python
# En settings.py
CELERY_BEAT_SCHEDULE = {
    'calcular-metricas-diarias': {
        'task': 'reportes_app.tasks.calcular_metricas_periodicas',
        'schedule': crontab(hour=1, minute=0),  # Diario a las 1:00 AM
    },
    'limpiar-reportes-expirados': {
        'task': 'reportes_app.tasks.limpiar_reportes_expirados',
        'schedule': crontab(hour=2, minute=0),  # Diario a las 2:00 AM
    },
}
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
python manage.py test

# Tests específicos
python manage.py test reportes_app.tests.ReporteModelTest
python manage.py test reportes_app.tests.ReporteAPITest

# Con coverage
pip install coverage
coverage run manage.py test
coverage report
coverage html
```

### Tipos de Tests

- **Tests de Modelos**: Validación de modelos y relaciones
- **Tests de Repositorios**: Lógica de acceso a datos
- **Tests de Servicios**: Lógica de negocio
- **Tests de API**: Endpoints REST
- **Tests de Integración**: Flujos completos
- **Tests de Performance**: Optimización de consultas

## 📈 Monitoreo y Logging

### Configuración de Logs

Los logs se configuran en `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/reportes.log',
        },
    },
    'loggers': {
        'reportes_app': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

### Health Check

```http
GET /api/health/
```

**Respuesta**:
```json
{
    "status": "healthy",
    "timestamp": "2024-10-02T10:30:00Z",
    "database": "connected",
    "celery": "activo",
    "version": "1.0.0"
}
```

## 🔐 Seguridad

### Autenticación

- JWT tokens para autenticación
- Permisos basados en usuario
- Validación de permisos por reporte

### Validaciones

- Validación de parámetros de entrada
- Sanitización de datos
- Límites de tamaño de archivo
- Expiración automática de reportes

## 🚀 Despliegue

### Docker

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 3006

CMD ["gunicorn", "--bind", "0.0.0.0:3006", "reportes_service.wsgi:application"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  reportes:
    build: .
    ports:
      - "3006:3006"
    environment:
      - DEBUG=False
      - DB_HOST=mysql
    depends_on:
      - mysql
      - redis

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: reportes_db
    ports:
      - "3312:3306"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  celery:
    build: .
    command: celery -A reportes_service worker -l info
    depends_on:
      - mysql
      - redis
```

## 📚 Ejemplos de Uso

### Generar Reporte de Ventas

```python
import requests

# Autenticación
headers = {'Authorization': 'Bearer your-jwt-token'}

# Generar reporte
response = requests.post('http://localhost:3006/api/reportes/generar/', 
    headers=headers,
    json={
        'tipo': 'ventas',
        'formato': 'pdf',
        'titulo': 'Ventas Q1 2024',
        'parametros': {
            'fecha_inicio': '2024-01-01',
            'fecha_fin': '2024-03-31',
            'incluir_graficos': True,
            'nivel_detalle': 'detallado'
        }
    }
)

reporte_id = response.json()['reporte_id']

# Verificar estado
status_response = requests.get(f'http://localhost:3006/api/reportes/{reporte_id}/estado/', 
    headers=headers
)

# Descargar cuando esté listo
if status_response.json()['estado'] == 'completado':
    download_response = requests.get(f'http://localhost:3006/api/reportes/{reporte_id}/descargar/', 
        headers=headers
    )
    with open('reporte_ventas.pdf', 'wb') as f:
        f.write(download_response.content)
```

## 🔄 Integración con Otros Microservicios

### Consumir APIs Externas

```python
# En services.py
import requests
from django.conf import settings

class ReporteService:
    def obtener_datos_ventas(self, fecha_inicio, fecha_fin):
        """Obtener datos del microservicio de ventas"""
        url = f"{settings.VENTAS_SERVICE_URL}/api/ventas/"
        params = {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }
        response = requests.get(url, params=params)
        return response.json()
```

## 🐛 Troubleshooting

### Problemas Comunes

1. **Error de conexión a MySQL**:
   - Verificar que MySQL esté ejecutándose en puerto 3312
   - Revisar credenciales en settings.py

2. **Celery no procesa tareas**:
   - Verificar que Redis esté ejecutándose
   - Comprobar configuración de CELERY_BROKER_URL

3. **Reportes no se generan**:
   - Verificar logs en `logs/reportes.log`
   - Comprobar permisos de archivos

4. **Error de memoria en reportes grandes**:
   - Ajustar configuración de Celery
   - Implementar paginación en consultas

### Logs Importantes

```bash
# Logs de Django
tail -f logs/reportes.log

# Logs de Celery
celery -A reportes_service events

# Logs de MySQL
tail -f /var/log/mysql/error.log
```

## 📝 Changelog

### v1.0.0 (2024-10-02)
- ✨ Implementación inicial del microservicio
- 🔧 Configuración de Django, MySQL y Celery
- 📊 Modelos de Reporte, Métrica y ReporteMetrica
- 🏗️ Patrón Repository y Service Layer
- 🔌 API REST completa con DRF
- 📋 Tareas asíncronas con Celery
- 🧪 Suite completa de tests
- 📚 Documentación completa

## 🤝 Contribución

1. Fork el proyecto
2. Crear branch para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver archivo [LICENSE](LICENSE) para detalles.

## 👥 Equipo

- **Desarrollador Principal**: Sistema Pontificia Team
- **Arquitectura**: Microservicios con Django
- **Contacto**: dev@sistemapontificia.com

---

**Sistema Pontificia - Microservicio de Reportes v1.0.0**