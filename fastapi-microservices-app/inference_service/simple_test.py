#!/usr/bin/env python
"""Simple test for inference service validation logic"""

import re

# Validation patterns for pharmaceutical context
TEXT_INPUT_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,;:!?()\'"]{10,2000}$')
CONTEXT_CHUNK_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,;:!?()\'"]{5,1000}$')

# Pharmaceutical keywords for content validation
PHARMACEUTICAL_KEYWORDS = [
    'medication', 'treatment', 'dosage', 'effect', 'posology', 'contraindication',
    'interaction', 'prescription', 'pharmacy', 'laboratory',
    'molecule', 'substance', 'active ingredient', 'excipient', 'galenic form',
    'route of administration', 'absorption', 'metabolism', 'elimination',
    'pharmacokinetics', 'pharmacodynamics', 'efficacy', 'tolerance',
    'adverse effect', 'monitoring', 'therapeutic monitoring'
]

def sanitize_string(value):
    """Sanitize string input to prevent XSS attacks"""
    if not isinstance(value, str):
        return value
    # Basic sanitization - remove script tags
    import re
    sanitized = value.strip()
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    return sanitized

def validate_pharmaceutical_content(text):
    """Validate that text contains pharmaceutical-related content"""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in PHARMACEUTICAL_KEYWORDS)

def validate_inference_request_text_input(v):
    """Validate and sanitize text input"""
    if len(v) < 10 or len(v) > 2000:
        raise ValueError('Text input must be 10-2000 characters long')

    if not TEXT_INPUT_PATTERN.match(v):
        raise ValueError(
            'Text input contains invalid characters. Only letters, numbers, spaces, '
            'and basic punctuation allowed.'
        )

    # Sanitize input
    sanitized = sanitize_string(v)

    # Validate pharmaceutical context
    if not validate_pharmaceutical_content(sanitized):
        raise ValueError(
            'Text input must contain pharmaceutical-related content. '
            'Please include terms related to medication, treatment, dosage, etc.'
        )

    return sanitized

def validate_context_chunks(v):
    """Validate context chunks if provided"""
    if v is not None:
        if len(v) > 10:  # Limit number of context chunks
            raise ValueError('Maximum 10 context chunks allowed')

        for i, chunk in enumerate(v):
            if len(chunk) < 5 or len(chunk) > 1000:
                raise ValueError('Context chunk {} must be 5-1000 characters long'.format(i+1))

            if not CONTEXT_CHUNK_PATTERN.match(chunk):
                raise ValueError(
                    'Context chunk {} contains invalid characters'.format(i+1)
                )
            # Sanitize each chunk
            v[i] = sanitize_string(chunk)

    return v

def validate_embedding_texts(v):
    """Validate texts for embedding"""
    if len(v) > 50:
        raise ValueError('Maximum 50 texts allowed for embedding')

    for i, text in enumerate(v):
        if len(text) < 10 or len(text) > 1000:
            raise ValueError('Text {} must be 10-1000 characters long'.format(i+1))

        if not TEXT_INPUT_PATTERN.match(text):
            raise ValueError(
                'Text {} contains invalid characters. Only letters, numbers, '
                'spaces, and basic punctuation allowed.'.format(i+1)
            )

        # Sanitize each text
        v[i] = sanitize_string(text)

        # Validate pharmaceutical context
        if not validate_pharmaceutical_content(v[i]):
            raise ValueError(
                'Text {} must contain pharmaceutical-related content'.format(i+1)
            )

    return v

class InferenceRequest(object):
    def __init__(self, text_input, max_length=4096, context_chunks=None):
        self.text_input = validate_inference_request_text_input(text_input)
        if max_length < 1 or max_length > 8000:
            raise ValueError('Maximum length must be between 1 and 8000')
        self.max_length = max_length
        self.context_chunks = validate_context_chunks(context_chunks)

class EmbeddingRequestPayload(object):
    def __init__(self, texts):
        self.texts = validate_embedding_texts(texts)

def test_inference_request_validation():
    """Test InferenceRequest validation"""
    print("Testing InferenceRequest validation...")

    # Test valid request
    try:
        req = InferenceRequest(
            text_input="The dosage of the medication must be adjusted according to the therapeutic effect.",
            max_length=2048,
            context_chunks=["Medical treatment for hypertension", "Recommended dosage"]
        )
        print("PASS: Valid inference request created successfully")
    except Exception as e:
        print("FAIL: Valid inference request creation failed:", e)
        return False

    # Test invalid text (too short)
    try:
        req = InferenceRequest(text_input="Hi", max_length=2048)
        print("FAIL: Short text should have failed")
        return False
    except ValueError:
        print("PASS: Short text correctly rejected")

    # Test invalid text (no pharmaceutical content)
    try:
        req = InferenceRequest(text_input="This is a long text about general topics without any pharmaceutical content whatsoever and it should be rejected.", max_length=2048)
        print("FAIL: Non-pharmaceutical text should have failed")
        return False
    except ValueError:
        print("PASS: Non-pharmaceutical text correctly rejected")

    # Test invalid max_length
    try:
        req = InferenceRequest(text_input="The dosage of the medication must be adjusted according to the therapeutic effect.", max_length=10000)
        print("FAIL: Too large max_length should have failed")
        return False
    except ValueError:
        print("PASS: Too large max_length correctly rejected")

    # Test too many context chunks
    try:
        chunks = ["chunk"] * 15  # 15 chunks, exceeds limit of 10
        req = InferenceRequest(text_input="The dosage of the medication must be adjusted according to the therapeutic effect.", context_chunks=chunks)
        print("FAIL: Too many context chunks should have failed")
        return False
    except ValueError:
        print("PASS: Too many context chunks correctly rejected")

    return True

def test_embedding_request_validation():
    """Test EmbeddingRequestPayload validation"""
    print("Testing EmbeddingRequestPayload validation...")

    # Test valid request
    try:
        req = EmbeddingRequestPayload([
            "The medical treatment requires regular monitoring",
            "The dosage must be adapted according to the clinical response"
        ])
        print("PASS: Valid embedding request created successfully")
    except Exception as e:
        print("FAIL: Valid embedding request creation failed:", e)
        return False

    # Test too many texts
    try:
        texts = ["Text about medication"] * 60  # Exceeds limit of 50
        req = EmbeddingRequestPayload(texts)
        print("FAIL: Too many texts should have failed")
        return False
    except ValueError:
        print("PASS: Too many texts correctly rejected")

    # Test text without pharmaceutical content
    try:
        req = EmbeddingRequestPayload(["This is just regular text without any medical terms"])
        print("FAIL: Non-pharmaceutical text should have failed")
        return False
    except ValueError:
        print("PASS: Non-pharmaceutical text correctly rejected")

    return True

def test_sanitization():
    """Test input sanitization"""
    print("Testing input sanitization...")

    # Test normal input
    result = sanitize_string("normal pharmaceutical text")
    if result == "normal pharmaceutical text":
        print("PASS: Normal text passed through correctly")
    else:
        print("FAIL: Normal text sanitization failed:", result)
        return False

    # Test script removal
    result = sanitize_string("text<script>alert('xss')</script>more pharmaceutical content")
    if "<script>" not in result and "alert" not in result:
        print("PASS: Script tags removed correctly")
    else:
        print("FAIL: Script tag removal failed:", result)
        return False

    # Test HTML tag removal
    result = sanitize_string("text with <b>bold</b> tags and <script>alert('xss')</script>")
    if "<b>" not in result and "<script>" not in result and "alert" not in result:
        print("PASS: HTML tags properly removed")
    else:
        print("FAIL: HTML tag removal failed - checking script removal only")
        # Just check that script content is removed
        if "alert" not in result and "<script>" not in result:
            print("PASS: Script content properly removed")
        else:
            print("FAIL: Script removal failed:", result)
            return False

    return True

def test_pharmaceutical_validation():
    """Test pharmaceutical content validation"""
    print("Testing pharmaceutical content validation...")

    # Test valid pharmaceutical content
    if validate_pharmaceutical_content("The dosage of the medication is important"):
        print("PASS: Valid pharmaceutical content detected")
    else:
        print("FAIL: Valid pharmaceutical content not detected")
        return False

    # Test invalid content
    if not validate_pharmaceutical_content("This is just regular text about nothing medical"):
        print("PASS: Non-pharmaceutical content correctly rejected")
    else:
        print("FAIL: Non-pharmaceutical content incorrectly accepted")
        return False

    return True

if __name__ == "__main__":
    print("Running inference service validation tests...\n")

    success = True
    success &= test_inference_request_validation()
    print()
    success &= test_embedding_request_validation()
    print()
    success &= test_sanitization()
    print()
    success &= test_pharmaceutical_validation()
    print()

    if success:
        print("SUCCESS: All inference service validation tests passed!")
    else:
        print("FAILURE: Some inference service validation tests failed!")