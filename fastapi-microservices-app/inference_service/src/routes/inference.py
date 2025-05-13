from fastapi import APIRouter, Depends, HTTPException, Request
from ..models.payload import InferenceRequest, InferenceResponse
# Changement ici : importer la fonction predict mise à jour
from ..utils.model_loader import predict 
from ..utils.security import validate_api_key, ValidatedUserData
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate", response_model=InferenceResponse)
async def generate_inference(
    fastapi_request: Request, # Renommé `request` en `fastapi_request` pour éviter conflit avec la variable `request` de FastAPI
    payload: InferenceRequest,
    validated_data: ValidatedUserData = Depends(validate_api_key) 
) -> InferenceResponse:
    logger.info(f"Requête d'inférence reçue pour l'utilisateur {validated_data.user_id} (clé préfixe: {validated_data.key_prefix})")
    
    # Récupérer le modèle et le tokenizer depuis l'état de l'application
    model = fastapi_request.app.state.model
    tokenizer = fastapi_request.app.state.tokenizer

    if model is None or tokenizer is None:
        logger.error("Le modèle d'inférence ou le tokenizer n'a pas été chargé dans l'état de l'application.")
        raise HTTPException(status_code=503, detail="Modèle ou tokenizer non chargé ou indisponible.")
    
    try:
        # Utiliser la nouvelle fonction predict avec le modèle et le tokenizer
        generated_text = predict(text_input=payload.input_data, model=model, tokenizer=tokenizer)
        
        logger.info(f"Inférence réussie pour l'utilisateur {validated_data.user_id}. Entrée: {payload.input_data[:50]}...")
        # Retourner la réponse avec le texte généré
        return InferenceResponse(output_data=generated_text, status="success")
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction pour l'utilisateur {validated_data.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération de l'inférence: {str(e)}")