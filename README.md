# SothemaAI - Production-Ready LLM Inference Platform

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue)](https://reactjs.org)

**Production Status**: MVP Complete - Ready for Production Deployment

> **🎓 PFE Internship Project** - This platform was designed and developed by [Abderrahman Benzaouia](https://github.com/abdobzx) as part of a Professional Internship (PFE) at Sothema. As the full-stack architect and designer, I conceptualized, designed, and implemented the entire platform from ground up, including system architecture, microservices design, UI/UX design, and production deployment strategy.

A comprehensive, production-ready AI inference platform built with microservices architecture, featuring user authentication, API key management, LLM inference with RAG capabilities, comprehensive logging, and a modern React frontend.

## 🚀 Quick Start

```bash
git clone <repository-url>
cd SothemaAI
cp fastapi-microservices-app/.env.*.example fastapi-microservices-app/
# Edit environment files with your credentials
docker-compose up --build
```

Access the application at [http://localhost](http://localhost)

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Services](#-services)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### Core Features
- 🔐 **User Authentication** - JWT-based authentication with email verification
- 🔑 **API Key Management** - Create, manage, and revoke API keys per user
- 🤖 **LLM Inference** - GPU-accelerated inference with Hugging Face models
- 📚 **RAG Support** - Retrieval Augmented Generation capabilities
- 📊 **Comprehensive Logging** - Centralized logging across all services
- 🌐 **Modern Frontend** - React SPA with Tailwind CSS
- 🐳 **Containerized** - Full Docker orchestration with Docker Compose

### Production Features
- 🔒 **Security Hardened** - Input validation, CORS, rate limiting
- 📈 **Monitoring Ready** - Health checks, metrics endpoints
- 🔄 **Scalable Architecture** - Independent service scaling
- 📝 **API Documentation** - Interactive OpenAPI/Swagger docs
- 🧪 **Testing Suite** - Unit, integration, and E2E tests
- 🚀 **CI/CD Ready** - GitHub Actions workflow templates

## 🏗️ Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React SPA     │◄──►│     Nginx       │◄──►│   API Gateway   │
│   (Frontend)    │    │  (Reverse Proxy)│    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Auth Service   │◄──►│   PostgreSQL    │◄──►│ Logging Service │
│  (JWT + API)    │    │   (Database)    │    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│Inference Service│
│ (LLM + RAG)     │
│   (FastAPI)     │
└─────────────────┘
```

### Service Overview

| Service | Technology | Port | Purpose |
|---------|------------|------|---------|
| **Frontend** | React + Vite | 80 | User interface |
| **Nginx** | Nginx | 80 | Reverse proxy & static files |
| **API Gateway** | FastAPI | 8000 | Request routing & authentication |
| **Auth Service** | FastAPI | 8001 | User auth & API key management |
| **Inference Service** | FastAPI | 8002 | LLM inference with GPU support |
| **Logging Service** | FastAPI | 8003 | Centralized logging |
| **PostgreSQL** | PostgreSQL | 5432 | Data persistence |

## 📦 Prerequisites

### System Requirements
- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Git** for repository cloning
- **4GB+ RAM** recommended
- **GPU** (optional but recommended for inference)

### Accounts & Tokens
- **HuggingFace** account with access token (for LLM models)
- **Gmail** account with app password (for email verification)
- **Domain** (for production SSL certificates)

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd SothemaAI/fastapi-microservices-app
```

### 2. Environment Setup
```bash
# Copy environment templates
cp .env.auth.example .env.auth
cp .env.inference.example .env.inference
cp .env.gateway.example .env.gateway
cp .env.frontend.example .env.frontend

# Edit with your credentials (see Configuration section)
```

### 3. Launch Application
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Verify Installation
```bash
# Check service health
curl http://localhost/api/health

# Access frontend
open http://localhost

# View API documentation
open http://localhost/api/docs
```

## ⚙️ Configuration

### Environment Variables

#### Auth Service (.env.auth)
```bash
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/sothema_db

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# Security
SECRET_KEY=your-secret-key-here
BCRYPT_ROUNDS=12
```

#### Inference Service (.env.inference)
```bash
# HuggingFace
HUGGING_FACE_HUB_TOKEN=your-hf-token-here

# Model Configuration
MODEL_NAME=microsoft/DialoGPT-medium
MAX_NEW_TOKENS=100
TEMPERATURE=0.7

# GPU Settings
CUDA_VISIBLE_DEVICES=0
TORCH_USE_CUDA_DSA=1
```

#### Gateway Service (.env.gateway)
```bash
# Service URLs
AUTH_SERVICE_URL=http://auth_service:8000
INFERENCE_SERVICE_URL=http://inference_service:8001
LOGGING_SERVICE_URL=http://logging_service:8002

# Security
SECRET_KEY=your-gateway-secret-key
```

#### Frontend (.env.frontend)
```bash
# API Configuration
VITE_API_BASE_URL=http://localhost/api
VITE_APP_NAME=SothemaAI
VITE_APP_VERSION=1.0.0
```

### Database Initialization
```bash
# Run database migrations (when implemented)
docker-compose exec auth_service alembic upgrade head

# Or use the current init script
docker-compose exec postgres bash /docker-entrypoint-initdb.d/init-db.sh
```

## 🚀 Usage

### User Registration & Authentication
1. Visit [http://localhost](http://localhost)
2. Click "Register" and create an account
3. Check your email for verification code
4. Login with your credentials
5. Generate API keys from your dashboard

### API Usage Examples

#### Get Authentication Token
```bash
curl -X POST "http://localhost/api/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your-email@example.com&password=your-password"
```

#### Generate Text with LLM
```bash
curl -X POST "http://localhost/api/inference/generate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{"prompt": "Hello, how are you?", "max_tokens": 50}'
```

#### Manage API Keys
```bash
# List your API keys
curl -X GET "http://localhost/api/auth/apikeys" \
  -H "Authorization: Bearer your-jwt-token"

# Create new API key
curl -X POST "http://localhost/api/auth/apikeys" \
  -H "Authorization: Bearer your-jwt-token" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "permissions": ["inference"]}'
```

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: [http://localhost/api/docs](http://localhost/api/docs)
- **ReDoc**: [http://localhost/api/redoc](http://localhost/api/redoc)
- **OpenAPI Schema**: [http://localhost/api/openapi.json](http://localhost/api/openapi.json)

### Service-Specific Docs
- **Auth Service**: [http://localhost:8001/docs](http://localhost:8001/docs)
- **Inference Service**: [http://localhost:8002/docs](http://localhost:8002/docs)
- **Logging Service**: [http://localhost:8003/docs](http://localhost:8003/docs)

### Postman Collection
Import the Postman collection from `docs/SothemaAI.postman_collection.json` for comprehensive API testing.

## 💻 Development

### Local Development Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd frontend_react && npm install

# Run services individually for development
# Auth Service
cd auth_service && python -m uvicorn src.main:app --reload --port 8001

# Inference Service
cd inference_service && python -m uvicorn src.main:app --reload --port 8002

# Frontend
cd frontend_react && npm run dev
```

### Testing
```bash
# Run all tests
docker-compose exec auth_service pytest
docker-compose exec inference_service pytest

# Run frontend tests
cd frontend_react && npm test

# Run integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### Code Quality
```bash
# Lint Python code
docker-compose exec auth_service flake8 src/
docker-compose exec auth_service black src/

# Lint JavaScript/React code
cd frontend_react && npm run lint
```

## 🚢 Deployment

### Production Deployment
```bash
# Build for production
docker-compose -f docker-compose.prod.yml build

# Deploy with SSL
docker-compose -f docker-compose.prod.yml up -d

# Scale services as needed
docker-compose up -d --scale inference_service=3
```

### Environment-Specific Configurations
- **Development**: `docker-compose.yml`
- **Production**: `docker-compose.prod.yml`
- **Testing**: `docker-compose.test.yml`

### SSL/TLS Setup (Production)
```bash
# Install certbot for Let's Encrypt
sudo apt-get install certbot

# Generate SSL certificates
sudo certbot certonly --standalone -d yourdomain.com

# Configure nginx for SSL (see nginx/nginx.prod.conf)
```

## 📊 Monitoring

### Health Checks
```bash
# Overall system health
curl http://localhost/api/health

# Individual service health
curl http://localhost/api/health/auth
curl http://localhost/api/health/inference
curl http://localhost/api/health/logging
```

### Metrics Endpoints
```bash
# Prometheus metrics (when implemented)
curl http://localhost:9090/metrics

# Service-specific metrics
curl http://localhost:8001/metrics
curl http://localhost:8002/metrics
```

### Logging
```bash
# View centralized logs
docker-compose logs -f logging_service

# View specific service logs
docker-compose logs -f auth_service
```

## 🔒 Security

### Authentication & Authorization
- JWT tokens with configurable expiration
- API key-based service authentication
- Role-based access control (RBAC) ready
- Password hashing with bcrypt

### Data Protection
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- XSS protection in React frontend
- CORS configuration

### Production Security
- SSL/TLS encryption (required in production)
- Rate limiting on API endpoints
- Security headers (HSTS, CSP, etc.)
- Regular dependency updates

### Security Checklist
- [ ] SSL/TLS certificates configured
- [ ] Secrets moved to environment variables
- [ ] Database credentials rotated
- [ ] Firewall rules configured
- [ ] Regular security audits performed

## 🔧 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker logs
docker-compose logs

# Verify environment files
ls -la .env.*

# Check port conflicts
netstat -tlnp | grep :80
```

#### Database Connection Issues
```bash
# Check PostgreSQL container
docker-compose ps postgres

# Verify database credentials
docker-compose exec postgres psql -U sothema_user -d sothema_db

# Reset database
docker-compose down -v
docker-compose up --build postgres
```

#### GPU Issues
```bash
# Verify GPU availability
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

#### Email Issues
```bash
# Test email configuration
docker-compose exec auth_service python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
print('Email configuration OK')
"
```

### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check service logs for errors
docker-compose logs --tail=100 auth_service

# Profile inference performance
curl -X POST "http://localhost/api/inference/generate" \
  -H "X-API-Key: your-key" \
  -d '{"prompt": "test", "benchmark": true}'
```

### Reset Everything
```bash
# Complete cleanup
docker-compose down -v --remove-orphans
docker system prune -a --volumes

# Fresh start
docker-compose up --build
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and add tests
4. Run the test suite: `docker-compose -f docker-compose.test.yml up`
5. Commit your changes: `git commit -am 'Add your feature'`
6. Push to the branch: `git push origin feature/your-feature`
7. Submit a pull request

### Code Standards
- **Python**: Follow PEP 8, use Black for formatting
- **JavaScript**: Use ESLint, follow Airbnb style guide
- **Documentation**: Update README and API docs for changes
- **Testing**: Maintain >80% test coverage

### Commit Guidelines
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Keep commits atomic and descriptive
- Reference issues in commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **React** - Frontend library
- **Hugging Face** - LLM model hosting
- **PostgreSQL** - Reliable database
- **Docker** - Containerization platform

## 📞 Support

For support and questions:
- 📧 Email: support@sothema.ai
- 📖 Documentation: [docs.sothema.ai](https://docs.sothema.ai)
- 🐛 Issues: [GitHub Issues](https://github.com/abdobzx/SothemaAI/issues)

---

**Built with ❤️ for the AI community**