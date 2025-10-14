#!/usr/bin/env python
"""Test script for auth service validation"""

import sys
import os

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Now import from routes.auth
from routes.auth import UserCreate, VerifyEmailRequest, sanitize_input

def test_user_create_validation():
    """Test UserCreate validation"""
    print("Testing UserCreate validation...")

    # Test valid user
    try:
        user = UserCreate("testuser", "test@mysothemalab.com", "password123")
        print("PASS: Valid user created successfully")
    except Exception as e:
        print("FAIL: Valid user creation failed:", e)
        return False

    # Test invalid username (too short)
    try:
        user = UserCreate("ab", "test@mysothemalab.com", "password123")
        print("FAIL: Short username should have failed")
        return False
    except:
        print("PASS: Short username correctly rejected")

    # Test invalid email domain
    try:
        user = UserCreate("testuser", "test@gmail.com", "password123")
        print("FAIL: Wrong domain email should have failed")
        return False
    except:
        print("PASS: Wrong domain email correctly rejected")

    # Test short password
    try:
        user = UserCreate("testuser", "test@mysothemalab.com", "123")
        print("FAIL: Short password should have failed")
        return False
    except:
        print("PASS: Short password correctly rejected")

    return True

def test_verify_email_validation():
    """Test VerifyEmailRequest validation"""
    print("Testing VerifyEmailRequest validation...")

    # Test valid request
    try:
        req = VerifyEmailRequest("test@mysothemalab.com", "123456")
        print("PASS: Valid verification request created successfully")
    except Exception as e:
        print("FAIL: Valid verification request creation failed:", e)
        return False

    # Test invalid email domain
    try:
        req = VerifyEmailRequest("test@gmail.com", "123456")
        print("FAIL: Wrong domain email should have failed")
        return False
    except:
        print("PASS: Wrong domain email correctly rejected")

    # Test invalid code (not 6 digits)
    try:
        req = VerifyEmailRequest("test@mysothemalab.com", "12345")
        print("FAIL: Short code should have failed")
        return False
    except:
        print("PASS: Short code correctly rejected")

    return True

def test_sanitization():
    """Test input sanitization"""
    print("Testing input sanitization...")

    # Test normal input
    result = sanitize_input("normal text")
    if result == "normal text":
        print("PASS: Normal text passed through correctly")
    else:
        print("FAIL: Normal text sanitization failed:", result)
        return False

    # Test script removal
    result = sanitize_input("text<script>alert('xss')</script>more text")
    if "<script>" not in result and "alert" not in result:
        print("PASS: Script tags removed correctly")
    else:
        print("FAIL: Script tag removal failed:", result)
        return False

    # Test javascript removal
    result = sanitize_input("text javascript:alert('xss') more text")
    if "javascript:" not in result:
        print("PASS: JavaScript protocol removed correctly")
    else:
        print("FAIL: JavaScript protocol removal failed:", result)
        return False

    return True

if __name__ == "__main__":
    print("Running auth service validation tests...\n")

    success = True
    success &= test_user_create_validation()
    print()
    success &= test_verify_email_validation()
    print()
    success &= test_sanitization()
    print()

    if success:
        print("SUCCESS: All validation tests passed!")
        sys.exit(0)
    else:
        print("FAILURE: Some validation tests failed!")
        sys.exit(1)