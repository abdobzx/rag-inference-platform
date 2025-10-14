import re
import json
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import logging

logger = logging.getLogger(__name__)

# Validation patterns
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@mysothemalab\.com$')
PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
API_KEY_PATTERN = re.compile(r'^sk-[a-zA-Z0-9]{32,64}$')
VERIFICATION_CODE_PATTERN = re.compile(r'^\d{6}$')

# Pharmaceutical keywords for content validation
PHARMACEUTICAL_KEYWORDS = [
    'medication', 'treatment', 'dosage', 'effect', 'posology', 'contraindication',
    'interaction', 'prescription', 'pharmacy', 'laboratory',
    'molecule', 'substance', 'active ingredient', 'excipient', 'galenic form',
    'route of administration', 'absorption', 'metabolism', 'elimination',
    'pharmacokinetics', 'pharmacodynamics', 'efficacy', 'tolerance',
    'adverse effect', 'monitoring', 'therapeutic monitoring'
]

def sanitize_string(value: str) -> str:
    """Sanitize string input to prevent XSS attacks"""
    if not isinstance(value, str):
        return value
    # Remove HTML tags and escape special characters
    import html
    sanitized = html.escape(value.strip())
    # Remove potential script tags (double protection)
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    return sanitized

def validate_pharmaceutical_content(text: str) -> bool:
    """Validate that text contains pharmaceutical-related content"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in PHARMACEUTICAL_KEYWORDS)

# Validation Models
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="Username for authentication")
    password: str = Field(..., min_length=1, max_length=100, description="Password for authentication")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate and sanitize username"""
        if not isinstance(v, str):
            raise ValueError('Username must be a string')
        v = sanitize_string(v)
        if not USERNAME_PATTERN.match(v):
            raise ValueError('Username must be 3-30 characters, alphanumeric with underscores only')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate and sanitize password"""
        if not isinstance(v, str):
            raise ValueError('Password must be a string')
        v = sanitize_string(v)
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30, description="Username (3-30 chars, alphanumeric)")
    email: str = Field(..., description="Email address from mysothemalab.com domain")
    password: str = Field(..., min_length=8, description="Password with complexity requirements")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        """Validate and sanitize username"""
        if not isinstance(v, str):
            raise ValueError('Username must be a string')
        v = sanitize_string(v)
        if not USERNAME_PATTERN.match(v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate and sanitize email"""
        if not isinstance(v, str):
            raise ValueError('Email must be a string')
        v = sanitize_string(v)
        if not EMAIL_PATTERN.match(v):
            raise ValueError('Email must be from mysothemalab.com domain')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password complexity"""
        if not isinstance(v, str):
            raise ValueError('Password must be a string')
        v = sanitize_string(v)
        if not PASSWORD_PATTERN.match(v):
            raise ValueError('Password must contain uppercase, lowercase, digit, and special character')
        return v

class VerifyEmailRequest(BaseModel):
    email: str = Field(..., description="Email address to verify")
    verification_code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate and sanitize email"""
        if not isinstance(v, str):
            raise ValueError('Email must be a string')
        v = sanitize_string(v)
        if not EMAIL_PATTERN.match(v):
            raise ValueError('Email must be from mysothemalab.com domain')
        return v

    @field_validator('verification_code')
    @classmethod
    def validate_code(cls, v):
        """Validate verification code format"""
        if not isinstance(v, str):
            raise ValueError('Verification code must be a string')
        if not VERIFICATION_CODE_PATTERN.match(v):
            raise ValueError('Verification code must be exactly 6 digits')
        return v

class APIKeyCreateRequest(BaseModel):
    description: Optional[str] = Field(None, min_length=1, max_length=200, description="Optional description")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate and sanitize description"""
        if v is not None:
            if not isinstance(v, str):
                raise ValueError('Description must be a string')
            v = sanitize_string(v)
            if len(v) > 200:
                raise ValueError('Description must be 200 characters or less')
        return v

class InferenceRequest(BaseModel):
    text_input: str = Field(..., min_length=10, max_length=2000, description="Input text for inference")
    max_length: int = Field(4096, ge=1, le=8000, description="Maximum response length")
    context_chunks: Optional[List[str]] = Field(None, description="Optional context chunks")

    @field_validator('text_input')
    @classmethod
    def validate_text_input(cls, v):
        """Validate and sanitize text input"""
        if not isinstance(v, str):
            raise ValueError('Text input must be a string')
        v = sanitize_string(v)
        if len(v) < 10 or len(v) > 2000:
            raise ValueError('Text input must be 10-2000 characters')

        # Validate pharmaceutical content
        if not validate_pharmaceutical_content(v):
            raise ValueError('Text input must contain pharmaceutical-related content')
        return v

    @field_validator('context_chunks')
    @classmethod
    def validate_context_chunks(cls, v):
        """Validate context chunks"""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError('Context chunks must be a list')
            if len(v) > 10:
                raise ValueError('Maximum 10 context chunks allowed')

            for i, chunk in enumerate(v):
                if not isinstance(chunk, str):
                    raise ValueError(f'Context chunk {i+1} must be a string')
                chunk = sanitize_string(chunk)
                if len(chunk) < 5 or len(chunk) > 1000:
                    raise ValueError(f'Context chunk {i+1} must be 5-1000 characters')
                v[i] = chunk
        return v

class EmbeddingRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, max_length=50, description="List of texts to embed")

    @field_validator('texts')
    @classmethod
    def validate_texts(cls, v):
        """Validate texts for embedding"""
        if not isinstance(v, list):
            raise ValueError('Texts must be a list')
        if len(v) > 50:
            raise ValueError('Maximum 50 texts allowed for embedding')

        for i, text in enumerate(v):
            if not isinstance(text, str):
                raise ValueError(f'Text {i+1} must be a string')
            text = sanitize_string(text)
            if len(text) < 10 or len(text) > 1000:
                raise ValueError(f'Text {i+1} must be 10-1000 characters')

            # Validate pharmaceutical content
            if not validate_pharmaceutical_content(text):
                raise ValueError(f'Text {i+1} must contain pharmaceutical-related content')
            v[i] = text
        return v

def validate_api_key_header(api_key: str) -> str:
    """Validate API key format from header"""
    if not isinstance(api_key, str):
        raise ValueError('API key must be a string')
    if not API_KEY_PATTERN.match(api_key):
        raise ValueError('API key must be in format sk-xxxxxxxxxxxxxxxx')
    return api_key

def validate_json_payload(raw_body: bytes, expected_model) -> Dict[str, Any]:
    """Validate JSON payload against a Pydantic model"""
    try:
        payload = json.loads(raw_body)
        # Validate using the model
        validated_payload = expected_model(**payload)
        return validated_payload.model_dump()
    except json.JSONDecodeError:
        raise ValueError('Invalid JSON payload')
    except Exception as e:
        raise ValueError(f'Validation error: {str(e)}')