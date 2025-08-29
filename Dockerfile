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
    libcurl4-openssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Clone and build llama.cpp with explicit configuration
WORKDIR /build
RUN git clone https://github.com/ggerganov/llama.cpp.git
WORKDIR /build/llama.cpp
RUN mkdir build
WORKDIR /build/llama.cpp/build
RUN cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLAMA_CURL=OFF \
    -DGGML_CCACHE=OFF \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_BUILD_EXAMPLES=OFF
RUN make -j$(nproc) llama-server

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

# Create startup script with better error handling
COPY <<EOF /app/start.sh
#!/bin/bash
set -e

echo "🚀 Starting AmpAI deployment..."

# Check if model exists
if [ ! -f "/app/models/Llama-3.2-3B-Instruct-Q6_K.gguf" ]; then
    echo "❌ Model file not found!"
    exit 1
fi

# Start llama.cpp server in background with proper logging
echo "🤖 Starting llama.cpp server..."
/usr/local/bin/llama-server \
    --model /app/models/Llama-3.2-3B-Instruct-Q6_K.gguf \
    --host 0.0.0.0 \
    --port 8000 \
    --ctx-size 2048 \
    --threads \$(nproc) \
    --log-format text \
    --verbose &

LLAMA_PID=\$!
echo "📋 Llama server PID: \$LLAMA_PID"

# Wait for llama server to be ready with better checking
echo "⏳ Waiting for llama server to start..."
for i in {1..60}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1 || curl -s http://localhost:8000/v1/models > /dev/null 2>&1; then
        echo "✅ Llama server is ready!"
        break
    fi
    if [ \$i -eq 60 ]; then
        echo "❌ Llama server failed to start within 2 minutes"
        kill \$LLAMA_PID 2>/dev/null || true
        exit 1
    fi
    echo "   Waiting... (\$i/60)"
    sleep 2
done

# Initialize RAG system
echo "📚 Initializing RAG system..."
cd /app/rag
python3 rag_simple.py reindex

# Start Flask app
echo "🌐 Starting Flask web server..."
exec python3 web_chat.py
EOF

RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8081/api/status || exit 1

CMD ["/app/start.sh"]
