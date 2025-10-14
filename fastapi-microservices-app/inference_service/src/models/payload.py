import re
import html

# Validation patterns for pharmaceutical context
TEXT_INPUT_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,;:!?()\'"À-ÿ]{10,2000}$')
CONTEXT_CHUNK_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,;:!?()\'"À-ÿ]{5,1000}$')

# Pharmaceutical keywords for content validation
PHARMACEUTICAL_KEYWORDS = [
    'médicament', 'traitement', 'dosage', 'effet', 'posologie', 'contre-indication',
    'interaction', 'prescription', 'ordonnance', 'pharmacie', 'laboratoire',
    'molecule', 'substance', 'principe actif', 'excipient', 'forme galénique',
    'voie d\'administration', 'absorption', 'métabolisme', 'élimination',
    'pharmacocinétique', 'pharmacodynamie', 'efficacité', 'tolérance',
    'effet indésirable', 'surveillance', 'suivi thérapeutique'
]

def sanitize_string(value):
    """Sanitize string input to prevent XSS attacks"""
    if not isinstance(value, str):
        return value
    # Remove HTML tags and escape special characters
    sanitized = html.escape(value.strip())
    # Remove potential script tags (double protection)
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

def validate_output_data(v):
    """Validate output data"""
    if v and len(v) > 10000:  # Reasonable limit for response
        raise ValueError('Output data too long (max 10000 characters)')
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

def validate_embeddings(v):
    """Validate embedding dimensions"""
    if not v:
        return v

    # Check that all embeddings have the same dimension
    first_dim = len(v[0])
    for i, embedding in enumerate(v):
        if len(embedding) != first_dim:
            raise ValueError('Embedding {} has inconsistent dimensions'.format(i))

        # Reasonable bounds for embedding values
        for val in embedding:
            if not (-10 <= val <= 10):
                raise ValueError('Embedding value {} out of reasonable range'.format(val))

    return v

class InferenceRequest(object):
    def __init__(self, text_input, max_length=4096, context_chunks=None):
        self.text_input = validate_inference_request_text_input(text_input)
        if max_length < 1 or max_length > 8000:
            raise ValueError('Maximum length must be between 1 and 8000')
        self.max_length = max_length
        self.context_chunks = validate_context_chunks(context_chunks)

class InferenceResponse(object):
    def __init__(self, output_data, status, error=None):
        self.output_data = validate_output_data(output_data)
        self.status = status
        self.error = error

class EmbeddingRequestPayload(object):
    def __init__(self, texts):
        self.texts = validate_embedding_texts(texts)

class EmbeddingResponsePayload(object):
    def __init__(self, embeddings, status, error=None):
        self.embeddings = validate_embeddings(embeddings)
        self.status = status
        self.error = error
