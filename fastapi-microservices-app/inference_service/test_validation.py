#!/usr/bin/env python
"""Test script for inference service validation"""

import sys
import os

# Add the src directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from models.payload import (
    InferenceRequest, InferenceResponse, EmbeddingRequestPayload, EmbeddingResponsePayload,
    validate_pharmaceutical_content, sanitize_string
)

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

    # Test HTML escaping
    result = sanitize_string("text with <b>bold</b> tags and & symbols")
    if "<b>" not in result and "&" in result:  # & should be escaped to &amp;
        print("PASS: HTML properly escaped")
    else:
        print("FAIL: HTML escaping failed:", result)
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