# Microservicio de Gestión de Documentos - Sistema Pontificia

## 📋 Descripción

Este microservicio proporciona una solución completa para la gestión de documentos en el Sistema Pontificia. Incluye funcionalidades para el manejo de documentos, versionado, sistema de solicitudes, flujos de trabajo y notificaciones automáticas.

## 🏗️ Arquitectura

El sistema está construido con **Django 4.2.7** y sigue una arquitectura por capas con patrones de diseño:

### Patrones Implementados
- **Factory Pattern**: Para la generación de documentos y código
- **Observer Pattern**: Para el sistema de notificaciones
- **Repository Pattern**: Para la abstracción de datos
- **Service Layer**: Para la lógica de negocio

### Estructura del Proyecto
```
backend/documentos/
├── documentos/              # Configuración principal del proyecto
│   ├── __init__.py
│   ├── settings.py         # Configuración de Django
│   ├── urls.py            # URLs principales
│   └── wsgi.py
├── documentos_app/         # Aplicación principal
│   ├── models.py          # Modelos de datos
│   ├── views.py           # Vistas de la API REST
│   ├── serializers.py     # Serializadores DRF
│   ├── services.py        # Lógica de negocio
│   ├── repositories.py    # Capa de datos
│   ├── observers.py       # Patrón Observer
│   ├── factories.py       # Patrón Factory
│   ├── utils.py           # Utilidades
│   ├── admin.py           # Interfaz de administración
│   ├── tests.py           # Pruebas unitarias
│   └── urls.py            # URLs de la aplicación
├── api_docs.py            # Documentación de API
├── requirements.txt       # Dependencias
└── README.md             # Este archivo
```

## 🚀 Características Principales

### Gestión de Documentos
- ✅ CRUD completo de documentos
- ✅ Versionado automático
- ✅ Clasificación por tipos (Académico, Administrativo, Legal, etc.)
- ✅ Estados de flujo de trabajo (Borrador, Revisión, Aprobado, Rechazado)
- ✅ Subida y descarga de archivos
- ✅ Búsqueda y filtrado avanzado

### Sistema de Solicitudes
- ✅ Solicitudes de acceso a documentos
- ✅ Flujo de aprobación/rechazo
- ✅ Seguimiento de solicitudes
- ✅ Notificaciones automáticas

### Control de Versiones
- ✅ Historial completo de versiones
- ✅ Comentarios por versión
- ✅ Comparación entre versiones
- ✅ Restauración de versiones anteriores

### Flujos de Trabajo
- ✅ Definición de flujos personalizados
- ✅ Pasos configurables
- ✅ Condiciones y reglas de negocio
- ✅ Auditoría completa

## 🛠️ Tecnologías Utilizadas

- **Backend**: Django 4.2.7
- **API**: Django REST Framework
- **Base de Datos**: PostgreSQL (recomendado)
- **Autenticación**: JWT Token
- **Documentación**: Swagger/OpenAPI
- **Testing**: Django Test Framework + unittest.mock

## 📦 Instalación y Configuración

### Prerrequisitos
- Python 3.8+
- PostgreSQL 12+ (recomendado)
- pip y virtualenv

### Instalación

1. **Clonar y configurar el entorno:**
```bash
cd backend/documentos
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar base de datos:**
```bash
# Crear base de datos PostgreSQL
createdb sistema_pontificia_docs

# Configurar variables de entorno
export DATABASE_URL="postgresql://usuario:password@localhost/sistema_pontificia_docs"
export SECRET_KEY="tu-clave-secreta-aqui"
export DEBUG=True
```

4. **Aplicar migraciones:**
```bash
python manage.py makemigrations documentos_app
python manage.py migrate
```

5. **Crear superusuario:**
```bash
python manage.py createsuperuser
```

6. **Ejecutar servidor de desarrollo:**
```bash
python manage.py runserver
```

## 🔧 Configuración

### Variables de Entorno

```bash
# Base de datos
DATABASE_URL=postgresql://usuario:password@localhost/sistema_pontificia_docs

# Seguridad
SECRET_KEY=tu-clave-secreta-muy-segura
DEBUG=False  # En producción

# Archivos
MEDIA_ROOT=/ruta/a/archivos/media
STATIC_ROOT=/ruta/a/archivos/estaticos

# Email (para notificaciones)
EMAIL_HOST=smtp.pontificia.edu
EMAIL_PORT=587
EMAIL_USER=sistema@pontificia.edu
EMAIL_PASSWORD=password-email

# JWT
JWT_SECRET_KEY=clave-jwt-secreta
JWT_EXPIRATION_HOURS=24
```

### Configuración de Archivos

El sistema maneja archivos de documentos. Configurar en `settings.py`:

```python
# Configuración de archivos
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Tamaño máximo de archivo (100MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600

# Tipos de archivo permitidos
ALLOWED_FILE_TYPES = [
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/jpeg',
    'image/png',
    'text/plain'
]
```

## 📚 API Endpoints

### Documentos
```
GET    /api/documentos/              # Listar documentos
POST   /api/documentos/              # Crear documento
GET    /api/documentos/{id}/         # Obtener documento
PUT    /api/documentos/{id}/         # Actualizar documento
DELETE /api/documentos/{id}/         # Eliminar documento

# Acciones especiales
POST   /api/documentos/{id}/aprobar/    # Aprobar documento
POST   /api/documentos/{id}/rechazar/   # Rechazar documento
GET    /api/documentos/{id}/descargar/  # Descargar archivo
POST   /api/documentos/{id}/nueva_version/  # Crear nueva versión
```

### Solicitudes
```
GET    /api/solicitudes/             # Listar solicitudes
POST   /api/solicitudes/             # Crear solicitud
GET    /api/solicitudes/{id}/        # Obtener solicitud
PUT    /api/solicitudes/{id}/        # Actualizar solicitud
POST   /api/solicitudes/{id}/aprobar/   # Aprobar solicitud
POST   /api/solicitudes/{id}/rechazar/  # Rechazar solicitud
```

### Versiones
```
GET    /api/versiones/               # Listar versiones
GET    /api/versiones/{id}/          # Obtener versión
GET    /api/documentos/{id}/versiones/  # Versiones de un documento
```

## 🧪 Testing

### Ejecutar todas las pruebas:
```bash
python manage.py test documentos_app
```

### Ejecutar pruebas específicas:
```bash
# Pruebas del modelo
python manage.py test documentos_app.tests.DocumentoModelTest

# Pruebas del servicio
python manage.py test documentos_app.tests.DocumentoServiceTest

# Pruebas de API
python manage.py test documentos_app.tests.DocumentoAPITest

# Pruebas de integración
python manage.py test documentos_app.tests.IntegrationTest
```

### Cobertura de pruebas:
```bash
pip install coverage
coverage run manage.py test documentos_app
coverage report
coverage html  # Genera reporte HTML
```

## 📖 Uso de la API

### Autenticación

Todas las peticiones requieren autenticación JWT:

```bash
# Obtener token
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "usuario", "password": "password"}'

# Usar token en peticiones
curl -X GET http://localhost:8000/api/documentos/ \
  -H "Authorization: Bearer tu-token-jwt"
```

### Ejemplos de Uso

#### Crear un documento:
```bash
curl -X POST http://localhost:8000/api/documentos/ \
  -H "Authorization: Bearer tu-token" \
  -H "Content-Type: multipart/form-data" \
  -F "titulo=Mi Documento" \
  -F "descripcion=Descripción del documento" \
  -F "tipo_documento=ACADEMICO" \
  -F "archivo=@/ruta/al/archivo.pdf"
```

#### Aprobar un documento:
```bash
curl -X POST http://localhost:8000/api/documentos/1/aprobar/ \
  -H "Authorization: Bearer tu-token" \
  -H "Content-Type: application/json" \
  -d '{"comentarios": "Documento aprobado correctamente"}'
```

#### Buscar documentos:
```bash
curl -X GET "http://localhost:8000/api/documentos/?search=python&tipo_documento=ACADEMICO" \
  -H "Authorization: Bearer tu-token"
```

## 🔒 Seguridad

### Medidas Implementadas
- ✅ Autenticación JWT
- ✅ Validación de permisos por usuario
- ✅ Validación de tipos de archivo
- ✅ Sanitización de datos de entrada
- ✅ Protección CSRF
- ✅ Rate limiting (recomendado configurar)

### Configuración de Seguridad
```python
# En settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

## 📊 Monitoreo y Logging

### Configuración de Logs
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'documentos_service.log',
        },
    },
    'loggers': {
        'documentos_app': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 🚀 Despliegue

### Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "documentos.wsgi:application"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/sistema_pontificia
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: sistema_pontificia
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🤝 Contribución

1. Fork el proyecto
2. Crear una rama para la feature (`git checkout -b feature/AmazingFeature`)
3. Commit los cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico:
- Email: soporte@pontificia.edu
- Documentación: [Wiki del proyecto]
- Issues: [GitHub Issues]

## 📋 Roadmap

### Próximas Características
- [ ] Integración con sistemas de autenticación LDAP
- [ ] API GraphQL como alternativa
- [ ] Búsqueda de texto completo con Elasticsearch
- [ ] Integración con servicios de almacenamiento en la nube
- [ ] Dashboard de analytics
- [ ] Notificaciones push en tiempo real
- [ ] Integración con herramientas de firma digital

### Versiones
- **v1.0.0** - Funcionalidades básicas de gestión de documentos
- **v1.1.0** - Sistema de notificaciones y flujos de trabajo
- **v1.2.0** - API de búsqueda avanzada y filtros
- **v2.0.0** - Integración con servicios externos (próximo)

---

## 🎯 Estado del Proyecto

**Estado**: ✅ **Completado** - Microservicio completamente funcional

**Componentes Implementados**:
- ✅ Modelos de datos completos
- ✅ API REST completa
- ✅ Sistema de autenticación
- ✅ Patrones de diseño implementados
- ✅ Pruebas unitarias y de integración
- ✅ Documentación completa
- ✅ Interfaz de administración
- ✅ Sistema de notificaciones
- ✅ Flujos de trabajo

**Listo para**: Despliegue en producción, integración con frontend, testing extensivo.

---

*Desarrollado para el Sistema Pontificia - Microservicio de Gestión de Documentos*