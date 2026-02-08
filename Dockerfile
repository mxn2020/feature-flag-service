FROM python:3.12-slim AS base

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy dependency specification
COPY pyproject.toml ./

# Install production dependencies only
RUN uv pip install --system --no-cache ".[dev]"

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
