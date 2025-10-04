"""
Views para el servicio de documentos

Define las vistas de la API REST para la gestión de documentos,
versiones, solicitudes y flujo de trabajo
"""
import logging
from typing import Any, Dict
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import (
    Documento, VersionDocumento, SolicitudDocumento, FlujoDocumento,
    EstadoDocumento, EstadoSolicitud
)
from .serializers import (
    DocumentoListSerializer, DocumentoDetailSerializer, DocumentoCreateSerializer,
    DocumentoUpdateSerializer, VersionDocumentoSerializer, VersionDocumentoCreateSerializer,
    SolicitudDocumentoListSerializer, SolicitudDocumentoDetailSerializer,
    SolicitudDocumentoCreateSerializer, SolicitudDocumentoUpdateSerializer,
    AsignarSolicitudSerializer, ResponderSolicitudSerializer,
    FlujoDocumentoSerializer, AprobarDocumentoSerializer, RechazarDocumentoSerializer,
    FirmarDocumentoSerializer, EstadisticasSerializer, BusquedaSerializer,
    OpcionesSerializer
)
from .services import DocumentoService
from .utils import get_client_ip, get_user_agent


# Configurar logger
logger = logging.getLogger(__name__)


class DocumentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión de documentos
    
    Proporciona operaciones CRUD completas para documentos,
    incluyendo operaciones especiales como aprobar, rechazar, firmar
    """
    
    service = DocumentoService()
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """Obtiene el queryset base"""
        return self.service.documento_repo.obtener_todos()
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return DocumentoListSerializer
        elif self.action == 'create':
            return DocumentoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DocumentoUpdateSerializer
        else:
            return DocumentoDetailSerializer
    
    def _get_request_info(self, request: Request) -> Dict[str, Any]:
        """Obtiene información de la solicitud HTTP"""
        return {
            'ip_address': get_client_ip(request),
            'user_agent': get_user_agent(request),
            'usuario_id': getattr(request.user, 'id', 'anonimo')
        }
    
    @extend_schema(
        summary="Listar documentos",
        description="Obtiene una lista paginada de documentos con filtros opcionales",
        parameters=[
            OpenApiParameter("page", OpenApiTypes.INT, location="query", description="Número de página"),
            OpenApiParameter("page_size", OpenApiTypes.INT, location="query", description="Elementos por página"),
            OpenApiParameter("tipo", OpenApiTypes.STR, location="query", description="Filtrar por tipo"),
            OpenApiParameter("estado", OpenApiTypes.STR, location="query", description="Filtrar por estado"),
            OpenApiParameter("autor_id", OpenApiTypes.STR, location="query", description="Filtrar por autor"),
            OpenApiParameter("categoria", OpenApiTypes.STR, location="query", description="Filtrar por categoría"),
            OpenApiParameter("publico", OpenApiTypes.BOOL, location="query", description="Solo documentos públicos"),
            OpenApiParameter("busqueda", OpenApiTypes.STR, location="query", description="Búsqueda de texto"),
        ]
    )
    def list(self, request: Request) -> Response:
        """Lista documentos con filtros y paginación"""
        try:
            # Obtener parámetros de filtro
            filtros = {}
            for param in ['tipo', 'estado', 'autor_id', 'categoria', 'busqueda']:
                value = request.query_params.get(param)
                if value:
                    filtros[param] = value
            
            # Filtros booleanos
            publico = request.query_params.get('publico')
            if publico is not None:
                filtros['publico'] = publico.lower() == 'true'
            
            # Paginación
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            page_size = min(page_size, 100)  # Límite máximo
            
            # Obtener documentos
            documentos, metadatos = self.service.listar_documentos(
                filtros=filtros,
                page=page,
                page_size=page_size
            )
            
            # Serializar
            serializer = self.get_serializer(documentos, many=True)
            
            return Response({
                'results': serializer.data,
                'pagination': metadatos
            })
            
        except Exception as e:
            logger.error(f"Error listando documentos: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Crear documento",
        description="Crea un nuevo documento con archivo adjunto",
        request=DocumentoCreateSerializer
    )
    def create(self, request: Request) -> Response:
        """Crea un nuevo documento"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Obtener información de la solicitud
            request_info = self._get_request_info(request)
            
            # Crear documento usando el servicio
            exito, documento, mensaje = self.service.crear_documento(
                titulo=serializer.validated_data['titulo'],
                tipo=serializer.validated_data['tipo'],
                autor_id=request_info['usuario_id'],
                archivo=serializer.validated_data['archivo'],
                descripcion=serializer.validated_data.get('descripcion', ''),
                categoria=serializer.validated_data.get('categoria', ''),
                palabras_clave=serializer.validated_data.get('palabras_clave', ''),
                publico=serializer.validated_data.get('publico', False),
                confidencial=serializer.validated_data.get('confidencial', False),
                fecha_vigencia=serializer.validated_data.get('fecha_vigencia'),
                fecha_vencimiento=serializer.validated_data.get('fecha_vencimiento'),
                requiere_aprobacion=serializer.validated_data.get('requiere_aprobacion', True),
                ip_address=request_info['ip_address'],
                user_agent=request_info['user_agent']
            )
            
            if exito:
                response_serializer = DocumentoDetailSerializer(
                    documento, 
                    context={'request': request}
                )
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'error': mensaje},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error creando documento: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Obtener documento",
        description="Obtiene los detalles de un documento específico"
    )
    def retrieve(self, request: Request, pk=None) -> Response:
        """Obtiene un documento específico"""
        try:
            documento = self.service.obtener_documento(pk)
            if not documento:
                return Response(
                    {'error': 'Documento no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Incrementar visualizaciones
            documento.incrementar_visualizaciones()
            
            serializer = self.get_serializer(documento)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error obteniendo documento: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Actualizar documento",
        description="Actualiza los datos de un documento existente",
        request=DocumentoUpdateSerializer
    )
    def update(self, request: Request, pk=None) -> Response:
        """Actualiza un documento"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Obtener información de la solicitud
            request_info = self._get_request_info(request)
            
            # Actualizar documento usando el servicio
            exito, documento, mensaje = self.service.actualizar_documento(
                documento_id=pk,
                datos=serializer.validated_data,
                usuario_id=request_info['usuario_id'],
                ip_address=request_info['ip_address']
            )
            
            if exito:
                response_serializer = DocumentoDetailSerializer(
                    documento,
                    context={'request': request}
                )
                return Response(response_serializer.data)
            else:
                return Response(
                    {'error': mensaje},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error actualizando documento: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Eliminar documento",
        description="Elimina un documento del sistema"
    )
    def destroy(self, request: Request, pk=None) -> Response:
        """Elimina un documento"""
        try:
            request_info = self._get_request_info(request)
            
            exito, mensaje = self.service.eliminar_documento(
                documento_id=pk,
                usuario_id=request_info['usuario_id'],
                ip_address=request_info['ip_address']
            )
            
            if exito:
                return Response(
                    {'message': mensaje},
                    status=status.HTTP_204_NO_CONTENT
                )
            else:
                return Response(
                    {'error': mensaje},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error eliminando documento: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Descargar documento",
        description="Descarga el archivo de un documento",
        responses={200: {'type': 'string', 'format': 'binary'}}
    )
    @action(detail=True, methods=['get'])
    def descargar(self, request: Request, pk=None) -> HttpResponse:
        """Descarga el archivo de un documento"""
        try:
            request_info = self._get_request_info(request)
            
            exito, ruta_archivo, mensaje = self.service.descargar_documento(
                documento_id=pk,
                usuario_id=request_info['usuario_id'],
                ip_address=request_info['ip_address']
            )
            
            if not exito:
                return Response(
                    {'error': mensaje},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            documento = self.service.obtener_documento(pk)
            if not documento or not documento.archivo:
                raise Http404("Archivo no encontrado")
            
            # Preparar respuesta con archivo
            response = HttpResponse(
                documento.archivo.read(),
                content_type=documento.tipo_mime or 'application/octet-stream'
            )
            
            filename = f"{documento.codigo_documento}_{documento.titulo}.{documento.archivo.name.split('.')[-1]}"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error descargando documento: {e}")
            raise Http404("Error descargando archivo")
    
    @extend_schema(
        summary="Enviar a revisión",
        description="Envía un documento a revisión",
        request={'type': 'object', 'properties': {'comentarios': {'type': 'string'}}}
    )
    @action(detail=True, methods=['post'])
    def enviar_revision(self, request: Request, pk=None) -> Response:
        """Envía un documento a revisión"""
        try:
            request_info = self._get_request_info(request)
            comentarios = request.data.get('comentarios', '')
            
            exito, mensaje = self.service.enviar_a_revision(
                documento_id=pk,
                usuario_id=request_info['usuario_id'],
                comentarios=comentarios,
                ip_address=request_info['ip_address']
            )
            
            if exito:
                return Response({'message': mensaje})
            else:
                return Response(
                    {'error': mensaje},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error enviando a revisión: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Aprobar documento",
        description="Aprueba un documento en revisión",
        request=AprobarDocumentoSerializer
    )
    @action(detail=True, methods=['post'])
    def aprobar(self, request: Request, pk=None) -> Response:
        """Aprueba un documento"""
        try:
            serializer = AprobarDocumentoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            request_info = self._get_request_info(request)
            
            exito, mensaje = self.service.aprobar_documento(
                documento_id=pk,
                aprobador_id=request_info['usuario_id'],
                aprobador_nombre="Usuario",  # TODO: Obtener nombre real
                comentarios=serializer.validated_data.get('comentarios', ''),
                ip_address=request_info['ip_address']
            )
            
            if exito:
                return Response({'message': mensaje})
            else:
                return Response(
                    {'error': mensaje},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error aprobando documento: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Rechazar documento",
        description="Rechaza un documento en revisión",
        request=RechazarDocumentoSerializer
    )
    @action(detail=True, methods=['post'])
    def rechazar(self, request: Request, pk=None) -> Response:
        """Rechaza un documento"""
        try:
            serializer = RechazarDocumentoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            request_info = self._get_request_info(request)
            
            exito, mensaje = self.service.rechazar_documento(
                documento_id=pk,
                rechazador_id=request_info['usuario_id'],
                rechazador_nombre="Usuario",  # TODO: Obtener nombre real
                motivo=serializer.validated_data['motivo'],
                ip_address=request_info['ip_address']
            )
            
            if exito:
                return Response({'message': mensaje})
            else:
                return Response(
                    {'error': mensaje},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error rechazando documento: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Firmar documento",
        description="Firma digitalmente un documento aprobado",
        request=FirmarDocumentoSerializer
    )
    @action(detail=True, methods=['post'])
    def firmar(self, request: Request, pk=None) -> Response:
        """Firma un documento"""
        try:
            serializer = FirmarDocumentoSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            request_info = self._get_request_info(request)
            
            exito, mensaje = self.service.firmar_documento(
                documento_id=pk,
                firmante_id=request_info['usuario_id'],
                firma_digital=serializer.validated_data.get('firma_digital', ''),
                ip_address=request_info['ip_address']
            )
            
            if exito:
                return Response({'message': mensaje})
            else:
                return Response(
                    {'error': mensaje},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error firmando documento: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Versiones del documento",
        description="Obtiene todas las versiones de un documento"
    )
    @action(detail=True, methods=['get'])
    def versiones(self, request: Request, pk=None) -> Response:
        """Obtiene las versiones de un documento"""
        try:
            versiones = self.service.obtener_versiones_documento(pk)
            serializer = VersionDocumentoSerializer(
                versiones, 
                many=True, 
                context={'request': request}
            )
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error obteniendo versiones: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Crear nueva versión",
        description="Crea una nueva versión de un documento",
        request=VersionDocumentoCreateSerializer
    )
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def nueva_version(self, request: Request, pk=None) -> Response:
        """Crea una nueva versión del documento"""
        try:
            serializer = VersionDocumentoCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            request_info = self._get_request_info(request)
            
            exito, version, mensaje = self.service.crear_nueva_version(
                documento_id=pk,
                archivo=serializer.validated_data['archivo'],
                usuario_id=request_info['usuario_id'],
                comentarios=serializer.validated_data.get('comentarios', ''),
                ip_address=request_info['ip_address']
            )
            
            if exito:
                response_serializer = VersionDocumentoSerializer(
                    version,
                    context={'request': request}
                )
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'error': mensaje},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error creando versión: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Flujo del documento",
        description="Obtiene el historial de flujo de un documento"
    )
    @action(detail=True, methods=['get'])
    def flujo(self, request: Request, pk=None) -> Response:
        """Obtiene el flujo de un documento"""
        try:
            flujo = self.service.obtener_flujo_documento(pk)
            serializer = FlujoDocumentoSerializer(flujo, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error obteniendo flujo: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SolicitudDocumentoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión de solicitudes de documentos
    """
    
    service = DocumentoService()
    
    def get_queryset(self):
        """Obtiene el queryset base"""
        return self.service.solicitud_repo.obtener_todos()
    
    def get_serializer_class(self):
        """Retorna el serializer apropiado según la acción"""
        if self.action == 'list':
            return SolicitudDocumentoListSerializer
        elif self.action == 'create':
            return SolicitudDocumentoCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SolicitudDocumentoUpdateSerializer
        else:
            return SolicitudDocumentoDetailSerializer
    
    def _get_request_info(self, request: Request) -> Dict[str, Any]:
        """Obtiene información de la solicitud HTTP"""
        return {
            'ip_address': get_client_ip(request),
            'user_agent': get_user_agent(request),
            'usuario_id': getattr(request.user, 'id', 'anonimo')
        }
    
    @extend_schema(
        summary="Crear solicitud",
        description="Crea una nueva solicitud de documento",
        request=SolicitudDocumentoCreateSerializer
    )
    def create(self, request: Request) -> Response:
        """Crea una nueva solicitud"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            request_info = self._get_request_info(request)
            
            exito, solicitud, mensaje = self.service.crear_solicitud(
                solicitante_id=request_info['usuario_id'],
                tipo=serializer.validated_data['tipo'],
                titulo=serializer.validated_data['titulo'],
                descripcion=serializer.validated_data['descripcion'],
                documento_id=serializer.validated_data.get('documento'),
                prioridad=serializer.validated_data.get('prioridad', 'MEDIA'),
                fecha_limite=serializer.validated_data.get('fecha_limite'),
                archivo_adjunto=serializer.validated_data.get('archivo_adjunto'),
                ip_address=request_info['ip_address']
            )
            
            if exito:
                response_serializer = SolicitudDocumentoDetailSerializer(
                    solicitud,
                    context={'request': request}
                )
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'error': mensaje},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error creando solicitud: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Asignar solicitud",
        description="Asigna una solicitud a un usuario",
        request=AsignarSolicitudSerializer
    )
    @action(detail=True, methods=['post'])
    def asignar(self, request: Request, pk=None) -> Response:
        """Asigna una solicitud"""
        try:
            serializer = AsignarSolicitudSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            request_info = self._get_request_info(request)
            
            exito, mensaje = self.service.asignar_solicitud(
                solicitud_id=pk,
                asignado_a=serializer.validated_data['asignado_a'],
                asignado_por=request_info['usuario_id'],
                ip_address=request_info['ip_address']
            )
            
            if exito:
                return Response({'message': mensaje})
            else:
                return Response(
                    {'error': mensaje},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error asignando solicitud: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @extend_schema(
        summary="Responder solicitud",
        description="Responde una solicitud asignada",
        request=ResponderSolicitudSerializer
    )
    @action(detail=True, methods=['post'])
    def responder(self, request: Request, pk=None) -> Response:
        """Responde una solicitud"""
        try:
            serializer = ResponderSolicitudSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            request_info = self._get_request_info(request)
            
            solicitud = self.service.obtener_solicitud(pk)
            if not solicitud:
                return Response(
                    {'error': 'Solicitud no encontrada'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            solicitud.responder(
                respuesta=serializer.validated_data['respuesta'],
                usuario_id=request_info['usuario_id'],
                estado=serializer.validated_data['estado']
            )
            
            return Response({'message': 'Solicitud respondida exitosamente'})
            
        except Exception as e:
            logger.error(f"Error respondiendo solicitud: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    summary="Estadísticas del sistema",
    description="Obtiene estadísticas generales del sistema de documentos"
)
class EstadisticasView(viewsets.GenericViewSet):
    """Vista para estadísticas del sistema"""
    
    service = DocumentoService()
    
    def list(self, request: Request) -> Response:
        """Obtiene estadísticas del sistema"""
        try:
            estadisticas = self.service.obtener_estadisticas()
            serializer = EstadisticasSerializer(estadisticas)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    summary="Opciones del sistema",
    description="Obtiene opciones y configuraciones del sistema"
)
class OpcionesView(viewsets.GenericViewSet):
    """Vista para opciones del sistema"""
    
    def list(self, request: Request) -> Response:
        """Obtiene opciones del sistema"""
        try:
            serializer = OpcionesSerializer({})
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error obteniendo opciones: {e}")
            return Response(
                {'error': 'Error interno del servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
