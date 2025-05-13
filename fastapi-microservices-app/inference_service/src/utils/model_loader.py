from typing import Any, Dict, Tuple
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer, PreTrainedModel, PreTrainedTokenizer
import torch

logger = logging.getLogger(__name__)

# Variable globale pour stocker le modèle et le tokenizer chargés
# afin d'éviter de les recharger à chaque requête.
# Ils seront initialisés au démarrage de l'application FastAPI.
_model: PreTrainedModel | None = None
_tokenizer: PreTrainedTokenizer | None = None

# Changer le nom du modèle par défaut ici
DEFAULT_MODEL_NAME = "deepseek-ai/deepseek-coder-1.3b-instruct" 

def load_model_and_tokenizer(model_name: str = DEFAULT_MODEL_NAME) -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
    """
    Charge un modèle de langage causal et son tokenizer associé depuis Hugging Face.
    Utilise des variables globales pour stocker le modèle et le tokenizer une fois chargés.
    """
    global _model, _tokenizer
    if _model is not None and _tokenizer is not None:
        logger.info(f"Modèle '{model_name}' et tokenizer déjà chargés.")
        return _model, _tokenizer

    try:
        logger.info(f"Chargement du modèle '{model_name}'...")
        # Déterminer le périphérique à utiliser (GPU si disponible, sinon CPU)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Utilisation du périphérique : {device}")

        model = AutoModelForCausalLM.from_pretrained(model_name)
        model.to(device) # Déplacer le modèle vers le périphérique sélectionné
        model.eval() # Mettre le modèle en mode évaluation (important pour certains modèles comme ceux avec dropout)
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        # S'assurer que le pad_token est défini pour le tokenizer, essentiel pour le padding.
        # Pour les modèles GPT-like, le token EOS (End Of Sentence) est souvent utilisé comme token de padding.
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            logger.info(f"Token de padding non défini. Utilisation de eos_token ('{tokenizer.eos_token}') comme token de padding.")
        
        # Ajout pour certains modèles qui n'ont pas de pad_token_id explicite mais ont un eos_token_id
        if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
            tokenizer.pad_token_id = tokenizer.eos_token_id
            logger.info(f"pad_token_id non défini. Utilisation de eos_token_id ('{tokenizer.eos_token_id}') comme pad_token_id.")

        _model = model
        _tokenizer = tokenizer
        logger.info(f"Modèle '{model_name}' et tokenizer chargés avec succès sur {device}.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle '{model_name}' ou du tokenizer: {e}", exc_info=True)
        raise  # Relancer l'exception pour que l'application FastAPI puisse la gérer

def predict(text_input: str, model: PreTrainedModel, tokenizer: PreTrainedTokenizer, max_length: int = 150) -> str:
    """
    Génère du texte en utilisant le modèle et le tokenizer chargés.
    """
    try:
        # Pour les modèles de type "instruct", il est souvent utile de formater le prompt.
        # Deepseek Instruct utilise un format spécifique, mais pour un usage général avec RAG,
        # nous allons d'abord essayer sans formatage spécifique complexe autre que celui du RAG.
        # Si les résultats sont mauvais, nous pourrions avoir besoin d'ajouter un template de prompt ici.
        # Exemple de template pour Deepseek Instruct (à adapter si nécessaire) :
        # formatted_prompt = f"### Instruction:\\n{text_input}\\n### Response:\\n"
        # Pour l'instant, nous utilisons text_input directement, qui sera le prompt augmenté par RAG.
        
        logger.info(f"Génération de texte pour l'entrée : '{text_input[:200]}...'") # Afficher un peu plus du prompt
        
        # Récupérer le périphérique sur lequel le modèle est chargé
        device = model.device

        # Tokeniser l'entrée
        inputs = tokenizer.encode_plus(
            text_input, 
            return_tensors="pt", 
            padding=True, 
            truncation=True,
            max_length=tokenizer.model_max_length if tokenizer.model_max_length else 2048 # Assurer une valeur par défaut si model_max_length est None
        )
        
        # Déplacer les tenseurs d'entrée vers le même périphérique que le modèle
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs["attention_mask"].to(device)

        # Ajuster les paramètres de génération si nécessaire pour le nouveau modèle
        output_sequences = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=max_length, # Utiliser max_new_tokens pour contrôler la longueur de la sortie générée
            num_return_sequences=1,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=2,
            do_sample=True,
            temperature=0.7, # Ajout/Ajustement de la température
            top_k=50,
            top_p=0.95
        )
        
        # Décoder la sortie. Pour certains modèles, il faut décoder uniquement les tokens générés.
        # La séquence de sortie contient les tokens d'entrée + les tokens générés.
        generated_ids = output_sequences[0][input_ids.shape[-1]:]
        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        logger.info(f"Texte généré (brut): {generated_text[:200]}...")

        # Le post-traitement pour enlever le prompt d'entrée n'est plus nécessaire
        # si on décode uniquement les `generated_ids`.
        
        return generated_text.strip()

    except Exception as e:
        logger.error(f"Erreur lors de la génération de texte : {e}", exc_info=True)
        # Retourner une chaîne d'erreur ou relancer l'exception selon la politique de gestion des erreurs souhaitée.
        return "Erreur lors de la génération de la réponse."