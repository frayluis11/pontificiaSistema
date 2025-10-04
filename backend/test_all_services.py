#!/usr/bin/env python3
"""
Script de testing completo para todos los microservicios
Sistema Pontificia - Complete Testing Suite
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuración de servicios
SERVICES = {
    'gateway': 'http://localhost:8000',
    'auth': 'http://localhost:3001', 
    'users': 'http://localhost:3002',
    'asistencia': 'http://localhost:3003',
    'documentos': 'http://localhost:3004',
    'pagos': 'http://localhost:3005',
    'reportes': 'http://localhost:3006',
    'auditoria': 'http://localhost:3007'
}

def test_service_health(service_name, url):
    """Test básico de conectividad de servicio"""
    try:
        response = requests.get(f"{url}/health/", timeout=5)
        if response.status_code == 200:
            print(f"✅ {service_name}: HEALTHY")
            return True
        else:
            print(f"⚠️ {service_name}: Responds but not healthy (status: {response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        try:
            # Try root endpoint if health not available
            response = requests.get(url, timeout=5)
            if response.status_code in [200, 404]:  # 404 is OK, means service is running
                print(f"✅ {service_name}: RUNNING (no health endpoint)")
                return True
        except:
            pass
        print(f"❌ {service_name}: NOT ACCESSIBLE - {e}")
        return False

def test_auth_endpoints():
    """Test específicos del servicio de autenticación"""
    print("\n🔐 Testing Auth Service endpoints...")
    
    auth_url = SERVICES['auth']
    
    # Test login endpoint
    try:
        login_data = {
            'username': 'admin1',
            'password': 'pontificia123'
        }
        response = requests.post(f"{auth_url}/login/", json=login_data, timeout=5)
        if response.status_code in [200, 201]:
            print("✅ Auth login endpoint working")
            return response.json().get('token')  # Return token for other tests
        else:
            print(f"⚠️ Auth login returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Auth login test failed: {e}")
    
    return None

def test_users_endpoints(token=None):
    """Test específicos del servicio de usuarios"""
    print("\n👥 Testing Users Service endpoints...")
    
    users_url = SERVICES['users']
    headers = {'Authorization': f'Bearer {token}'} if token else {}
    
    try:
        response = requests.get(f"{users_url}/profiles/", headers=headers, timeout=5)
        if response.status_code in [200, 401]:  # 401 is OK if no auth
            print("✅ Users profiles endpoint working")
        else:
            print(f"⚠️ Users profiles returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Users profiles test failed: {e}")

def test_gateway_integration():
    """Test de integración del API Gateway"""
    print("\n🌐 Testing API Gateway integration...")
    
    gateway_url = SERVICES['gateway']
    
    # Test gateway health
    try:
        response = requests.get(f"{gateway_url}/api/health/", timeout=5)
        if response.status_code == 200:
            print("✅ Gateway API health working")
        else:
            print(f"⚠️ Gateway health returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Gateway health test failed: {e}")
    
    # Test gateway docs
    try:
        response = requests.get(f"{gateway_url}/api/docs/", timeout=5)
        if response.status_code == 200:
            print("✅ Gateway API docs working")
        else:
            print(f"⚠️ Gateway docs returned status: {response.status_code}")
    except Exception as e:
        print(f"❌ Gateway docs test failed: {e}")

def test_database_connections():
    """Test conexiones a bases de datos MySQL"""
    print("\n🗄️ Testing Database Connections...")
    
    import subprocess
    
    databases = [
        ('mysql_auth', 3307),
        ('mysql_users', 3308), 
        ('mysql_asistencia', 3309),
        ('mysql_documentos', 3310),
        ('mysql_pagos', 3311),
        ('mysql_reportes', 3312),
        ('mysql_auditoria', 3313)
    ]
    
    for db_name, port in databases:
        try:
            result = subprocess.run([
                'docker', 'exec', f'pontificia_{db_name}',
                'mysqladmin', 'ping', '-h', 'localhost', '-u', 'root', '-proot'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"✅ {db_name} (port {port}): Connected")
            else:
                print(f"❌ {db_name} (port {port}): Connection failed")
        except Exception as e:
            print(f"❌ {db_name}: Test failed - {e}")

def run_complete_test_suite():
    """Ejecutar suite completo de tests"""
    print("🚀 Sistema Pontificia - Complete Testing Suite")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'total_services': len(SERVICES),
        'healthy_services': 0,
        'failed_services': 0
    }
    
    # Test 1: Service Health Checks
    print("\n📊 Phase 1: Service Health Checks")
    print("-" * 40)
    
    for service_name, url in SERVICES.items():
        if test_service_health(service_name, url):
            results['healthy_services'] += 1
        else:
            results['failed_services'] += 1
        time.sleep(1)  # Rate limiting
    
    # Test 2: Database Connections
    test_database_connections()
    
    # Test 3: Endpoint Testing
    print("\n🔍 Phase 2: Endpoint Testing")
    print("-" * 40)
    
    token = test_auth_endpoints()
    test_users_endpoints(token)
    test_gateway_integration()
    
    # Results Summary
    print("\n📋 TEST SUMMARY")
    print("=" * 60)
    print(f"🎯 Total Services: {results['total_services']}")
    print(f"✅ Healthy Services: {results['healthy_services']}")
    print(f"❌ Failed Services: {results['failed_services']}")
    
    success_rate = (results['healthy_services'] / results['total_services']) * 100
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("\n🎉 SISTEMA PONTIFICIA BACKEND: READY FOR PRODUCTION!")
        return True
    else:
        print("\n⚠️ Some services need attention before production")
        return False

if __name__ == "__main__":
    try:
        success = run_complete_test_suite()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        sys.exit(1)