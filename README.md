# feature-flag-service

A minimal but serious feature flag platform: an API-first service with deterministic percentage rollout, targeting, and basic rule evaluation.

[![CI](https://github.com/mxn2020/feature-flag-service/actions/workflows/ci.yml/badge.svg)](https://github.com/mxn2020/feature-flag-service/actions/workflows/ci.yml)

## Features

- **Feature flag CRUD** — create, read, update, delete flags via REST API
- **Multi-environment** — manage dev, staging, production, and custom environments
- **Rule engine** — attribute-based targeting with 9 predicate operators
- **Deterministic rollout** — consistent hashing for percentage-based rollouts (0.01% granularity)
- **Targeting lists** — per-flag, per-environment allow/deny lists
- **API key auth** — separate admin and read-only keys
- **Bulk evaluation** — evaluate multiple flags in a single request
- **OpenAPI docs** — auto-generated, committed under `docs/openapi.json`

## Tech Stack

| Component | Choice |
|---|---|
| Language | Python 3.12 |
| Web framework | FastAPI + Uvicorn |
| Database | SQLite (SQLAlchemy 2.0) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | API keys (`X-API-Key` header) |
| Testing | pytest + pytest-cov |
| Lint/Format | ruff |
| Type checking | mypy |
| Docs | mkdocs-material |
| Container | Docker + docker-compose |
| CI | GitHub Actions |

## Quick Start

### Prerequisites

- **Python 3.12+** (3.12 and 3.13 are tested in CI)
- [uv](https://github.com/astral-sh/uv) (recommended)

### Install & Run

```bash
git clone https://github.com/mxn2020/feature-flag-service.git
cd feature-flag-service

# Install uv if you don't have it (pick one)
brew install uv          # macOS (preferred, PEP 668 safe)
pipx install uv          # cross-platform alternative

# Create virtualenv and install all dependencies
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Copy env config
cp .env.example .env

# Start the server
uvicorn app.main:app --reload --port 8000
```

The API is live at `http://localhost:8000/api/v1/`. Interactive docs at `http://localhost:8000/docs`.

### Docker

```bash
docker compose up --build
```

## Demo in 60 Seconds

Start the server (see Quick Start above), then seed demo data:

```bash
python scripts/seed_demo.py
```

This creates a `dev` environment and a `new_checkout` flag with rules, rollout, and targeting.

Now try these curl commands:

```bash
ADMIN_KEY="change-me-admin-key"
READ_KEY="change-me-read-key"

# 1. Health check
curl -s http://localhost:8000/api/v1/healthz

# 2. Evaluate deny-list user → enabled=false, reason=targeted_deny
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: $READ_KEY" \
  -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"user_deny1"}'

# 3. Evaluate allow-list user → enabled=true, reason=targeted_allow
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: $READ_KEY" \
  -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"user_allow1"}'

# 4. Evaluate rule-match user (country=EG) → enabled=true, reason=rule_match, variant=egypt-ui
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: $READ_KEY" \
  -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"user99","attributes":{"country":"EG"}}'

# 5. Deterministic rollout — same user_id always gets the same result
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: $READ_KEY" \
  -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"rollout-test-42"}'

curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: $READ_KEY" \
  -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"rollout-test-42"}'
```

## API Overview

All endpoints are under `/api/v1`. Auth is via `X-API-Key` header.

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/flags` | admin | Create a flag |
| `GET` | `/flags` | admin | List all flags |
| `GET` | `/flags/{flag_id}` | admin | Get flag details |
| `PATCH` | `/flags/{flag_id}` | admin | Partial update |
| `DELETE` | `/flags/{flag_id}` | admin | Delete flag |
| `POST` | `/environments` | admin | Create environment |
| `GET` | `/environments` | admin | List environments |
| `POST` | `/rules` | admin | Create rule |
| `GET` | `/rules?flag_id=...&env=...` | admin | List rules |
| `POST` | `/evaluate` | read/admin | Evaluate flag(s) |
| `GET` | `/healthz` | public | Liveness check |
| `GET` | `/readyz` | public | Readiness check |

### Example: Create & Evaluate a Flag

```bash
ADMIN_KEY="change-me-admin-key"
READ_KEY="change-me-read-key"

# Create a flag
curl -s -X POST http://localhost:8000/api/v1/flags \
  -H "X-API-Key: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key": "dark-mode", "name": "Dark Mode", "enabled": true, "rollout_percentage": 50}'

# Create an environment
curl -s -X POST http://localhost:8000/api/v1/environments \
  -H "X-API-Key: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key": "production", "name": "Production"}'

# Evaluate
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: $READ_KEY" \
  -H "Content-Type: application/json" \
  -d '{"flag_key": "dark-mode", "env_key": "production", "user_id": "user-42"}'
```

## Evaluation Logic

Flags are evaluated in this strict order:

1. **Disabled/archived** → `reason: "disabled"`
2. **Targeted deny list** → `reason: "targeted_deny"`
3. **Targeted allow list** → `reason: "targeted_allow"`
4. **Rule matching** (ascending priority) → `reason: "rule_match"`
5. **Percentage rollout** (deterministic hash) → `reason: "rollout"`
6. **Default value** → `reason: "default"`

See [docs/evaluation.md](docs/evaluation.md) for full details.

## Rule Predicates

| Operator | Description |
|---|---|
| `exists` | Attribute is present |
| `equals` | Value equality (string/number/bool) |
| `not_equals` | Value inequality |
| `contains` | String contains substring |
| `in_list` | Value in list |
| `gt`, `gte`, `lt`, `lte` | Numeric comparisons |

See [Rules & Targeting](docs/rules.md) for full rule docs, condition structure, and JSON examples.

## Development

```bash
# Run tests
pytest --cov=app --cov-report=term-missing

# Lint & format
ruff check app/ tests/
ruff format app/ tests/

# Type check
mypy app/

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Build docs
pip install -e ".[docs]"
mkdocs serve
```

## Configuration

| Variable | Description | Default |
|---|---|---|
| `ADMIN_API_KEY` | Admin API key | `change-me-admin-key` |
| `READ_API_KEY` | Read-only API key | `change-me-read-key` |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///./feature_flags.db` |

## Security

- API keys must be changed from defaults before production use
- Read-only key can only access the `/evaluate` endpoint
- All inputs are validated via Pydantic v2
- SQL injection is prevented by SQLAlchemy's parameterized queries
- Run `bandit -r app/` for security scanning
- CI runs `pip-audit` for dependency vulnerability scanning (see `.github/workflows/ci.yml`)

## Production Notes

- **Reverse proxy**: Use a reverse proxy (e.g., nginx, Caddy, or a cloud load balancer) in front of this service for rate limiting, TLS termination, and request logging.
- **API key rotation**: Rotate `ADMIN_API_KEY` and `READ_API_KEY` regularly. Update the environment variables and restart the service — no database changes needed.
- **Database**: For production workloads, switch from SQLite to PostgreSQL by changing `DATABASE_URL`.

## License

MIT
