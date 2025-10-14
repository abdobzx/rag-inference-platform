# FastAPI Microservices Application for LLM Inference

**Statut du Projet : En développement actif** (Privé)
**Date de dernière mise à jour : 13 Mai 2025**

## Table des Matières

1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Services](#services)
    * [Auth Service](#auth-service)
    * [Inference Service](#inference-service)
    * [Logging Service](#logging-service)
    * [Gateway Service](#gateway-service)
    * [Frontend React](#frontend-react)
    * [Nginx](#nginx)
    * [PostgreSQL](#postgresql)
4. [Fonctionnalités Clés](#fonctionnalités-clés)
5. [Technologies Utilisées](#technologies-utilisées)
6. [Prérequis](#prérequis)
7. [Installation et Lancement](#installation-et-lancement)
8. [Accès aux Services](#accès-aux-services)
9. [Authentification](#authentification)
    * [Authentification des Utilisateurs (JWT)](#authentification-des-utilisateurs-jwt)
    * [Authentification des Services (Clé API)](#authentification-des-services-clé-api)
10. [Utilisation du GPU](#utilisation-du-gpu)
11. [Prochaines Étapes (Roadmap RAG)](#prochaines-étapes-roadmap-rag)
12. [Considérations de Sécurité](#considérations-de-sécurité)
13. [Scalabilité](#scalabilité)
14. [Contribution](#contribution)

## Introduction

Ce projet est une application web full-stack conçue pour fournir un accès à des modèles de langage open-source (LLM) via une architecture de microservices robuste et scalable. L'application permet aux utilisateurs de s'inscrire, de gérer des clés API personnelles, et d'utiliser ces clés pour accéder au service d'inférence LLM. Le backend est construit avec Python (FastAPI) et le frontend avec React (Vite, Tailwind CSS).

## Architecture

L'application suit une architecture de microservices, orchestrée avec Docker Compose. Les principaux composants sont :

```text
+---------------------+     +---------------------+     +---------------------+
|   Frontend React    |<--->|        Nginx        |<--->|   Gateway Service   |
| (SPA - Vite)        |     |   (Reverse Proxy)   |     |    (FastAPI)      |
+---------------------+     +---------------------+     +---------------------+
                                                            |         ^
                                                            |         | (API Calls)
                                                            v         |
+---------------------+     +---------------------+     +---------------------+
|    Auth Service     |<--->|     PostgreSQL      |<--->|   Logging Service   |
| (FastAPI, JWT,     |     |      (Database)     |     |      (FastAPI)      |
|  API Key Mgmt)      |     +---------------------+     +---------------------+
+---------------------+
          ^
          | (API Key Validation)
          v
+---------------------+
|  Inference Service  |
| (FastAPI, LLM, GPU) |
+---------------------+
```

*   **Nginx** : Sert de reverse proxy, dirigeant le trafic UI vers le frontend React et le trafic API vers le Gateway Service.
*   **Frontend React**: Interface utilisateur single-page pour l'interaction avec l'application.
*   **Gateway Service**: Point d'entrée unique pour toutes les requêtes API. Il route les requêtes vers les services internes appropriés (Auth, Inference, Logging).
*   **Auth Service**: Gère l'authentification des utilisateurs (enregistrement, login via JWT) et la gestion des clés API (création, listage, révocation, validation).
*   **Inference Service**: Exécute les inférences LLM. Il est protégé par une authentification basée sur les clés API validées par l'Auth Service. Il est configuré pour utiliser le GPU si disponible.
*   **Logging Service**: (Prévu) Centralisera les logs de tous les services.
*   **PostgreSQL**: Base de données relationnelle utilisée par l'Auth Service pour stocker les informations des utilisateurs et les clés API.

## Services

### Auth Service

*   **Rôle**: Gestion des utilisateurs et des clés API.
*   **Fonctionnalités**:
    *   Enregistrement et connexion des utilisateurs (émission de tokens JWT).
    *   Création, listage, révocation de clés API par les utilisateurs authentifiés.
    *   Endpoint interne pour la validation des clés API par d'autres services (utilisé par l'Inference Service).
*   **Technologies**: FastAPI, SQLAlchemy, PostgreSQL, JWT.

### Inference Service

*   **Rôle**: Fournir des capacités d'inférence LLM.
*   **Fonctionnalités**:
    *   Endpoint `/generate` pour obtenir des complétions de texte à partir d'un prompt.
    *   Protégé par une clé API (en-tête `X-API-Key`).
    *   Charge un modèle LLM (actuellement `distilgpt2` via `transformers`).
    *   Conçu pour utiliser le GPU de l'hôte via Docker.
*   **Technologies**: FastAPI, Hugging Face Transformers, PyTorch.

### Logging Service

*   **Rôle**: (En cours de développement) Collecter et stocker les logs de manière centralisée.
*   **Technologies**: FastAPI.

### Gateway Service

*   **Rôle**: Point d'entrée unique et routeur pour les requêtes API.
*   **Fonctionnalités**:
    *   Redirige les requêtes `/auth/*` et `/token` vers l'Auth Service.
    *   Redirige les requêtes `/inference/*` vers l'Inference Service, en propageant la clé API.
    *   (Prévu) Redirige les requêtes `/logs` vers le Logging Service.
*   **Technologies**: FastAPI, HTTPX.

### Frontend React

*   **Rôle**: Interface utilisateur.
*   **Fonctionnalités**:
    *   Pages d'accueil, de connexion, d'enregistrement.
    *   Tableau de bord utilisateur pour la gestion des clés API (création, affichage, révocation).
    *   Formulaire pour envoyer des requêtes au service d'inférence.
*   **Technologies**: React, Vite, Tailwind CSS, Axios (ou `fetch`).

### Nginx

*   **Rôle**: Reverse proxy et serveur web pour le frontend.
*   **Fonctionnalités**:
    *   Sert l'application React buildée statiquement.
    *   Route les appels API (ex: `/api/...`) vers le Gateway Service.
*   **Configuration**: `nginx/nginx.conf`

### PostgreSQL

*   **Rôle**: Base de données persistante.
*   **Utilisation**: Stocke les utilisateurs, les mots de passe hashés, et les clés API.
*   **Accès**: Principalement utilisé par l'Auth Service.

## Fonctionnalités Clés

*   Architecture microservices avec Docker.
*   Authentification des utilisateurs basée sur JWT.
*   Gestion complète des clés API par utilisateur.
*   Authentification par clé API pour l'accès au service d'inférence.
*   Service d'inférence LLM avec support GPU.
*   Frontend React moderne pour l'interaction utilisateur.

## Technologies Utilisées

*   **Backend**: Python, FastAPI, SQLAlchemy, Pydantic, Uvicorn
*   **Frontend**: JavaScript, React, Vite, Tailwind CSS
*   **Base de données**: PostgreSQL
*   **Modèles LLM**: Hugging Face Transformers, PyTorch
*   **Conteneurisation & Orchestration**: Docker, Docker Compose
*   **Reverse Proxy**: Nginx
*   **Communication Inter-services**: HTTPX
*   **Authentification**: JWT (JSON Web Tokens), API Keys

## Prérequis

Avant de lancer l'application, assurez-vous d'avoir :

- **Docker** et **Docker Compose** installés
- **Git** pour cloner le repository
- Un compte **HuggingFace** avec un token d'accès (pour les modèles d'IA)
- Un compte **Gmail** avec un mot de passe d'application (pour les emails de vérification)

## Installation et Lancement

### 1. Cloner le repository

```bash
git clone <repository-url>
cd SothemaAI/fastapi-microservices-app
```

### 2. Configuration des variables d'environnement

Copiez les fichiers d'exemple d'environnement et configurez vos credentials :

```bash
# Auth Service
cp .env.auth.example .env.auth
# Éditez .env.auth avec vos vraies credentials

# Inference Service
cp .env.inference.example .env.inference
# Éditez .env.inference avec votre token HuggingFace

# Gateway Service
cp .env.gateway.example .env.gateway

# Frontend
cp .env.frontend.example .env.frontend
```

**Variables importantes à configurer :**

- **`.env.auth`** : `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `JWT_SECRET_KEY`
- **`.env.inference`** : `HUGGING_FACE_HUB_TOKEN`
- **`.env.gateway`** : URLs des services (généralement pas besoin de modifier)
- **`.env.frontend`** : URLs des API (généralement pas besoin de modifier)

### 3. Lancement de l'application

```bash
docker-compose up --build
```

L'application sera accessible sur :
- **Frontend** : http://localhost
- **API Gateway** : http://localhost:8000
- **Documentation API** : http://localhost:8000/docs

### 4. Accès initial

1. Allez sur http://localhost
2. Créez un compte utilisateur (doit être @mysothemalab.com)
3. Vérifiez votre email pour le code de vérification
4. Connectez-vous et générez une clé API
5. Utilisez la clé API pour accéder aux fonctionnalités d'IA

## Accès aux Services

Une fois les conteneurs lancés :

*   **Application Frontend**: `http://localhost` (ou `http://localhost:80` via Nginx)
*   **Gateway API (via Nginx)**: `http://localhost/api/...` (par exemple, `http://localhost/api/token`, `http://localhost/api/inference/generate`)
*   **Ports directs des services (principalement pour le débogage ou si Nginx n'est pas utilisé)**:
    *   Gateway: `http://localhost:8000` (mappé sur le port 8080 du conteneur)
    *   Auth Service: `http://localhost:8001` (mappé sur le port 8000 du conteneur)
    *   Inference Service: `http://localhost:8002` (mappé sur le port 8001 du conteneur)
    *   Logging Service: `http://localhost:8003` (mappé sur le port 8002 du conteneur)
    *   PostgreSQL: `localhost:5432`

## Authentification

### Authentification des Utilisateurs (JWT)

*   Les utilisateurs s'inscrivent et se connectent via les endpoints `/auth/register` et `/token` (proxied par le Gateway).
*   Lors d'une connexion réussie, l'Auth Service retourne un token JWT.
*   Ce token JWT doit être inclus dans l'en-tête `Authorization: Bearer <token>` pour les routes protégées (ex: gestion des clés API).

### Authentification des Services (Clé API)

*   Le service d'inférence (`/inference/generate`) est protégé par une clé API.
*   Les utilisateurs génèrent leurs clés API via le frontend (qui appelle l'Auth Service).
*   La clé API doit être fournie dans l'en-tête `X-API-Key` lors de l'appel à l'endpoint d'inférence.
*   L'Inference Service valide cette clé en appelant un endpoint interne de l'Auth Service (`/internal/apikeys/validate`).

## Utilisation du GPU

*   L'`inference_service` est configuré dans `docker-compose.yml` pour demander l'accès à un GPU NVIDIA via la section `deploy.resources`.
*   Le code de chargement du modèle dans `inference_service/src/utils/model_loader.py` détecte automatiquement la disponibilité de CUDA et déplace le modèle sur le GPU.
*   **Prérequis Hôte**: NVIDIA Container Toolkit et pilotes NVIDIA à jour.

## Prochaines Étapes (Roadmap RAG)

L'objectif est d'étendre cette application pour supporter des fonctionnalités de Retrieval Augmented Generation (RAG). Cela impliquera :

1.  **Mise en place d'une base de connaissances**:
    *   Choix et intégration d'une base de données vectorielle (ex: FAISS, Milvus, Weaviate, Pinecone).
    *   Processus pour charger, découper (chunking), et vectoriser (embedding) des documents dans cette base.
2.  **Implémentation du mécanisme de Récupération (Retrieval)**:
    *   Un nouveau service ou une extension de l'`inference_service` pour :
        *   Prendre une requête utilisateur.
        *   La vectoriser.
        *   Effectuer une recherche de similarité dans la base de données vectorielle pour trouver les N documents/chunks les plus pertinents.
3.  **Logique d'Augmentation et Génération**:
    *   Modifier l'`inference_service` (ou le nouveau service RAG) pour :
        *   Prendre la requête utilisateur originale et les documents récupérés.
        *   Construire un prompt augmenté (contexte + question).
        *   Envoyer ce prompt augmenté au modèle LLM (actuellement `distilgpt2` ou un autre plus performant) pour générer la réponse finale.
    *   L'API key existante continuera de protéger l'accès à cette fonctionnalité de génération augmentée.

## Considérations de Sécurité

*   **Mots de passe**: Stockés hashés (bcrypt).
*   **Secrets**: Les secrets (clés JWT, identifiants de base de données) devraient idéalement être gérés via des variables d'environnement injectées ou un système de gestion de secrets (ex: HashiCorp Vault, Docker secrets) en production. Actuellement, certains sont dans `docker-compose.yml` pour la simplicité locale.
*   **Validation des entrées**: Pydantic est utilisé pour la validation des données dans les requêtes FastAPI.
*   **HTTPS**: Essentiel en production. Nginx peut être configuré pour la terminaison SSL.
*   **Permissions des clés API**: (Futur) Possibilité d'ajouter des permissions/scopes aux clés API.
*   **Rate Limiting**: À considérer pour protéger contre les abus.

## Scalabilité

*   Chaque microservice peut être scalé indépendamment en augmentant le nombre de répliques de conteneurs (ex: `docker-compose up --scale <service_name>=<num_replicas>`).
*   Pour une scalabilité avancée et une gestion en production, des orchestrateurs comme Kubernetes sont recommandés.
*   Le choix de modèles LLM plus petits ou quantifiés peut aider à la scalabilité de l'inférence.

## Contribution

Ce projet est actuellement privé. Pour toute suggestion ou question, veuillez contacter le propriétaire du dépôt.

---
*Ce README est destiné à un usage interne et suppose un accès contrôlé au dépôt.*