from typing import Any, Dict, Tuple, List
import logging
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
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2" 
TOKENIZER_NAME = "mistralai/Mistral-7B-Instruct-v0.2"

# Modèle d'embedding (MODIFIABLE SI NÉCESSAIRE)
# Ancien modèle: sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def load_model_and_tokenizer() -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
    """Charge le modèle LLM et le tokenizer."""
    global _model, _tokenizer
    if _model is not None and _tokenizer is not None:
        logger.info(f"Modèle '{MODEL_NAME}' et tokenizer déjà chargés.")
        return _model, _tokenizer

    try:
        logger.info(f"Tentative de chargement du tokenizer : {TOKENIZER_NAME}")
        # Ajout de trust_remote_code=True si nécessaire pour certains modèles, mais pas typiquement pour Mistral
        tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME)
        logger.info("Tokenizer chargé avec succès.")

        logger.info(f"Tentative de chargement du modèle : {MODEL_NAME}")
        # Pour les modèles plus grands, device_map="auto" est recommandé.
        # Assurez-vous que 'accelerate' est installé.
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME, 
            trust_remote_code=True, # Certains modèles peuvent le nécessiter
            device_map="auto", # Répartit le modèle sur les GPU disponibles / CPU si pas de GPU ou pas assez de VRAM
            torch_dtype=torch.bfloat16 # Utilise bfloat16 pour économiser de la mémoire et potentiellement accélérer si supporté
        )
        logger.info(f"Modèle LLM chargé avec succès sur le device : {model.device}")
        
        # Gestion du pad_token_id si non défini (courant pour les modèles Llama et Mistral)
        if tokenizer.pad_token_id is None:
            if tokenizer.eos_token_id is not None:
                logger.info("tokenizer.pad_token_id non défini. Utilisation de tokenizer.eos_token_id comme pad_token_id.")
                tokenizer.pad_token_id = tokenizer.eos_token_id
            else:
                # Si eos_token_id n'est pas non plus défini, ajoutez un nouveau pad_token.
                # Cela est moins courant pour les modèles pré-entraînés bien configurés.
                logger.warning("tokenizer.pad_token_id et tokenizer.eos_token_id non définis. Ajout d'un nouveau pad_token.")
                tokenizer.add_special_tokens({'pad_token': '[PAD]'})
                model.resize_token_embeddings(len(tokenizer)) # Redimensionner les embeddings du modèle

        _model = model
        _tokenizer = tokenizer
        return model, tokenizer
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle '{MODEL_NAME}' ou du tokenizer: {e}", exc_info=True)
        raise  # Relancer l'exception pour que l'application FastAPI puisse la gérer

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
        
        embedding_model = SentenceTransformer(model_name, device=device)
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
        embeddings = embedding_model.encode(texts, convert_to_tensor=False) # convert_to_tensor=False pour obtenir des listes de floats
        # S'assurer que la sortie est une liste de listes de floats
        if hasattr(embeddings, 'tolist'): # Si c'est un ndarray numpy ou un tenseur PyTorch
            embeddings_list = embeddings.tolist()
        else: # Si c'est déjà une liste de listes (ou similaire)
            embeddings_list = list(map(list, embeddings))

        logger.info(f"Embeddings générés avec succès. Premier embedding (tronqué): {str(embeddings_list[0][:5]) if embeddings_list and embeddings_list[0] else 'N/A'}...")
        return embeddings_list
    except Exception as e:
        logger.error(f"Erreur lors de la génération des embeddings: {e}", exc_info=True)
        raise # Relancer pour une gestion d'erreur plus haut niveau

def predict(text_input: str, model: PreTrainedModel, tokenizer: PreTrainedTokenizer, max_length: int = 150) -> str:
    """
    Génère du texte en utilisant le modèle et le tokenizer chargés.
    """
    try:
        logger.info(f"Génération de texte pour l'entrée : '{text_input[:200]}...'") # Afficher un peu plus du prompt
        
        # Récupérer le périphérique sur lequel le modèle est chargé
        device = model.device

        # Déterminer la longueur maximale pour l'encodage du prompt
        # en tenant compte des nouveaux tokens à générer.
        # Utiliser une valeur sûre si tokenizer.model_max_length n'est pas défini.
        model_max_len = tokenizer.model_max_length if tokenizer.model_max_length else 2048
        # max_length ici est le nombre de nouveaux tokens que l'on veut générer (anciennement max_new_tokens)
        max_input_length = model_max_len - max_length 

        if max_input_length <= 0:
            logger.warning(f"max_new_tokens ({max_length}) est trop grand par rapport à model_max_length ({model_max_len}). Le prompt sera fortement tronqué ou vide. Ajustement de max_input_length.")
            max_input_length = model_max_len // 2 

        # Tokeniser l'entrée
        inputs = tokenizer.encode_plus(
            text_input, 
            return_tensors="pt", 
            padding=True, 
            truncation=True,
            max_length=max_input_length # Utiliser la longueur d'entrée calculée
        )
        
        # Déplacer les tenseurs d'entrée vers le même périphérique que le modèle
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs["attention_mask"].to(device)

        # S'assurer que input_ids n'est pas vide après troncature
        if input_ids.shape[-1] == 0:
            logger.error("Input IDs sont vides après tokenisation et troncature. Impossible de générer du texte.")
            return "Erreur: Le prompt d'entrée est devenu vide après traitement."

        logger.info(f"Shape des input_ids avant génération: {input_ids.shape}")

        # Ajuster les paramètres de génération si nécessaire pour le nouveau modèle
        output_sequences = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_length, # Utiliser max_new_tokens pour contrôler la longueur de la sortie générée
            num_return_sequences=1,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            do_sample=True,
            temperature=0.75,
            top_k=50,
            top_p=0.95
        )
        
        logger.info(f"Output sequences (brut) from model.generate: {output_sequences}") # Log des séquences de sortie brutes

        # Décoder la sortie. Pour certains modèles, il faut décoder uniquement les tokens générés.
        # La séquence de sortie contient les tokens d'entrée + les tokens générés.
        generated_ids = output_sequences[0][input_ids.shape[-1]:]
        
        logger.info(f"Generated IDs (après slicing du prompt): {generated_ids}") # Log des IDs générés
        logger.info(f"Nombre de generated IDs: {len(generated_ids)}")

        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        logger.info(f"Texte généré (brut): {generated_text[:200]}...")

        return generated_text.strip()

    except Exception as e:
        logger.error(f"Erreur lors de la génération de texte : {e}", exc_info=True)
        return "Erreur lors de la génération de la réponse."