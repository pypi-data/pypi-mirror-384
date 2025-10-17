# DcisionAI MCP Server - Production Docker Image
# Zero-dependency deployment for seamless customer experience

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Install the package in development mode
RUN pip install -e .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash dcisionai
RUN chown -R dcisionai:dcisionai /app
USER dcisionai

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD dcisionai-mcp-server health-check || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["dcisionai-mcp-server", "start", "--host", "0.0.0.0", "--port", "8000"]
