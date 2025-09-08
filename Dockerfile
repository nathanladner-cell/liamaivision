# Cloud-Native AmpAI Dockerfile - Zero Local Dependencies
FROM python:3.11-slim

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy Python requirements first (for better caching)
COPY rag/vision_requirements.txt ./vision_requirements.txt
RUN pip install --no-cache-dir -r vision_requirements.txt

# Copy vision app files
COPY rag/vision_app.py ./rag/
COPY rag/start.py ./rag/
COPY rag/cloud_vector_db.py ./rag/
COPY rag/static/ ./rag/static/
COPY rag/templates/ ./rag/templates/

# Set environment variables for vision app deployment
ENV PYTHONPATH=/app
ENV FLASK_APP=rag/vision_app.py
ENV FLASK_ENV=production

# Expose port (Railway will set PORT environment variable)
EXPOSE $PORT

# Health check for vision app
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start the vision application
CMD ["python3", "rag/start.py"]
