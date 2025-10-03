"""
Middleware y utilidades para observar cambios en otros microservicios
"""

import json
import logging
import requests
from typing import Dict, Any, Optional
from django.conf import settings
from django.utils import timezone
from datetime import datetime

from ..services import AuditoriaService

logger = logging.getLogger('audit.observer')


class MicroserviceObserver:
    """
    Observer para registrar cambios en otros microservicios
    """
    
    def __init__(self):
        self.auditoria_service = AuditoriaService()
        self.config = getattr(settings, 'OBSERVER_CONFIG', {})
        self.enabled = self.config.get('ENABLED', True)
        self.microservices = self.config.get('MICROSERVICES', {})
    
    def notify_document_change(self, action: str, document_id: str, user_id: Optional[int] = None, 
                             details: Optional[Dict] = None):
        """
        Notificar cambio en documentos
        """
        if not self.enabled:
            return
        
        try:
            self.auditoria_service.registrar_cambio_documento(
                usuario_id=user_id,
                documento_id=document_id,
                accion=action,
                detalle=details or {},
                microservicio='DOCUMENTS'
            )
            logger.info(f"Registrado cambio en documento {document_id}: {action}")
            
        except Exception as e:
            logger.error(f"Error al registrar cambio de documento: {str(e)}")
    
    def notify_payment_change(self, action: str, payment_id: str, user_id: Optional[int] = None,
                            details: Optional[Dict] = None):
        """
        Notificar cambio en pagos
        """
        if not self.enabled:
            return
        
        try:
            self.auditoria_service.registrar_cambio_pago(
                usuario_id=user_id,
                pago_id=payment_id,
                accion=action,
                detalle=details or {},
                microservicio='PAYMENTS'
            )
            logger.info(f"Registrado cambio en pago {payment_id}: {action}")
            
        except Exception as e:
            logger.error(f"Error al registrar cambio de pago: {str(e)}")
    
    def notify_user_change(self, action: str, user_id: int, details: Optional[Dict] = None):
        """
        Notificar cambio en usuarios
        """
        if not self.enabled:
            return
        
        try:
            self.auditoria_service.registrar_cambio_usuario(
                usuario_id=user_id,
                accion=action,
                detalle=details or {},
                microservicio='USERS'
            )
            logger.info(f"Registrado cambio en usuario {user_id}: {action}")
            
        except Exception as e:
            logger.error(f"Error al registrar cambio de usuario: {str(e)}")
    
    def notify_attendance_change(self, action: str, attendance_id: str, user_id: Optional[int] = None,
                               details: Optional[Dict] = None):
        """
        Notificar cambio en asistencias
        """
        if not self.enabled:
            return
        
        try:
            self.auditoria_service.registrar_cambio_asistencia(
                usuario_id=user_id,
                asistencia_id=attendance_id,
                accion=action,
                detalle=details or {},
                microservicio='ATTENDANCE'
            )
            logger.info(f"Registrado cambio en asistencia {attendance_id}: {action}")
            
        except Exception as e:
            logger.error(f"Error al registrar cambio de asistencia: {str(e)}")
    
    def notify_custom_event(self, event_type: str, resource: str, resource_id: str,
                          user_id: Optional[int] = None, details: Optional[Dict] = None,
                          microservice: str = 'UNKNOWN'):
        """
        Notificar evento personalizado
        """
        if not self.enabled:
            return
        
        try:
            self.auditoria_service.registrar_evento_personalizado(
                usuario_id=user_id,
                tipo_evento=event_type,
                recurso=resource,
                recurso_id=resource_id,
                detalle=details or {},
                microservicio=microservice
            )
            logger.info(f"Registrado evento personalizado {event_type} en {resource} {resource_id}")
            
        except Exception as e:
            logger.error(f"Error al registrar evento personalizado: {str(e)}")


class WebhookHandler:
    """
    Manejador de webhooks para recibir notificaciones de otros microservicios
    """
    
    def __init__(self):
        self.observer = MicroserviceObserver()
    
    def handle_document_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Manejar webhook de documentos
        """
        try:
            action = payload.get('action')
            document_id = payload.get('document_id')
            user_id = payload.get('user_id')
            details = payload.get('details', {})
            
            if not action or not document_id:
                logger.warning("Webhook de documento inválido: faltan campos requeridos")
                return False
            
            self.observer.notify_document_change(
                action=action,
                document_id=document_id,
                user_id=user_id,
                details=details
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error al procesar webhook de documento: {str(e)}")
            return False
    
    def handle_payment_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Manejar webhook de pagos
        """
        try:
            action = payload.get('action')
            payment_id = payload.get('payment_id')
            user_id = payload.get('user_id')
            details = payload.get('details', {})
            
            if not action or not payment_id:
                logger.warning("Webhook de pago inválido: faltan campos requeridos")
                return False
            
            self.observer.notify_payment_change(
                action=action,
                payment_id=payment_id,
                user_id=user_id,
                details=details
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error al procesar webhook de pago: {str(e)}")
            return False
    
    def handle_user_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Manejar webhook de usuarios
        """
        try:
            action = payload.get('action')
            user_id = payload.get('user_id')
            details = payload.get('details', {})
            
            if not action or not user_id:
                logger.warning("Webhook de usuario inválido: faltan campos requeridos")
                return False
            
            self.observer.notify_user_change(
                action=action,
                user_id=user_id,
                details=details
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error al procesar webhook de usuario: {str(e)}")
            return False
    
    def handle_attendance_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Manejar webhook de asistencias
        """
        try:
            action = payload.get('action')
            attendance_id = payload.get('attendance_id')
            user_id = payload.get('user_id')
            details = payload.get('details', {})
            
            if not action or not attendance_id:
                logger.warning("Webhook de asistencia inválido: faltan campos requeridos")
                return False
            
            self.observer.notify_attendance_change(
                action=action,
                attendance_id=attendance_id,
                user_id=user_id,
                details=details
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error al procesar webhook de asistencia: {str(e)}")
            return False
    
    def handle_generic_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Manejar webhook genérico
        """
        try:
            event_type = payload.get('event_type')
            resource = payload.get('resource')
            resource_id = payload.get('resource_id')
            user_id = payload.get('user_id')
            details = payload.get('details', {})
            microservice = payload.get('microservice', 'UNKNOWN')
            
            if not event_type or not resource or not resource_id:
                logger.warning("Webhook genérico inválido: faltan campos requeridos")
                return False
            
            self.observer.notify_custom_event(
                event_type=event_type,
                resource=resource,
                resource_id=resource_id,
                user_id=user_id,
                details=details,
                microservice=microservice
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error al procesar webhook genérico: {str(e)}")
            return False


class AuditNotifier:
    """
    Cliente para notificar al microservicio de auditoría desde otros servicios
    """
    
    def __init__(self, audit_service_url: Optional[str] = None):
        self.audit_service_url = audit_service_url or 'http://localhost:3007'
        self.webhook_endpoints = {
            'document': '/api/webhooks/documents/',
            'payment': '/api/webhooks/payments/',
            'user': '/api/webhooks/users/',
            'attendance': '/api/webhooks/attendance/',
            'generic': '/api/webhooks/generic/'
        }
        self.timeout = 5  # seconds
    
    def notify_document_change(self, action: str, document_id: str, user_id: Optional[int] = None,
                             details: Optional[Dict] = None) -> bool:
        """
        Notificar cambio en documento al servicio de auditoría
        """
        payload = {
            'action': action,
            'document_id': document_id,
            'user_id': user_id,
            'details': details or {},
            'timestamp': timezone.now().isoformat()
        }
        
        return self._send_webhook('document', payload)
    
    def notify_payment_change(self, action: str, payment_id: str, user_id: Optional[int] = None,
                            details: Optional[Dict] = None) -> bool:
        """
        Notificar cambio en pago al servicio de auditoría
        """
        payload = {
            'action': action,
            'payment_id': payment_id,
            'user_id': user_id,
            'details': details or {},
            'timestamp': timezone.now().isoformat()
        }
        
        return self._send_webhook('payment', payload)
    
    def notify_user_change(self, action: str, user_id: int, details: Optional[Dict] = None) -> bool:
        """
        Notificar cambio en usuario al servicio de auditoría
        """
        payload = {
            'action': action,
            'user_id': user_id,
            'details': details or {},
            'timestamp': timezone.now().isoformat()
        }
        
        return self._send_webhook('user', payload)
    
    def notify_attendance_change(self, action: str, attendance_id: str, user_id: Optional[int] = None,
                               details: Optional[Dict] = None) -> bool:
        """
        Notificar cambio en asistencia al servicio de auditoría
        """
        payload = {
            'action': action,
            'attendance_id': attendance_id,
            'user_id': user_id,
            'details': details or {},
            'timestamp': timezone.now().isoformat()
        }
        
        return self._send_webhook('attendance', payload)
    
    def notify_custom_event(self, event_type: str, resource: str, resource_id: str,
                          user_id: Optional[int] = None, details: Optional[Dict] = None,
                          microservice: str = 'UNKNOWN') -> bool:
        """
        Notificar evento personalizado al servicio de auditoría
        """
        payload = {
            'event_type': event_type,
            'resource': resource,
            'resource_id': resource_id,
            'user_id': user_id,
            'details': details or {},
            'microservice': microservice,
            'timestamp': timezone.now().isoformat()
        }
        
        return self._send_webhook('generic', payload)
    
    def _send_webhook(self, webhook_type: str, payload: Dict[str, Any]) -> bool:
        """
        Enviar webhook al servicio de auditoría
        """
        try:
            endpoint = self.webhook_endpoints.get(webhook_type)
            if not endpoint:
                logger.error(f"Tipo de webhook desconocido: {webhook_type}")
                return False
            
            url = f"{self.audit_service_url}{endpoint}"
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook {webhook_type} enviado exitosamente")
                return True
            else:
                logger.warning(f"Webhook {webhook_type} falló con código {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error al enviar webhook {webhook_type}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado al enviar webhook {webhook_type}: {str(e)}")
            return False


# Instancia global del observador
observer = MicroserviceObserver()

# Instancia global del notificador (para usar en otros microservicios)
notifier = AuditNotifier()

# Instancia global del manejador de webhooks
webhook_handler = WebhookHandler()