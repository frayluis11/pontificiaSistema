"""
Tests para la aplicación de perfiles
Sistema Pontificia - Users Service
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
import json
from unittest.mock import patch, MagicMock

from .models import Profile
from .services import ProfileService
from .repository import ProfileRepository
from .serializers import ProfileCreateSerializer, ProfileUpdateSerializer


class ProfileModelTest(TestCase):
    """
    Tests para el modelo Profile
    """
    
    def setUp(self):
        self.profile_data = {
            'usuario_id': 1,
            'telefono': '1234567890',
            'direccion': 'Calle 123',
            'cargo': 'Profesor',
            'departamento': 'Matemáticas',
            'fecha_ingreso': date(2020, 1, 1),
            'fecha_nacimiento': date(1985, 5, 15),
            'biografia': 'Profesor de matemáticas',
            'perfil_publico': True,
            'mostrar_telefono': False,
            'mostrar_correo': True
        }
    
    def test_crear_profile(self):
        """Test creación de perfil"""
        profile = Profile.objects.create(**self.profile_data)
        
        self.assertEqual(profile.usuario_id, 1)
        self.assertEqual(profile.telefono, '1234567890')
        self.assertEqual(profile.cargo, 'Profesor')
        self.assertTrue(profile.perfil_publico)
        self.assertTrue(profile.activo)
    
    def test_calcular_edad(self):
        """Test cálculo de edad"""
        profile = Profile.objects.create(**self.profile_data)
        edad_esperada = (date.today() - self.profile_data['fecha_nacimiento']).days // 365
        
        self.assertEqual(profile.edad, edad_esperada)
    
    def test_calcular_anos_institucion(self):
        """Test cálculo de años en institución"""
        profile = Profile.objects.create(**self.profile_data)
        anos_esperados = (date.today() - self.profile_data['fecha_ingreso']).days // 365
        
        self.assertEqual(profile.anos_en_institucion, anos_esperados)
    
    def test_str_representation(self):
        """Test representación en string"""
        profile = Profile.objects.create(**self.profile_data)
        expected = f"Profile(usuario_id=1, cargo=Profesor, departamento=Matemáticas)"
        
        self.assertEqual(str(profile), expected)


class ProfileRepositoryTest(TestCase):
    """
    Tests para ProfileRepository
    """
    
    def setUp(self):
        self.profile_data = {
            'usuario_id': 1,
            'telefono': '1234567890',
            'cargo': 'Profesor',
            'departamento': 'Matemáticas',
            'perfil_publico': True
        }
    
    def test_crear_profile(self):
        """Test crear perfil via repository"""
        profile = ProfileRepository.crear_profile(self.profile_data)
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile.usuario_id, 1)
        self.assertEqual(profile.cargo, 'Profesor')
    
    def test_obtener_por_usuario_id(self):
        """Test obtener perfil por usuario_id"""
        # Crear perfil
        ProfileRepository.crear_profile(self.profile_data)
        
        # Obtener perfil
        profile = ProfileRepository.obtener_por_usuario_id(1)
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile.usuario_id, 1)
    
    def test_existe_profile(self):
        """Test verificar existencia de perfil"""
        # Inicialmente no existe
        self.assertFalse(ProfileRepository.existe_profile(1))
        
        # Crear perfil
        ProfileRepository.crear_profile(self.profile_data)
        
        # Ahora existe
        self.assertTrue(ProfileRepository.existe_profile(1))
    
    def test_actualizar_profile(self):
        """Test actualizar perfil"""
        # Crear perfil
        ProfileRepository.crear_profile(self.profile_data)
        
        # Actualizar
        datos_actualizacion = {'cargo': 'Director', 'telefono': '0987654321'}
        profile = ProfileRepository.actualizar_profile(1, datos_actualizacion)
        
        self.assertIsNotNone(profile)
        self.assertEqual(profile.cargo, 'Director')
        self.assertEqual(profile.telefono, '0987654321')
    
    def test_obtener_publicos(self):
        """Test obtener perfiles públicos"""
        # Crear perfil público
        ProfileRepository.crear_profile(self.profile_data)
        
        # Crear perfil privado
        profile_privado = self.profile_data.copy()
        profile_privado['usuario_id'] = 2
        profile_privado['perfil_publico'] = False
        ProfileRepository.crear_profile(profile_privado)
        
        # Obtener públicos
        publicos = ProfileRepository.obtener_publicos()
        
        self.assertEqual(len(publicos), 1)
        self.assertEqual(publicos[0].usuario_id, 1)
    
    def test_buscar_por_departamento(self):
        """Test buscar por departamento"""
        # Crear perfiles
        ProfileRepository.crear_profile(self.profile_data)
        
        profile_2 = self.profile_data.copy()
        profile_2['usuario_id'] = 2
        profile_2['departamento'] = 'Física'
        ProfileRepository.crear_profile(profile_2)
        
        # Buscar por departamento
        matematicas = ProfileRepository.buscar_por_departamento('Matemáticas')
        fisica = ProfileRepository.buscar_por_departamento('Física')
        
        self.assertEqual(len(matematicas), 1)
        self.assertEqual(len(fisica), 1)
        self.assertEqual(matematicas[0].departamento, 'Matemáticas')


class ProfileServiceTest(TestCase):
    """
    Tests para ProfileService
    """
    
    def setUp(self):
        self.profile_data = {
            'usuario_id': 1,
            'telefono': '1234567890',
            'cargo': 'Profesor',
            'departamento': 'Matemáticas',
            'perfil_publico': True
        }
    
    def test_crear_profile_exitoso(self):
        """Test creación exitosa de perfil"""
        resultado = ProfileService.crear_profile(self.profile_data)
        
        self.assertTrue(resultado['exito'])
        self.assertEqual(resultado['mensaje'], 'Perfil creado exitosamente')
        self.assertIn('data', resultado)
    
    def test_crear_profile_duplicado(self):
        """Test creación de perfil duplicado"""
        # Crear perfil
        ProfileService.crear_profile(self.profile_data)
        
        # Intentar crear duplicado
        resultado = ProfileService.crear_profile(self.profile_data)
        
        self.assertFalse(resultado['exito'])
        self.assertIn('Ya existe un perfil', resultado['mensaje'])
    
    def test_obtener_profile_existente(self):
        """Test obtener perfil existente"""
        # Crear perfil
        ProfileService.crear_profile(self.profile_data)
        
        # Obtener perfil
        resultado = ProfileService.obtener_profile(1, 1)  # mismo usuario
        
        self.assertTrue(resultado['exito'])
        self.assertIn('data', resultado)
    
    def test_obtener_profile_inexistente(self):
        """Test obtener perfil inexistente"""
        resultado = ProfileService.obtener_profile(999)
        
        self.assertFalse(resultado['exito'])
        self.assertEqual(resultado['mensaje'], 'Perfil no encontrado')
    
    def test_actualizar_profile_exitoso(self):
        """Test actualización exitosa de perfil"""
        # Crear perfil
        ProfileService.crear_profile(self.profile_data)
        
        # Actualizar
        datos_actualizacion = {'cargo': 'Director'}
        resultado = ProfileService.actualizar_profile(1, datos_actualizacion, 1)
        
        self.assertTrue(resultado['exito'])
        self.assertEqual(resultado['data']['cargo'], 'Director')
    
    def test_actualizar_profile_sin_permisos(self):
        """Test actualización sin permisos"""
        # Crear perfil
        ProfileService.crear_profile(self.profile_data)
        
        # Intentar actualizar como otro usuario
        datos_actualizacion = {'cargo': 'Director'}
        resultado = ProfileService.actualizar_profile(1, datos_actualizacion, 2)
        
        self.assertFalse(resultado['exito'])
        self.assertIn('permisos', resultado['mensaje'])
    
    def test_listar_profiles_publicos(self):
        """Test listar perfiles públicos"""
        # Crear perfiles
        ProfileService.crear_profile(self.profile_data)
        
        profile_privado = self.profile_data.copy()
        profile_privado['usuario_id'] = 2
        profile_privado['perfil_publico'] = False
        ProfileService.crear_profile(profile_privado)
        
        # Listar públicos
        resultado = ProfileService.listar_profiles(publicos_solo=True)
        
        self.assertTrue(resultado['exito'])
        self.assertEqual(resultado['total'], 1)
    
    def test_sincronizar_con_auth_service(self):
        """Test sincronización con auth_service"""
        datos_usuario = {
            'departamento': 'Informática',
            'cargo': 'Analista'
        }
        
        resultado = ProfileService.sincronizar_con_auth_service(1, datos_usuario)
        
        self.assertTrue(resultado['exito'])
        self.assertEqual(resultado['accion'], 'creado')


class ProfileViewsTest(TestCase):
    """
    Tests para las vistas de perfiles
    """
    
    def setUp(self):
        self.client = Client()
        self.profile_data = {
            'usuario_id': 1,
            'telefono': '1234567890',
            'cargo': 'Profesor',
            'departamento': 'Matemáticas',
            'perfil_publico': True
        }
    
    @patch('profiles_app.views.IsAuthenticated')
    def test_crear_profile_endpoint(self, mock_auth):
        """Test endpoint de creación de perfil"""
        mock_auth.return_value = True
        
        # Mock user para simular autenticación
        mock_user = MagicMock()
        mock_user.id = 1
        
        with patch('profiles_app.views.request') as mock_request:
            mock_request.user = mock_user
            
            response = self.client.post(
                '/api/profiles/',
                data=json.dumps(self.profile_data),
                content_type='application/json'
            )
            
            # Note: Este test requerirá más configuración para funcionar completamente
            # debido a la autenticación JWT real
    
    def test_health_check_endpoint(self):
        """Test endpoint de health check"""
        response = self.client.get('/api/health/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'users_service')
    
    def test_sync_endpoint(self):
        """Test endpoint de sincronización"""
        sync_data = {
            'usuario_id': 1,
            'departamento': 'Informática',
            'cargo': 'Analista'
        }
        
        response = self.client.post(
            '/api/sync/',
            data=json.dumps(sync_data),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 201])
        data = json.loads(response.content)
        self.assertTrue(data['exito'])


class ProfileSerializersTest(TestCase):
    """
    Tests para los serializadores
    """
    
    def setUp(self):
        self.valid_data = {
            'usuario_id': 1,
            'telefono': '1234567890',
            'cargo': 'Profesor',
            'departamento': 'Matemáticas',
            'perfil_publico': True,
            'fecha_nacimiento': '1985-05-15'
        }
    
    def test_profile_create_serializer_valid(self):
        """Test serializador de creación válido"""
        serializer = ProfileCreateSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
    
    def test_profile_create_serializer_invalid_usuario_id(self):
        """Test serializador con usuario_id inválido"""
        data = self.valid_data.copy()
        data['usuario_id'] = -1
        
        serializer = ProfileCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('usuario_id', serializer.errors)
    
    def test_profile_create_serializer_fecha_nacimiento_futura(self):
        """Test serializador con fecha de nacimiento futura"""
        data = self.valid_data.copy()
        data['fecha_nacimiento'] = (date.today() + timedelta(days=1)).isoformat()
        
        serializer = ProfileCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('fecha_nacimiento', serializer.errors)
    
    def test_profile_update_serializer_valid(self):
        """Test serializador de actualización válido"""
        update_data = {
            'cargo': 'Director',
            'perfil_publico': False
        }
        
        serializer = ProfileUpdateSerializer(data=update_data)
        self.assertTrue(serializer.is_valid())
