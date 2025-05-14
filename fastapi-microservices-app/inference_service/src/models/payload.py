from pydantic import BaseModel, Field
from typing import List, Optional

class InferenceRequest(BaseModel):
    text_input: str = Field(..., example="Expliquez l'importance de l'IA.")
    max_length: int = Field(4096, gt=0, le=8000, example=4096)
    context_chunks: Optional[List[str]] = Field(None, example=["Chunk 1 de contexte.", "Chunk 2 de contexte."])

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