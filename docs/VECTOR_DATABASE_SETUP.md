# Vector Database Setup Guide

This guide explains how to set up a self-hosted vector database for the Liam AI Assistant RAG system.

## 🚀 Quick Setup Options

### Option 1: Railway + Built-in Vector Database (Recommended)
Railway handles everything automatically - no additional setup required.

### Option 2: Railway + Qdrant (Advanced)
For dedicated vector database performance:

1. **Deploy Qdrant on Railway:**
   ```bash
   # Railway Dashboard → New Project
   # Choose "Empty Project"
   # Add Qdrant service
   ```

2. **Environment Variables:**
   ```
   QDRANT_URL=https://your-qdrant-service.railway.app
   OPENAI_API_KEY=your_key_here
   ```

### Option 3: Local Development with Docker

```bash
# Start Qdrant locally
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.7.4

# Set environment variable
export QDRANT_URL=http://localhost:6333

# Initialize database
cd rag
python3 init_vector_db.py
```

## 🏗️ Architecture

### Supported Vector Databases:

1. **Qdrant** (Recommended)
   - High-performance vector search
   - REST and gRPC APIs
   - Persistent storage
   - Scalable architecture

2. **ChromaDB** (Fallback)
   - Local file-based storage
   - Simple setup
   - Good for development

3. **PostgreSQL + pgvector** (Enterprise)
   - ACID compliance
   - Advanced querying
   - Enterprise features

## 🔧 Configuration

### Environment Variables

```bash
# Qdrant Configuration
QDRANT_URL=http://localhost:6333

# PostgreSQL Configuration (if using pgvector)
DATABASE_URL=postgresql://user:password@localhost:5432/liam_db

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Vector Database Settings
VECTOR_DB_TYPE=qdrant  # or chromadb or postgres
COLLECTION_NAME=liam_rag_collection
```

### Railway Setup

1. **Go to Railway Dashboard**
2. **Select your Liam project**
3. **Go to Variables tab**
4. **Add these variables:**
   ```
   OPENAI_API_KEY → your_openai_api_key_here
   QDRANT_URL → https://your-qdrant-service.railway.app (if using Qdrant)
   VECTOR_DB_TYPE → qdrant
   ```

## 📊 Database Schema

### Collection Structure

```json
{
  "collection_name": "liam_rag_collection",
  "vector_size": 384,
  "distance_metric": "cosine",
  "documents": [
    {
      "id": "source_file_0",
      "vector": [0.1, 0.2, ...],
      "payload": {
        "text": "Document content...",
        "source": "nfpa70e.jsonl",
        "chunk_index": 0,
        "metadata": {
          "title": "NFPA 70E Standards",
          "category": "Electrical Safety"
        }
      }
    }
  ]
}
```

## 🔄 Data Flow

1. **Document Processing:**
   - Load JSONL files from `sources/` directory
   - Split into chunks
   - Generate embeddings
   - Store in vector database

2. **Query Processing:**
   - User submits question
   - Generate query embedding
   - Search vector database
   - Retrieve relevant documents
   - Send to OpenAI with context

3. **Response Generation:**
   - OpenAI GPT generates response
   - Include retrieved documents as context
   - Return formatted response

## 📈 Performance Optimization

### Indexing Strategies

1. **Chunk Size:** 500-1000 tokens per chunk
2. **Overlap:** 50-100 tokens between chunks
3. **Embedding Model:** Sentence Transformers or OpenAI
4. **Index Type:** HNSW for Qdrant

### Query Optimization

1. **Top-K Retrieval:** 3-5 most relevant documents
2. **Re-ranking:** Optional re-ranking with cross-encoders
3. **Caching:** Cache frequent queries
4. **Batch Processing:** Process multiple queries together

## 🛠️ Maintenance

### Regular Tasks

1. **Re-indexing:**
   ```bash
   cd rag
   python3 init_vector_db.py
   ```

2. **Backup:**
   ```bash
   # For Qdrant
   docker exec qdrant_container qdrant-backup create
   ```

3. **Monitoring:**
   - Check Railway logs
   - Monitor API usage
   - Verify vector search performance

### Troubleshooting

1. **Connection Issues:**
   ```
   # Check Qdrant status
   curl http://localhost:6333/health

   # Check Railway variables
   echo $QDRANT_URL
   ```

2. **Indexing Problems:**
   ```
   # Reinitialize database
   cd rag
   rm -rf ../chroma_db
   python3 init_vector_db.py
   ```

3. **Performance Issues:**
   ```
   # Check Railway metrics
   # Monitor memory usage
   # Adjust chunk sizes
   ```

## 🚀 Deployment Checklist

- [ ] Vector database service deployed
- [ ] Environment variables configured
- [ ] Database initialized with documents
- [ ] Application can connect to database
- [ ] Search functionality working
- [ ] Performance optimized
- [ ] Backup strategy in place

## 📞 Support

For vector database issues:
1. Check Railway deployment logs
2. Verify environment variables
3. Test database connectivity
4. Review initialization scripts

The vector database setup ensures your RAG system is scalable, reliable, and independent of local file storage! 🎯

