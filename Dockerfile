# Cloud-Native AmpAI Dockerfile - Zero Local Dependencies
FROM python:3.11-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary application files (no local database files)
COPY rag/web_chat_cloud.py ./rag/
COPY rag/cloud_vector_db.py ./rag/
COPY rag/static/ ./rag/static/
COPY rag/templates/ ./rag/templates/

# Set environment variables for cloud deployment
ENV PYTHONPATH=/app
ENV FLASK_APP=rag/web_chat_cloud.py
ENV FLASK_ENV=production

# Expose port (Railway will set PORT environment variable)
EXPOSE $PORT

# Health check for cloud version
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8081}/api/status || exit 1

# Create cloud startup script
RUN echo '#!/bin/bash\n\
echo "🌩️  Starting AmpAI Cloud on Railway..."\n\
echo "📋 Environment: Cloud-Native (Pinecone + OpenAI + GitHub)"\n\
echo "📋 No local dependencies required"\n\
\n\
cd /app/rag\n\
echo "🚀 Starting cloud Flask application..."\n\
python3 web_chat_cloud.py\n\
' > /app/start_cloud.sh && chmod +x /app/start_cloud.sh

# Start the cloud application
CMD ["/app/start_cloud.sh"]
