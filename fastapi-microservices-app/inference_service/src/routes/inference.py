from fastapi import APIRouter, Depends, HTTPException, Request # Request ajouté
from ..models.payload import InferenceRequest, InferenceResponse
# Importer uniquement predict, load_model n'est plus nécessaire ici
from ..utils.model_loader import predict
# from ..utils.security import get_current_user # Commenté pour l'instant

router = APIRouter()

# Supprimer le chargement global du modèle ici :
# model = load_model()

@router.post("/generate", response_model=InferenceResponse)
async def generate_inference(
    fastapi_request: Request, # Injecter l'objet Request
    payload: InferenceRequest # Renommé 'request' en 'payload' pour éviter les conflits
) -> InferenceResponse:
    model = fastapi_request.app.state.model
    if model is None:
        # Ce cas devrait idéalement être géré par un échec de démarrage
        # ou un statut plus clair.
        raise HTTPException(status_code=503, detail="Model not loaded or unavailable.")
    prediction = predict(model, payload.input_data)
    return InferenceResponse(prediction=prediction)