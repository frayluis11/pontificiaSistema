"""
Observer Pattern para notificaciones del servicio de documentos

Implementa el patrón Observer para notificar cambios en documentos,
solicitudes y otros eventos importantes del sistema
"""
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from django.utils import timezone
from django.conf import settings
import requests
from .factories import NotificacionFactory


# Configurar logger
logger = logging.getLogger(__name__)


class Observer(ABC):
    """
    Interfaz base para observadores
    """
    
    @abstractmethod
    def notificar(self, evento: str, datos: Dict[str, Any]) -> None:
        """
        Método que debe implementar cada observador
        
        Args:
            evento: Tipo de evento ocurrido
            datos: Datos del evento
        """
        pass


class Observable:
    """
    Clase base para objetos observables
    
    Maneja la lista de observadores y notifica cambios
    """
    
    def __init__(self):
        self._observadores: List[Observer] = []
    
    def agregar_observador(self, observador: Observer) -> None:
        """
        Agrega un observador a la lista
        
        Args:
            observador: Observador a agregar
        """
        if observador not in self._observadores:
            self._observadores.append(observador)
    
    def remover_observador(self, observador: Observer) -> None:
        """
        Remueve un observador de la lista
        
        Args:
            observador: Observador a remover
        """
        if observador in self._observadores:
            self._observadores.remove(observador)
    
    def notificar_observadores(self, evento: str, datos: Dict[str, Any]) -> None:
        """
        Notifica a todos los observadores sobre un evento
        
        Args:
            evento: Tipo de evento
            datos: Datos del evento
        """
        for observador in self._observadores:
            try:
                observador.notificar(evento, datos)
            except Exception as e:
                logger.error(
                    f"Error notificando a observador {observador.__class__.__name__}: {e}"
                )


class NotificacionUsuarioObserver(Observer):
    """
    Observer para enviar notificaciones a usuarios específicos
    """
    
    def notificar(self, evento: str, datos: Dict[str, Any]) -> None:
        """
        Envía notificación a usuarios relevantes
        
        Args:
            evento: Tipo de evento
            datos: Datos del evento
        """
        try:
            # Determinar destinatarios según el evento
            destinatarios = self._obtener_destinatarios(evento, datos)
            
            for destinatario_id in destinatarios:
                # Crear notificación usando el factory
                notificacion = NotificacionFactory.crear_notificacion(
                    evento, destinatario_id, datos
                )
                
                if notificacion and 'error' not in notificacion:
                    # Enviar notificación al servicio de usuarios
                    self._enviar_notificacion_usuario(notificacion)
                    
        except Exception as e:
            logger.error(f"Error en NotificacionUsuarioObserver: {e}")
    
    def _obtener_destinatarios(self, evento: str, datos: Dict[str, Any]) -> List[str]:
        """
        Determina los destinatarios según el evento
        
        Args:
            evento: Tipo de evento
            datos: Datos del evento
            
        Returns:
            Lista de IDs de usuarios destinatarios
        """
        destinatarios = []
        
        if evento in ['documento_creado', 'documento_modificado']:
            # Notificar al autor y supervisores
            if 'autor_id' in datos:
                destinatarios.append(datos['autor_id'])
            
            # Obtener supervisores del área
            supervisores = self._obtener_supervisores_area(datos.get('categoria', ''))
            destinatarios.extend(supervisores)
            
        elif evento in ['documento_aprobado', 'documento_rechazado']:
            # Notificar al autor
            if 'autor_id' in datos:
                destinatarios.append(datos['autor_id'])
                
        elif evento == 'solicitud_creada':
            # Notificar a administradores del área
            administradores = self._obtener_administradores_area(datos.get('tipo', ''))
            destinatarios.extend(administradores)
            
        elif evento == 'solicitud_asignada':
            # Notificar al asignado
            if 'asignado_a' in datos:
                destinatarios.append(datos['asignado_a'])
                
        elif evento == 'documento_vencimiento':
            # Notificar a responsables del documento
            if 'autor_id' in datos:
                destinatarios.append(datos['autor_id'])
            if 'responsable_id' in datos:
                destinatarios.append(datos['responsable_id'])
                
        return list(set(destinatarios))  # Eliminar duplicados
    
    def _obtener_supervisores_area(self, categoria: str) -> List[str]:
        """
        Obtiene los supervisores de un área específica
        
        Args:
            categoria: Categoría del documento
            
        Returns:
            Lista de IDs de supervisores
        """
        try:
            # Llamada al servicio de usuarios para obtener supervisores
            response = requests.get(
                f"{settings.USERS_SERVICE_URL}/api/supervisores/",
                params={'categoria': categoria},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return [user['id'] for user in data.get('supervisores', [])]
                
        except Exception as e:
            logger.warning(f"Error obteniendo supervisores: {e}")
            
        return []
    
    def _obtener_administradores_area(self, tipo_solicitud: str) -> List[str]:
        """
        Obtiene los administradores de un área específica
        
        Args:
            tipo_solicitud: Tipo de solicitud
            
        Returns:
            Lista de IDs de administradores
        """
        try:
            # Llamada al servicio de usuarios para obtener administradores
            response = requests.get(
                f"{settings.USERS_SERVICE_URL}/api/administradores/",
                params={'tipo': tipo_solicitud},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                return [user['id'] for user in data.get('administradores', [])]
                
        except Exception as e:
            logger.warning(f"Error obteniendo administradores: {e}")
            
        return []
    
    def _enviar_notificacion_usuario(self, notificacion: Dict[str, Any]) -> None:
        """
        Envía notificación al servicio de usuarios
        
        Args:
            notificacion: Datos de la notificación
        """
        try:
            response = requests.post(
                f"{settings.USERS_SERVICE_URL}/api/notificaciones/",
                json=notificacion,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(
                    f"Notificación enviada a usuario {notificacion['destinatario_id']}"
                )
            else:
                logger.warning(
                    f"Error enviando notificación: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"Error enviando notificación a usuario: {e}")


class EmailObserver(Observer):
    """
    Observer para enviar notificaciones por email
    """
    
    def notificar(self, evento: str, datos: Dict[str, Any]) -> None:
        """
        Envía notificación por email
        
        Args:
            evento: Tipo de evento
            datos: Datos del evento
        """
        try:
            # Solo enviar emails para eventos importantes
            eventos_email = [
                'documento_aprobado',
                'documento_rechazado',
                'solicitud_asignada',
                'documento_vencimiento'
            ]
            
            if evento not in eventos_email:
                return
            
            # Obtener destinatarios de email
            destinatarios_email = self._obtener_emails_destinatarios(evento, datos)
            
            for email in destinatarios_email:
                self._enviar_email(evento, datos, email)
                
        except Exception as e:
            logger.error(f"Error en EmailObserver: {e}")
    
    def _obtener_emails_destinatarios(
        self, 
        evento: str, 
        datos: Dict[str, Any]
    ) -> List[str]:
        """
        Obtiene los emails de los destinatarios
        
        Args:
            evento: Tipo de evento
            datos: Datos del evento
            
        Returns:
            Lista de emails
        """
        emails = []
        
        try:
            # Obtener IDs de usuarios
            user_ids = []
            
            if evento in ['documento_aprobado', 'documento_rechazado']:
                if 'autor_id' in datos:
                    user_ids.append(datos['autor_id'])
                    
            elif evento == 'solicitud_asignada':
                if 'asignado_a' in datos:
                    user_ids.append(datos['asignado_a'])
                    
            elif evento == 'documento_vencimiento':
                if 'autor_id' in datos:
                    user_ids.append(datos['autor_id'])
                if 'responsable_id' in datos:
                    user_ids.append(datos['responsable_id'])
            
            # Obtener emails del servicio de usuarios
            for user_id in user_ids:
                response = requests.get(
                    f"{settings.USERS_SERVICE_URL}/api/usuarios/{user_id}/",
                    timeout=5
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    if user_data.get('email'):
                        emails.append(user_data['email'])
                        
        except Exception as e:
            logger.warning(f"Error obteniendo emails: {e}")
            
        return emails
    
    def _enviar_email(self, evento: str, datos: Dict[str, Any], email: str) -> None:
        """
        Envía email usando un servicio externo
        
        Args:
            evento: Tipo de evento
            datos: Datos del evento
            email: Email destinatario
        """
        try:
            # Crear contenido del email
            asunto, cuerpo = self._generar_contenido_email(evento, datos)
            
            # Datos del email
            email_data = {
                'destinatario': email,
                'asunto': asunto,
                'cuerpo': cuerpo,
                'tipo': 'documentos',
                'datos_adicionales': datos
            }
            
            # Enviar al servicio de email (si existe)
            # Por ahora solo registrar en logs
            logger.info(f"Email a enviar: {email} - {asunto}")
            
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
    
    def _generar_contenido_email(
        self, 
        evento: str, 
        datos: Dict[str, Any]
    ) -> tuple[str, str]:
        """
        Genera el contenido del email
        
        Args:
            evento: Tipo de evento
            datos: Datos del evento
            
        Returns:
            Tupla con (asunto, cuerpo)
        """
        plantillas = {
            'documento_aprobado': {
                'asunto': 'Documento Aprobado: {documento_titulo}',
                'cuerpo': '''
                Su documento "{documento_titulo}" ha sido aprobado.
                
                Detalles:
                - Tipo: {documento_tipo}
                - Código: {documento_codigo}
                - Aprobado por: {aprobador_nombre}
                - Fecha: {fecha_aprobacion}
                
                Puede acceder al documento desde el sistema de gestión documental.
                '''
            },
            'documento_rechazado': {
                'asunto': 'Documento Rechazado: {documento_titulo}',
                'cuerpo': '''
                Su documento "{documento_titulo}" ha sido rechazado.
                
                Detalles:
                - Tipo: {documento_tipo}
                - Código: {documento_codigo}
                - Motivo: {motivo}
                - Rechazado por: {rechazador_nombre}
                - Fecha: {fecha_rechazo}
                
                Por favor, revise los comentarios y realice las correcciones necesarias.
                '''
            },
            'solicitud_asignada': {
                'asunto': 'Nueva Solicitud Asignada: {solicitud_numero}',
                'cuerpo': '''
                Se le ha asignado una nueva solicitud para atender.
                
                Detalles:
                - Número: {solicitud_numero}
                - Título: {solicitud_titulo}
                - Tipo: {solicitud_tipo}
                - Solicitante: {solicitante_nombre}
                - Fecha límite: {fecha_limite}
                
                Ingrese al sistema para revisar los detalles completos.
                '''
            },
            'documento_vencimiento': {
                'asunto': 'Documento Próximo a Vencer: {documento_titulo}',
                'cuerpo': '''
                El documento "{documento_titulo}" está próximo a vencer.
                
                Detalles:
                - Código: {documento_codigo}
                - Fecha de vencimiento: {fecha_vencimiento}
                - Días restantes: {dias_restantes}
                
                Por favor, revise si es necesario renovar o actualizar el documento.
                '''
            }
        }
        
        plantilla = plantillas.get(evento, {
            'asunto': 'Notificación del Sistema Documental',
            'cuerpo': 'Ha ocurrido un evento en el sistema documental.'
        })
        
        try:
            asunto = plantilla['asunto'].format(**datos)
            cuerpo = plantilla['cuerpo'].format(**datos)
            return asunto, cuerpo
        except KeyError:
            return plantilla['asunto'], plantilla['cuerpo']


class AuditoriaObserver(Observer):
    """
    Observer para registrar eventos de auditoría
    """
    
    def notificar(self, evento: str, datos: Dict[str, Any]) -> None:
        """
        Registra evento de auditoría
        
        Args:
            evento: Tipo de evento
            datos: Datos del evento
        """
        try:
            # Crear registro de auditoría
            registro = {
                'timestamp': timezone.now().isoformat(),
                'evento': evento,
                'modulo': 'documentos',
                'datos': datos,
                'ip_address': datos.get('ip_address'),
                'user_agent': datos.get('user_agent')
            }
            
            # Registrar en logs
            logger.info(f"Auditoría: {evento} - {json.dumps(registro)}")
            
            # Enviar al servicio de auditoría si existe
            self._enviar_auditoria(registro)
            
        except Exception as e:
            logger.error(f"Error en AuditoriaObserver: {e}")
    
    def _enviar_auditoria(self, registro: Dict[str, Any]) -> None:
        """
        Envía registro de auditoría a servicio externo
        
        Args:
            registro: Datos del registro
        """
        try:
            # Por ahora solo almacenar localmente
            # En el futuro se puede integrar con un servicio de auditoría
            pass
            
        except Exception as e:
            logger.error(f"Error enviando auditoría: {e}")


class EstadisticasObserver(Observer):
    """
    Observer para actualizar estadísticas del sistema
    """
    
    def notificar(self, evento: str, datos: Dict[str, Any]) -> None:
        """
        Actualiza estadísticas según el evento
        
        Args:
            evento: Tipo de evento
            datos: Datos del evento
        """
        try:
            # Eventos que afectan estadísticas
            if evento == 'documento_creado':
                self._incrementar_contador('documentos_creados')
                self._incrementar_contador_tipo(datos.get('documento_tipo', 'OTRO'))
                
            elif evento == 'documento_aprobado':
                self._incrementar_contador('documentos_aprobados')
                
            elif evento == 'documento_rechazado':
                self._incrementar_contador('documentos_rechazados')
                
            elif evento == 'solicitud_creada':
                self._incrementar_contador('solicitudes_creadas')
                self._incrementar_contador_solicitud(datos.get('solicitud_tipo', 'OTRO'))
                
            elif evento == 'documento_descargado':
                self._incrementar_contador('descargas_totales')
                
        except Exception as e:
            logger.error(f"Error en EstadisticasObserver: {e}")
    
    def _incrementar_contador(self, tipo_contador: str) -> None:
        """
        Incrementa un contador de estadísticas
        
        Args:
            tipo_contador: Tipo de contador a incrementar
        """
        try:
            # Por ahora almacenar en cache local
            # En el futuro integrar con Redis o base de datos
            from django.core.cache import cache
            
            key = f"stats:{tipo_contador}:{timezone.now().date()}"
            current = cache.get(key, 0)
            cache.set(key, current + 1, 86400)  # 24 horas
            
        except Exception as e:
            logger.warning(f"Error incrementando contador {tipo_contador}: {e}")
    
    def _incrementar_contador_tipo(self, tipo_documento: str) -> None:
        """
        Incrementa contador por tipo de documento
        
        Args:
            tipo_documento: Tipo de documento
        """
        try:
            from django.core.cache import cache
            
            key = f"stats:doc_tipo:{tipo_documento}:{timezone.now().date()}"
            current = cache.get(key, 0)
            cache.set(key, current + 1, 86400)
            
        except Exception as e:
            logger.warning(f"Error incrementando contador tipo: {e}")
    
    def _incrementar_contador_solicitud(self, tipo_solicitud: str) -> None:
        """
        Incrementa contador por tipo de solicitud
        
        Args:
            tipo_solicitud: Tipo de solicitud
        """
        try:
            from django.core.cache import cache
            
            key = f"stats:sol_tipo:{tipo_solicitud}:{timezone.now().date()}"
            current = cache.get(key, 0)
            cache.set(key, current + 1, 86400)
            
        except Exception as e:
            logger.warning(f"Error incrementando contador solicitud: {e}")


class DocumentoObservable(Observable):
    """
    Clase observable específica para documentos
    
    Maneja los eventos relacionados con documentos
    """
    
    def __init__(self):
        super().__init__()
        # Agregar observadores por defecto
        self.agregar_observador(NotificacionUsuarioObserver())
        self.agregar_observador(EmailObserver())
        self.agregar_observador(AuditoriaObserver())
        self.agregar_observador(EstadisticasObserver())
    
    def documento_creado(self, documento, usuario_id: str, ip_address: str = None):
        """
        Notifica creación de documento
        
        Args:
            documento: Instancia del documento creado
            usuario_id: ID del usuario que creó el documento
            ip_address: IP del usuario
        """
        datos = {
            'documento_id': str(documento.id),
            'documento_titulo': documento.titulo,
            'documento_tipo': documento.get_tipo_display(),
            'documento_codigo': documento.codigo_documento,
            'autor_id': documento.autor_id,
            'usuario_id': usuario_id,
            'categoria': documento.categoria,
            'ip_address': ip_address,
            'timestamp': timezone.now().isoformat()
        }
        
        self.notificar_observadores('documento_creado', datos)
    
    def documento_aprobado(
        self, 
        documento, 
        aprobador_id: str, 
        aprobador_nombre: str,
        ip_address: str = None
    ):
        """
        Notifica aprobación de documento
        
        Args:
            documento: Instancia del documento aprobado
            aprobador_id: ID del usuario que aprobó
            aprobador_nombre: Nombre del aprobador
            ip_address: IP del usuario
        """
        datos = {
            'documento_id': str(documento.id),
            'documento_titulo': documento.titulo,
            'documento_tipo': documento.get_tipo_display(),
            'documento_codigo': documento.codigo_documento,
            'autor_id': documento.autor_id,
            'aprobador_id': aprobador_id,
            'aprobador_nombre': aprobador_nombre,
            'fecha_aprobacion': documento.fecha_aprobacion.isoformat() if documento.fecha_aprobacion else '',
            'ip_address': ip_address,
            'timestamp': timezone.now().isoformat()
        }
        
        self.notificar_observadores('documento_aprobado', datos)
    
    def documento_rechazado(
        self, 
        documento, 
        rechazador_id: str, 
        rechazador_nombre: str,
        motivo: str,
        ip_address: str = None
    ):
        """
        Notifica rechazo de documento
        
        Args:
            documento: Instancia del documento rechazado
            rechazador_id: ID del usuario que rechazó
            rechazador_nombre: Nombre del rechazador
            motivo: Motivo del rechazo
            ip_address: IP del usuario
        """
        datos = {
            'documento_id': str(documento.id),
            'documento_titulo': documento.titulo,
            'documento_tipo': documento.get_tipo_display(),
            'documento_codigo': documento.codigo_documento,
            'autor_id': documento.autor_id,
            'rechazador_id': rechazador_id,
            'rechazador_nombre': rechazador_nombre,
            'motivo': motivo,
            'fecha_rechazo': timezone.now().isoformat(),
            'ip_address': ip_address,
            'timestamp': timezone.now().isoformat()
        }
        
        self.notificar_observadores('documento_rechazado', datos)


class SolicitudObservable(Observable):
    """
    Clase observable específica para solicitudes
    """
    
    def __init__(self):
        super().__init__()
        # Agregar observadores por defecto
        self.agregar_observador(NotificacionUsuarioObserver())
        self.agregar_observador(EmailObserver())
        self.agregar_observador(AuditoriaObserver())
        self.agregar_observador(EstadisticasObserver())
    
    def solicitud_creada(self, solicitud, ip_address: str = None):
        """
        Notifica creación de solicitud
        
        Args:
            solicitud: Instancia de la solicitud creada
            ip_address: IP del usuario
        """
        datos = {
            'solicitud_id': str(solicitud.id),
            'solicitud_numero': solicitud.numero_seguimiento,
            'solicitud_titulo': solicitud.titulo,
            'solicitud_tipo': solicitud.get_tipo_display(),
            'solicitante_id': solicitud.solicitante_id,
            'tipo': solicitud.tipo,
            'ip_address': ip_address,
            'timestamp': timezone.now().isoformat()
        }
        
        self.notificar_observadores('solicitud_creada', datos)
    
    def solicitud_asignada(
        self, 
        solicitud, 
        asignado_por: str,
        ip_address: str = None
    ):
        """
        Notifica asignación de solicitud
        
        Args:
            solicitud: Instancia de la solicitud asignada
            asignado_por: ID del usuario que asignó
            ip_address: IP del usuario
        """
        datos = {
            'solicitud_id': str(solicitud.id),
            'solicitud_numero': solicitud.numero_seguimiento,
            'solicitud_titulo': solicitud.titulo,
            'solicitud_tipo': solicitud.get_tipo_display(),
            'solicitante_id': solicitud.solicitante_id,
            'asignado_a': solicitud.asignado_a,
            'asignado_por': asignado_por,
            'fecha_limite': solicitud.fecha_limite.isoformat() if solicitud.fecha_limite else '',
            'ip_address': ip_address,
            'timestamp': timezone.now().isoformat()
        }
        
        self.notificar_observadores('solicitud_asignada', datos)


# Instancias globales de observables
documento_observable = DocumentoObservable()
solicitud_observable = SolicitudObservable()