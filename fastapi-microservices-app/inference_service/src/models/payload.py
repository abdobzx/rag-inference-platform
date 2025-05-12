from pydantic import BaseModel

class InferenceRequest(BaseModel):
    input_data: str

class InferenceResponse(BaseModel):
    output_data: str
    status: str
    error: str = None