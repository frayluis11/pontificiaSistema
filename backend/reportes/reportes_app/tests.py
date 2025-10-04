"""
Tests para el microservicio de reportes
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, date
import json
import tempfile
import os

from .models import Reporte, Metrica, ReporteMetrica
from .services import ReporteService, MetricaService
from .repositories import ReporteRepository, MetricaRepository
from .exceptions import (
    ReporteNoEncontradoException, FormatoNoSoportadoException,
    ParametrosInvalidosException
)


# ========== Tests de Modelos ==========

class ReporteModelTest(TestCase):
    """Tests para el modelo Reporte"""
    
    def setUp(self):
        """Configuración inicial para tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
    
    def test_crear_reporte(self):
        """Test creación de reporte"""
        reporte = Reporte.objects.create(
            tipo='ventas',
            formato='pdf',
            autor_id=self.user.id,
            titulo='Reporte de prueba',
            parametros={'fecha_inicio': '2024-01-01'}
        )
        
        self.assertEqual(reporte.tipo, 'ventas')
        self.assertEqual(reporte.formato, 'pdf')
        self.assertEqual(reporte.estado, 'pendiente')
        self.assertEqual(reporte.autor_id, self.user.id)
        self.assertIsNotNone(reporte.id)
        self.assertIsNotNone(reporte.fecha_creacion)
    
    def test_reporte_str(self):
        """Test representación string del reporte"""
        reporte = Reporte.objects.create(
            tipo='usuarios',
            formato='excel',
            autor_id=self.user.id,
            titulo='Test Reporte'
        )
        expected = f"Reporte usuarios - excel ({reporte.id})"
        self.assertEqual(str(reporte), expected)
    
    def test_reporte_expirado(self):
        """Test verificación de expiración"""
        # Reporte expirado
        reporte_expirado = Reporte.objects.create(
            tipo='ventas',
            formato='pdf',
            autor_id=self.user.id,
            expires_at=timezone.now() - timedelta(days=1)
        )
        self.assertTrue(reporte_expirado.esta_expirado())
        
        # Reporte válido
        reporte_valido = Reporte.objects.create(
            tipo='ventas',
            formato='pdf',
            autor_id=self.user.id,
            expires_at=timezone.now() + timedelta(days=1)
        )
        self.assertFalse(reporte_valido.esta_expirado())
    
    def test_validar_parametros(self):
        """Test validación de parámetros"""
        reporte = Reporte(
            tipo='ventas',
            formato='pdf',
            autor_id=self.user.id
        )
        
        # Parámetros válidos
        parametros_validos = {
            'fecha_inicio': '2024-01-01',
            'fecha_fin': '2024-01-31'
        }
        self.assertTrue(reporte.validar_parametros(parametros_validos))
        
        # Parámetros inválidos (fecha_inicio > fecha_fin)
        parametros_invalidos = {
            'fecha_inicio': '2024-01-31',
            'fecha_fin': '2024-01-01'
        }
        self.assertFalse(reporte.validar_parametros(parametros_invalidos))


class MetricaModelTest(TestCase):
    """Tests para el modelo Métrica"""
    
    def test_crear_metrica(self):
        """Test creación de métrica"""
        metrica = Metrica.objects.create(
            nombre='ventas_totales',
            valor=15000.50,
            periodo='mensual'
        )
        
        self.assertEqual(metrica.nombre, 'ventas_totales')
        self.assertEqual(metrica.valor, 15000.50)
        self.assertEqual(metrica.periodo, 'mensual')
        self.assertTrue(metrica.activa)
        self.assertIsNotNone(metrica.fecha_calculo)
    
    def test_metrica_str(self):
        """Test representación string de métrica"""
        metrica = Metrica.objects.create(
            nombre='usuarios_activos',
            valor=1200,
            periodo='diario'
        )
        expected = f"usuarios_activos: 1200.0 (diario)"
        self.assertEqual(str(metrica), expected)
    
    def test_formatear_valor(self):
        """Test formateo de valores"""
        # Métrica de porcentaje
        metrica_porcentaje = Metrica.objects.create(
            nombre='tasa_conversion',
            valor=15.75,
            periodo='mensual',
            metadatos={'formato': 'porcentaje'}
        )
        self.assertEqual(metrica_porcentaje.formatear_valor(), "15.75%")
        
        # Métrica de moneda
        metrica_moneda = Metrica.objects.create(
            nombre='ingresos',
            valor=25000.99,
            periodo='mensual',
            metadatos={'formato': 'moneda'}
        )
        self.assertEqual(metrica_moneda.formatear_valor(), "$25,000.99")


# ========== Tests de Repositorios ==========

class ReporteRepositoryTest(TestCase):
    """Tests para ReporteRepository"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.repository = ReporteRepository()
    
    def test_crear_reporte(self):
        """Test creación de reporte a través del repositorio"""
        datos = {
            'tipo': 'ventas',
            'formato': 'pdf',
            'autor_id': self.user.id,
            'titulo': 'Reporte de ventas'
        }
        
        reporte = self.repository.crear(datos)
        self.assertIsInstance(reporte, Reporte)
        self.assertEqual(reporte.tipo, 'ventas')
    
    def test_obtener_por_autor(self):
        """Test obtener reportes por autor"""
        # Crear reportes
        Reporte.objects.create(
            tipo='ventas', formato='pdf', autor_id=self.user.id
        )
        Reporte.objects.create(
            tipo='usuarios', formato='excel', autor_id=self.user.id
        )
        
        # Otro usuario
        otro_user = User.objects.create_user(
            username='otro', email='otro@example.com', password='pass'
        )
        Reporte.objects.create(
            tipo='ventas', formato='pdf', autor_id=otro_user.id
        )
        
        reportes = self.repository.obtener_por_autor(self.user.id)
        self.assertEqual(reportes.count(), 2)
    
    def test_obtener_estadisticas(self):
        """Test obtener estadísticas"""
        # Crear reportes con diferentes estados
        Reporte.objects.create(
            tipo='ventas', formato='pdf', autor_id=self.user.id, estado='completado'
        )
        Reporte.objects.create(
            tipo='usuarios', formato='excel', autor_id=self.user.id, estado='pendiente'
        )
        
        stats = self.repository.obtener_estadisticas(self.user.id)
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['completados'], 1)
        self.assertEqual(stats['pendientes'], 1)


class MetricaRepositoryTest(TestCase):
    """Tests para MetricaRepository"""
    
    def setUp(self):
        """Configuración inicial"""
        self.repository = MetricaRepository()
    
    def test_obtener_por_periodo(self):
        """Test obtener métricas por período"""
        # Crear métricas
        Metrica.objects.create(
            nombre='ventas', valor=1000, periodo='mensual'
        )
        Metrica.objects.create(
            nombre='usuarios', valor=500, periodo='diario'
        )
        Metrica.objects.create(
            nombre='ingresos', valor=2000, periodo='mensual'
        )
        
        metricas_mensuales = self.repository.obtener_por_periodo('mensual')
        self.assertEqual(metricas_mensuales.count(), 2)
    
    def test_calcular_promedio(self):
        """Test cálculo de promedio"""
        # Crear métricas del mismo tipo
        Metrica.objects.create(
            nombre='ventas_diarias', valor=100, periodo='diario'
        )
        Metrica.objects.create(
            nombre='ventas_diarias', valor=200, periodo='diario'
        )
        Metrica.objects.create(
            nombre='ventas_diarias', valor=150, periodo='diario'
        )
        
        promedio = self.repository.calcular_promedio('ventas_diarias', 'diario')
        self.assertEqual(promedio, 150.0)


# ========== Tests de Servicios ==========

class ReporteServiceTest(TestCase):
    """Tests para ReporteService"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.service = ReporteService()
    
    @patch('reportes_app.services.ReporteService._generar_pdf')
    def test_generar_reporte_sync_pdf(self, mock_generar_pdf):
        """Test generación síncrona de reporte PDF"""
        # Mock del archivo generado
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp.write(b'PDF content')
            mock_generar_pdf.return_value = tmp.name
        
        try:
            reporte = self.service.generar_reporte_sync(
                tipo='ventas',
                formato='pdf',
                parametros={'fecha_inicio': '2024-01-01'},
                autor_id=self.user.id
            )
            
            self.assertEqual(reporte.tipo, 'ventas')
            self.assertEqual(reporte.formato, 'pdf')
            self.assertEqual(reporte.estado, 'completado')
            self.assertTrue(reporte.archivo)
        finally:
            # Limpiar
            if os.path.exists(tmp.name):
                os.remove(tmp.name)
    
    def test_validar_parametros_reporte(self):
        """Test validación de parámetros"""
        # Parámetros válidos
        parametros_validos = {
            'fecha_inicio': date(2024, 1, 1),
            'fecha_fin': date(2024, 1, 31),
            'usuario_id': self.user.id
        }
        self.assertTrue(
            self.service.validar_parametros_reporte('ventas', parametros_validos)
        )
        
        # Parámetros inválidos
        parametros_invalidos = {
            'fecha_inicio': date(2024, 1, 31),
            'fecha_fin': date(2024, 1, 1)
        }
        with self.assertRaises(ParametrosInvalidosException):
            self.service.validar_parametros_reporte('ventas', parametros_invalidos)
    
    def test_formato_no_soportado(self):
        """Test formato no soportado"""
        with self.assertRaises(FormatoNoSoportadoException):
            self.service.generar_reporte_sync(
                tipo='ventas',
                formato='xml',  # Formato no soportado
                parametros={},
                autor_id=self.user.id
            )


class MetricaServiceTest(TestCase):
    """Tests para MetricaService"""
    
    def setUp(self):
        """Configuración inicial"""
        self.service = MetricaService()
    
    def test_crear_metrica(self):
        """Test creación de métrica"""
        metrica = self.service.crear_metrica(
            nombre='test_metrica',
            valor=100.5,
            periodo='diario',
            metadatos={'fuente': 'test'}
        )
        
        self.assertEqual(metrica.nombre, 'test_metrica')
        self.assertEqual(metrica.valor, 100.5)
        self.assertEqual(metrica.periodo, 'diario')
        self.assertEqual(metrica.metadatos['fuente'], 'test')
    
    def test_calcular_tendencia(self):
        """Test cálculo de tendencia"""
        # Crear métricas históricas
        base_date = timezone.now() - timedelta(days=5)
        
        Metrica.objects.create(
            nombre='test_tendencia',
            valor=100,
            periodo='diario',
            fecha_calculo=base_date
        )
        Metrica.objects.create(
            nombre='test_tendencia',
            valor=150,
            periodo='diario',
            fecha_calculo=base_date + timedelta(days=1)
        )
        
        tendencia = self.service.calcular_tendencia('test_tendencia', 'diario')
        self.assertEqual(tendencia, 'ascendente')


# ========== Tests de API ==========

class ReporteAPITest(APITestCase):
    """Tests para la API de reportes"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_crear_reporte_api(self):
        """Test creación de reporte vía API"""
        url = reverse('reportes_app:generar_reporte')
        data = {
            'tipo': 'ventas',
            'formato': 'pdf',
            'titulo': 'Reporte de prueba API',
            'parametros': {
                'fecha_inicio': '2024-01-01',
                'fecha_fin': '2024-01-31'
            }
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('reporte_id', response.data)
    
    def test_listar_reportes_api(self):
        """Test listado de reportes vía API"""
        # Crear reportes
        Reporte.objects.create(
            tipo='ventas', formato='pdf', autor_id=self.user.id
        )
        Reporte.objects.create(
            tipo='usuarios', formato='excel', autor_id=self.user.id
        )
        
        url = reverse('reportes_app:listar_reportes')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_obtener_reporte_api(self):
        """Test obtener reporte específico vía API"""
        reporte = Reporte.objects.create(
            tipo='ventas',
            formato='pdf',
            autor_id=self.user.id,
            estado='completado'
        )
        
        url = reverse('reportes_app:reporte-detail', kwargs={'pk': reporte.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(reporte.id))
    
    def test_estadisticas_api(self):
        """Test endpoint de estadísticas"""
        # Crear reportes para estadísticas
        Reporte.objects.create(
            tipo='ventas', formato='pdf', autor_id=self.user.id, estado='completado'
        )
        Reporte.objects.create(
            tipo='usuarios', formato='excel', autor_id=self.user.id, estado='pendiente'
        )
        
        url = reverse('reportes_app:estadisticas_reportes')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_reportes', response.data)
        self.assertIn('reportes_completados', response.data)
    
    def test_health_check_api(self):
        """Test endpoint de health check"""
        url = reverse('reportes_app:health_check')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')


# ========== Tests de Autenticación ==========

class AutenticacionTest(APITestCase):
    """Tests de autenticación y permisos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.otro_user = User.objects.create_user(
            username='otrouser',
            email='otro@example.com',
            password='pass'
        )
    
    def test_acceso_sin_autenticacion(self):
        """Test acceso sin autenticación"""
        url = reverse('reportes_app:generar_reporte')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_acceso_reporte_otro_usuario(self):
        """Test acceso a reporte de otro usuario"""
        # Crear reporte de otro usuario
        reporte = Reporte.objects.create(
            tipo='ventas',
            formato='pdf',
            autor_id=self.otro_user.id
        )
        
        # Intentar acceder con usuario diferente
        self.client.force_authenticate(user=self.user)
        url = reverse('reportes_app:reporte-detail', kwargs={'pk': reporte.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ========== Tests de Integración ==========

class IntegracionTest(TransactionTestCase):
    """Tests de integración completos"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
    
    @patch('reportes_app.tasks.procesar_reporte_async.delay')
    def test_flujo_completo_reporte(self, mock_task):
        """Test del flujo completo de generación de reporte"""
        # Mock de la tarea asíncrona
        mock_task.return_value = MagicMock()
        
        # 1. Crear reporte
        service = ReporteService()
        reporte = service.generar_reporte_async(
            tipo='ventas',
            formato='pdf',
            parametros={'fecha_inicio': date(2024, 1, 1)},
            autor_id=self.user.id
        )
        
        # 2. Verificar estado inicial
        self.assertEqual(reporte.estado, 'pendiente')
        
        # 3. Verificar que la tarea fue llamada
        mock_task.assert_called_once_with(str(reporte.id))
        
        # 4. Simular completación
        reporte.estado = 'completado'
        reporte.save()
        
        # 5. Verificar estado final
        reporte.refresh_from_db()
        self.assertEqual(reporte.estado, 'completado')


# ========== Tests de Performance ==========

class PerformanceTest(TestCase):
    """Tests de performance"""
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
    
    def test_consulta_reportes_optimizada(self):
        """Test que las consultas estén optimizadas"""
        # Crear múltiples reportes
        reportes = []
        for i in range(50):
            reportes.append(Reporte(
                tipo='ventas',
                formato='pdf',
                autor_id=self.user.id,
                titulo=f'Reporte {i}'
            ))
        Reporte.objects.bulk_create(reportes)
        
        # Test de consulta con select_related/prefetch_related
        with self.assertNumQueries(1):  # Debería ser solo 1 query
            repository = ReporteRepository()
            reportes_queryset = repository.obtener_por_autor(self.user.id)
            list(reportes_queryset)  # Forzar evaluación
