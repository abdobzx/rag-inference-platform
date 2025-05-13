import os
import faiss
from sentence_transformers import SentenceTransformer
from loguru import logger

MODEL_NAME = 'all-MiniLM-L6-v2' # Modèle compact et efficace pour les embeddings
KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), '../knowledge_data')
INDEX_PATH = os.path.join(os.path.dirname(__file__), 'faiss_index.idx')

class KnowledgeBase:
    def __init__(self, model_name: str = MODEL_NAME, knowledge_dir: str = KNOWLEDGE_BASE_DIR, index_path: str = INDEX_PATH):
        logger.info(f"Initialisation du modèle d'embedding: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.knowledge_dir = knowledge_dir
        self.index_path = index_path
        self.documents = []
        self.index = None
        self._load_or_create_index()

    def _load_documents(self):
        logger.info(f"Chargement des documents depuis: {self.knowledge_dir}")
        docs = []
        for filename in os.listdir(self.knowledge_dir):
            if filename.endswith(".txt"): # On ne traite que les .txt pour l'instant
                file_path = os.path.join(self.knowledge_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        # Simple découpage par ligne, pourrait être plus sophistiqué (chunking)
                        chunks = [line.strip() for line in f if line.strip()] 
                        docs.extend(chunks)
                        logger.info(f"Document {filename} chargé et découpé en {len(chunks)} chunks.")
                except Exception as e:
                    logger.error(f"Erreur lors du chargement du document {filename}: {e}")
        self.documents = docs
        if not self.documents:
            logger.warning("Aucun document n'a été chargé. La base de connaissances sera vide.")

    def _build_index(self):
        if not self.documents:
            logger.warning("Aucun document à indexer. L'index ne sera pas construit.")
            return

        logger.info("Création des embeddings pour les documents...")
        embeddings = self.model.encode(self.documents, show_progress_bar=True)
        dimension = embeddings.shape[1]
        logger.info(f"Dimension des embeddings: {dimension}")
        
        logger.info("Construction de l'index FAISS...")
        self.index = faiss.IndexFlatL2(dimension)  # Index simple pour la similarité L2
        self.index.add(embeddings)
        logger.info(f"Index FAISS construit avec {self.index.ntotal} vecteurs.")
        
        logger.info(f"Sauvegarde de l'index FAISS sur: {self.index_path}")
        faiss.write_index(self.index, self.index_path)

    def _load_or_create_index(self):
        if os.path.exists(self.index_path):
            try:
                logger.info(f"Chargement de l'index FAISS depuis: {self.index_path}")
                self.index = faiss.read_index(self.index_path)
                # Charger aussi les documents pour pouvoir les retourner lors de la recherche
                # Note: Pour une solution robuste, les documents devraient être stockés/référencés 
                # d'une manière qui permette de les récupérer à partir de l'ID de l'index.
                # Ici, on recharge simplement tous les documents. Ce n'est pas idéal si l'index
                # et les documents sources divergent.
                self._load_documents() 
                if not self.documents and self.index.ntotal > 0:
                    logger.warning("L'index existe mais aucun document source n'a été chargé. La recherche pourrait ne pas retourner de contenu textuel.")
                elif self.index.ntotal == 0 and self.documents:
                     logger.warning("L'index est vide mais des documents sources existent. Reconstruction de l'index.")
                     self._build_index()
                elif self.index.ntotal > 0 and not self.documents:
                    logger.warning("L'index existe mais les documents sources sont manquants. La recherche ne renverra que des ID.")
                elif self.index.ntotal == 0 and not self.documents:
                    logger.info("L'index et les documents sources sont vides. L'index sera construit si des documents sont ajoutés plus tard.")
                else:
                    logger.info(f"Index FAISS chargé avec {self.index.ntotal} vecteurs.")

            except Exception as e:
                logger.error(f"Erreur lors du chargement de l'index FAISS depuis {self.index_path}: {e}. Reconstruction de l'index.")
                self._load_documents()
                self._build_index()
        else:
            logger.info("Aucun index FAISS trouvé. Construction d'un nouvel index.")
            self._load_documents()
            self._build_index()

    def add_document(self, text_content: str):
        """Ajoute un nouveau document (ou chunk) à la base de connaissances et met à jour l'index."""
        if not text_content.strip():
            logger.warning("Tentative d'ajout d'un document vide.")
            return

        logger.info(f"Ajout d'un nouveau document à la base de connaissances.")
        self.documents.append(text_content)
        new_embedding = self.model.encode([text_content])
        
        if self.index is None:
            dimension = new_embedding.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            logger.info("Nouvel index FAISS créé car il n'existait pas.")

        self.index.add(new_embedding)
        logger.info(f"Document ajouté à l'index. Nombre total de vecteurs: {self.index.ntotal}")
        faiss.write_index(self.index, self.index_path) # Sauvegarder l'index mis à jour
        logger.info(f"Index FAISS mis à jour et sauvegardé sur: {self.index_path}")

# Pour tester (peut être exécuté directement)
if __name__ == '__main__':
    logger.add("knowledge_base.log")
    kb = KnowledgeBase()
    if kb.index:
        logger.info(f"Base de connaissances initialisée. Nombre de documents indexés: {kb.index.ntotal}")
    else:
        logger.warning("La base de connaissances n'a pas pu être initialisée correctement.")

    # Exemple d'ajout de document
    # kb.add_document("Un nouveau fait passionnant sur les transformateurs de phrases.")
    # logger.info(f"Après ajout, nombre de documents indexés: {kb.index.ntotal}")
