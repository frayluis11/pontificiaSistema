#!/usr/bin/env python3
"""
Test completo para todos los endpoints del API Gateway
"""

import requests
import json
import time

def test_all_endpoints():
    base_url = "http://127.0.0.1:8000"
    passed = 0
    failed = 0
    
    print("🚀 Testing API Gateway - Complete Test Suite")
    print("=" * 50)
    
    endpoints = [
        ("Root endpoint", "/"),
        ("Health check", "/health/"),
        ("Gateway info", "/api/gateway/"),
        ("Documentation", "/docs/")
    ]
    
    for name, endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"\n🧪 Testing {name}: {endpoint}")
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Status: {response.status_code} OK")
                
                # Verificar content type
                content_type = response.headers.get('content-type', '')
                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"📄 JSON Response: {list(data.keys())[:5]}...")
                    except:
                        print("📄 Invalid JSON response")
                elif 'html' in content_type:
                    print(f"📄 HTML Response: {len(response.text)} characters")
                
                passed += 1
            else:
                print(f"❌ Status: {response.status_code}")
                failed += 1
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Error: Cannot connect to {url}")
            failed += 1
        except Exception as e:
            print(f"❌ Error: {e}")
            failed += 1
    
    # Test OpenAPI endpoints
    print(f"\n🧪 Testing OpenAPI endpoints...")
    
    openapi_endpoints = [
        ("OpenAPI Schema", "/api/schema/"),
        ("Swagger UI", "/api/docs/"),
        ("ReDoc UI", "/api/redoc/")
    ]
    
    for name, endpoint in openapi_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {name}: OK")
                passed += 1
            else:
                print(f"❌ {name}: {response.status_code}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            failed += 1
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%")
    
    if failed == 0:
        print("\n🎉 All tests passed! Gateway is working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed. Check the gateway configuration.")
        return False

if __name__ == "__main__":
    success = test_all_endpoints()