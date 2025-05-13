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

def load_model_and_tokenizer(model_name: str = "distilgpt2") -> Tuple[PreTrainedModel, PreTrainedTokenizer]:
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

        _model = model
        _tokenizer = tokenizer
        logger.info(f"Modèle '{model_name}' et tokenizer chargés avec succès sur {device}.")
        return model, tokenizer
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle '{model_name}' ou du tokenizer: {e}", exc_info=True)
        raise  # Relancer l'exception pour que l'application FastAPI puisse la gérer

def predict(text_input: str, model: PreTrainedModel, tokenizer: PreTrainedTokenizer, max_length: int = 50) -> str:
    """
    Génère du texte en utilisant le modèle et le tokenizer chargés.
    """
    try:
        logger.info(f"Génération de texte pour l'entrée : '{text_input[:100]}...'")
        
        # Récupérer le périphérique sur lequel le modèle est chargé
        device = model.device

        # Tokeniser l'entrée
        # `return_tensors='pt'` retourne des tenseurs PyTorch.
        # `padding=True` et `truncation=True` sont importants si vous traitez des lots d'entrées de différentes longueurs.
        # Pour une seule entrée, la troncature peut ne pas être strictement nécessaire si l'entrée est courte.
        inputs = tokenizer.encode_plus(
            text_input, 
            return_tensors="pt", 
            padding=True, 
            truncation=True,
            max_length=tokenizer.model_max_length # Utiliser la longueur maximale supportée par le modèle pour l'entrée
        )
        
        # Déplacer les tenseurs d'entrée vers le même périphérique que le modèle
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs["attention_mask"].to(device)

        # Générer la sortie
        # `max_length` ici contrôle la longueur totale de la séquence (entrée + sortie générée).
        # `num_return_sequences=1` car nous voulons une seule sortie.
        # `pad_token_id` est important pour la génération.
        # `no_repeat_ngram_size` peut aider à éviter les répétitions.
        # `do_sample=True`, `top_k`, `top_p` peuvent rendre la génération plus créative.
        output_sequences = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_length=input_ids.shape[1] + max_length, # Longueur de l'entrée + longueur de la génération souhaitée
            num_return_sequences=1,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=2, # Évite la répétition de bi-grammes
            do_sample=True, # Active l'échantillonnage pour une génération plus variée
            top_k=50, # Considère les k tokens les plus probables à chaque étape
            top_p=0.95 # Échantillonnage Nucleus
        )

        # Décoder la sortie
        generated_text = tokenizer.decode(output_sequences[0], skip_special_tokens=True)
        
        # La sortie générée inclut souvent le texte d'entrée. Nous pouvons le retirer si nécessaire.
        # Ceci est une heuristique simple et pourrait nécessiter des ajustements.
        if generated_text.startswith(text_input):
            generated_text = generated_text[len(text_input):].lstrip()

        logger.info(f"Texte généré : '{generated_text[:200]}...'")
        return generated_text
    except Exception as e:
        logger.error(f"Erreur lors de la génération de texte : {e}", exc_info=True)
        # Retourner une chaîne d'erreur ou relancer l'exception selon la politique de gestion des erreurs souhaitée.
        return "Erreur lors de la génération de la réponse."