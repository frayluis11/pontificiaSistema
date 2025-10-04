#!/usr/bin/env python3
"""
Test simple para verificar que el gateway funciona
"""

import requests
import json

def test_gateway():
    try:
        print("🧪 Testing Gateway...")
        
        # Test endpoint raíz
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print(f"Root endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Service: {data.get('service')}")
            print("✅ Root endpoint working!")
        else:
            print(f"❌ Root endpoint failed with status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to gateway. Is it running?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_gateway()