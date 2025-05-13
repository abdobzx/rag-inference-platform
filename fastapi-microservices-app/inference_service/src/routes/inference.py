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
    fastapi_request: Request, 
    payload: InferenceRequest, # Utilise le payload.py mis à jour
    validated_data: ValidatedUserData = Depends(validate_api_key) 
) -> InferenceResponse:
    logger.info(f"Requête d'inférence reçue pour l'utilisateur {validated_data.user_id} (clé préfixe: {validated_data.key_prefix}) avec text_input: '{payload.text_input[:50]}...' et max_length: {payload.max_length}")
    
    model = fastapi_request.app.state.model
    tokenizer = fastapi_request.app.state.tokenizer
    rag_augmenter = fastapi_request.app.state.rag_augmenter

    if model is None or tokenizer is None:
        logger.error("Le modèle d'inférence ou le tokenizer n'a pas été chargé dans l'état de l'application.")
        raise HTTPException(status_code=503, detail="Modèle ou tokenizer non chargé ou indisponible.")
    
    # Utiliser payload.text_input pour l'augmentation et la prédiction
    prompt_to_use = payload.text_input 
    if rag_augmenter:
        try:
            logger.info(f"Tentative d'augmentation du prompt pour l'utilisateur {validated_data.user_id}")
            augmented_prompt = rag_augmenter.augment_prompt(user_prompt=payload.text_input)
            if augmented_prompt != payload.text_input:
                logger.info(f"Prompt augmenté avec succès pour l'utilisateur {validated_data.user_id}.")
                prompt_to_use = augmented_prompt
            else:
                logger.info(f"Aucun contexte pertinent trouvé ou le prompt est resté inchangé pour l'utilisateur {validated_data.user_id}.")
        except Exception as e:
            logger.error(f"Erreur lors de l'augmentation du prompt pour l'utilisateur {validated_data.user_id}: {e}. Utilisation du prompt original.", exc_info=True)
            # Continuer avec le prompt original en cas d'erreur d'augmentation
    else:
        logger.warning("L'augmentateur RAG n'est pas disponible. Utilisation du prompt original sans augmentation.")

    try:
        # Utiliser le prompt (augmenté ou original) et payload.max_length pour la prédiction
        generated_text = predict(
            text_input=prompt_to_use, 
            model=model, 
            tokenizer=tokenizer, 
            max_length=payload.max_length # Passer max_length ici
        )
        
        logger.info(f"Inférence réussie pour l'utilisateur {validated_data.user_id}. Entrée (après augmentation potentielle): {prompt_to_use[:100]}... Sortie: {generated_text[:100]}...")
        return InferenceResponse(output_data=generated_text, status="success")
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction pour l'utilisateur {validated_data.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération de l'inférence: {str(e)}")