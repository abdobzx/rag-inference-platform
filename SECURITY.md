# Security Documentation

## Overview

This document outlines the security measures implemented in the SothemaAI platform to protect sensitive data and ensure secure operations.

## Environment Variables & Secrets Management

### Critical Security Fix Applied ✅

**Issue**: Hardcoded credentials were exposed in `docker-compose.yml` and `.env` files.

**Solution Implemented**:
- Removed hardcoded `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` from `docker-compose.yml`
- Removed exposed `HUGGING_FACE_HUB_TOKEN` from `.env` file
- Created separate environment files for each service:
  - `.env.auth` - Authentication service credentials
  - `.env.inference` - AI model tokens and configuration
  - `.env.gateway` - Service routing configuration
  - `.env.frontend` - Client-side configuration

### Environment File Structure

Each service now uses dedicated environment files with proper variable scoping:

#### .env.auth
```bash
JWT_SECRET_KEY=your-super-secret-jwt-key
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
ALLOWED_EMAIL_DOMAIN=@mysothemalab.com
```

#### .env.inference
```bash
HUGGING_FACE_HUB_TOKEN=your-huggingface-token
MODEL_NAME=mistralai/Mistral-7B-Instruct-v0.2
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
```

## Security Best Practices Implemented

### 1. Secrets Management
- ✅ No hardcoded credentials in source code
- ✅ Environment variables for all sensitive data
- ✅ Separate environment files per service
- ✅ .env files added to .gitignore

### 2. Authentication & Authorization
- ✅ JWT-based user authentication
- ✅ API key-based service authorization
- ✅ Email domain restrictions (@mysothemalab.com)
- ✅ Password hashing with secure algorithms

### 3. Input Validation
- ✅ Pydantic models for request validation
- ✅ Email format validation
- ✅ Domain restrictions for user registration

### 4. Network Security
- ✅ Service-to-service communication via Docker network
- ✅ External access only through Nginx reverse proxy
- ✅ CORS configuration (restrictable to specific origins)

## Setup Instructions for Secure Deployment

### 1. Environment Configuration
```bash
# Copy example files
cp .env.auth.example .env.auth
cp .env.inference.example .env.inference
cp .env.gateway.example .env.gateway
cp .env.frontend.example .env.frontend

# Edit with your actual credentials
nano .env.auth  # Add real email credentials
nano .env.inference  # Add real HuggingFace token
```

### 2. Required Credentials
- **Gmail App Password**: Generate from Google Account settings
- **HuggingFace Token**: Create from HuggingFace account settings
- **JWT Secret Key**: Generate a secure random string (256-bit recommended)

### 3. Production Deployment Checklist
- [ ] Change all default passwords and secrets
- [ ] Use production-grade JWT secret (256+ bits)
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS/TLS in production
- [ ] Set up proper logging and monitoring
- [ ] Regular security updates of dependencies

## Security Monitoring

### Implemented Features
- Structured logging with service correlation
- Request/response logging for API calls
- Error tracking with context information
- User authentication event logging

### Recommended Additional Measures
- Implement rate limiting per user/IP
- Add request/response size limits
- Set up intrusion detection systems
- Regular security audits and penetration testing
- Dependency vulnerability scanning

## Incident Response

### Exposed Credentials Incident (FIXED)
**Date**: October 2025
**Issue**: Credentials were hardcoded in repository
**Impact**: Potential unauthorized access if repository was public
**Resolution**: Moved all credentials to environment variables, created secure templates
**Prevention**: Added .gitignore for .env files, implemented proper secrets management

## Contact

For security concerns, please contact the development team or create a security issue in the repository.