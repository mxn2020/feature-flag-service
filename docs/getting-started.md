# Getting Started

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Installation

```bash
git clone https://github.com/mxn2020/feature-flag-service.git
cd feature-flag-service

# Create virtualenv and install dependencies
pip install uv
uv venv .venv
source .venv/bin/activate  # Linux/macOS
uv pip install -e ".[dev]"
```

## Configuration

Copy the example env file and edit as needed:

```bash
cp .env.example .env
```

Environment variables:

| Variable | Description | Default |
|---|---|---|
| `ADMIN_API_KEY` | API key for admin endpoints | `change-me-admin-key` |
| `READ_API_KEY` | API key for evaluate endpoint | `change-me-read-key` |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./feature_flags.db` |

## Running the Service

```bash
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000/api/v1/`.

Interactive docs: `http://localhost:8000/docs`

## Docker

```bash
docker compose up --build
```

## Running Tests

```bash
pytest --cov=app --cov-report=term-missing
```

## Linting & Type Checking

```bash
ruff check app/ tests/
ruff format --check app/ tests/
mypy app/
```

## Database Migrations

```bash
# Generate a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```
