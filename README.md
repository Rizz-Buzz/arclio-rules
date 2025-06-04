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

## Prerequisites

- Python 3.12.8 or higher
- Docker (optional, for containerized deployment)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/arclio-rules.git
cd arclio-rules
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -e .
```

## Usage

The service can be run in two modes:

### Session-Based Mode
```bash
arclio-rules
```

### Stateless Mode (using stdio)
```bash
arclio-rules-stdio
```

### Development Mode
```bash
poe start-dev
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
└── docker-compose.yml # Docker composition file


## Configuration

The project uses various configuration files:

- `pyproject.toml`: Project metadata and dependencies
- `pyrightconfig.json`: Python type checking configuration
- `.sops.yaml`: Secrets management configuration
- `docker-compose.yml`: Container orchestration settings

## Development

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