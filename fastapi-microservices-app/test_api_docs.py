#!/usr/bin/env python3
"""
Test script for API documentation functionality.
Tests that OpenAPI/Swagger documentation is properly generated.
"""

import requests
import json
import sys
import time

def test_gateway_docs():
    """Test gateway service API documentation"""
    print("Testing Gateway Service API Documentation...")

    try:
        # Test OpenAPI schema
        response = requests.get("http://localhost:8003/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            print("✅ Gateway OpenAPI schema accessible")

            # Check for security schemes
            if 'components' in schema and 'securitySchemes' in schema['components']:
                schemes = schema['components']['securitySchemes']
                if 'BearerAuth' in schemes and 'ApiKeyAuth' in schemes:
                    print("✅ Security schemes properly configured")
                else:
                    print("❌ Missing security schemes")
            else:
                print("❌ No security schemes found")

            # Check for documented paths
            paths = schema.get('paths', {})
            expected_paths = ['/token', '/auth/register', '/auth/verify-email',
                            '/auth/apikeys', '/inference/generate', '/inference/embed']
            found_paths = [path for path in expected_paths if path in paths]
            print(f"✅ Found {len(found_paths)}/{len(expected_paths)} documented endpoints")

        else:
            print(f"❌ Gateway docs not accessible: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        print("   (Services may not be running - this is expected)")

def test_service_info():
    """Test that service information is properly documented"""
    print("\nTesting Service Information Documentation...")

    services = [
        ("Gateway", "http://localhost:8003"),
        ("Auth", "http://localhost:8000"),
        ("Inference", "http://localhost:8001"),
        ("Logging", "http://localhost:8002")
    ]

    for service_name, url in services:
        try:
            response = requests.get(f"{url}/openapi.json", timeout=3)
            if response.status_code == 200:
                schema = response.json()
                info = schema.get('info', {})
                title = info.get('title', 'Unknown')
                version = info.get('version', 'Unknown')
                print(f"✅ {service_name}: {title} v{version}")
            else:
                print(f"❌ {service_name}: Docs not accessible ({response.status_code})")
        except:
            print(f"❌ {service_name}: Connection failed")

def test_documentation_quality():
    """Test documentation quality and completeness"""
    print("\nTesting Documentation Quality...")

    try:
        response = requests.get("http://localhost:8003/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get('paths', {})

            # Check for detailed descriptions
            detailed_endpoints = 0
            total_endpoints = len(paths)

            for path, methods in paths.items():
                for method, details in methods.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE']:
                        if 'summary' in details and 'description' in details:
                            detailed_endpoints += 1

            quality_score = detailed_endpoints / total_endpoints * 100 if total_endpoints > 0 else 0
            print(f"📊 Documentation completeness: {quality_score:.1f}%")
            if quality_score >= 80:
                print("✅ High documentation quality")
            elif quality_score >= 60:
                print("⚠️  Moderate documentation quality")
            else:
                print("❌ Low documentation quality")

    except Exception as e:
        print(f"❌ Could not assess documentation quality: {e}")

def main():
    print("🔍 SothemaAI API Documentation Test Suite")
    print("=" * 50)

    # Add the project root to Python path
    sys.path.insert(0, '/Users/abderrahman/Desktop/ecommerce-microservices/SothemaAI/fastapi-microservices-app')

    test_gateway_docs()
    test_service_info()
    test_documentation_quality()

    print("\n" + "=" * 50)
    print("📚 API Documentation Test Complete!")
    print("\nTo view the documentation interactively:")
    print("1. Start services: docker-compose up")
    print("2. Visit: http://localhost:8003/docs (Swagger UI)")
    print("3. Visit: http://localhost:8003/redoc (ReDoc)")

if __name__ == "__main__":
    main()