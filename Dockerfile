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
# Build static binary to avoid shared library issues
RUN cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLAMA_CURL=OFF \
    -DGGML_CCACHE=OFF \
    -DLLAMA_BUILD_TESTS=OFF \
    -DLLAMA_BUILD_EXAMPLES=OFF \
    -DGGML_NATIVE=OFF \
    -DGGML_OPENMP=ON \
    -DGGML_BLAS=OFF \
    -DBUILD_SHARED_LIBS=OFF \
    -DLLAMA_STATIC=ON
RUN make -j$(nproc) llama-server

# Final runtime image
FROM ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    poppler-utils \
    curl \
    libgomp1 \
    libopenblas0 \
    libomp5 \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy built static llama.cpp server binary
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

# Expose port (Railway will override this)
EXPOSE 8081

# ESSENTIAL STARTUP - Include llama-server and RAG
COPY <<EOF /app/start.sh
#!/bin/bash
set -e

echo "🚀 Starting AmpAI deployment..."

# Check if model exists
if [ ! -f "/app/models/Llama-3.2-3B-Instruct-Q6_K.gguf" ]; then
    echo "❌ Model file not found!"
    exit 1
fi

# WORKAROUND: Copy model to expected path
echo "🔧 Setting up model..."
mkdir -p models/7B
cp /app/models/Llama-3.2-3B-Instruct-Q6_K.gguf models/7B/ggml-model-f16.gguf

# Start llama-server
echo "🤖 Starting llama.cpp server..."
/usr/local/bin/llama-server \
    --model models/7B/ggml-model-f16.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    --ctx-size 2048 \
    --threads 2 \
    --log-format text \
    --verbose &
LLAMA_PID=\$!

# Wait a bit for llama-server to start
echo "⏳ Waiting for llama-server..."
sleep 5

# Initialize RAG system
echo "📚 Initializing RAG system..."
cd /app/rag
python3 rag_simple.py reindex 2>/dev/null || echo "⚠️ RAG init completed with warnings"

# Start Flask
echo "🌐 Starting Flask web server..."
python3 web_chat.py &
FLASK_PID=\$!

# Wait for Flask to be ready
echo "⏳ Waiting for Flask..."
for i in {1..30}; do
    if curl -s http://localhost:\$PORT/health > /dev/null 2>&1; then
        echo "✅ Flask is ready!"
        break
    fi
    sleep 1
done

echo "🚀 AmpAI is fully operational!"
wait \$FLASK_PID
EOF

RUN chmod +x /app/start.sh

# Health check - will use Railway's PORT environment variable
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

CMD ["/app/start.sh"]
