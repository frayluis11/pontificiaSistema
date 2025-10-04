#!/usr/bin/env python3
"""
Test rápido del Gateway completo
"""

import requests
import json
import time

def test_gateway_endpoints():
    """
    Test de endpoints principales del gateway
    """
    base_url = "http://127.0.0.1:8000"
    
    endpoints = [
        "/",
        "/health/",
        "/docs/", 
        "/api/gateway/",
        "/api/docs/",
    ]
    
    print("🧪 TESTING API GATEWAY")
    print("=" * 30)
    
    results = {}
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\n🔍 Testing {endpoint}")
        
        try:
            response = requests.get(url, timeout=5)
            status = response.status_code
            
            if status == 200:
                print(f"✅ {endpoint} - Status: {status}")
                # Intentar parsear JSON si es posible
                try:
                    data = response.json()
                    print(f"   📊 Response: {json.dumps(data, indent=2)[:200]}...")
                except:
                    # Si no es JSON, mostrar texto
                    text = response.text[:200]
                    print(f"   📄 Response: {text}...")
                    
                results[endpoint] = {"status": status, "success": True}
            else:
                print(f"⚠️  {endpoint} - Status: {status}")
                results[endpoint] = {"status": status, "success": False}
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint} - Connection Error (Server not running?)")
            results[endpoint] = {"status": "Connection Error", "success": False}
        except requests.exceptions.Timeout:
            print(f"⏱️  {endpoint} - Timeout")
            results[endpoint] = {"status": "Timeout", "success": False}
        except Exception as e:
            print(f"💥 {endpoint} - Error: {str(e)}")
            results[endpoint] = {"status": f"Error: {e}", "success": False}
    
    # Resumen
    print("\n" + "=" * 30)
    print("📊 RESUMEN")
    print("=" * 30)
    
    successful = sum(1 for r in results.values() if r["success"])
    total = len(results)
    
    print(f"✅ Exitosos: {successful}/{total}")
    print(f"❌ Fallidos: {total - successful}/{total}")
    
    if successful == total:
        print("\n🎉 ¡TODOS LOS TESTS PASARON!")
        print("🚀 Gateway funcionando correctamente")
    else:
        print(f"\n⚠️  {total - successful} endpoints con problemas")
        
    return results

if __name__ == "__main__":
    print("⏳ Esperando 2 segundos para que el servidor esté listo...")
    time.sleep(2)
    
    results = test_gateway_endpoints()
    
    # Salir con código apropiado
    successful = sum(1 for r in results.values() if r["success"])
    total = len(results)
    
    if successful == total:
        exit(0)  # Éxito
    else:
        exit(1)  # Falló algún test