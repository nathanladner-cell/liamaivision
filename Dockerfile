# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy minimal requirements
COPY minimal_requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy minimal vision app
COPY minimal_vision.py ./
COPY minimal_requirements.txt ./

# Make sure our entry point is executable
RUN chmod +x minimal_vision.py

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_ENV=production

# Expose port
EXPOSE $PORT

# Health check - Railway checks /api/status by default
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/status || exit 1

# Start the application
CMD ["python3", "minimal_vision.py"]
