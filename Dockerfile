FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/
COPY config/ ./config/
COPY sql/ ./sql/
COPY main.py ./

# Create logs directory
RUN mkdir -p logs

# Install dependencies
RUN uv sync --frozen

# Create non-root user
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check - verify the application can import properly
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD uv run python -c "from config.settings import DATABASE_ENABLED; import sys; sys.exit(0)"

# Run the application with unbuffered output
CMD ["uv", "run", "python", "-u", "main.py"]