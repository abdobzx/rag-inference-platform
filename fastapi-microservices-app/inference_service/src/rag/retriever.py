# Code pour la récupération d'informations depuis la base de connaissances

from sentence_transformers import SentenceTransformer
import faiss
from loguru import logger
from .knowledge_base import KnowledgeBase, MODEL_NAME

class Retriever:
    def __init__(self, knowledge_base: KnowledgeBase, model_name: str = MODEL_NAME):
        logger.info("Initialisation du Retriever.")
        self.knowledge_base = knowledge_base
        # Le modèle d'embedding est déjà dans knowledge_base, nous pouvons le réutiliser
        # ou s'assurer qu'il est accessible si nécessaire pour encoder la requête ici.
        # Pour l'instant, nous supposons que knowledge_base gère l'encodage ou que son modèle est accessible.
        if self.knowledge_base.model is None:
            logger.warning("Le modèle d'embedding n'est pas chargé dans KnowledgeBase. Tentative de chargement.")
            # Cette ligne pourrait être redondante si KnowledgeBase garantit que le modèle est chargé.
            self.model = SentenceTransformer(model_name)
        else:
            self.model = self.knowledge_base.model 

    def search(self, query: str, top_k: int = 5) -> list[tuple[float, str]]:
        """Recherche les chunks de documents les plus pertinents pour une requête donnée."""
        if self.knowledge_base.index is None or self.knowledge_base.index.ntotal == 0:
            logger.warning("L'index de la base de connaissances est vide ou non initialisé. Aucune recherche ne peut être effectuée.")
            return []

        if not query.strip():
            logger.warning("La requête de recherche est vide.")
            return []

        logger.info(f"Recherche pour la requête: '{query}' (top_k={top_k})")
        
        try:
            query_embedding = self.model.encode([query])
            # FAISS attend un array 2D pour la recherche
            distances, indices = self.knowledge_base.index.search(query_embedding, top_k)
            
            results = []
            for i in range(len(indices[0])):
                idx = indices[0][i]
                dist = distances[0][i]
                if idx < len(self.knowledge_base.documents):
                    results.append((float(dist), self.knowledge_base.documents[idx]))
                else:
                    logger.warning(f"L'index {idx} est hors des limites pour les documents chargés (taille: {len(self.knowledge_base.documents)}).")
            
            logger.info(f"Recherche terminée. {len(results)} résultats trouvés.")
            return results
        except Exception as e:
            logger.error(f"Erreur pendant la recherche FAISS: {e}")
            return []

# Pour tester (peut être exécuté directement si knowledge_base.py est dans le même répertoire et fonctionne)
if __name__ == '__main__':
    logger.add("retriever.log")
    
    # Assurez-vous que la base de connaissances peut être initialisée correctement
    # Cela nécessitera que les dépendances soient installées et que les fichiers de données existent.
    try:
        kb = KnowledgeBase() # Utilise les chemins par défaut
        if kb.index and kb.index.ntotal > 0:
            retriever = Retriever(knowledge_base=kb)
            
            sample_query = "Qu'est-ce que l'intelligence artificielle?"
            logger.info(f"Test de recherche avec la requête: '{sample_query}'")
            search_results = retriever.search(sample_query, top_k=2)
            
            if search_results:
                logger.info("Résultats de la recherche:")
                for distance, text in search_results:
                    logger.info(f"  Distance: {distance:.4f} - Texte: {text}")
            else:
                logger.info("Aucun résultat trouvé pour la requête de test.")
        else:
            logger.error("La base de connaissances est vide ou n'a pas pu être initialisée. Le test du Retriever ne peut pas continuer.")
    except ImportError as e:
        logger.error(f"Erreur d'importation lors de l'initialisation pour le test: {e}. Assurez-vous que les dépendances (faiss, sentence-transformers, loguru) sont installées.")
    except Exception as e:
        logger.error(f"Une erreur s'est produite lors du test du Retriever: {e}")
