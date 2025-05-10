FROM python:3.10-slim as builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir poetry

# Copy project definition
COPY pyproject.toml poetry.lock* ./

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install runtime dependencies only
RUN poetry install --no-dev --no-interaction

# Second stage - minimal runtime image
FROM python:3.10-slim

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY quantum_analyzer ./quantum_analyzer
COPY patterns ./patterns
COPY README.md ./

# Create a non-root user
RUN useradd -m appuser
USER appuser

# Set up environment
ENV PYTHONPATH=/app
ENV QA_CONFIG=/config/quantum_analyzer.yaml

# Default to help
ENTRYPOINT ["quantum-analyzer"]
CMD ["--help"]