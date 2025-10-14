from typing import Any, Dict, Tuple, List
import logging
import os
from transformers import AutoModelForCausalLM, AutoTokenizer, PreTrainedModel, PreTrainedTokenizer
import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Variable globale pour stocker le modèle et le tokenizer chargés
# afin d'éviter de les recharger à chaque requête.
# Ils seront initialisés au démarrage de l'application FastAPI.
_model: PreTrainedModel | None = None
_tokenizer: PreTrainedTokenizer | None = None
_embedding_model: SentenceTransformer | None = None

# Configuration du modèle et du tokenizer (MODIFIABLE)
# Ancien modèle: deepseek-ai/deepseek-coder-1.3b-instruct
MODEL_NAME = os.getenv("MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.2")
TOKENIZER_NAME = os.getenv("TOKENIZER_NAME", "mistralai/Mistral-7B-Instruct-v0.2")

# Modèle d'embedding (MODIFIABLE SI NÉCESSAIRE)
# Ancien modèle: sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")

# HuggingFace token for authentication
HUGGINGFACE_TOKEN = os.getenv("HUGGING_FACE_HUB_TOKEN")

def load_model_and_tokenizer() -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
    """Charge le modèle LLM et le tokenizer."""
    global _model, _tokenizer
    if _model is not None and _tokenizer is not None:
        logger.info(f"Modèle '{MODEL_NAME}' et tokenizer déjà chargés.")
        return _model, _tokenizer

    try:
        logger.info(f"Tentative de chargement du tokenizer : {TOKENIZER_NAME}")
        tokenizer = AutoTokenizer.from_pretrained(
            TOKENIZER_NAME,
            token=HUGGINGFACE_TOKEN,
            trust_remote_code=True
        )
        logger.info("Tokenizer chargé avec succès.")

        # CORRECTION POUR model_max_length ABERRANT
        if tokenizer.model_max_length is None or tokenizer.model_max_length > 1_000_000_000:  # Seuil très grand
            corrected_max_length = 8192
            logger.warning(f"tokenizer.model_max_length était {tokenizer.model_max_length}. Correction à {corrected_max_length}.")
            tokenizer.model_max_length = corrected_max_length

        logger.info(f"Tokenizer model_max_length (après correction potentielle): {tokenizer.model_max_length}")
        logger.info(f"Tokenizer padding_side: {tokenizer.padding_side}")
        logger.info(f"Tokenizer chat_template: {tokenizer.chat_template}")

        logger.info(f"Tentative de chargement du modèle : {MODEL_NAME}")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME, 
            trust_remote_code=True,
            token=HUGGINGFACE_TOKEN,
            device_map="auto",
            torch_dtype=torch.bfloat16
        )
        logger.info(f"Modèle LLM chargé avec succès sur le device : {model.device}")
        
        if tokenizer.pad_token_id is None:
            logger.info("tokenizer.pad_token_id non défini. Utilisation de tokenizer.eos_token_id comme pad_token_id.")
            tokenizer.pad_token_id = tokenizer.eos_token_id
        
        if model.config.pad_token_id is None:
            model.config.pad_token_id = tokenizer.pad_token_id

        _model = model
        _tokenizer = tokenizer
        return model, tokenizer
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle '{MODEL_NAME}' ou du tokenizer: {e}", exc_info=True)
        raise RuntimeError(f"Erreur lors du chargement du modèle '{MODEL_NAME}' ou du tokenizer: {e}") from e

def load_embedding_model(model_name: str = EMBEDDING_MODEL_NAME) -> SentenceTransformer:
    """
    Charge un modèle de sentence-transformer depuis Hugging Face.
    Utilise une variable globale pour stocker le modèle une fois chargé.
    """
    global _embedding_model
    if _embedding_model is not None:
        logger.info(f"Modèle d'embedding '{model_name}' déjà chargé.")
        return _embedding_model

    try:
        logger.info(f"Chargement du modèle d'embedding '{model_name}'...")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Utilisation du périphérique pour le modèle d'embedding : {device}")
        
        embedding_model = SentenceTransformer(
            model_name, 
            device=device,
            token=HUGGINGFACE_TOKEN
        )
        _embedding_model = embedding_model
        logger.info(f"Modèle d'embedding '{model_name}' chargé avec succès sur {device}.")
        return embedding_model
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle d'embedding '{model_name}': {e}", exc_info=True)
        raise

def generate_embeddings(texts: List[str], embedding_model: SentenceTransformer) -> List[List[float]]:
    """
    Génère des embeddings pour une liste de textes en utilisant le modèle de sentence-transformer chargé.
    """
    try:
        logger.info(f"Génération d'embeddings pour {len(texts)} textes.")
        embeddings = embedding_model.encode(texts, convert_to_tensor=False)
        if hasattr(embeddings, 'tolist'):
            embeddings_list = embeddings.tolist()
        else:
            embeddings_list = list(map(list, embeddings))

        logger.info(f"Embeddings générés avec succès. Premier embedding (tronqué): {str(embeddings_list[0][:5]) if embeddings_list and embeddings_list[0] else 'N/A'}...")
        return embeddings_list
    except Exception as e:
        logger.error(f"Erreur lors de la génération des embeddings: {e}", exc_info=True)
        raise

def predict(text_input: str, max_length_request: int, model: PreTrainedModel, tokenizer: PreTrainedTokenizer) -> str:
    """
    Génère du texte en utilisant le modèle et le tokenizer chargés.
    """
    logger.info(f"Génération de texte pour l'entrée : '{text_input[:100]}...'")
    device = model.device

    try:
        tokenizer_max_len = tokenizer.model_max_length if tokenizer.model_max_length is not None else 4096
        resolved_max_length_for_tokenizer = tokenizer_max_len
        max_new_tokens = int(max_length_request)

        logger.info(f"predict: text_input='{text_input[:100]}...', max_new_tokens (demandé pour la réponse)={max_new_tokens}, tokenizer_max_len_for_prompt={resolved_max_length_for_tokenizer}")

        inputs = tokenizer.encode_plus(
            text_input,
            return_tensors="pt",
            truncation=True, 
            padding="longest",
            max_length=resolved_max_length_for_tokenizer, 
            add_special_tokens=True
        )
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs["attention_mask"].to(device)
        
        current_prompt_length = input_ids.shape[1]

        if tokenizer.pad_token_id is None:
            pad_token_id = tokenizer.eos_token_id
        else:
            pad_token_id = tokenizer.pad_token_id

        output_sequences = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_new_tokens,
            num_return_sequences=1,
            temperature=0.7, 
            top_k=50,        
            top_p=0.95,      
            do_sample=True,  
            pad_token_id=pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
        
        generated_ids = output_sequences[0][input_ids.shape[-1]:]
        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)

        logger.info(f"Texte généré (nouveaux tokens uniquement): '{generated_text}'")
        return generated_text.strip()

    except OverflowError as oe:
        logger.error(f"OverflowError lors de la tokenisation/génération : {oe}")
        logger.error(f"Détails: text_input='{text_input[:100]}...', max_new_tokens={max_new_tokens}, tokenizer_max_len_for_prompt={resolved_max_length_for_tokenizer}")
        return "Erreur OverflowError lors de la génération de la réponse."
    except Exception as e:
        logger.error(f"Erreur lors de la génération de texte : {e}")
        if 'input_ids' in locals():
            logger.error(f"Shape des input_ids: {input_ids.shape}")
        logger.error(f"Max new tokens pour la génération: {max_new_tokens if 'max_new_tokens' in locals() else 'N/A'}")
        return "Erreur lors de la génération de la réponse."