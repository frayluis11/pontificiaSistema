"""
Repository Pattern para el servicio de documentos

Implementa el patrón Repository para abstraer el acceso a datos
y proporcionar una interfaz uniforme para las operaciones CRUD
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from django.db.models import QuerySet, Q
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal
from datetime import date, datetime

from .models import (
    Documento, VersionDocumento, SolicitudDocumento, 
    FlujoDocumento, EstadoDocumento, EstadoSolicitud,
    TipoDocumento, TipoSolicitud
)


class BaseRepository(ABC):
    """
    Repositorio base con operaciones CRUD genéricas
    """
    
    def __init__(self, model_class):
        self.model_class = model_class
    
    @abstractmethod
    def obtener_por_id(self, entity_id: str):
        """Obtiene una entidad por su ID"""
        pass
    
    @abstractmethod
    def obtener_todos(self, filtros: Dict[str, Any] = None) -> QuerySet:
        """Obtiene todas las entidades con filtros opcionales"""
        pass
    
    @abstractmethod
    def crear(self, datos: Dict[str, Any]):
        """Crea una nueva entidad"""
        pass
    
    @abstractmethod
    def actualizar(self, entity_id: str, datos: Dict[str, Any]):
        """Actualiza una entidad existente"""
        pass
    
    @abstractmethod
    def eliminar(self, entity_id: str) -> bool:
        """Elimina una entidad"""
        pass


class DocumentoRepository(BaseRepository):
    """
    Repositorio para la gestión de documentos
    """
    
    def __init__(self):
        super().__init__(Documento)
    
    def obtener_por_id(self, documento_id: str) -> Optional[Documento]:
        """
        Obtiene un documento por su ID
        
        Args:
            documento_id: ID del documento
            
        Returns:
            Instancia del documento o None
        """
        try:
            return Documento.objects.select_related().get(
                id=documento_id, 
                activo=True
            )
        except Documento.DoesNotExist:
            return None
    
    def obtener_por_codigo(self, codigo: str) -> Optional[Documento]:
        """
        Obtiene un documento por su código
        
        Args:
            codigo: Código del documento
            
        Returns:
            Instancia del documento o None
        """
        try:
            return Documento.objects.get(
                codigo_documento=codigo,
                activo=True
            )
        except Documento.DoesNotExist:
            return None
    
    def obtener_todos(self, filtros: Dict[str, Any] = None) -> QuerySet:
        """
        Obtiene todos los documentos con filtros opcionales
        
        Args:
            filtros: Diccionario con filtros
            
        Returns:
            QuerySet de documentos
        """
        queryset = Documento.objects.filter(activo=True)
        
        if not filtros:
            return queryset.order_by('-fecha_actualizacion')
        
        # Aplicar filtros
        if 'autor_id' in filtros:
            queryset = queryset.filter(autor_id=filtros['autor_id'])
        
        if 'tipo' in filtros:
            queryset = queryset.filter(tipo=filtros['tipo'])
        
        if 'estado' in filtros:
            queryset = queryset.filter(estado=filtros['estado'])
        
        if 'categoria' in filtros:
            queryset = queryset.filter(categoria__icontains=filtros['categoria'])
        
        if 'publico' in filtros:
            queryset = queryset.filter(publico=filtros['publico'])
        
        if 'confidencial' in filtros:
            queryset = queryset.filter(confidencial=filtros['confidencial'])
        
        if 'fecha_desde' in filtros:
            queryset = queryset.filter(fecha_creacion__gte=filtros['fecha_desde'])
        
        if 'fecha_hasta' in filtros:
            queryset = queryset.filter(fecha_creacion__lte=filtros['fecha_hasta'])
        
        if 'busqueda' in filtros:
            termino = filtros['busqueda']
            queryset = queryset.filter(
                Q(titulo__icontains=termino) |
                Q(descripcion__icontains=termino) |
                Q(codigo_documento__icontains=termino) |
                Q(palabras_clave__icontains=termino)
            )
        
        return queryset.order_by('-fecha_actualizacion')
    
    def obtener_paginados(
        self, 
        page: int = 1, 
        page_size: int = 20, 
        filtros: Dict[str, Any] = None
    ) -> Tuple[List[Documento], Dict[str, Any]]:
        """
        Obtiene documentos paginados
        
        Args:
            page: Número de página
            page_size: Tamaño de página
            filtros: Filtros opcionales
            
        Returns:
            Tupla con (lista de documentos, metadatos de paginación)
        """
        queryset = self.obtener_todos(filtros)
        paginator = Paginator(queryset, page_size)
        
        page_obj = paginator.get_page(page)
        
        metadatos = {
            'total': paginator.count,
            'pages': paginator.num_pages,
            'current_page': page_obj.number,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None
        }
        
        return list(page_obj.object_list), metadatos
    
    def crear(self, datos: Dict[str, Any]) -> Documento:
        """
        Crea un nuevo documento
        
        Args:
            datos: Datos del documento
            
        Returns:
            Instancia del documento creado
        """
        documento = Documento.objects.create(**datos)
        return documento
    
    def actualizar(self, documento_id: str, datos: Dict[str, Any]) -> Optional[Documento]:
        """
        Actualiza un documento existente
        
        Args:
            documento_id: ID del documento
            datos: Datos a actualizar
            
        Returns:
            Instancia del documento actualizado o None
        """
        try:
            documento = self.obtener_por_id(documento_id)
            if not documento:
                return None
            
            for campo, valor in datos.items():
                if hasattr(documento, campo):
                    setattr(documento, campo, valor)
            
            documento.save()
            return documento
            
        except Exception:
            return None
    
    def eliminar(self, documento_id: str) -> bool:
        """
        Elimina un documento (soft delete)
        
        Args:
            documento_id: ID del documento
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            documento = self.obtener_por_id(documento_id)
            if documento:
                documento.activo = False
                documento.save()
                return True
            return False
        except Exception:
            return False
    
    def obtener_por_autor(self, autor_id: str) -> QuerySet:
        """
        Obtiene documentos por autor
        
        Args:
            autor_id: ID del autor
            
        Returns:
            QuerySet de documentos del autor
        """
        return self.obtener_todos({'autor_id': autor_id})
    
    def obtener_por_tipo(self, tipo: str) -> QuerySet:
        """
        Obtiene documentos por tipo
        
        Args:
            tipo: Tipo de documento
            
        Returns:
            QuerySet de documentos del tipo
        """
        return self.obtener_todos({'tipo': tipo})
    
    def obtener_por_estado(self, estado: str) -> QuerySet:
        """
        Obtiene documentos por estado
        
        Args:
            estado: Estado del documento
            
        Returns:
            QuerySet de documentos en el estado
        """
        return self.obtener_todos({'estado': estado})
    
    def obtener_publicos(self) -> QuerySet:
        """
        Obtiene documentos públicos
        
        Returns:
            QuerySet de documentos públicos
        """
        return self.obtener_todos({'publico': True})
    
    def obtener_vigentes(self) -> QuerySet:
        """
        Obtiene documentos vigentes
        
        Returns:
            QuerySet de documentos vigentes
        """
        hoy = date.today()
        
        return Documento.objects.filter(
            activo=True,
            estado__in=[
                EstadoDocumento.APROBADO,
                EstadoDocumento.FIRMADO,
                EstadoDocumento.PUBLICADO
            ]
        ).filter(
            Q(fecha_vigencia__isnull=True) | Q(fecha_vigencia__lte=hoy)
        ).filter(
            Q(fecha_vencimiento__isnull=True) | Q(fecha_vencimiento__gte=hoy)
        )
    
    def obtener_proximos_vencer(self, dias: int = 30) -> QuerySet:
        """
        Obtiene documentos próximos a vencer
        
        Args:
            dias: Días de anticipación
            
        Returns:
            QuerySet de documentos próximos a vencer
        """
        from datetime import timedelta
        
        fecha_limite = date.today() + timedelta(days=dias)
        
        return Documento.objects.filter(
            activo=True,
            fecha_vencimiento__isnull=False,
            fecha_vencimiento__lte=fecha_limite,
            fecha_vencimiento__gte=date.today()
        )
    
    def buscar_texto(self, termino: str) -> QuerySet:
        """
        Búsqueda de texto completo
        
        Args:
            termino: Término de búsqueda
            
        Returns:
            QuerySet de documentos que coinciden
        """
        return self.obtener_todos({'busqueda': termino})
    
    def obtener_estadisticas(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de documentos
        
        Returns:
            Diccionario con estadísticas
        """
        total = Documento.objects.filter(activo=True).count()
        
        por_estado = {}
        for estado in EstadoDocumento:
            count = Documento.objects.filter(
                activo=True, 
                estado=estado.value
            ).count()
            por_estado[estado.label] = count
        
        por_tipo = {}
        for tipo in TipoDocumento:
            count = Documento.objects.filter(
                activo=True, 
                tipo=tipo.value
            ).count()
            por_tipo[tipo.label] = count
        
        return {
            'total': total,
            'por_estado': por_estado,
            'por_tipo': por_tipo,
            'publicos': Documento.objects.filter(activo=True, publico=True).count(),
            'confidenciales': Documento.objects.filter(activo=True, confidencial=True).count(),
            'vigentes': self.obtener_vigentes().count(),
            'proximos_vencer': self.obtener_proximos_vencer().count()
        }


class VersionDocumentoRepository(BaseRepository):
    """
    Repositorio para la gestión de versiones de documentos
    """
    
    def __init__(self):
        super().__init__(VersionDocumento)
    
    def obtener_por_id(self, version_id: str) -> Optional[VersionDocumento]:
        """
        Obtiene una versión por su ID
        
        Args:
            version_id: ID de la versión
            
        Returns:
            Instancia de la versión o None
        """
        try:
            return VersionDocumento.objects.select_related('documento').get(
                id=version_id,
                activo=True
            )
        except VersionDocumento.DoesNotExist:
            return None
    
    def obtener_todos(self, filtros: Dict[str, Any] = None) -> QuerySet:
        """
        Obtiene todas las versiones con filtros opcionales
        
        Args:
            filtros: Diccionario con filtros
            
        Returns:
            QuerySet de versiones
        """
        queryset = VersionDocumento.objects.filter(activo=True)
        
        if not filtros:
            return queryset.order_by('-numero_version')
        
        if 'documento_id' in filtros:
            queryset = queryset.filter(documento_id=filtros['documento_id'])
        
        if 'vigente' in filtros:
            queryset = queryset.filter(vigente=filtros['vigente'])
        
        if 'creado_por' in filtros:
            queryset = queryset.filter(creado_por=filtros['creado_por'])
        
        return queryset.order_by('-numero_version')
    
    def crear(self, datos: Dict[str, Any]) -> VersionDocumento:
        """
        Crea una nueva versión
        
        Args:
            datos: Datos de la versión
            
        Returns:
            Instancia de la versión creada
        """
        version = VersionDocumento.objects.create(**datos)
        return version
    
    def actualizar(self, version_id: str, datos: Dict[str, Any]) -> Optional[VersionDocumento]:
        """
        Actualiza una versión existente
        
        Args:
            version_id: ID de la versión
            datos: Datos a actualizar
            
        Returns:
            Instancia de la versión actualizada o None
        """
        try:
            version = self.obtener_por_id(version_id)
            if not version:
                return None
            
            for campo, valor in datos.items():
                if hasattr(version, campo):
                    setattr(version, campo, valor)
            
            version.save()
            return version
            
        except Exception:
            return None
    
    def eliminar(self, version_id: str) -> bool:
        """
        Elimina una versión (soft delete)
        
        Args:
            version_id: ID de la versión
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            version = self.obtener_por_id(version_id)
            if version:
                version.activo = False
                version.save()
                return True
            return False
        except Exception:
            return False
    
    def obtener_por_documento(self, documento_id: str) -> QuerySet:
        """
        Obtiene versiones de un documento
        
        Args:
            documento_id: ID del documento
            
        Returns:
            QuerySet de versiones del documento
        """
        return self.obtener_todos({'documento_id': documento_id})
    
    def obtener_version_vigente(self, documento_id: str) -> Optional[VersionDocumento]:
        """
        Obtiene la versión vigente de un documento
        
        Args:
            documento_id: ID del documento
            
        Returns:
            Versión vigente o None
        """
        try:
            return VersionDocumento.objects.get(
                documento_id=documento_id,
                vigente=True,
                activo=True
            )
        except VersionDocumento.DoesNotExist:
            return None
    
    def activar_version(self, version_id: str) -> bool:
        """
        Activa una versión específica
        
        Args:
            version_id: ID de la versión a activar
            
        Returns:
            True si se activó correctamente
        """
        try:
            version = self.obtener_por_id(version_id)
            if not version:
                return False
            
            # Desactivar otras versiones del mismo documento
            VersionDocumento.objects.filter(
                documento=version.documento,
                activo=True
            ).update(vigente=False)
            
            # Activar esta versión
            version.vigente = True
            version.save()
            
            return True
        except Exception:
            return False


class SolicitudDocumentoRepository(BaseRepository):
    """
    Repositorio para la gestión de solicitudes de documentos
    """
    
    def __init__(self):
        super().__init__(SolicitudDocumento)
    
    def obtener_por_id(self, solicitud_id: str) -> Optional[SolicitudDocumento]:
        """
        Obtiene una solicitud por su ID
        
        Args:
            solicitud_id: ID de la solicitud
            
        Returns:
            Instancia de la solicitud o None
        """
        try:
            return SolicitudDocumento.objects.select_related('documento').get(
                id=solicitud_id,
                activo=True
            )
        except SolicitudDocumento.DoesNotExist:
            return None
    
    def obtener_por_numero(self, numero: str) -> Optional[SolicitudDocumento]:
        """
        Obtiene una solicitud por su número de seguimiento
        
        Args:
            numero: Número de seguimiento
            
        Returns:
            Instancia de la solicitud o None
        """
        try:
            return SolicitudDocumento.objects.get(
                numero_seguimiento=numero,
                activo=True
            )
        except SolicitudDocumento.DoesNotExist:
            return None
    
    def obtener_todos(self, filtros: Dict[str, Any] = None) -> QuerySet:
        """
        Obtiene todas las solicitudes con filtros opcionales
        
        Args:
            filtros: Diccionario con filtros
            
        Returns:
            QuerySet de solicitudes
        """
        queryset = SolicitudDocumento.objects.filter(activo=True)
        
        if not filtros:
            return queryset.order_by('-fecha_solicitud')
        
        if 'solicitante_id' in filtros:
            queryset = queryset.filter(solicitante_id=filtros['solicitante_id'])
        
        if 'tipo' in filtros:
            queryset = queryset.filter(tipo=filtros['tipo'])
        
        if 'estado' in filtros:
            queryset = queryset.filter(estado=filtros['estado'])
        
        if 'asignado_a' in filtros:
            queryset = queryset.filter(asignado_a=filtros['asignado_a'])
        
        if 'prioridad' in filtros:
            queryset = queryset.filter(prioridad=filtros['prioridad'])
        
        if 'documento_id' in filtros:
            queryset = queryset.filter(documento_id=filtros['documento_id'])
        
        if 'fecha_desde' in filtros:
            queryset = queryset.filter(fecha_solicitud__gte=filtros['fecha_desde'])
        
        if 'fecha_hasta' in filtros:
            queryset = queryset.filter(fecha_solicitud__lte=filtros['fecha_hasta'])
        
        return queryset.order_by('-fecha_solicitud')
    
    def crear(self, datos: Dict[str, Any]) -> SolicitudDocumento:
        """
        Crea una nueva solicitud
        
        Args:
            datos: Datos de la solicitud
            
        Returns:
            Instancia de la solicitud creada
        """
        solicitud = SolicitudDocumento.objects.create(**datos)
        return solicitud
    
    def actualizar(self, solicitud_id: str, datos: Dict[str, Any]) -> Optional[SolicitudDocumento]:
        """
        Actualiza una solicitud existente
        
        Args:
            solicitud_id: ID de la solicitud
            datos: Datos a actualizar
            
        Returns:
            Instancia de la solicitud actualizada o None
        """
        try:
            solicitud = self.obtener_por_id(solicitud_id)
            if not solicitud:
                return None
            
            for campo, valor in datos.items():
                if hasattr(solicitud, campo):
                    setattr(solicitud, campo, valor)
            
            solicitud.save()
            return solicitud
            
        except Exception:
            return None
    
    def eliminar(self, solicitud_id: str) -> bool:
        """
        Elimina una solicitud (soft delete)
        
        Args:
            solicitud_id: ID de la solicitud
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            solicitud = self.obtener_por_id(solicitud_id)
            if solicitud:
                solicitud.activo = False
                solicitud.save()
                return True
            return False
        except Exception:
            return False
    
    def obtener_por_solicitante(self, solicitante_id: str) -> QuerySet:
        """
        Obtiene solicitudes de un solicitante
        
        Args:
            solicitante_id: ID del solicitante
            
        Returns:
            QuerySet de solicitudes del solicitante
        """
        return self.obtener_todos({'solicitante_id': solicitante_id})
    
    def obtener_por_asignado(self, asignado_id: str) -> QuerySet:
        """
        Obtiene solicitudes asignadas a un usuario
        
        Args:
            asignado_id: ID del usuario asignado
            
        Returns:
            QuerySet de solicitudes asignadas
        """
        return self.obtener_todos({'asignado_a': asignado_id})
    
    def obtener_pendientes(self) -> QuerySet:
        """
        Obtiene solicitudes pendientes
        
        Returns:
            QuerySet de solicitudes pendientes
        """
        return self.obtener_todos({'estado': EstadoSolicitud.PENDIENTE})
    
    def obtener_vencidas(self) -> QuerySet:
        """
        Obtiene solicitudes vencidas
        
        Returns:
            QuerySet de solicitudes vencidas
        """
        ahora = timezone.now()
        
        return SolicitudDocumento.objects.filter(
            activo=True,
            fecha_limite__isnull=False,
            fecha_limite__lt=ahora,
            estado__in=[
                EstadoSolicitud.PENDIENTE,
                EstadoSolicitud.EN_PROCESO
            ]
        )


class FlujoDocumentoRepository(BaseRepository):
    """
    Repositorio para la gestión del flujo de documentos
    """
    
    def __init__(self):
        super().__init__(FlujoDocumento)
    
    def obtener_por_id(self, flujo_id: str) -> Optional[FlujoDocumento]:
        """
        Obtiene un registro de flujo por su ID
        
        Args:
            flujo_id: ID del registro de flujo
            
        Returns:
            Instancia del flujo o None
        """
        try:
            return FlujoDocumento.objects.select_related('documento').get(
                id=flujo_id,
                activo=True
            )
        except FlujoDocumento.DoesNotExist:
            return None
    
    def obtener_todos(self, filtros: Dict[str, Any] = None) -> QuerySet:
        """
        Obtiene todos los registros de flujo con filtros opcionales
        
        Args:
            filtros: Diccionario con filtros
            
        Returns:
            QuerySet de registros de flujo
        """
        queryset = FlujoDocumento.objects.filter(activo=True)
        
        if not filtros:
            return queryset.order_by('-fecha_accion')
        
        if 'documento_id' in filtros:
            queryset = queryset.filter(documento_id=filtros['documento_id'])
        
        if 'usuario_id' in filtros:
            queryset = queryset.filter(usuario_id=filtros['usuario_id'])
        
        if 'paso' in filtros:
            queryset = queryset.filter(paso=filtros['paso'])
        
        if 'estado_anterior' in filtros:
            queryset = queryset.filter(estado_anterior=filtros['estado_anterior'])
        
        if 'estado_nuevo' in filtros:
            queryset = queryset.filter(estado_nuevo=filtros['estado_nuevo'])
        
        if 'fecha_desde' in filtros:
            queryset = queryset.filter(fecha_accion__gte=filtros['fecha_desde'])
        
        if 'fecha_hasta' in filtros:
            queryset = queryset.filter(fecha_accion__lte=filtros['fecha_hasta'])
        
        return queryset.order_by('-fecha_accion')
    
    def crear(self, datos: Dict[str, Any]) -> FlujoDocumento:
        """
        Crea un nuevo registro de flujo
        
        Args:
            datos: Datos del flujo
            
        Returns:
            Instancia del flujo creado
        """
        flujo = FlujoDocumento.objects.create(**datos)
        return flujo
    
    def actualizar(self, flujo_id: str, datos: Dict[str, Any]) -> Optional[FlujoDocumento]:
        """
        Actualiza un registro de flujo existente
        
        Args:
            flujo_id: ID del flujo
            datos: Datos a actualizar
            
        Returns:
            Instancia del flujo actualizado o None
        """
        try:
            flujo = self.obtener_por_id(flujo_id)
            if not flujo:
                return None
            
            for campo, valor in datos.items():
                if hasattr(flujo, campo):
                    setattr(flujo, campo, valor)
            
            flujo.save()
            return flujo
            
        except Exception:
            return None
    
    def eliminar(self, flujo_id: str) -> bool:
        """
        Elimina un registro de flujo (soft delete)
        
        Args:
            flujo_id: ID del flujo
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            flujo = self.obtener_por_id(flujo_id)
            if flujo:
                flujo.activo = False
                flujo.save()
                return True
            return False
        except Exception:
            return False
    
    def obtener_por_documento(self, documento_id: str) -> QuerySet:
        """
        Obtiene el flujo de un documento
        
        Args:
            documento_id: ID del documento
            
        Returns:
            QuerySet del flujo del documento
        """
        return self.obtener_todos({'documento_id': documento_id})
    
    def obtener_por_usuario(self, usuario_id: str) -> QuerySet:
        """
        Obtiene acciones realizadas por un usuario
        
        Args:
            usuario_id: ID del usuario
            
        Returns:
            QuerySet de acciones del usuario
        """
        return self.obtener_todos({'usuario_id': usuario_id})
    
    def registrar_accion(
        self,
        documento_id: str,
        paso: str,
        usuario_id: str,
        detalle: str,
        estado_anterior: str = '',
        estado_nuevo: str = '',
        ip_address: str = None,
        user_agent: str = '',
        datos_adicionales: Dict[str, Any] = None
    ) -> FlujoDocumento:
        """
        Registra una nueva acción en el flujo
        
        Args:
            documento_id: ID del documento
            paso: Tipo de paso
            usuario_id: ID del usuario
            detalle: Detalle de la acción
            estado_anterior: Estado anterior del documento
            estado_nuevo: Estado nuevo del documento
            ip_address: IP del usuario
            user_agent: User agent del navegador
            datos_adicionales: Datos adicionales
            
        Returns:
            Instancia del flujo creado
        """
        return self.crear({
            'documento_id': documento_id,
            'paso': paso,
            'usuario_id': usuario_id,
            'detalle': detalle,
            'estado_anterior': estado_anterior,
            'estado_nuevo': estado_nuevo,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'datos_adicionales': datos_adicionales or {}
        })