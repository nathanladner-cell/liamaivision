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

# Start the cloud application directly
CMD ["python3", "rag/web_chat_cloud.py"]
