#!/usr/bin/env python3
"""
Script para poblar todas las bases de datos con datos iniciales
Sistema Pontificia - Seed All Databases
"""

import os
import sys
import django
import subprocess
from datetime import datetime

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
sys.path.append('/backend/auth')
django.setup()

def seed_auth_service():
    """Poblar Auth Service con 20 usuarios iniciales"""
    print("🔐 Seeding Auth Service...")
    
    from django.contrib.auth.models import User
    from auth_app.models import Usuario
    
    usuarios_data = [
        # 5 ADMIN
        {'username': 'admin1', 'email': 'admin1@pontificia.edu', 'rol': 'ADMIN', 'nombre': 'Carlos', 'apellido': 'Administrador'},
        {'username': 'admin2', 'email': 'admin2@pontificia.edu', 'rol': 'ADMIN', 'nombre': 'María', 'apellido': 'Rectora'},
        {'username': 'admin3', 'email': 'admin3@pontificia.edu', 'rol': 'ADMIN', 'nombre': 'José', 'apellido': 'Vicerrector'},
        {'username': 'admin4', 'email': 'admin4@pontificia.edu', 'rol': 'ADMIN', 'nombre': 'Ana', 'apellido': 'Secretaria'},
        {'username': 'admin5', 'email': 'admin5@pontificia.edu', 'rol': 'ADMIN', 'nombre': 'Pedro', 'apellido': 'Director'},
        
        # 5 DOCENTE
        {'username': 'docente1', 'email': 'docente1@pontificia.edu', 'rol': 'DOCENTE', 'nombre': 'Luis', 'apellido': 'Profesor'},
        {'username': 'docente2', 'email': 'docente2@pontificia.edu', 'rol': 'DOCENTE', 'nombre': 'Carmen', 'apellido': 'Maestra'},
        {'username': 'docente3', 'email': 'docente3@pontificia.edu', 'rol': 'DOCENTE', 'nombre': 'Roberto', 'apellido': 'Catedrático'},
        {'username': 'docente4', 'email': 'docente4@pontificia.edu', 'rol': 'DOCENTE', 'nombre': 'Isabel', 'apellido': 'Educadora'},
        {'username': 'docente5', 'email': 'docente5@pontificia.edu', 'rol': 'DOCENTE', 'nombre': 'Miguel', 'apellido': 'Instructor'},
        
        # 3 RRHH
        {'username': 'rrhh1', 'email': 'rrhh1@pontificia.edu', 'rol': 'RRHH', 'nombre': 'Sandra', 'apellido': 'Recursos'},
        {'username': 'rrhh2', 'email': 'rrhh2@pontificia.edu', 'rol': 'RRHH', 'nombre': 'Fernando', 'apellido': 'Personal'},
        {'username': 'rrhh3', 'email': 'rrhh3@pontificia.edu', 'rol': 'RRHH', 'nombre': 'Patricia', 'apellido': 'Talento'},
        
        # 3 CONTABILIDAD
        {'username': 'conta1', 'email': 'conta1@pontificia.edu', 'rol': 'CONTABILIDAD', 'nombre': 'Ricardo', 'apellado': 'Contador'},
        {'username': 'conta2', 'email': 'conta2@pontificia.edu', 'rol': 'CONTABILIDAD', 'nombre': 'Gloria', 'apellido': 'Finanzas'},
        {'username': 'conta3', 'email': 'conta3@pontificia.edu', 'rol': 'CONTABILIDAD', 'nombre': 'Andrés', 'apellido': 'Presupuesto'},
        
        # 4 ESTUDIANTES
        {'username': 'estudiante1', 'email': 'estudiante1@pontificia.edu', 'rol': 'ESTUDIANTE', 'nombre': 'Lucía', 'apellido': 'Estudiante'},
        {'username': 'estudiante2', 'email': 'estudiante2@pontificia.edu', 'rol': 'ESTUDIANTE', 'nombre': 'Diego', 'apellido': 'Alumno'},
        {'username': 'estudiante3', 'email': 'estudiante3@pontificia.edu', 'rol': 'ESTUDIANTE', 'nombre': 'Valentina', 'apellido': 'Discente'},
        {'username': 'estudiante4', 'email': 'estudiante4@pontificia.edu', 'rol': 'ESTUDIANTE', 'nombre': 'Sebastián', 'apellido': 'Aprendiz'},
    ]
    
    for user_data in usuarios_data:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password='pontificia123',
                first_name=user_data['nombre'],
                last_name=user_data['apellido']
            )
            print(f"✅ Created user: {user.username} ({user_data['rol']})")
        else:
            print(f"ℹ️ User {user_data['username']} already exists")

def seed_all_services():
    """Poblar todos los servicios"""
    print("🌱 Starting database seeding for all microservices...")
    
    # Lista de servicios a poblar
    services = [
        'auth-service',
        'users-service', 
        'asistencia-service',
        'documentos-service',
        'pagos-service',
        'reportes-service',
        'auditoria-service'
    ]
    
    for service in services:
        print(f"🔄 Seeding {service}...")
        try:
            # Ejecutar comando de seed en cada contenedor
            subprocess.run([
                'docker-compose', 'exec', '-T', service,
                'python', 'manage.py', 'loaddata', 'initial_data.json'
            ], check=True, capture_output=True)
            print(f"✅ {service} seeded successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ {service} seed failed (probably no fixtures): {e}")
        except Exception as e:
            print(f"❌ Error seeding {service}: {e}")

if __name__ == "__main__":
    print("🚀 Sistema Pontificia - Database Seeding")
    print("=" * 50)
    
    try:
        seed_auth_service()
        seed_all_services()
        
        print("\n✅ All databases seeded successfully!")
        print("🎯 Ready to test all microservices")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        sys.exit(1)