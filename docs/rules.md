# Rules & Targeting

Rules let you enable a flag for specific users based on their **attributes** (country, plan, age, etc.).
Rules are evaluated in ascending `priority` order—the first matching rule wins.

## Rule Object Structure

| Field            | Type             | Required | Description                                           |
|------------------|------------------|----------|-------------------------------------------------------|
| `flag_id`        | `string` (UUID)  | yes*     | ID of the flag this rule belongs to                   |
| `flag_key`       | `string`         | yes*     | Key of the flag (alternative to `flag_id`)            |
| `environment_id` | `string` (UUID)  | yes*     | ID of the environment                                 |
| `env_key`        | `string`         | yes*     | Key of the environment (alternative to `environment_id`) |
| `priority`       | `integer` (≥ 0)  | yes      | Lower number = higher precedence                      |
| `conditions`     | `array[Predicate]` | yes    | All must match (AND logic)                            |
| `enabled`        | `boolean`        | no       | Default `true`                                        |
| `variant`        | `string`         | no       | Variant returned on match (default `"on"`)            |

!!! note
    You can identify the flag and environment by **either** IDs or keys.
    When using keys, pass `flag_key` + `env_key` instead of `flag_id` + `environment_id`.

## Predicate (Condition) Structure

Each entry in `conditions` is a **Predicate**:

| Field       | Type     | Required | Description                        |
|-------------|----------|----------|------------------------------------|
| `attribute` | `string` | yes      | Name of the user attribute to test |
| `operator`  | `string` | yes      | One of the operators below         |
| `value`     | any      | depends  | Comparison value (not needed for `exists`) |

### Allowed Operators

| Operator     | Value Type              | Description                                |
|--------------|-------------------------|--------------------------------------------|
| `exists`     | *(none)*                | Attribute is present (any value)           |
| `equals`     | `string/number/bool`    | Exact equality (with type coercion)        |
| `not_equals` | `string/number/bool`    | Inequality                                 |
| `contains`   | `string`                | Attribute string contains the value        |
| `in_list`    | `array[string/number]`  | Attribute value is one of the listed items |
| `gt`         | `number`                | Attribute > value                          |
| `gte`        | `number`                | Attribute ≥ value                          |
| `lt`         | `number`                | Attribute < value                          |
| `lte`        | `number`                | Attribute ≤ value                          |

## Outcome Structure

When a rule matches, the evaluation response contains:

```json
{
  "flag_key": "new_checkout",
  "env_key": "dev",
  "enabled": true,
  "variant": "on",
  "reason": "rule_match",
  "rule_id": "a1b2c3d4-...",
  "eval_id": "e5f6g7h8-...",
  "timestamp": "2025-01-15T12:00:00Z"
}
```

- `enabled` is always `true` when a rule matches.
- `variant` is the rule's configured variant (defaults to `"on"`).
- `rule_id` identifies which rule matched.

## Precedence & Priority Order

Rules are sorted by `priority` **ascending** — priority `0` is evaluated first.

### Worked Example

Imagine two rules for flag `new_checkout` in environment `dev`:

| Priority | Condition                        | Variant       |
|----------|----------------------------------|---------------|
| **0**    | `country` equals `"EG"`         | `"egypt-ui"`  |
| **1**    | `plan` equals `"enterprise"`    | `"enterprise-ui"` |

A user with `{"country": "EG", "plan": "enterprise"}` matches **both** rules,
but **priority 0** wins because it is evaluated first.

Result: `enabled=true, variant="egypt-ui", reason="rule_match"`.

If the same user had `{"country": "US", "plan": "enterprise"}`, only rule at
priority 1 matches → `variant="enterprise-ui"`.

## JSON Request Examples

### 1. Create a rule using flag/env keys — `equals` operator

```json
POST /api/v1/rules
{
  "flag_key": "new_checkout",
  "env_key": "dev",
  "priority": 0,
  "conditions": [
    {"attribute": "country", "operator": "equals", "value": "EG"}
  ],
  "variant": "egypt-ui"
}
```

### 2. Create a rule using IDs — `in_list` operator

```json
POST /api/v1/rules
{
  "flag_id": "550e8400-e29b-41d4-a716-446655440000",
  "environment_id": "660e8400-e29b-41d4-a716-446655440001",
  "priority": 1,
  "conditions": [
    {"attribute": "country", "operator": "in_list", "value": ["US", "CA", "UK"]}
  ],
  "variant": "intl-ui"
}
```

### 3. `exists` operator — check if attribute is present

```json
POST /api/v1/rules
{
  "flag_key": "beta-feature",
  "env_key": "dev",
  "priority": 0,
  "conditions": [
    {"attribute": "beta_tester", "operator": "exists"}
  ],
  "variant": "beta"
}
```

### 4. `contains` operator — substring match

```json
POST /api/v1/rules
{
  "flag_key": "internal-tools",
  "env_key": "dev",
  "priority": 0,
  "conditions": [
    {"attribute": "email", "operator": "contains", "value": "@mycompany.com"}
  ],
  "variant": "internal"
}
```

### 5. `gt` / `lte` operators — numeric range

```json
POST /api/v1/rules
{
  "flag_key": "premium-feature",
  "env_key": "production",
  "priority": 0,
  "conditions": [
    {"attribute": "account_age_days", "operator": "gt", "value": 30},
    {"attribute": "account_age_days", "operator": "lte", "value": 365}
  ],
  "variant": "mature-account"
}
```

### 6. `not_equals` operator — exclude a value

```json
POST /api/v1/rules
{
  "flag_key": "paid-feature",
  "env_key": "production",
  "priority": 0,
  "conditions": [
    {"attribute": "plan", "operator": "not_equals", "value": "free"}
  ],
  "variant": "paid"
}
```
