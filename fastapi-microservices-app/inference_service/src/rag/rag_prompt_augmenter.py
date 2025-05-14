from loguru import logger
from .retriever import Retriever
from .knowledge_base import KnowledgeBase # Nécessaire pour l'initialisation si on le fait ici

# Nouveau template de prompt final, plus directif
# FINAL_PROMPT_WITH_CONTEXT_TEMPLATE = """En te basant UNIQUEMENT sur le contexte suivant :
# ---
# {context}
# ---
# Réponds à la question ci-dessous. Si le contexte ne fournit pas la réponse, indique que l'information n'est pas disponible dans le document.

# Question :
# {user_prompt}"""

# Modèle de prompt alternatif pour les modèles "instruct"
FINAL_PROMPT_WITH_CONTEXT_TEMPLATE = """### Instruction:
Répondez à la question en vous basant uniquement sur le contexte fourni. Si l'information n'est pas dans le contexte, dites que vous ne pouvez pas répondre à partir des documents fournis.

### Contexte:
{context}

### Question:
{user_prompt}

### Réponse:
"""

class RagPromptAugmenter:
    def __init__(self, retriever: Retriever):
        logger.info("Initialisation du RagPromptAugmenter.")
        self.retriever = retriever

    def augment_prompt(self, user_prompt: str, top_k_retrieval: int = 3) -> str:
        """
        Augmente le prompt de l'utilisateur avec le contexte récupéré de la base de connaissances,
        en utilisant le FINAL_PROMPT_WITH_CONTEXT_TEMPLATE.
        """
        logger.info(f"Augmentation du prompt pour l'utilisateur: '{user_prompt}' avec top_k={top_k_retrieval}")
        
        if not user_prompt.strip():
            logger.warning("Le prompt de l'utilisateur est vide. Retour du prompt original (non recommandé pour ce template).")
            return user_prompt 

        retrieved_contexts = self.retriever.search(query=user_prompt, top_k=top_k_retrieval)

        if not retrieved_contexts:
            logger.info("Aucun contexte pertinent trouvé par le RAG interne. Construction d'un prompt sans contexte spécifique.")
            context_str = "Aucune information contextuelle spécifique n'a été trouvée dans les documents pour cette question."
        else:
            # Formater le contexte récupéré
            context_str = "\n".join([f"- {text}" for _, text in retrieved_contexts])
        
        final_prompt = FINAL_PROMPT_WITH_CONTEXT_TEMPLATE.format(
            context=context_str,
            user_prompt=user_prompt
        )
        
        logger.info("Prompt final (avec ou sans contexte récupéré) généré.")
        return final_prompt

# Exemple d'utilisation (nécessite que KnowledgeBase et Retriever soient fonctionnels)
if __name__ == '__main__':
    logger.add("rag_prompt_augmenter.log")

    # Configuration minimale pour le test (similaire à ce qui serait fait dans le service)
    try:
        # Assurez-vous que le chemin vers knowledge_data est correct ou que l'index existe déjà
        # KNOWLEDGE_BASE_DIR_FOR_TEST = "../knowledge_data" # Ajustez si nécessaire
        # INDEX_PATH_FOR_TEST = "./faiss_index.idx" # Ajustez si nécessaire
        
        # kb = KnowledgeBase(knowledge_dir=KNOWLEDGE_BASE_DIR_FOR_TEST, index_path=INDEX_PATH_FOR_TEST)
        kb = KnowledgeBase() # Utilise les chemins par défaut définis dans knowledge_base.py
        
        if kb.index and kb.index.ntotal > 0:
            retriever_instance = Retriever(knowledge_base=kb)
            augmenter = RagPromptAugmenter(retriever=retriever_instance)

            test_prompt = "Parle-moi des avancées en intelligence artificielle."
            logger.info(f"Test avec le prompt: '{test_prompt}'")
            
            augmented = augmenter.augment_prompt(test_prompt)
            
            logger.info("--- Prompt Augmenté --- ")
            print(augmented)
            logger.info("--- Fin du Prompt Augmenté ---")

            test_prompt_no_context = "Une question sur un sujet non présent dans les documents."
            logger.info(f"Test avec le prompt: '{test_prompt_no_context}'")
            augmented_no_context = augmenter.augment_prompt(test_prompt_no_context)
            logger.info("--- Prompt Augmenté (sans contexte attendu) --- ")
            print(augmented_no_context)
            logger.info("--- Fin du Prompt Augmenté (sans contexte attendu) ---")

        else:
            logger.error("La base de connaissances est vide ou n'a pas pu être initialisée. Le test de RagPromptAugmenter ne peut pas continuer.")

    except ImportError as e:
        logger.error(f"Erreur d'importation lors de l'initialisation pour le test: {e}. Assurez-vous que les dépendances (faiss, sentence-transformers, loguru) sont installées et que les modules RAG sont accessibles.")
    except Exception as e:
        logger.error(f"Une erreur générale s'est produite lors du test: {e}", exc_info=True)
