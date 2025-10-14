#!/usr/bin/env python3
"""
Test script for gateway validation functionality.
Tests various endpoints with invalid data to ensure validation works.
"""

import requests
import json
import sys
import time

# Gateway service URL (assuming it's running locally)
GATEWAY_URL = "http://localhost:8003"

def test_invalid_login():
    """Test login with invalid data"""
    print("Testing invalid login data...")

    # Test with missing fields
    try:
        response = requests.post(f"{GATEWAY_URL}/token", json={})
        print(f"Empty payload: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")

    # Test with invalid username format
    try:
        response = requests.post(f"{GATEWAY_URL}/token", json={
            "username": "us",  # Too short
            "password": "ValidPass123!"
        })
        print(f"Invalid username: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")

def test_invalid_registration():
    """Test registration with invalid data"""
    print("\nTesting invalid registration data...")

    # Test with invalid email domain
    try:
        response = requests.post(f"{GATEWAY_URL}/auth/register", json={
            "username": "testuser",
            "email": "test@gmail.com",  # Wrong domain
            "password": "ValidPass123!"
        })
        print(f"Invalid email domain: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")

    # Test with weak password
    try:
        response = requests.post(f"{GATEWAY_URL}/auth/register", json={
            "username": "testuser",
            "email": "test@mysothemalab.com",
            "password": "weak"  # Too weak
        })
        print(f"Weak password: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")

def test_invalid_api_key_creation():
    """Test API key creation with invalid data"""
    print("\nTesting invalid API key creation...")

    # This would require authentication, so we'll just test the validation logic
    # by checking if the models work correctly
    try:
        from gateway.src.validation import APIKeyCreateRequest

        # Test invalid description length
        try:
            invalid_key = APIKeyCreateRequest(description="a" * 201)  # Too long
            print("ERROR: Should have failed validation for long description")
        except ValueError as e:
            print(f"Correctly caught long description: {e}")

        # Test valid description
        try:
            valid_key = APIKeyCreateRequest(description="Valid API key for testing")
            print("Successfully validated API key creation request")
        except ValueError as e:
            print(f"Unexpected validation error: {e}")

    except ImportError as e:
        print(f"Import error: {e}")

def test_invalid_inference_request():
    """Test inference request with invalid data"""
    print("\nTesting invalid inference request...")

    # Test with missing API key
    try:
        response = requests.post(f"{GATEWAY_URL}/inference/generate", json={
            "text": "Test query",
            "context": ["context1"]
        })
        print(f"Missing API key: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")

    # Test with invalid API key format
    try:
        headers = {"X-API-Key": "invalid-key-format"}
        response = requests.post(f"{GATEWAY_URL}/inference/generate",
                               json={"text": "Test", "context": ["ctx"]},
                               headers=headers)
        print(f"Invalid API key format: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Connection error: {e}")

def test_pharmaceutical_content_validation():
    """Test pharmaceutical content validation"""
    print("\nTesting pharmaceutical content validation...")

    try:
        from gateway.src.validation import InferenceRequest

        # Test with non-pharmaceutical content
        try:
            invalid_request = InferenceRequest(
                text_input="I want to buy a car",
                max_length=4096,
                context_chunks=["general context"]
            )
            print("ERROR: Should have failed pharmaceutical validation")
        except ValueError as e:
            print(f"Correctly caught non-pharmaceutical content: {e}")

        # Test with valid pharmaceutical content
        try:
            valid_request = InferenceRequest(
                text_input="What is the dosage for aspirin medication?",
                max_length=4096,
                context_chunks=["pharmaceutical context about aspirin"]
            )
            print("Successfully validated pharmaceutical content")
        except ValueError as e:
            print(f"Unexpected validation error: {e}")

    except ImportError as e:
        print(f"Import error: {e}")

def main():
    print("Starting gateway validation tests...")
    print("=" * 50)

    # Add the project root to Python path
    sys.path.insert(0, '/Users/abderrahman/Desktop/ecommerce-microservices/SothemaAI/fastapi-microservices-app')

    test_invalid_login()
    test_invalid_registration()
    test_invalid_api_key_creation()
    test_invalid_inference_request()
    test_pharmaceutical_content_validation()

    print("\n" + "=" * 50)
    print("Validation tests completed!")
    print("Note: Some tests may fail if the gateway service is not running.")
    print("Start the services with: docker-compose up")

if __name__ == "__main__":
    main()