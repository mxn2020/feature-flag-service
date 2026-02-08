# Security

## Reporting Vulnerabilities

If you discover a security vulnerability, please open a private security advisory on GitHub
or email the maintainer directly. Do **not** open a public issue.

## Dependency Auditing

This project runs **pip-audit** in CI on every push and pull request to detect known
vulnerabilities in Python dependencies. The audit step is non-blocking (advisory) so that
development is not halted by upstream issues, but its output is always visible in the CI
logs.

To run locally:

```bash
pip install pip-audit
pip-audit
```

## API Key Management

- Change the default keys (`change-me-admin-key` / `change-me-read-key`) before deploying.
- Rotate keys regularly by updating the environment variables and restarting the service.
- Use a reverse proxy (nginx, Caddy, cloud LB) for rate limiting and TLS termination.
