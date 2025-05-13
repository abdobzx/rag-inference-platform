from fastapi import APIRouter, Depends, HTTPException, Request
from ..models.payload import InferenceRequest, InferenceResponse, EmbeddingRequestPayload, EmbeddingResponsePayload
from ..utils.model_loader import predict, generate_embeddings
from ..utils.security import validate_api_key, ValidatedUserData
# Importer UNIQUEMENT le template de prompt nécessaire
from ..rag.rag_prompt_augmenter import FINAL_PROMPT_WITH_CONTEXT_TEMPLATE
import logging
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/generate", response_model=InferenceResponse)
async def generate_inference(
    fastapi_request: Request, 
    payload: InferenceRequest,
    validated_data: ValidatedUserData = Depends(validate_api_key) 
) -> InferenceResponse:
    logger.info(f"Requête d'inférence reçue pour l'utilisateur {validated_data.user_id} (clé préfixe: {validated_data.key_prefix}) avec text_input: '{payload.text_input[:50]}...' et max_length: {payload.max_length}")
    
    model = fastapi_request.app.state.model
    tokenizer = fastapi_request.app.state.tokenizer
    rag_augmenter = fastapi_request.app.state.rag_augmenter

    if model is None or tokenizer is None:
        logger.error("Le modèle d'inférence ou le tokenizer n'a pas été chargé dans l'état de l'application.")
        raise HTTPException(status_code=503, detail="Modèle ou tokenizer non chargé ou indisponible.")
    
    prompt_to_use: str

    if payload.context_chunks:
        logger.info(f"Utilisation des context_chunks fournis directement ({len(payload.context_chunks)} chunks) pour l'utilisateur {validated_data.user_id}.")
        context_str = "\n".join([f"- {chunk}" for chunk in payload.context_chunks])
        
        prompt_to_use = FINAL_PROMPT_WITH_CONTEXT_TEMPLATE.format(
            context=context_str,
            user_prompt=payload.text_input # La question originale de l'utilisateur
        )
        logger.info(f"Prompt construit avec les chunks fournis pour l'utilisateur {validated_data.user_id}. Début du prompt: {prompt_to_use[:250]}...")
    elif rag_augmenter: # Fallback: utiliser le RAG interne si aucun chunk n'est fourni
        try:
            logger.info(f"Tentative d'augmentation du prompt via RAG interne pour l'utilisateur {validated_data.user_id} car context_chunks non fourni.")
            # rag_augmenter.augment_prompt utilise maintenant FINAL_PROMPT_WITH_CONTEXT_TEMPLATE
            prompt_to_use = rag_augmenter.augment_prompt(user_prompt=payload.text_input)
            logger.info(f"Prompt augmenté (ou non) via RAG interne pour l'utilisateur {validated_data.user_id}. Début du prompt: {prompt_to_use[:250]}...")
        except Exception as e:
            logger.error(f"Erreur lors de l'augmentation du prompt via RAG interne pour l'utilisateur {validated_data.user_id}: {e}. Utilisation d'un prompt simple avec la question.", exc_info=True)
            # Fallback très simple si rag_augmenter échoue
            prompt_to_use = payload.text_input 
    else:
        logger.warning("Ni context_chunks fournis, ni augmentateur RAG disponible. Utilisation du prompt original sans augmentation (question seule).")
        prompt_to_use = payload.text_input # Question seule

    try:
        generated_text = predict(
            text_input=prompt_to_use, 
            model=model, 
            tokenizer=tokenizer, 
            max_length=payload.max_length
        )
        
        logger.info(f"Inférence réussie pour l'utilisateur {validated_data.user_id}. Entrée (après augmentation potentielle): {prompt_to_use[:100]}... Sortie: {generated_text[:100]}...")
        return InferenceResponse(output_data=generated_text, status="success")
    except Exception as e:
        logger.error(f"Erreur lors de la prédiction pour l'utilisateur {validated_data.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération de l'inférence: {str(e)}")

@router.post("/embed", response_model=EmbeddingResponsePayload)
async def create_embeddings(
    fastapi_request: Request,
    payload: EmbeddingRequestPayload,
    validated_data: ValidatedUserData = Depends(validate_api_key)
) -> EmbeddingResponsePayload:
    logger.info(f"Requête d'embedding reçue pour l'utilisateur {validated_data.user_id} (clé préfixe: {validated_data.key_prefix}) pour {len(payload.texts)} textes.")
    
    embedding_model = fastapi_request.app.state.embedding_model

    if embedding_model is None:
        logger.error("Le modèle d'embedding n'a pas été chargé dans l'état de l'application.")
        raise HTTPException(status_code=503, detail="Modèle d'embedding non chargé ou indisponible.")

    try:
        embeddings = generate_embeddings(texts=payload.texts, embedding_model=embedding_model)
        logger.info(f"Embeddings créés avec succès pour l'utilisateur {validated_data.user_id}.")
        return EmbeddingResponsePayload(embeddings=embeddings, status="success")
    except Exception as e:
        logger.error(f"Erreur lors de la création des embeddings pour l'utilisateur {validated_data.user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création des embeddings: {str(e)}")