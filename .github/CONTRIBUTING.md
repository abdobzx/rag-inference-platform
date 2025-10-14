# Contributing to SothemaAI

Thank you for your interest in contributing to SothemaAI! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [Getting Started](#-getting-started)
- [Development Setup](#️-development-setup)
- [How to Contribute](#-how-to-contribute)
- [Development Workflow](#-development-workflow)
- [Coding Standards](#-coding-standards)
- [Testing](#-testing)
- [Documentation](#-documentation)
- [Commit Guidelines](#-commit-guidelines)
- [Pull Request Process](#-pull-request-process)
- [Reporting Issues](#-reporting-issues)

## 🤝 Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** and **Docker Compose** (latest versions)
- **Git** for version control
- **Python 3.10+** (for local development)
- **Node.js 18+** (for frontend development)
- **HuggingFace account** with API token (for AI features)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

   ```bash
   git clone https://github.com/your-username/SothemaAI.git
   cd SothemaAI
   ```

3. Add the upstream remote:

   ```bash
   git remote add upstream https://github.com/abdobzx/SothemaAI.git
   ```

## 🛠️ Development Setup

### Quick Start with Docker

1. Copy environment templates:
   ```bash
   cp fastapi-microservices-app/.env.*.example fastapi-microservices-app/
   ```

2. Edit environment files with your credentials:
   - `.env.auth` - Database and email settings
   - `.env.inference` - HuggingFace API token
   - `.env.gateway` - Service URLs
   - `.env.frontend` - Frontend configuration

3. Launch the application:
   ```bash
   docker-compose up --build
   ```

4. Access the application:
   - Frontend: <http://localhost>
   - API Docs: <http://localhost/api/docs>

### Local Development Setup

For individual service development:

#### Backend Services

```bash
# Auth Service
cd fastapi-microservices-app/auth_service
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 8001

# Inference Service
cd fastapi-microservices-app/inference_service
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 8002

# Gateway Service
cd fastapi-microservices-app/gateway
pip install -r requirements.txt
python -m uvicorn src.main:app --reload --port 8000
```

#### Frontend

```bash
cd fastapi-microservices-app/frontend_react
npm install
npm run dev
```

## 🤝 How to Contribute

### Types of Contributions

- **🐛 Bug Fixes**: Fix bugs and issues
- **✨ New Features**: Add new functionality
- **📚 Documentation**: Improve documentation
- **🧪 Tests**: Add or improve tests
- **🔧 Code Refactoring**: Improve code quality
- **🔒 Security**: Security improvements

### Finding Issues to Work On

1. Check the [Issues](https://github.com/abdobzx/SothemaAI/issues) page
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on the issue to indicate you're working on it

## 🔄 Development Workflow

1. **Choose an issue** or create one for your contribution
2. **Create a branch** from `main`:

   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number-description
   ```

3. **Make your changes** following the coding standards
4. **Test your changes** thoroughly
5. **Update documentation** if needed
6. **Commit your changes** with clear commit messages
7. **Push your branch** and create a Pull Request

## 💻 Coding Standards

### Python (Backend)

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use [Black](https://black.readthedocs.io/) for code formatting
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use [Flake8](https://flake8.pycqa.org/) for linting
- Add type hints where possible
- Write docstrings for functions and classes

### JavaScript/React (Frontend)

- Follow [Airbnb JavaScript Style Guide](https://airbnb.io/javascript/)
- Use [ESLint](https://eslint.org/) for linting
- Use [Prettier](https://prettier.io/) for code formatting
- Use functional components with hooks
- Follow component naming conventions

### General

- Write clear, concise commit messages
- Add comments for complex logic
- Use meaningful variable and function names
- Keep functions small and focused
- Follow the existing code patterns

## 🧪 Testing

### Running Tests

```bash
# Run all tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Run specific service tests
cd fastapi-microservices-app/auth_service
pytest src/ -v --cov=src

# Run frontend tests
cd fastapi-microservices-app/frontend_react
npm test
```

### Test Coverage

- Maintain >80% code coverage for backend services
- Write unit tests for new functions
- Write integration tests for API endpoints
- Add E2E tests for critical user flows

### Test Guidelines

- Use descriptive test names
- Test both positive and negative scenarios
- Mock external dependencies
- Use fixtures for test data
- Clean up after tests

## 📚 Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Update API documentation for new endpoints
- Document complex algorithms and business logic
- Keep comments up to date with code changes

### User Documentation

- Update README.md for new features
- Add examples and usage instructions
- Update API documentation
- Create tutorials for complex features

## 📝 Commit Guidelines

Follow conventional commit format:

```text
type(scope): description

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```text
feat(auth): add password reset functionality

fix(api): resolve memory leak in inference service

docs(readme): update installation instructions

test(auth): add unit tests for user registration
```

## 🔄 Pull Request Process

1. **Ensure your PR is ready**:
   - All tests pass
   - Code follows style guidelines
   - Documentation is updated
   - No merge conflicts

2. **Create a Pull Request**:
   - Use the PR template
   - Provide a clear description
   - Reference related issues
   - Add screenshots for UI changes

3. **PR Review Process**:
   - Automated checks must pass
   - At least one maintainer review required
   - Address review feedback
   - Squash commits if requested

4. **After Approval**:
   - PR will be merged by a maintainer
   - Branch will be deleted automatically

## 🐛 Reporting Issues

### Bug Reports

When reporting bugs, please include:

- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, browser, version)
- Screenshots if applicable
- Error logs

### Feature Requests

For feature requests, please include:

- Clear description of the feature
- Use case and benefits
- Implementation suggestions
- Mockups or examples if applicable

## 📞 Getting Help

- **Issues**: Use GitHub Issues for bugs and feature requests
- **Discussions**: Use GitHub Discussions for questions and general discussion
- **Documentation**: Check the [Wiki](https://github.com/abdobzx/SothemaAI/wiki) for guides

## 🎉 Recognition

Contributors will be recognized in:

- Repository contributors list
- Release notes
- Project documentation

Thank you for contributing to SothemaAI! 🚀
