"""
Documentación de la API del Microservicio de Documentos

Este módulo define la documentación y esquemas para la API REST
del sistema de gestión de documentos del Sistema Pontificia.
"""

from rest_framework import status
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


# Definiciones de esquemas para Swagger/OpenAPI
documento_schema = openapi.Schema(
    title="Documento",
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID único del documento'),
        'titulo': openapi.Schema(type=openapi.TYPE_STRING, description='Título del documento'),
        'descripcion': openapi.Schema(type=openapi.TYPE_STRING, description='Descripción del documento'),
        'tipo_documento': openapi.Schema(type=openapi.TYPE_STRING, description='Tipo de documento'),
        'estado': openapi.Schema(type=openapi.TYPE_STRING, description='Estado actual del documento'),
        'archivo': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description='URL del archivo'),
        'fecha_creacion': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'fecha_actualizacion': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
    },
    required=['titulo', 'tipo_documento']
)

version_documento_schema = openapi.Schema(
    title="Versión de Documento",
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID de la versión'),
        'documento': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID del documento padre'),
        'numero_version': openapi.Schema(type=openapi.TYPE_STRING, description='Número de versión'),
        'archivo': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI),
        'comentarios': openapi.Schema(type=openapi.TYPE_STRING, description='Comentarios de la versión'),
        'fecha_creacion': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
    }
)

solicitud_documento_schema = openapi.Schema(
    title="Solicitud de Documento",
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID de la solicitud'),
        'documento': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID del documento solicitado'),
        'usuario_solicitante': openapi.Schema(type=openapi.TYPE_STRING, description='Usuario que solicita'),
        'motivo': openapi.Schema(type=openapi.TYPE_STRING, description='Motivo de la solicitud'),
        'estado': openapi.Schema(type=openapi.TYPE_STRING, description='Estado de la solicitud'),
        'fecha_solicitud': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
        'fecha_respuesta': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
    }
)

# Respuestas comunes para la documentación
response_200 = openapi.Response('Operación exitosa')
response_201 = openapi.Response('Recurso creado exitosamente')
response_400 = openapi.Response('Solicitud incorrecta')
response_401 = openapi.Response('No autorizado')
response_403 = openapi.Response('Acceso prohibido')
response_404 = openapi.Response('Recurso no encontrado')
response_500 = openapi.Response('Error interno del servidor')

# Parámetros comunes
page_param = openapi.Parameter(
    'page',
    openapi.IN_QUERY,
    description='Número de página para paginación',
    type=openapi.TYPE_INTEGER,
    default=1
)

page_size_param = openapi.Parameter(
    'page_size',
    openapi.IN_QUERY,
    description='Número de elementos por página',
    type=openapi.TYPE_INTEGER,
    default=20
)

search_param = openapi.Parameter(
    'search',
    openapi.IN_QUERY,
    description='Término de búsqueda',
    type=openapi.TYPE_STRING
)

# Decoradores para endpoints específicos
documento_list_docs = swagger_auto_schema(
    operation_description="Listar todos los documentos con paginación y filtros",
    manual_parameters=[page_param, page_size_param, search_param],
    responses={
        200: openapi.Response('Lista de documentos', documento_schema),
        400: response_400,
        401: response_401,
    }
)

documento_create_docs = swagger_auto_schema(
    operation_description="Crear un nuevo documento",
    request_body=documento_schema,
    responses={
        201: openapi.Response('Documento creado', documento_schema),
        400: response_400,
        401: response_401,
    }
)

documento_retrieve_docs = swagger_auto_schema(
    operation_description="Obtener detalles de un documento específico",
    responses={
        200: openapi.Response('Detalles del documento', documento_schema),
        404: response_404,
        401: response_401,
    }
)

documento_update_docs = swagger_auto_schema(
    operation_description="Actualizar un documento existente",
    request_body=documento_schema,
    responses={
        200: openapi.Response('Documento actualizado', documento_schema),
        400: response_400,
        404: response_404,
        401: response_401,
    }
)

documento_delete_docs = swagger_auto_schema(
    operation_description="Eliminar un documento",
    responses={
        204: openapi.Response('Documento eliminado'),
        404: response_404,
        401: response_401,
    }
)

# Documentación para acciones personalizadas
aprobar_docs = swagger_auto_schema(
    operation_description="Aprobar un documento",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'comentarios': openapi.Schema(type=openapi.TYPE_STRING, description='Comentarios de aprobación')
        }
    ),
    responses={
        200: openapi.Response('Documento aprobado'),
        400: response_400,
        404: response_404,
    }
)

rechazar_docs = swagger_auto_schema(
    operation_description="Rechazar un documento",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'comentarios': openapi.Schema(type=openapi.TYPE_STRING, description='Comentarios de rechazo', required=['comentarios'])
        },
        required=['comentarios']
    ),
    responses={
        200: openapi.Response('Documento rechazado'),
        400: response_400,
        404: response_404,
    }
)

descargar_docs = swagger_auto_schema(
    operation_description="Descargar archivo del documento",
    responses={
        200: openapi.Response('Archivo del documento', schema=openapi.Schema(type=openapi.TYPE_FILE)),
        404: response_404,
        401: response_401,
    }
)

# Configuración principal de Swagger
swagger_config = {
    'SWAGGER_SETTINGS': {
        'DEFAULT_MODEL_RENDERING': 'example',
        'USE_SESSION_AUTH': False,
        'JSON_EDITOR': True,
        'SUPPORTED_SUBMIT_METHODS': [
            'get',
            'post',
            'put',
            'delete',
            'patch'
        ],
        'OPERATIONS_SORTER': 'alpha',
        'TAGS_SORTER': 'alpha',
        'DOC_EXPANSION': 'none',
        'DEEP_LINKING': True,
        'SHOW_EXTENSIONS': True,
        'DEFAULT_MODEL_DEPTH': 3,
    },
    'REDOC_SETTINGS': {
        'LAZY_RENDERING': False,
        'HIDE_HOSTNAME': True,
        'EXPAND_RESPONSES': [200, 201],
    }
}

# Información general de la API
api_info = openapi.Info(
    title="API del Microservicio de Documentos",
    default_version='v1',
    description="""
    API REST para el sistema de gestión de documentos del Sistema Pontificia.
    
    ## Características
    - Gestión completa de documentos con versionado
    - Sistema de solicitudes y aprobaciones
    - Flujo de trabajo configurable
    - Notificaciones automáticas
    - Búsqueda y filtrado avanzado
    
    ## Autenticación
    Este API utiliza autenticación basada en tokens JWT.
    
    ## Endpoints Principales
    - `/api/documentos/` - Gestión de documentos
    - `/api/solicitudes/` - Gestión de solicitudes
    - `/api/versiones/` - Gestión de versiones
    - `/api/flujos/` - Gestión de flujos de trabajo
    """,
    terms_of_service="https://www.pontificia.edu/terms/",
    contact=openapi.Contact(email="soporte@pontificia.edu"),
    license=openapi.License(name="MIT License"),
)