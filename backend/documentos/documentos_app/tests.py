"""
Tests para el microservicio de documentos

Este módulo contiene las pruebas unitarias e de integración
para el sistema de gestión de documentos.
"""

from django.test import TestCase, TransactionTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from unittest.mock import Mock, patch
import tempfile
import os

from documentos_app.models import (
    Documento, VersionDocumento, SolicitudDocumento, FlujoDocumento
)
from documentos_app.services import DocumentoService
from documentos_app.repositories import DocumentoRepository


class DocumentoModelTest(TestCase):
    """
    Pruebas para el modelo Documento
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@pontificia.edu',
            password='testpass123'
        )
        
        # Crear archivo de prueba
        self.test_file = SimpleUploadedFile(
            "test_document.pdf",
            b"file_content",
            content_type="application/pdf"
        )
    
    def test_crear_documento(self):
        """Prueba la creación de un documento"""
        documento = Documento.objects.create(
            titulo="Documento de Prueba",
            descripcion="Un documento para testing",
            tipo_documento="ACADEMICO",
            creado_por=self.user,
            archivo=self.test_file
        )
        
        self.assertEqual(documento.titulo, "Documento de Prueba")
        self.assertEqual(documento.estado, "BORRADOR")
        self.assertEqual(documento.creado_por, self.user)
        self.assertTrue(documento.archivo)
    
    def test_documento_str_method(self):
        """Prueba el método __str__ del documento"""
        documento = Documento.objects.create(
            titulo="Test Document",
            tipo_documento="ADMINISTRATIVO",
            creado_por=self.user
        )
        
        self.assertEqual(str(documento), "Test Document")
    
    def test_obtener_version_actual(self):
        """Prueba el método obtener_version_actual"""
        documento = Documento.objects.create(
            titulo="Test Document",
            tipo_documento="ACADEMICO",
            creado_por=self.user
        )
        
        # Crear versiones
        v1 = VersionDocumento.objects.create(
            documento=documento,
            numero_version="1.0",
            creado_por=self.user
        )
        v2 = VersionDocumento.objects.create(
            documento=documento,
            numero_version="1.1",
            creado_por=self.user
        )
        
        version_actual = documento.obtener_version_actual()
        self.assertEqual(version_actual, v2)
    
    def test_puede_editar(self):
        """Prueba el método puede_editar"""
        documento = Documento.objects.create(
            titulo="Test Document",
            tipo_documento="ACADEMICO",
            creado_por=self.user
        )
        
        # El creador puede editar
        self.assertTrue(documento.puede_editar(self.user))
        
        # Otro usuario no puede editar
        otro_user = User.objects.create_user(
            username='otheruser',
            password='pass123'
        )
        self.assertFalse(documento.puede_editar(otro_user))


class DocumentoServiceTest(TestCase):
    """
    Pruebas para el servicio de documentos
    """
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@pontificia.edu',
            password='testpass123'
        )
        self.service = DocumentoService()
    
    def test_crear_documento(self):
        """Prueba la creación de documento a través del servicio"""
        data = {
            'titulo': 'Documento desde servicio',
            'descripcion': 'Descripción de prueba',
            'tipo_documento': 'ACADEMICO'
        }
        
        documento = self.service.crear_documento(data, self.user)
        
        self.assertIsInstance(documento, Documento)
        self.assertEqual(documento.titulo, 'Documento desde servicio')
        self.assertEqual(documento.creado_por, self.user)
    
    @patch('documentos_app.observers.NotificacionObserver.notify')
    def test_aprobar_documento(self, mock_notify):
        """Prueba la aprobación de documento"""
        documento = Documento.objects.create(
            titulo="Test Document",
            tipo_documento="ACADEMICO",
            estado="REVISION",
            creado_por=self.user
        )
        
        resultado = self.service.aprobar_documento(documento.id, self.user, "Aprobado")
        
        self.assertTrue(resultado)
        documento.refresh_from_db()
        self.assertEqual(documento.estado, "APROBADO")
        mock_notify.assert_called_once()
    
    def test_rechazar_documento(self):
        """Prueba el rechazo de documento"""
        documento = Documento.objects.create(
            titulo="Test Document",
            tipo_documento="ACADEMICO",
            estado="REVISION",
            creado_por=self.user
        )
        
        resultado = self.service.rechazar_documento(
            documento.id, 
            self.user, 
            "Necesita correcciones"
        )
        
        self.assertTrue(resultado)
        documento.refresh_from_db()
        self.assertEqual(documento.estado, "RECHAZADO")


class DocumentoRepositoryTest(TestCase):
    """
    Pruebas para el repositorio de documentos
    """
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.repository = DocumentoRepository()
    
    def test_buscar_por_titulo(self):
        """Prueba la búsqueda por título"""
        # Crear documentos de prueba
        doc1 = Documento.objects.create(
            titulo="Python Programming",
            tipo_documento="ACADEMICO",
            creado_por=self.user
        )
        doc2 = Documento.objects.create(
            titulo="Java Development",
            tipo_documento="ACADEMICO",
            creado_por=self.user
        )
        doc3 = Documento.objects.create(
            titulo="Python Advanced",
            tipo_documento="ADMINISTRATIVO",
            creado_por=self.user
        )
        
        # Buscar por "Python"
        resultados = self.repository.buscar_por_titulo("Python")
        
        self.assertEqual(len(resultados), 2)
        self.assertIn(doc1, resultados)
        self.assertIn(doc3, resultados)
        self.assertNotIn(doc2, resultados)
    
    def test_obtener_por_usuario(self):
        """Prueba obtener documentos por usuario"""
        otro_user = User.objects.create_user(
            username='otheruser',
            password='pass123'
        )
        
        # Crear documentos
        doc1 = Documento.objects.create(
            titulo="Doc del usuario 1",
            tipo_documento="ACADEMICO",
            creado_por=self.user
        )
        doc2 = Documento.objects.create(
            titulo="Doc del usuario 2",
            tipo_documento="ACADEMICO",
            creado_por=otro_user
        )
        
        resultados = self.repository.obtener_por_usuario(self.user)
        
        self.assertEqual(len(resultados), 1)
        self.assertIn(doc1, resultados)
        self.assertNotIn(doc2, resultados)


class DocumentoAPITest(APITestCase):
    """
    Pruebas para la API REST de documentos
    """
    
    def setUp(self):
        """Configuración inicial para las pruebas de API"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@pontificia.edu',
            password='testpass123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_listar_documentos(self):
        """Prueba el endpoint de listado de documentos"""
        # Crear documentos de prueba
        Documento.objects.create(
            titulo="Doc 1",
            tipo_documento="ACADEMICO",
            creado_por=self.user
        )
        Documento.objects.create(
            titulo="Doc 2",
            tipo_documento="ADMINISTRATIVO",
            creado_por=self.user
        )
        
        url = reverse('documento-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_crear_documento_api(self):
        """Prueba la creación de documento vía API"""
        url = reverse('documento-list')
        data = {
            'titulo': 'Nuevo Documento API',
            'descripcion': 'Descripción desde API',
            'tipo_documento': 'ACADEMICO'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['titulo'], 'Nuevo Documento API')
        
        # Verificar que se creó en la base de datos
        self.assertTrue(
            Documento.objects.filter(titulo='Nuevo Documento API').exists()
        )
    
    def test_obtener_documento(self):
        """Prueba obtener un documento específico"""
        documento = Documento.objects.create(
            titulo="Test Document",
            tipo_documento="ACADEMICO",
            creado_por=self.user
        )
        
        url = reverse('documento-detail', kwargs={'pk': documento.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['titulo'], 'Test Document')
    
    def test_actualizar_documento(self):
        """Prueba la actualización de documento"""
        documento = Documento.objects.create(
            titulo="Original Title",
            tipo_documento="ACADEMICO",
            creado_por=self.user
        )
        
        url = reverse('documento-detail', kwargs={'pk': documento.pk})
        data = {
            'titulo': 'Updated Title',
            'descripcion': 'Updated description',
            'tipo_documento': 'ADMINISTRATIVO'
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['titulo'], 'Updated Title')
        
        # Verificar en base de datos
        documento.refresh_from_db()
        self.assertEqual(documento.titulo, 'Updated Title')
    
    def test_eliminar_documento(self):
        """Prueba la eliminación de documento"""
        documento = Documento.objects.create(
            titulo="To Delete",
            tipo_documento="ACADEMICO",
            creado_por=self.user
        )
        
        url = reverse('documento-detail', kwargs={'pk': documento.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar que se marcó como inactivo
        documento.refresh_from_db()
        self.assertFalse(documento.activo)
    
    def test_aprobar_documento_endpoint(self):
        """Prueba el endpoint de aprobación"""
        documento = Documento.objects.create(
            titulo="Test Document",
            tipo_documento="ACADEMICO",
            estado="REVISION",
            creado_por=self.user
        )
        
        url = reverse('documento-aprobar', kwargs={'pk': documento.pk})
        data = {'comentarios': 'Documento aprobado correctamente'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        documento.refresh_from_db()
        self.assertEqual(documento.estado, 'APROBADO')
    
    def test_buscar_documentos(self):
        """Prueba la funcionalidad de búsqueda"""
        Documento.objects.create(
            titulo="Python Tutorial",
            descripcion="Learn Python programming",
            tipo_documento="ACADEMICO",
            creado_por=self.user
        )
        Documento.objects.create(
            titulo="Java Guide",
            descripcion="Java development guide",
            tipo_documento="ACADEMICO",
            creado_por=self.user
        )
        
        url = reverse('documento-list')
        response = self.client.get(url, {'search': 'Python'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['titulo'], 'Python Tutorial')


class SolicitudDocumentoTest(TestCase):
    """
    Pruebas para el modelo de solicitud de documento
    """
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.documento = Documento.objects.create(
            titulo="Test Document",
            tipo_documento="ACADEMICO",
            creado_por=self.user
        )
    
    def test_crear_solicitud(self):
        """Prueba la creación de solicitud"""
        solicitud = SolicitudDocumento.objects.create(
            documento=self.documento,
            usuario_solicitante="estudiante@pontificia.edu",
            motivo="Necesito el documento para mi investigación"
        )
        
        self.assertEqual(solicitud.documento, self.documento)
        self.assertEqual(solicitud.estado, "PENDIENTE")
        self.assertEqual(solicitud.usuario_solicitante, "estudiante@pontificia.edu")
    
    def test_aprobar_solicitud(self):
        """Prueba la aprobación de solicitud"""
        solicitud = SolicitudDocumento.objects.create(
            documento=self.documento,
            usuario_solicitante="estudiante@pontificia.edu",
            motivo="Investigación académica"
        )
        
        solicitud.aprobar("Solicitud aprobada por el administrador")
        
        self.assertEqual(solicitud.estado, "APROBADA")
        self.assertIsNotNone(solicitud.fecha_respuesta)
        self.assertIn("aprobada", solicitud.comentarios_respuesta.lower())


class IntegrationTest(TransactionTestCase):
    """
    Pruebas de integración para el flujo completo
    """
    
    def setUp(self):
        """Configuración inicial"""
        self.user = User.objects.create_user(
            username='admin',
            email='admin@pontificia.edu',
            password='admin123',
            is_staff=True
        )
        self.service = DocumentoService()
    
    def test_flujo_completo_documento(self):
        """Prueba el flujo completo desde creación hasta aprobación"""
        # 1. Crear documento
        data = {
            'titulo': 'Documento Integración',
            'descripcion': 'Prueba de integración completa',
            'tipo_documento': 'ACADEMICO'
        }
        
        documento = self.service.crear_documento(data, self.user)
        self.assertEqual(documento.estado, 'BORRADOR')
        
        # 2. Enviar a revisión
        documento.estado = 'REVISION'
        documento.save()
        
        # 3. Aprobar documento
        resultado = self.service.aprobar_documento(
            documento.id, 
            self.user, 
            "Documento aprobado tras revisión"
        )
        
        self.assertTrue(resultado)
        documento.refresh_from_db()
        self.assertEqual(documento.estado, 'APROBADO')
        
        # 4. Crear solicitud de acceso
        solicitud = SolicitudDocumento.objects.create(
            documento=documento,
            usuario_solicitante="estudiante@pontificia.edu",
            motivo="Para mi tesis de grado"
        )
        
        # 5. Aprobar solicitud
        solicitud.aprobar("Solicitud válida")
        
        self.assertEqual(solicitud.estado, 'APROBADA')
        
        # 6. Crear nueva versión
        nueva_version = VersionDocumento.objects.create(
            documento=documento,
            numero_version="2.0",
            comentarios="Versión actualizada con correcciones",
            creado_por=self.user
        )
        
        # Verificar que es la versión actual
        self.assertEqual(documento.obtener_version_actual(), nueva_version)
