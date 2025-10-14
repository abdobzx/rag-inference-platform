from fastapi import APIRouter
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

router = APIRouter()

@router.post("/register")
def register_user(user_data):
    # Basic validation
    if len(user_data.username) < 3 or len(user_data.username) > 30:
        return {"error": "Username must be 3-30 characters"}
    if not user_data.email.endswith('@mysothemalab.com'):
        return {"error": "Email must be from mysothemalab.com domain"}
    if len(user_data.password) < 8:
        return {"error": "Password must be at least 8 characters"}

    # Sanitize inputs
    sanitized_username = sanitize_input(user_data.username)
    sanitized_email = sanitize_input(user_data.email)

    return {"message": "User registered successfully", "username": sanitized_username}

@router.post("/verify-email")
def verify_email(request):
    if not request.email.endswith('@mysothemalab.com'):
        return {"error": "Email must be from mysothemalab.com domain"}
    if not re.match(r'^\d{6}$', request.verification_code):
        return {"error": "Verification code must be exactly 6 digits"}

    sanitized_email = sanitize_input(request.email)
    return {"message": "Email verified successfully", "email": sanitized_email}
