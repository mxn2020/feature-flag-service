# FEEDBACK_FOR_REVIEW.md

## 1) Summary of Changes

- **README: Fix uv install instructions** — Replaced `pip install uv` with `brew install uv` (macOS, preferred) and `pipx install uv` (cross-platform). Added Python version note ("3.12 and 3.13 are tested in CI"). Same fix applied to `docs/getting-started.md`.
- **Demo seed script** — Added `scripts/seed_demo.py` using stdlib `urllib` (no extra deps). Creates a `dev` environment, `new_checkout` flag with 50% rollout, allow/deny targeting, and two rules (country==EG at priority 0, country exists at priority 1). Fully idempotent.
- **"Demo in 60 seconds" README section** — 5 curl commands: healthz, deny-list user, allow-list user, rule-match (country=EG), deterministic rollout (same user twice).
- **Rules docs page** — Created `docs/rules.md` with rule object structure, predicate/condition structure, all 9 operators, outcome structure, precedence/priority worked example, and 6 complete JSON request examples. Linked from mkdocs nav and README.
- **RuleCreate DX: flag_key/env_key support** — Updated `RuleCreate` schema to accept `flag_key`+`env_key` as alternatives to `flag_id`+`environment_id`. Backwards compatible. Updated endpoint logic in `app/api/v1/rules.py`.
- **Tests for key-based rule creation** — 3 new tests: create by keys, 404 for bad keys, 422 for missing identifiers.
- **CI dependency audit** — Added `dependency-audit` job to `.github/workflows/ci.yml` running `pip-audit` (non-blocking with `|| true`).
- **SECURITY.md** — Documents vulnerability reporting, pip-audit usage, and API key management.
- **Production notes** — Short section in README recommending reverse proxy, API key rotation, and PostgreSQL for production.
- **OpenAPI spec regenerated** — `docs/openapi.json` updated to reflect the new `RuleCreate` schema.

## 2) Exact Commands Run

```bash
# Install dependencies
pip install uv
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev,docs]"
cp .env.example .env

# Linting
ruff format --check app/ tests/
ruff check app/ tests/

# Type checking
mypy app/

# Tests
pytest --cov=app --cov-report=term-missing

# Docs build
mkdocs build

# Start server
uvicorn app.main:app --port 8000 &

# Seed demo data
python scripts/seed_demo.py

# Verify idempotency
python scripts/seed_demo.py

# API smoke tests
READ_KEY="change-me-read-key"

# 1. Health check
curl -s http://localhost:8000/api/v1/healthz

# 2. Deny-list user
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: $READ_KEY" -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"user_deny1"}'

# 3. Allow-list user
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: $READ_KEY" -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"user_allow1"}'

# 4. Rule match (country=EG)
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: $READ_KEY" -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"user99","attributes":{"country":"EG"}}'

# 5. Deterministic rollout (same user twice)
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: $READ_KEY" -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"rollout-test-42"}'
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: $READ_KEY" -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"rollout-test-42"}'

# Regenerate OpenAPI
python -c "
import json
from app.main import create_app
app = create_app(run_startup=False)
with open('docs/openapi.json', 'w') as f:
    json.dump(app.openapi(), f, indent=2)
    f.write('\n')
"
```

## 3) Test/CI Status

| Tool | Result | Details |
|------|--------|---------|
| `ruff format --check app/ tests/` | ✅ PASS | 27 files already formatted |
| `ruff check app/ tests/` | ✅ PASS | All checks passed |
| `mypy app/` | ✅ PASS | Success: no issues found in 19 source files |
| `pytest --cov=app --cov-report=term-missing` | ✅ PASS | 42 passed, 89.7% coverage (70% required) |
| `mkdocs build` | ✅ PASS | Documentation built in 0.37 seconds |
| CodeQL | ✅ PASS | 0 alerts (actions + python) |

## 4) API Verification

### Health check
```
curl -s http://localhost:8000/api/v1/healthz
→ {"status":"ok"}
```

### Deny-list user
```
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: change-me-read-key" -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"user_deny1"}'
→ {"flag_key":"new_checkout","env_key":"dev","enabled":false,"variant":"off",
   "reason":"targeted_deny","rule_id":null,"eval_id":"...","timestamp":"..."}
```

### Allow-list user
```
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: change-me-read-key" -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"user_allow1"}'
→ {"flag_key":"new_checkout","env_key":"dev","enabled":true,"variant":"on",
   "reason":"targeted_allow","rule_id":null,"eval_id":"...","timestamp":"..."}
```

### Rule match (country=EG)
```
curl -s -X POST http://localhost:8000/api/v1/evaluate \
  -H "X-API-Key: change-me-read-key" -H "Content-Type: application/json" \
  -d '{"flag_key":"new_checkout","env_key":"dev","user_id":"user99","attributes":{"country":"EG"}}'
→ {"flag_key":"new_checkout","env_key":"dev","enabled":true,"variant":"egypt-ui",
   "reason":"rule_match","rule_id":"e45c7cc1-...","eval_id":"...","timestamp":"..."}
```

### Deterministic rollout (same user, two calls)
```
Call 1 → {"enabled":false,"variant":"off","reason":"rollout",...}
Call 2 → {"enabled":false,"variant":"off","reason":"rollout",...}
✅ Same result both times — deterministic
```

All responses include the required fields: `enabled`, `reason`, `rule_id`, `eval_id`, `timestamp`.

## 5) Remaining Issues / Risks + Suggested Next Steps

### Issues
- **None blocking** — all tools pass, API works end-to-end.

### Risks (low)
1. **`pip-audit` non-blocking in CI** — The `|| true` means vulnerabilities won't fail the build. This is intentional to avoid blocking on upstream issues, but teams should monitor the output.
2. **RuleCreate accepts all four fields** — When both `flag_id` and `flag_key` are provided, `flag_id` takes precedence silently. A stricter approach would reject the request. Current behavior is safe and backwards-compatible.

### Suggested Next Steps (prioritized)
1. **Add Pydantic model validator** to `RuleCreate` that rejects requests providing both `flag_id` and `flag_key` simultaneously (mutual exclusion).
2. **Add `FlagEnvironment` seed** to `seed_demo.py` to demonstrate per-environment overrides (e.g., `default_enabled=false` for dev).
3. **Promote `pip-audit` to blocking** once upstream dependencies are confirmed clean.
4. **Add rate limiting** via a lightweight middleware or reverse proxy documentation.
5. **Add pagination** to list endpoints (`GET /flags`, `GET /rules`, `GET /environments`).
6. **Add OpenAPI spec diff** to CI to catch accidental schema drift.
