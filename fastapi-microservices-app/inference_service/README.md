# Inference Service Documentation

## Overview

The Inference Service is a microservice designed to handle model inference requests. It provides endpoints for:

- Generating text based on prompts.
- Creating text embeddings.
- Performing Retrieval Augmented Generation (RAG) by leveraging a knowledge base to answer questions.

This service is built using FastAPI and utilizes Hugging Face transformer models. It's designed with security and scalability in mind.

## Features

- **Text Generation**: Provides an endpoint to generate text using a pre-trained Large Language Model (LLM), currently `mistralai/Mistral-7B-Instruct-v0.2`.
- **Text Embedding**: Offers an endpoint to generate embeddings for input texts using a sentence-transformer model, currently `sentence-transformers/all-MiniLM-L6-v2`.
- **Retrieval Augmented Generation (RAG)**: Can augment prompts with context retrieved from an internal knowledge base before generating a response.
- **Scalability**: Designed to be easily scalable by deploying multiple instances.
- **Security**: Implements authentication and authorization mechanisms to secure endpoints. Requires an API key for access.

## Directory Structure

```text
inference_service/
├── src/
│   ├── main.py               # Entry point for the FastAPI application
│   ├── knowledge_data/       # Directory for storing knowledge base files (e.g., sample_document.txt)
│   │   └── sample_document.txt
│   ├── models/
│   │   └── payload.py        # Data models for requests and responses
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── knowledge_base.py   # Manages loading and accessing the knowledge base
│   │   ├── rag_prompt_augmenter.py # Augments prompts with context
│   │   └── retriever.py        # (If implemented separately for retrieval logic)
│   ├── routes/
│   │   └── inference.py      # Defines inference, embedding, and RAG-related routes
│   └── utils/
│       ├── model_loader.py   # Utility functions for loading Hugging Face models (LLM and embedding)
│       └── security.py       # Security-related utilities
├── requirements.txt          # Dependencies for the inference service
├── Dockerfile                # Docker configuration for the service
└── README.md                 # Documentation for the inference service
```

## Setup

1. Environment Variables:
    - Ensure you have a `.env` file in the root of the `fastapi-microservices-app` project (or configure environment variables directly in your deployment).
    - This file must contain `HUGGING_FACE_HUB_TOKEN=<your_hf_token>` if using gated models like Mistral.

    ```env
    HUGGING_FACE_HUB_TOKEN=your_hugging_face_token_here
    ```

2. Install Dependencies: Navigate to the `inference_service` directory and run:

    ```bash
    pip install -r requirements.txt
    ```

3. Run the Service (Standalone): Start the FastAPI application by executing:

    ```bash
    uvicorn src.main:app --host 0.0.0.0 --port 8000
    ```

    Typically, this service is run as part of the `docker-compose` setup for the entire microservices application.

## API Endpoints

### POST /inference/generate

- **Description**: Generates text based on the provided input. Can optionally use RAG if `context_chunks` are provided or if internal RAG logic is triggered by the prompt.
- **Request Body**: Expects a JSON payload.

    ```json
    {
        "text_input": "Your question or prompt here",
        "max_length": 150, // Optional: defaults to a model-specific value or 150
        "context_chunks": [ // Optional: for RAG, provide pre-retrieved context
            "Context chunk 1...",
            "Context chunk 2..."
        ]
    }
    ```

- **Response**: Returns the generated text.

    ```json
    {
        "output_data": "The model's generated response."
    }
    ```

### POST /inference/embed

- **Description**: Generates embeddings for a list of input texts.
- **Request Body**: Expects a JSON payload.

    ```json
    {
        "texts": ["Text to embed 1", "Another text to embed"]
    }
    ```

- **Response**: Returns a list of embeddings.

    ```json
    {
        "embeddings": [
            [0.01, 0.02, ..., -0.05],
            [-0.1, 0.3, ..., 0.002]
        ]
    }
    ```

## Models Used

- **Language Model**: `mistralai/Mistral-7B-Instruct-v0.2` (or as configured in `model_loader.py`). Requires access on Hugging Face.
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (or as configured in `model_loader.py`).

## Security

Ensure that the service is secured using appropriate authentication mechanisms. It is recommended to use OAuth2 or JWT tokens for securing the endpoints.

## Logging

Integrate with the logging service to capture and store logs for monitoring and debugging purposes.

## Contributing

Contributions are welcome! Please follow the standard guidelines for contributing to this project.

## License

This project is licensed under the MIT License. See the LICENSE file for details.