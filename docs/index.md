# Feature Flag Service

A minimal but serious feature flag platform: an API-first service with deterministic percentage rollout, targeting, and basic rule evaluation.

## Features

- **Feature Flags**: Create, read, update, delete feature flags
- **Environments**: Manage environments (dev, staging, production, custom)
- **Rules Engine**: Attribute-based targeting with multiple operators
- **Deterministic Rollout**: Percentage-based rollout using consistent hashing
- **Targeting Lists**: Allow/deny lists per flag per environment
- **API Key Auth**: Admin and read-only API keys
- **Bulk Evaluation**: Evaluate multiple flags in a single request

## Quick Start

```bash
# Clone and install
git clone https://github.com/mxn2020/feature-flag-service.git
cd feature-flag-service
pip install uv
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# Run
cp .env.example .env
uvicorn app.main:app --reload
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive API docs.
