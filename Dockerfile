# Multi-stage build to reduce final image size
FROM ubuntu:22.04 as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Build llama.cpp
WORKDIR /build
COPY llama.cpp/ ./llama.cpp/
WORKDIR /build/llama.cpp
RUN mkdir build && cd build && \
    cmake .. -DLLAMA_CURL=ON -DCMAKE_BUILD_TYPE=Release && \
    make -j$(nproc) llama-server

# Final runtime image
FROM ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy built llama.cpp server
COPY --from=builder /build/llama.cpp/build/bin/llama-server /usr/local/bin/

# Copy application files (excluding large model files)
COPY rag/ ./rag/
COPY sources/ ./sources/
COPY scripts/ ./scripts/
COPY download_model.py .

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Download the AI model during build
RUN python3 download_model.py

# Create necessary directories
RUN mkdir -p /app/rag/chroma_db /app/rag/static /app/rag/templates

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=rag/web_chat.py
ENV FLASK_ENV=production

# Expose port
EXPOSE 8081

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting AmpAI deployment..."\n\
\n\
# Start llama.cpp server in background\n\
echo "Starting llama.cpp server..."\n\
llama-server \\\n\
    --model /app/models/Llama-3.2-3B-Instruct-Q6_K.gguf \\\n\
    --host 0.0.0.0 \\\n\
    --port 8000 \\\n\
    --ctx-size 4096 \\\n\
    --threads $(nproc) \\\n\
    --log-format text &\n\
\n\
# Wait for llama server to be ready\n\
echo "Waiting for llama server to start..."\n\
for i in {1..30}; do\n\
    if curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then\n\
        echo "Llama server is ready!"\n\
        break\n\
    fi\n\
    echo "Waiting... ($i/30)"\n\
    sleep 2\n\
done\n\
\n\
# Initialize RAG system\n\
echo "Initializing RAG system..."\n\
cd /app/rag\n\
python3 rag_simple.py reindex\n\
\n\
# Start Flask app\n\
echo "Starting Flask web server..."\n\
python3 web_chat.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8081/api/status || exit 1

CMD ["/app/start.sh"]
