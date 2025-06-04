# Arclio Rules 🚀

Arclio Rules is a FastAPI-based service that implements rule processing using the FastMCP framework. It provides a robust and efficient system for managing and executing business rules in a microservices architecture.

## Overview

Arclio Rules is built with Python 3.12+ and leverages modern async capabilities to provide high-performance rule processing. The service can be run either with session management or in a stateless mode using standard I/O.

## Features

- FastAPI-based REST API
- Built on FastMCP framework for efficient rule processing
- Elasticsearch integration for rule storage and querying
- Git integration for version control of rules
- Support for both session-based and stateless operation modes
- Frontmatter parsing capabilities
- Comprehensive logging with Loguru
- UV package management for fast, reliable dependency handling
- Make-based workflow automation

## Prerequisites

- Python 3.12.8 or higher
- UV package manager
- Docker (optional, for containerized deployment)
- Age (for secrets management)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/fisseha-estifanos/arclio-rules.git
cd arclio-rules
```

2. Install dependencies using UV:
```bash
make install
```

This will:
- Install project dependencies using UV
- Set up the development environment
- Sync all dependencies

## Environment Setup

1. Initialize SOPS for secret management:
```bash
make init-key
```

2. Create your environment file:
```bash
# Copy the example environment file
cp .env.example .env

# Decrypt existing secrets (if you have access)
make decrypt
```

Required Environment Variables:
```bash
# GitHub API Configuration
GITHUB_TOKEN="add your GH PAT here"
GITHUB_ORG="add your GH Organization here"
REPO_NAME="add your repo that holds the rules here"

# Server Configuration
PORT=8000                     # Application port
HOST=0.0.0.0                  # Host to bind to

# Additional Settings
LOG_LEVEL=INFO                # Logging level (DEBUG, INFO, WARNING, ERROR)
ENVIRONMENT=development       # Application environment
```

## Usage

The service can be run in two modes:


### Stateless Mode (using stdio)
```bash
source .env
arclio-rules
```

### Development Mode
```bash
make run-dev
```

## Development Commands

The project includes a comprehensive Makefile for common development tasks:

```bash
# Development
make run-dev         # Run development server
make install         # Install dependencies
make build           # Build the project
make publish         # Publish the project to pypi

# Code Quality
make lint            # Run Ruff linter
make type-check      # Run Pyright type checker
make format          # Format code with Ruff
make pre-commit      # Run all code quality checks

# Secrets Management
make init-key        # Generate new age key for SOPS
make encrypt         # Encrypt .env to .env.sops
make decrypt         # Decrypt .env.sops to .env
make add-recipient   # Add new public key (make add-recipient KEY=age1...)
```

## Project Structure
arclio-rules/
├── src/
│ └── arclio_rules/
│ ├── datamodels/ # Data models and schemas
│ ├── inhouse_rules/ # Internal rule implementations
│ ├── routes/ # API route handlers
│ ├── services/ # Business logic services
│ ├── main.py # Application entry point
│ ├── server_with_session.py # Session-based server
│ └── server_wo_session.py # Stateless server
├── dist/ # Distribution files
├── routes/ # API route definitions
├── Makefile # Development automation
├── pyproject.toml # Project configuration
├── .env.example # Example environment configuration
└── docker-compose.yml # Docker composition file


## Configuration

The project uses various configuration files:

- `pyproject.toml`: Project metadata and dependencies
- `pyrightconfig.json`: Python type checking configuration
- `.sops.yaml`: Secrets management configuration
- `docker-compose.yml`: Container orchestration settings
- `.env`: Environment variables (created from .env.example)

## Development

### Package Management with UV

The project uses UV for dependency management, offering:
- Faster package installation
- Reliable dependency resolution
- Consistent environments across development and production
- Integration with virtual environments

### Code Quality Tools

The project uses several tools to maintain code quality:

- **Ruff**: For linting and formatting
  - Enforces PEP 8 style guide
  - Manages import sorting
  - Checks docstring formatting (Google style)
- **MyPy**: For static type checking
- **Pytest**: For testing (with async support)

### Linting Rules

The project enforces specific linting rules through Ruff, including:
- PEP 8 compliance (E)
- PyFlakes checks (F)
- Import sorting (I)
- Docstring formatting (D)

## Dependencies

Key dependencies include:
- `fastapi`: Web framework
- `fastmcp`: MCP framework integration
- `elasticsearch`: Search and storage
- `aiohttp`: Async HTTP client
- `pydantic`: Data validation
- `uvicorn`: ASGI server

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]