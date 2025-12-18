FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Create app directory
WORKDIR /app

# Copy application code
COPY pyproject.toml README.md ./
COPY mcp_server/ ./mcp_server/

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install . && \
    python -m spacy download en_core_web_sm

# Create games directory (mount point)
RUN mkdir -p /games

# Default command runs the MCP server
ENTRYPOINT ["python", "-m", "mcp_server.server"]
CMD ["--games-dir", "/games"]
