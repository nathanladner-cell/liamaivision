# OpenAI-powered AmpAI Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY rag/ ./rag/
COPY sources/ ./sources/
COPY scripts/ ./scripts/

# Create necessary directories
RUN mkdir -p /app/rag/chroma_db /app/rag/static /app/rag/templates

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=rag/web_chat.py
ENV FLASK_ENV=production
ENV OPENAI_API_KEY=${OPENAI_API_KEY}

# Expose port (Railway will set PORT environment variable)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/status || exit 1

# Start the application
CMD ["sh", "-c", "python3 rag/web_chat.py"]
