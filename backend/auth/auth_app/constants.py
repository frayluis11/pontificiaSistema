"""
Constantes para el microservicio de autenticación
"""

class RolUsuario:
    """
    Roles de usuario disponibles en el sistema
    """
    ADMIN = 'ADMIN'
    DOCENTE = 'DOCENTE'
    ESTUDIANTE = 'ESTUDIANTE'
    RRHH = 'RRHH'
    CONTABILIDAD = 'CONTABILIDAD'
    
    choices = [
        (ADMIN, 'Administrador'),
        (DOCENTE, 'Docente'),
        (ESTUDIANTE, 'Estudiante'), 
        (RRHH, 'Recursos Humanos'),
        (CONTABILIDAD, 'Contabilidad'),
    ]


class EstadoUsuario:
    """
    Estados de usuario disponibles
    """
    ACTIVO = 'ACTIVO'
    INACTIVO = 'INACTIVO'
    SUSPENDIDO = 'SUSPENDIDO'
    
    choices = [
        (ACTIVO, 'Activo'),
        (INACTIVO, 'Inactivo'),
        (SUSPENDIDO, 'Suspendido'),
    ]


# Constantes de configuración
DEFAULT_PASSWORD = 'password123'
TOKEN_BLACKLIST_REASONS = [
    ('logout', 'Logout manual'),
    ('expired', 'Token expirado'),
    ('compromised', 'Token comprometido'),
    ('admin_action', 'Acción administrativa'),
]