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

# Expose port
EXPOSE 8081

# Create startup script with better error handling
COPY <<EOF /app/start.sh
#!/bin/bash
set -e

echo "🚀 Starting AmpAI deployment..."

# Check if model exists
echo "🔍 Checking for model file..."
ls -la /app/models/
if [ ! -f "/app/models/Llama-3.2-3B-Instruct-Q6_K.gguf" ]; then
    echo "❌ Model file not found at /app/models/Llama-3.2-3B-Instruct-Q6_K.gguf"
    echo "📋 Available files in /app/models/:"
    ls -la /app/models/ || echo "No models directory found"
    exit 1
fi
echo "✅ Model file found!"

# Check if llama-server binary works
echo "🔍 Testing llama-server binary..."
if ! /usr/local/bin/llama-server --help > /dev/null 2>&1; then
    echo "❌ llama-server binary has dependency issues"
    echo "📋 Checking dependencies:"
    ldd /usr/local/bin/llama-server || true
    exit 1
fi
echo "✅ llama-server binary is working"

# Use absolute path to avoid any path resolution issues
echo "🤖 Starting llama.cpp server..."
echo "📋 Working directory: $(pwd)"
echo "📋 Model file exists: $(ls -la /app/models/Llama-3.2-3B-Instruct-Q6_K.gguf)"
echo "📋 Environment: MODEL_PATH=$MODEL_PATH LLAMA_MODEL=$LLAMA_MODEL LLAMA_MODEL_PATH=$LLAMA_MODEL_PATH"

# Clear any llama.cpp environment variables that might interfere
unset LLAMA_MODEL_PATH
unset LLAMA_MODEL
unset MODEL_PATH

# WORKAROUND: Copy model to expected path
echo "🔧 Copying model to expected location..."
mkdir -p models/7B
cp /app/models/Llama-3.2-3B-Instruct-Q6_K.gguf models/7B/ggml-model-f16.gguf
echo "✅ Copied model to: models/7B/ggml-model-f16.gguf"
ls -la models/7B/

# Check for any llama.cpp config files that might override model path
echo "🔍 Checking for config files..."
find /usr/local -name "*.yaml" -o -name "*.yml" -o -name "*.json" -o -name "*.cfg" -o -name "*.conf" 2>/dev/null | head -10 || echo "No config files found"

echo "📋 Command: /usr/local/bin/llama-server --model models/7B/ggml-model-f16.gguf --host 0.0.0.0 --port 8080 --ctx-size 2048 --threads 4 --log-format text --verbose"

/usr/local/bin/llama-server \
    --model models/7B/ggml-model-f16.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    --ctx-size 2048 \
    --threads 4 \
    --log-format text \
    --verbose &

LLAMA_PID=\$!
echo "📋 Llama server PID: \$LLAMA_PID"

# Wait for llama server to be ready with better checking
echo "⏳ Waiting for llama server to start..."
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1 || curl -s http://localhost:8080/v1/models > /dev/null 2>&1; then
        echo "✅ Llama server is ready!"
        break
    fi
    if [ \$i -eq 30 ]; then
        echo "⚠️  Llama server not ready yet, but continuing with Flask startup"
    fi
    echo "   Waiting... (\$i/30)"
    sleep 2
done

# Initialize RAG system
echo "📚 Initializing RAG system..."
cd /app/rag
if python3 rag_simple.py reindex; then
    echo "✅ RAG system initialized successfully"
else
    echo "⚠️  RAG initialization failed, but continuing with Flask startup"
fi

# Start Flask app
echo "🌐 Starting Flask web server..."
cd /app/rag

# Start Flask in background and wait for it to be ready
python3 web_chat.py &
FLASK_PID=\$!
echo "📋 Flask PID: \$FLASK_PID"

# Wait for Flask to be ready
echo "⏳ Waiting for Flask to start..."
for i in {1..30}; do
    if curl -s http://localhost:8081/health > /dev/null 2>&1; then
        echo "✅ Flask is ready!"
        break
    fi
    if [ \$i -eq 30 ]; then
        echo "❌ Flask failed to start within 1 minute"
        kill \$FLASK_PID 2>/dev/null || true
        exit 1
    fi
    echo "   Waiting... (\$i/30)"
    sleep 2
done

# Keep the container running
echo "🚀 AmpAI is fully operational!"
wait \$FLASK_PID
EOF

RUN chmod +x /app/start.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8081/api/status || exit 1

CMD ["/app/start.sh"]
