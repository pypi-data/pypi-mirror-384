# 🚀 fastinit - FastAPI Project Generator CLI

A powerful, production-ready CLI tool built with **Typer** that bootstraps FastAPI applications with best practices, database support, JWT authentication, and more.

## ✨ Features

### 🎯 **Project Initialization**
- One-command project setup with intelligent defaults
- Interactive mode for guided configuration
- Multiple Python version support (3.8+)

### 🗄️ **Database Integration**
- **PostgreSQL**, **MySQL**, and **SQLite** support
- Pre-configured SQLAlchemy setup
- **Alembic migrations with automatic settings import from pydantic_settings**
- Database health checks included

### 🔐 **JWT Authentication**
- **PyJWT** integration for token creation/verification
- **PyJWKClient** support for remote JWK verification
- Configurable JWKS endpoints
- Protected route examples

### 📝 **Logging & Configuration**
- Structured logging setup
- Environment-based configuration with **Pydantic Settings**
- `.env` file support

### 🐳 **Docker Ready**
- Optimized Dockerfile
- Docker Compose with database services

### 🎨 **Code Generation**
- Generate SQLAlchemy models
- Generate service layers
- Generate API routes
- **CRUD generators** - create everything in one command

## Installation

### Install from source
```bash
pip install -e .
```

### Install as a package (once published)
```bash
pip install fastinit
```

### Install as dev dependency
```bash
pip install --dev fastinit
```

## Usage

### Initialize a new FastAPI project

```bash
# Basic project
fastinit init my-project

# With database support
fastinit init my-project --db

# With JWT authentication
fastinit init my-project --jwt

# With logging
fastinit init my-project --logging

# All features
fastinit init my-project --db --jwt --logging --docker

# Interactive mode
fastinit init my-project --interactive
```

### Generate new components

```bash
# Generate a new model
fastinit new model User --fields "name:str,email:str,age:int"

# Generate Pydantic schemas (for request/response validation)
fastinit new schema User --fields "name:str,email:str,age:int"

# Generate a new service
fastinit new service UserService --model User

# Generate a new route/controller
fastinit new route users --service UserService

# Generate all at once (model + schema + service + route)
fastinit new crud User --fields "name:str,email:str,age:int"

# Generate with different pagination strategies
fastinit new crud Product --pagination cursor        # Cursor-based pagination
fastinit new route users --pagination none           # No pagination
fastinit new service UserService --pagination cursor # Custom pagination for service
```

### Configuration Options

```bash
# Choose database type
fastinit init my-project --db --db-type postgresql
# Options: postgresql, mysql, sqlite

# Specify Python version
fastinit init my-project --python-version 3.11
```

## Project Structure

```
my-project/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   └── health.py
│   │   └── deps.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py (if --jwt)
│   ├── models/
│   │   └── __init__.py
│   ├── schemas/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   └── db/
│       ├── __init__.py
│       └── session.py (if --db)
├── tests/
│   └── __init__.py
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── Dockerfile (if --docker)
```

## Examples

### Basic FastAPI App
```bash
fastinit init my-api
cd my-api
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Full-Featured App
```bash
fastinit init my-api --db --jwt --logging --docker
cd my-api
docker-compose up
```

### Generate CRUD Components
```bash
cd my-api
fastinit new crud Product --fields "name:str,price:float,description:text"
# Creates:
# - app/models/product.py (SQLAlchemy model)
# - app/schemas/product.py (Pydantic schemas for validation)
# - app/services/product_service.py (Business logic)
# - app/api/routes/products.py (REST API endpoints)
```

## 📚 Documentation

- **[Quick Start](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[Usage Guide](docs/USAGE_GUIDE.md)** - Complete reference
- **[Visual Guide](docs/VISUAL_GUIDE.md)** - Visual diagrams and examples
- **[Alembic Integration](docs/ALEMBIC_INTEGRATION.md)** - Database migrations with auto-import settings
- **[Features](docs/FEATURES.md)** - Complete feature list
- **[Examples](examples/)** - Code examples

## 🛠️ Development

- **[Contributing](docs/CONTRIBUTING.md)** - How to contribute
- **[Changelog](docs/CHANGELOG.md)** - Version history
- **[Scripts](scripts/)** - Development and demo scripts

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details
