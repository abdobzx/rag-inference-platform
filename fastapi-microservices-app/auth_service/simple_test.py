#!/usr/bin/env python
"""Simple test for auth service validation logic"""

import re

class UserCreate(object):
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

class VerifyEmailRequest(object):
    def __init__(self, email, verification_code):
        self.email = email
        self.verification_code = verification_code

def sanitize_input(text):
    """Sanitize input to prevent XSS attacks"""
    if not isinstance(text, str):
        return ""
    # Basic sanitization - remove script tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    return text.strip()

def validate_user_create(user_data):
    """Validate UserCreate data"""
    errors = []

    # Username validation
    if len(user_data.username) < 3 or len(user_data.username) > 30:
        errors.append("Username must be 3-30 characters")

    # Email domain validation
    if not user_data.email.endswith('@mysothemalab.com'):
        errors.append("Email must be from mysothemalab.com domain")

    # Password length validation
    if len(user_data.password) < 8:
        errors.append("Password must be at least 8 characters")

    return errors

def validate_verify_email(request):
    """Validate VerifyEmailRequest data"""
    errors = []

    # Email domain validation
    if not request.email.endswith('@mysothemalab.com'):
        errors.append("Email must be from mysothemalab.com domain")

    # Verification code validation
    if not re.match(r'^\d{6}$', request.verification_code):
        errors.append("Verification code must be exactly 6 digits")

    return errors

def test_user_create_validation():
    """Test UserCreate validation"""
    print("Testing UserCreate validation...")

    # Test valid user
    user = UserCreate("testuser", "test@mysothemalab.com", "password123")
    errors = validate_user_create(user)
    if not errors:
        print("PASS: Valid user passed validation")
    else:
        print("FAIL: Valid user failed validation:", errors)
        return False

    # Test invalid username (too short)
    user = UserCreate("ab", "test@mysothemalab.com", "password123")
    errors = validate_user_create(user)
    if "Username must be 3-30 characters" in errors:
        print("PASS: Short username correctly rejected")
    else:
        print("FAIL: Short username should have been rejected")
        return False

    # Test invalid email domain
    user = UserCreate("testuser", "test@gmail.com", "password123")
    errors = validate_user_create(user)
    if "Email must be from mysothemalab.com domain" in errors:
        print("PASS: Wrong domain email correctly rejected")
    else:
        print("FAIL: Wrong domain email should have been rejected")
        return False

    # Test short password
    user = UserCreate("testuser", "test@mysothemalab.com", "123")
    errors = validate_user_create(user)
    if "Password must be at least 8 characters" in errors:
        print("PASS: Short password correctly rejected")
    else:
        print("FAIL: Short password should have been rejected")
        return False

    return True

def test_verify_email_validation():
    """Test VerifyEmailRequest validation"""
    print("Testing VerifyEmailRequest validation...")

    # Test valid request
    req = VerifyEmailRequest("test@mysothemalab.com", "123456")
    errors = validate_verify_email(req)
    if not errors:
        print("PASS: Valid verification request passed validation")
    else:
        print("FAIL: Valid verification request failed validation:", errors)
        return False

    # Test invalid email domain
    req = VerifyEmailRequest("test@gmail.com", "123456")
    errors = validate_verify_email(req)
    if "Email must be from mysothemalab.com domain" in errors:
        print("PASS: Wrong domain email correctly rejected")
    else:
        print("FAIL: Wrong domain email should have been rejected")
        return False

    # Test invalid code (not 6 digits)
    req = VerifyEmailRequest("test@mysothemalab.com", "12345")
    errors = validate_verify_email(req)
    if "Verification code must be exactly 6 digits" in errors:
        print("PASS: Short code correctly rejected")
    else:
        print("FAIL: Short code should have been rejected")
        return False

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
    else:
        print("FAILURE: Some validation tests failed!")