from pydantic import BaseModel, Field
from typing import List

class InferenceRequest(BaseModel):
    text_input: str = Field(..., description="The text prompt for the language model.")
    max_length: int | None = Field(default=150, description="Maximum number of new tokens to generate. Defaults to 150.")

class InferenceResponse(BaseModel):
    output_data: str
    status: str
    error: str = None

class EmbeddingRequestPayload(BaseModel):
    texts: List[str] = Field(..., description="A list of texts to embed.")

class EmbeddingResponsePayload(BaseModel):
    embeddings: List[List[float]] = Field(..., description="A list of embeddings, where each embedding is a list of floats.")
    status: str
    error: str = None