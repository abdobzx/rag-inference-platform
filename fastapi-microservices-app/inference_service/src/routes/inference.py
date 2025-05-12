from fastapi import APIRouter, Depends
from ..models.payload import InferenceRequest, InferenceResponse
from utils.model_loader import load_model, predict
from auth_service.src.utils.security import get_current_user

router = APIRouter()

# Load the model once when the service starts
model = load_model()

@router.post("/generate", response_model=InferenceResponse)
async def generate_inference(request: InferenceRequest, current_user: str = Depends(get_current_user)) -> InferenceResponse:
    prediction = predict(model, request.input_data)
    return InferenceResponse(prediction=prediction)