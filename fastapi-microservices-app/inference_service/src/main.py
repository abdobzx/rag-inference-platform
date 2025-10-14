from fastapi import FastAPI, Request
from .routes.inference import router as inference_router
from .routes.health import router as health_router
# Updated import to include new model loading function
from .utils.model_loader import load_model_and_tokenizer, load_embedding_model
from .rag.knowledge_base import KnowledgeBase
from .rag.retriever import Retriever
from .rag.rag_prompt_augmenter import RagPromptAugmenter
import logging

app = FastAPI(
    title="SothemaAI Inference Service",
    description="""
# SothemaAI AI Inference & RAG Service

Advanced AI-powered inference service specializing in pharmaceutical and medical content generation using state-of-the-art transformer models and Retrieval Augmented Generation (RAG).

## AI Capabilities

- **🤖 Text Generation**: GPT-style text completion with medical context awareness
- **🔍 Retrieval Augmented Generation (RAG)**: Enhanced responses using medical knowledge base
- **📊 Text Embeddings**: Vector representations for semantic search and similarity
- **🩺 Pharmaceutical Focus**: Specialized validation for medical and pharmaceutical content

## Models & Technology

- **Generation Model**: Llama-based transformer for coherent medical text generation
- **Embedding Model**: Sentence transformers for semantic understanding
- **Knowledge Base**: Curated medical literature and pharmaceutical data
- **RAG System**: Context-aware response generation with source attribution

## Content Validation

All requests are validated to ensure pharmaceutical relevance:
- Medical terminology detection
- Drug information validation
- Clinical context verification
- Safety-focused content filtering

## Performance Features

- GPU acceleration support
- Model caching and optimization
- Async processing for scalability
- Comprehensive error handling and logging
    """,
    version="1.0.0",
    contact={
        "name": "SothemaAI Development Team",
        "url": "https://github.com/abdobzx/SothemaAI",
        "email": "dev@sothema.ai",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    }
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    logger.info("Service d'inférence en cours de démarrage... Chargement des modèles.")
    # Charger le modèle de génération et le tokenizer
    try:
        model, tokenizer = load_model_and_tokenizer()
        app.state.model = model
        app.state.tokenizer = tokenizer
        if app.state.model and app.state.tokenizer:
            logger.info("Modèle de génération et tokenizer stockés dans app.state.")
        else:
            logger.error("Échec du chargement du modèle de génération et/ou du tokenizer dans app.state.")
    except Exception as e:
        logger.error(f"Erreur critique lors du chargement du modèle de génération au démarrage: {e}", exc_info=True)
        app.state.model = None
        app.state.tokenizer = None

    # Charger le modèle d'embedding
    try:
        embedding_model = load_embedding_model()
        app.state.embedding_model = embedding_model
        if app.state.embedding_model:
            logger.info("Modèle d'embedding stocké dans app.state.")
        else:
            logger.error("Échec du chargement du modèle d'embedding dans app.state.")
    except Exception as e:
        logger.error(f"Erreur critique lors du chargement du modèle d'embedding au démarrage: {e}", exc_info=True)
        app.state.embedding_model = None

    logger.info("Initialisation des composants RAG...")
    try:
        kb = KnowledgeBase() # Utilise les chemins par défaut définis dans knowledge_base.py
        retriever = Retriever(knowledge_base=kb)
        rag_augmenter = RagPromptAugmenter(retriever=retriever)
        app.state.rag_augmenter = rag_augmenter
        if kb.index and kb.index.ntotal > 0:
            logger.info(f"Composants RAG initialisés. Base de connaissances chargée avec {kb.index.ntotal} documents/chunks.")
        elif kb.index is not None: # L'index existe mais est vide
             logger.info("Composants RAG initialisés, mais la base de connaissances est actuellement vide.")
        else: # kb.index est None, problème d'initialisation de l'index
            logger.warning("Composants RAG initialisés, mais l'index de la base de connaissances n'a pas pu être chargé ou créé.")
        logger.info("Composants RAG initialisés et stockés dans app.state.")
    except Exception as e:
        logger.error(f"Erreur critique lors de l'initialisation des composants RAG: {e}", exc_info=True)
        app.state.rag_augmenter = None

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Inference service is shutting down...")

# Inclure les routes d'inférence
app.include_router(inference_router)
app.include_router(health_router)

@app.get("/")
def read_root():
    return {
        "message": "Service d'inférence SothemaAI - Actif et en cours d'exécution.",
        "description": "Ce service fournit des capacités d'inférence de modèle de langage, y compris la génération de texte augmentée par RAG et la création d'embeddings.",
        "available_routes": [
            {
                "path": "/generate",
                "method": "POST",
                "description": "Génère du texte basé sur une invite d'entrée. Peut utiliser RAG pour augmenter l'invite avec des informations pertinentes provenant d'une base de connaissances.",
                "request_body": {
                    "text_input": "(string, requis) L'invite de texte pour le modèle de langage.",
                    "max_length": "(integer, optionnel, défaut: 150) Le nombre maximum de nouveaux tokens à générer."
                },
                "headers": {
                    "X-API-Key": "(string, requis) Votre clé API pour l'authentification."
                },
                "example_curl": "curl -X POST http://<host>:<port>/generate -H 'Content-Type: application/json' -H 'X-API-Key: VOTRE_CLE_API' -d '{\"text_input\": \"Expliquez le concept de RAG.\", \"max_length\": 100}'"
            },
            {
                "path": "/embed",
                "method": "POST",
                "description": "Génère des embeddings pour une liste de textes fournis.",
                "request_body": {
                    "texts": "(list[string], requis) Une liste de chaînes de caractères pour lesquelles générer des embeddings."
                },
                "headers": {
                    "X-API-Key": "(string, requis) Votre clé API pour l'authentification."
                },
                "example_curl": "curl -X POST http://<host>:<port>/embed -H 'Content-Type: application/json' -H 'X-API-Key: VOTRE_CLE_API' -d '{\"texts\": [\"Ceci est un exemple de texte.\", \"Un autre exemple.\"]}'"
            },
            {
                "path": "/",
                "method": "GET",
                "description": "Affiche ce message d'aide."
            }
        ],
        "notes": "L'accès à l'endpoint /generate nécessite une clé API valide passée dans l'en-tête X-API-Key. Les clés API peuvent être gérées via le service d'authentification."
    }