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

# COMPLETE STARTUP - All services properly coordinated
COPY <<EOF /app/start.sh
#!/bin/bash

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
echo "✅ Model setup complete"

# Start llama-server with better error handling
echo "🤖 Starting llama.cpp server..."
/usr/local/bin/llama-server \
    --model models/7B/ggml-model-f16.gguf \
    --host 0.0.0.0 \
    --port 8080 \
    --ctx-size 2048 \
    --threads 2 \
    --log-format text \
    --verbose > /tmp/llama.log 2>&1 &
LLAMA_PID=\$!

echo "📋 llama-server PID: \$LLAMA_PID"

# Wait for llama-server to be ready (longer wait time)
echo "⏳ Waiting for llama-server to initialize..."
MAX_WAIT=45
for i in \$(seq 1 \$MAX_WAIT); do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ llama-server is ready!"
        break
    fi
    if [ \$i -eq \$MAX_WAIT ]; then
        echo "❌ llama-server failed to start within \$MAX_WAIT seconds"
        echo "📋 Last 10 lines of llama-server log:"
        tail -10 /tmp/llama.log || echo "No log file found"
        kill \$LLAMA_PID 2>/dev/null || true
        exit 1
    fi
    echo "   Waiting... (\$i/\$MAX_WAIT)"
    sleep 2
done

# Initialize RAG system
echo "📚 Initializing RAG system..."
cd /app/rag
if python3 rag_simple.py reindex; then
    echo "✅ RAG system initialized successfully"
else
    echo "❌ RAG system initialization failed"
    exit 1
fi

# Verify ChromaDB has collections
echo "🔍 Verifying ChromaDB collections..."
python3 -c "
import chromadb
from chromadb.config import Settings
import os

try:
    chroma = chromadb.PersistentClient(path='chroma_db', settings=Settings(anonymized_telemetry=True))
    collections = chroma.list_collections()
    ampai_collections = [col for col in collections if col.name.startswith('ampai_sources')]
    print(f'Found {len(ampai_collections)} ampai collections: {[c.name for c in ampai_collections]}')
    if len(ampai_collections) == 0:
        print('ERROR: No collections found!')
        exit(1)
    else:
        latest_collection = max(ampai_collections, key=lambda x: x.name)
        collection = chroma.get_collection(latest_collection.name)
        count = collection.count()
        print(f'Latest collection: {latest_collection.name} with {count} documents')
except Exception as e:
    print(f'ERROR: ChromaDB verification failed: {e}')
    exit(1)
"

# Start Flask
echo "🌐 Starting Flask web server..."
cd /app/rag
python3 web_chat.py &
FLASK_PID=\$!

echo "📋 Flask PID: \$FLASK_PID"

# Wait for Flask to be ready
echo "⏳ Waiting for Flask..."
for i in {1..30}; do
    if curl -s http://localhost:\$PORT/health > /dev/null 2>&1; then
        echo "✅ Flask is ready!"
        break
    fi
    if [ \$i -eq 30 ]; then
        echo "❌ Flask failed to start within 30 seconds"
        kill \$FLASK_PID 2>/dev/null || true
        exit 1
    fi
    echo "   Waiting... (\$i/30)"
    sleep 1
done

# Final verification
echo "🔍 Final system check..."
curl -s http://localhost:8080/health && echo "✅ llama-server responding" || echo "❌ llama-server not responding"
curl -s http://localhost:\$PORT/api/status && echo "✅ Flask API responding" || echo "❌ Flask API not responding"

echo "🚀 AmpAI is fully operational!"
echo "📋 Services running:"
echo "   - Flask web server on port \$PORT"
echo "   - llama-server on port 8080"
echo "   - ChromaDB with RAG collections ready"

# Keep the container running
wait \$FLASK_PID
EOF

RUN chmod +x /app/start.sh

# Health check - will use Railway's PORT environment variable
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

CMD ["/app/start.sh"]
