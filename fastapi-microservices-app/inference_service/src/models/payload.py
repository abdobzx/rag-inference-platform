from pydantic import BaseModel, Field

class InferenceRequest(BaseModel):
    text_input: str = Field(..., description="The text prompt for the language model.")
    max_length: int | None = Field(default=150, description="Maximum number of new tokens to generate. Defaults to 150.")

class InferenceResponse(BaseModel):
    output_data: str
    status: str
    error: str = None