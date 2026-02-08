# Evaluation Logic

The evaluation engine is the core of the feature flag service. It processes flag evaluations in a strict, deterministic order.

## Processing Order

When evaluating a flag for a user, the engine follows this exact order:

### 1. Flag Status Check

If the flag is **archived** or **disabled** (globally or per-environment), the evaluation returns:

- `enabled: false`
- `reason: "disabled"`

### 2. Targeted Deny List

If the `user_id` appears in the **targeted deny list**, the evaluation returns:

- `enabled: false`
- `reason: "targeted_deny"`

The deny list is checked **before** the allow list, meaning a user in both lists will be denied.

### 3. Targeted Allow List

If the `user_id` appears in the **targeted allow list**, the evaluation returns:

- `enabled: true`
- `reason: "targeted_allow"`

### 4. Rule Evaluation

Rules are evaluated in **ascending priority order** (lower number = higher priority).

For each rule:

1. All conditions must match (AND logic)
2. If all conditions match, the rule's outcome is applied
3. Processing stops at the first matching rule

Returns:

- `enabled: true`
- `reason: "rule_match"`
- `rule_id: <matching rule ID>`
- `variant: <rule variant>`

### 5. Percentage Rollout

If a `rollout_percentage` is configured (0-100, supports decimals like 12.5%):

1. A deterministic hash is computed from `(flag_key, env_key, user_id)`
2. The hash maps to a bucket in `[0, 9999]`
3. The user is enabled if `bucket < rollout_percentage * 100`

This ensures:

- The same user always gets the same result for the same flag
- Different flags produce different bucketing
- Rollout is uniformly distributed

Returns:

- `reason: "rollout"`

### 6. Default Value

If no other condition matched, the default variant for the environment is returned.

Returns:

- `reason: "default"`

## Deterministic Hashing

The rollout hash uses SHA-256 on the string `"{flag_key}:{env_key}:{user_id}"`:

```python
digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
bucket = int(digest[:8], 16) % 10000
```

This gives 10,000 buckets (0.01% granularity), supporting decimal percentages like 12.5%.

## Rule Conditions

Each rule has a list of conditions (predicates). All conditions must match for the rule to apply.

### Supported Operators

| Operator | Description | Example |
|---|---|---|
| `exists` | Attribute is present | `{"attribute": "beta", "operator": "exists"}` |
| `equals` | Value equality | `{"attribute": "plan", "operator": "equals", "value": "pro"}` |
| `not_equals` | Value inequality | `{"attribute": "plan", "operator": "not_equals", "value": "free"}` |
| `contains` | String contains | `{"attribute": "email", "operator": "contains", "value": "@company.com"}` |
| `in_list` | Value in list | `{"attribute": "country", "operator": "in_list", "value": ["US", "CA"]}` |
| `gt` | Greater than | `{"attribute": "age", "operator": "gt", "value": 18}` |
| `gte` | Greater than or equal | `{"attribute": "score", "operator": "gte", "value": 100}` |
| `lt` | Less than | `{"attribute": "risk", "operator": "lt", "value": 0.5}` |
| `lte` | Less than or equal | `{"attribute": "attempts", "operator": "lte", "value": 3}` |
