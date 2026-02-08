# API Reference

All endpoints are under `/api/v1`.

## Authentication

All endpoints (except health checks) require an `X-API-Key` header.

- **Admin key** (`ADMIN_API_KEY`): Access to all endpoints
- **Read key** (`READ_API_KEY`): Access to `/evaluate` endpoint only

```bash
curl -H "X-API-Key: your-admin-key" http://localhost:8000/api/v1/flags
```

## Flags

### Create Flag

```
POST /api/v1/flags
```

**Body:**
```json
{
  "key": "my-feature",
  "name": "My Feature",
  "description": "A new feature flag",
  "enabled": false,
  "default_variant": "off",
  "rollout_percentage": null,
  "targeted_allow": [],
  "targeted_deny": []
}
```

### List Flags

```
GET /api/v1/flags
```

### Get Flag

```
GET /api/v1/flags/{flag_id}
```

### Update Flag

```
PATCH /api/v1/flags/{flag_id}
```

**Body** (partial update):
```json
{
  "enabled": true,
  "rollout_percentage": 50.0
}
```

### Delete Flag

```
DELETE /api/v1/flags/{flag_id}
```

## Environments

### Create Environment

```
POST /api/v1/environments
```

**Body:**
```json
{
  "key": "production",
  "name": "Production",
  "description": "Production environment"
}
```

### List Environments

```
GET /api/v1/environments
```

## Rules

### Create Rule

```
POST /api/v1/rules
```

**Body:**
```json
{
  "flag_id": "uuid-here",
  "environment_id": "uuid-here",
  "priority": 1,
  "conditions": [
    {"attribute": "country", "operator": "equals", "value": "US"},
    {"attribute": "age", "operator": "gte", "value": 18}
  ],
  "enabled": true,
  "variant": "on"
}
```

### List Rules

```
GET /api/v1/rules?flag_id=...&env=production
```

## Evaluate

### Single Evaluation

```
POST /api/v1/evaluate
```

**Body:**
```json
{
  "flag_key": "my-feature",
  "env_key": "production",
  "user_id": "user-123",
  "attributes": {
    "country": "US",
    "plan": "pro"
  }
}
```

**Response:**
```json
{
  "flag_key": "my-feature",
  "env_key": "production",
  "enabled": true,
  "variant": "on",
  "reason": "rule_match",
  "rule_id": "uuid-here",
  "eval_id": "uuid-here",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Bulk Evaluation

```
POST /api/v1/evaluate
```

**Body:**
```json
{
  "evaluations": [
    {"flag_key": "flag-a", "env_key": "production", "user_id": "user-1"},
    {"flag_key": "flag-b", "env_key": "staging", "user_id": "user-1"}
  ]
}
```

## Health Checks

### Liveness

```
GET /api/v1/healthz
```

No authentication required.

### Readiness

```
GET /api/v1/readyz
```

No authentication required. Checks database connectivity.

## Predicate Operators

| Operator | Description | Value Type |
|---|---|---|
| `exists` | Attribute exists | None |
| `equals` | Equal to value | string/number/bool |
| `not_equals` | Not equal to value | string/number/bool |
| `contains` | String contains | string |
| `in_list` | Value in list | list of string/number |
| `gt` | Greater than | number |
| `gte` | Greater than or equal | number |
| `lt` | Less than | number |
| `lte` | Less than or equal | number |
