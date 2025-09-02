# OpenAI-powered AmpAI Dockerfile
FROM python:3.11-slim

# Install system dependencies including PostgreSQL client
RUN apt-get update && apt-get install -y \
    curl \
    poppler-utils \
    postgresql-client \
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

# Pre-index the RAG collection during build (if API key is available)
RUN if [ -n "$OPENAI_API_KEY" ]; then \
        cd /app/rag && python3 rag_simple.py reindex; \
    else \
        echo "Warning: OPENAI_API_KEY not set during build, RAG will be indexed at runtime"; \
    fi

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=rag/web_chat.py
ENV FLASK_ENV=production
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV CHROMA_TELEMETRY_ENABLED=false
ENV ANONYMIZED_TELEMETRY=false
ENV CHROMA_SERVER_NO_TELEMETRY=true

# Expose port (Railway will set PORT environment variable)
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/status || exit 1

# Create startup script with Railway-specific initialization
RUN echo '#!/bin/bash\n\
echo "🚀 Starting Liam AI Assistant on Railway..."\n\
\n\
# Railway-specific vector database initialization\n\
cd /app/rag\n\
echo "📊 Running Railway database initialization..."\n\
if python3 railway_init.py; then\n\
    echo "✅ Railway initialization successful"\n\
else\n\
    echo "⚠️  Railway initialization had issues, but continuing..."\n\
fi\n\
\n\
# Start the application\n\
echo "🤖 Starting Flask application..."\n\
python3 web_chat.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Start the application
CMD ["/app/start.sh"]
