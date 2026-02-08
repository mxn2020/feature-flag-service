# Contributing

Thank you for considering contributing to Feature Flag Service!

## Development Setup

```bash
git clone https://github.com/mxn2020/feature-flag-service.git
cd feature-flag-service
pip install uv
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env
```

## Code Quality

Before submitting a PR, ensure:

```bash
# Format code
ruff format app/ tests/

# Lint
ruff check app/ tests/

# Type check
mypy app/

# Run tests
pytest --cov=app --cov-report=term-missing
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes with tests
4. Ensure all checks pass
5. Submit a pull request

## Code Style

- Follow existing code patterns
- Use type hints everywhere
- Write docstrings for public functions
- Keep functions focused and small

## Reporting Issues

Please use GitHub Issues with:

- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
