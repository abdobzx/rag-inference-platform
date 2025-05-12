from fastapi import APIRouter, Depends, HTTPException
from ..models.payload import InferenceRequest, InferenceResponse
from ..utils.model_loader import load_model, predict
# from ..utils.security import get_current_user # Commenté pour l'instant

router = APIRouter()

# Load the model once when the service starts
model = load_model()

@router.post("/generate", response_model=InferenceResponse)
async def generate_inference(request: InferenceRequest) -> InferenceResponse: # current_user enlevé pour l'instant
    prediction = predict(model, request.input_data)
    return InferenceResponse(prediction=prediction)