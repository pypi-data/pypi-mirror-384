# Multi-stage Docker build for LLM Provider Factory
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir build twine

# Copy source code
COPY . .

# Build the package
RUN python -m build

# Production stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install the package from wheel
COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Create non-root user
RUN useradd --create-home --shell /bin/bash llm_user
USER llm_user

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from llm_provider import LLMProviderFactory; LLMProviderFactory()" || exit 1

# Default command
CMD ["python", "-c", "from llm_provider import LLMProviderFactory; print('🚀 LLM Provider Factory ready!')"]