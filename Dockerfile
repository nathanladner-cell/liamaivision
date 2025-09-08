# Clean Dockerfile for Glove Scanner
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY clean_requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the clean app
COPY glove_scanner_clean.py ./app.py

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/status || exit 1

# Start the application
CMD ["python3", "app.py"]
