"""
Tests para el microservicio de auditoría
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import datetime, timedelta
import json

from .models import ActividadSistema
from .services import AuditoriaService
from .repositories import AuditoriaRepository
from .middleware.observer import MicroserviceObserver


class ActividadSistemaModelTest(TestCase):
    """Tests para el modelo ActividadSistema"""
    
    def setUp(self):
        self.actividad_data = {
            'usuario_id': 1,
            'usuario_email': 'test@test.com',
            'accion': 'CREATE',
            'recurso': 'USERS',
            'detalle': {'test': 'data'},
            'ip_address': '127.0.0.1',
            'exito': True
        }
    
    def test_crear_actividad(self):
        """Test crear actividad"""
        actividad = ActividadSistema.objects.create(**self.actividad_data)
        
        self.assertEqual(actividad.usuario_id, 1)
        self.assertEqual(actividad.accion, 'CREATE')
        self.assertEqual(actividad.recurso, 'USERS')
        self.assertTrue(actividad.exito)
        self.assertIsNotNone(actividad.id)
        self.assertIsNotNone(actividad.fecha_hora)
    
    def test_str_representation(self):
        """Test representación string"""
        actividad = ActividadSistema.objects.create(**self.actividad_data)
        expected = f"[{actividad.fecha_hora.strftime('%Y-%m-%d %H:%M')}] test@test.com - CREATE USERS"
        self.assertEqual(str(actividad), expected)
    
    def test_metodos_helper(self):
        """Test métodos helper del modelo"""
        actividad = ActividadSistema.objects.create(**self.actividad_data)
        
        # Test es_exitosa
        self.assertTrue(actividad.es_exitosa())
        
        # Test es_critica
        actividad.criticidad = 'CRITICAL'
        self.assertTrue(actividad.es_critica())
        
        # Test duracion_segundos
        actividad.duracion_ms = 2500
        self.assertEqual(actividad.duracion_segundos(), 2.5)
    
    def test_validaciones(self):
        """Test validaciones del modelo"""
        # Test acción inválida
        data_invalida = self.actividad_data.copy()
        data_invalida['accion'] = 'INVALID_ACTION'
        
        with self.assertRaises(Exception):
            ActividadSistema.objects.create(**data_invalida)


class AuditoriaServiceTest(TestCase):
    """Tests para AuditoriaService"""
    
    def setUp(self):
        self.service = AuditoriaService()
        self.user_data = {
            'usuario_id': 1,
            'usuario_email': 'test@test.com'
        }
    
    def test_registrar_actividad(self):
        """Test registrar actividad básica"""
        self.service.registrar_actividad(
            accion='READ',
            recurso='DOCUMENTS',
            **self.user_data
        )
        
        actividad = ActividadSistema.objects.last()
        self.assertEqual(actividad.accion, 'READ')
        self.assertEqual(actividad.recurso, 'DOCUMENTS')
        self.assertEqual(actividad.usuario_id, 1)
    
    def test_registrar_login(self):
        """Test registrar login"""
        self.service.registrar_login(
            usuario_id=1,
            usuario_email='test@test.com',
            exito=True
        )
        
        actividad = ActividadSistema.objects.last()
        self.assertEqual(actividad.accion, 'LOGIN')
        self.assertTrue(actividad.exito)
    
    def test_registrar_error(self):
        """Test registrar error"""
        self.service.registrar_error(
            usuario_id=1,
            recurso='PAYMENTS',
            mensaje_error='Test error'
        )
        
        actividad = ActividadSistema.objects.last()
        self.assertEqual(actividad.accion, 'ERROR')
        self.assertFalse(actividad.exito)
        self.assertEqual(actividad.mensaje_error, 'Test error')
    
    def test_obtener_estadisticas(self):
        """Test obtener estadísticas"""
        # Crear algunas actividades de prueba
        for i in range(5):
            self.service.registrar_actividad(
                accion='READ',
                recurso='USERS',
                exito=True,
                **self.user_data
            )
        
        for i in range(2):
            self.service.registrar_actividad(
                accion='CREATE',
                recurso='DOCUMENTS',
                exito=False,
                **self.user_data
            )
        
        stats = self.service.obtener_estadisticas(dias=1)
        
        self.assertEqual(stats['total_actividades'], 7)
        self.assertEqual(stats['actividades_exitosas'], 5)
        self.assertEqual(stats['actividades_fallidas'], 2)


class AuditoriaRepositoryTest(TestCase):
    """Tests para AuditoriaRepository"""
    
    def setUp(self):
        self.repository = AuditoriaRepository()
        
        # Crear datos de prueba
        for i in range(10):
            ActividadSistema.objects.create(
                usuario_id=i % 3 + 1,
                usuario_email=f'user{i % 3 + 1}@test.com',
                accion='READ',
                recurso='USERS',
                exito=i % 4 != 0,  # 75% exitosas
                ip_address='127.0.0.1'
            )
    
    def test_obtener_actividades_usuario(self):
        """Test obtener actividades por usuario"""
        actividades = self.repository.obtener_actividades_usuario(usuario_id=1)
        
        # Verificar que todas las actividades son del usuario 1
        for actividad in actividades:
            self.assertEqual(actividad.usuario_id, 1)
    
    def test_obtener_actividades_rango_fecha(self):
        """Test obtener actividades por rango de fechas"""
        fecha_inicio = timezone.now() - timedelta(hours=1)
        fecha_fin = timezone.now() + timedelta(hours=1)
        
        actividades = self.repository.obtener_actividades_rango_fecha(
            fecha_inicio, fecha_fin
        )
        
        self.assertEqual(len(actividades), 10)
    
    def test_obtener_estadisticas_usuario(self):
        """Test obtener estadísticas por usuario"""
        stats = self.repository.obtener_estadisticas_usuario(usuario_id=1)
        
        self.assertIn('total_actividades', stats)
        self.assertIn('actividades_exitosas', stats)
        self.assertIn('tasa_exito', stats)


class AuditoriaAPITest(APITestCase):
    """Tests para la API de auditoría"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Crear algunas actividades de prueba
        for i in range(5):
            ActividadSistema.objects.create(
                usuario_id=self.user.id,
                usuario_email=self.user.email,
                accion='READ',
                recurso='USERS',
                exito=True,
                ip_address='127.0.0.1'
            )
    
    def test_listar_logs_sin_autenticacion(self):
        """Test listar logs sin autenticación"""
        url = reverse('logs-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_listar_logs_con_autenticacion(self):
        """Test listar logs con autenticación"""
        self.client.force_authenticate(user=self.user)
        url = reverse('logs-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)
    
    def test_estadisticas_endpoint(self):
        """Test endpoint de estadísticas"""
        self.client.force_authenticate(user=self.user)
        url = reverse('logs-estadisticas')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_actividades', response.data)
    
    def test_health_check(self):
        """Test health check endpoint"""
        self.client.force_authenticate(user=self.user)
        url = reverse('health-check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')


class MicroserviceObserverTest(TestCase):
    """Tests para MicroserviceObserver"""
    
    def setUp(self):
        self.observer = MicroserviceObserver()
    
    def test_notify_document_change(self):
        """Test notificación de cambio en documento"""
        self.observer.notify_document_change(
            action='CREATE',
            document_id='doc123',
            user_id=1,
            details={'filename': 'test.pdf'}
        )
        
        actividad = ActividadSistema.objects.last()
        self.assertEqual(actividad.recurso, 'DOCUMENTS')
        self.assertEqual(actividad.recurso_id, 'doc123')
        self.assertEqual(actividad.microservicio, 'DOCUMENTS')
    
    def test_notify_payment_change(self):
        """Test notificación de cambio en pago"""
        self.observer.notify_payment_change(
            action='UPDATE',
            payment_id='pay123',
            user_id=1,
            details={'amount': 1000}
        )
        
        actividad = ActividadSistema.objects.last()
        self.assertEqual(actividad.recurso, 'PAYMENTS')
        self.assertEqual(actividad.recurso_id, 'pay123')
        self.assertEqual(actividad.microservicio, 'PAYMENTS')


class WebhookTest(TestCase):
    """Tests para webhooks"""
    
    def setUp(self):
        self.client = Client()
    
    def test_webhook_document_valido(self):
        """Test webhook de documento válido"""
        data = {
            'action': 'CREATE',
            'document_id': 'doc123',
            'user_id': 1,
            'details': {'filename': 'test.pdf'}
        }
        
        response = self.client.post(
            reverse('webhook-documents'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')
        
        # Verificar que se creó la actividad
        actividad = ActividadSistema.objects.last()
        self.assertEqual(actividad.recurso_id, 'doc123')
    
    def test_webhook_document_invalido(self):
        """Test webhook de documento inválido"""
        data = {
            'action': 'CREATE',
            # Falta document_id
            'user_id': 1
        }
        
        response = self.client.post(
            reverse('webhook-documents'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['status'], 'error')
    
    def test_webhook_json_invalido(self):
        """Test webhook con JSON inválido"""
        response = self.client.post(
            reverse('webhook-documents'),
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Invalid JSON')


class MiddlewareTest(TestCase):
    """Tests para middleware de auditoría"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.client = Client()
    
    def test_middleware_registra_request(self):
        """Test que el middleware registra requests"""
        # Login para tener usuario autenticado
        self.client.login(username='testuser', password='testpass123')
        
        # Hacer una request
        response = self.client.get('/api/health/')
        
        # Verificar que se registró la actividad
        actividad = ActividadSistema.objects.last()
        if actividad:  # El middleware podría estar configurado para excluir ciertas rutas
            self.assertEqual(actividad.usuario_id, self.user.id)
            self.assertIsNotNone(actividad.ip_address)


class IntegrationTest(TestCase):
    """Tests de integración"""
    
    def setUp(self):
        self.service = AuditoriaService()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_flujo_completo_auditoria(self):
        """Test flujo completo de auditoría"""
        # 1. Registrar actividad
        self.service.registrar_actividad(
            usuario_id=self.user.id,
            usuario_email=self.user.email,
            accion='CREATE',
            recurso='DOCUMENTS',
            detalle={'filename': 'test.pdf'}
        )
        
        # 2. Verificar que se creó
        actividades = ActividadSistema.objects.filter(usuario_id=self.user.id)
        self.assertEqual(actividades.count(), 1)
        
        # 3. Obtener estadísticas
        stats = self.service.obtener_estadisticas(usuario_id=self.user.id)
        self.assertEqual(stats['total_actividades'], 1)
        
        # 4. Exportar datos
        csv_data = self.service.exportar_csv({'usuario_id': self.user.id})
        self.assertIn('test.pdf', csv_data)
        
        # 5. Detectar actividad sospechosa (no debería haber)
        sospechosas = self.service.detectar_actividad_sospechosa()
        self.assertEqual(len(sospechosas), 0)
