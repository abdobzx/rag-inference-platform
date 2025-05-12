from fastapi import APIRouter, Depends, HTTPException, Request
from ..models.payload import InferenceRequest, InferenceResponse
from ..utils.model_loader import predict
from ..utils.security import validate_api_key, ValidatedUserData # Ajout de ValidatedUserData
import logging # Ajout du logging

logger = logging.getLogger(__name__) # Ajout du logger

router = APIRouter()

@router.post("/generate", response_model=InferenceResponse)
async def generate_inference(
    fastapi_request: Request,
    payload: InferenceRequest,
    # La dépendance validate_api_key s'occupera de l'authentification.
    # Si la clé est valide, les informations de l'utilisateur seront dans validated_data.
    # Si la clé est invalide ou manquante, une HTTPException sera levée par la dépendance.
    validated_data: ValidatedUserData = Depends(validate_api_key) 
) -> InferenceResponse:
    # À ce stade, la clé API a été validée avec succès par le auth_service via la dépendance.
    # Nous avons accès à validated_data.user_id, validated_data.key_prefix, etc.
    logger.info(f"Requête d'inférence reçue pour l'utilisateur {validated_data.user_id} (clé préfixe: {validated_data.key_prefix})")
    
    model = fastapi_request.app.state.model
    if model is None:
        logger.error("Le modèle d'inférence n'a pas été chargé dans l'état de l'application.")
        raise HTTPException(status_code=503, detail="Modèle non chargé ou indisponible.")
    
    try:
        prediction = predict(model, payload.input_data)
        logger.info(f"Inférence réussie pour l'utilisateur {validated_data.user_id}. Entrée: {payload.input_data[:50]}...") # Log tronqué
        return InferenceResponse(prediction=prediction)
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction pour l'utilisateur {validated_data.user_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la génération de l'inférence.")