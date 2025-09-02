#!/usr/bin/env python3
"""
Vector Database Module for Liam AI Assistant
Supports multiple backends: ChromaDB (local), Qdrant (self-hosted), and PostgreSQL
"""

import os
import json
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod

# Import vector database clients
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class VectorDatabase(ABC):
    """Abstract base class for vector databases"""

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the vector database"""
        pass

    @abstractmethod
    def create_collection(self, name: str) -> bool:
        """Create a new collection"""
        pass

    @abstractmethod
    def add_documents(self, collection_name: str, documents: List[str], metadata: List[Dict], ids: List[str]) -> bool:
        """Add documents to collection"""
        pass

    @abstractmethod
    def search(self, collection_name: str, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar documents"""
        pass

    @abstractmethod
    def list_collections(self) -> List[str]:
        """List all collections"""
        pass

    @abstractmethod
    def delete_collection(self, name: str) -> bool:
        """Delete a collection"""
        pass


class QdrantVectorDB(VectorDatabase):
    """Qdrant-based vector database implementation"""

    def __init__(self, url: str = "http://localhost:6333"):
        self.url = url
        self.client = None
        self.collection_name = "liam_rag_collection"

    def initialize(self) -> bool:
        """Initialize Qdrant connection"""
        if not QDRANT_AVAILABLE:
            print("Qdrant client not available")
            return False

        try:
            self.client = QdrantClient(url=self.url)
            # Test connection
            self.client.get_collections()
            print(f"✅ Connected to Qdrant at {self.url}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Qdrant: {e}")
            return False

    def create_collection(self, name: str) -> bool:
        """Create a new collection in Qdrant"""
        if not self.client:
            return False

        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]

            if name in collection_names:
                print(f"Collection '{name}' already exists")
                return True

            # Create collection with vector configuration
            self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            print(f"✅ Created Qdrant collection: {name}")
            return True
        except Exception as e:
            print(f"❌ Failed to create collection: {e}")
            return False

    def add_documents(self, collection_name: str, documents: List[str], metadata: List[Dict], ids: List[str]) -> bool:
        """Add documents to Qdrant collection"""
        if not self.client:
            return False

        try:
            # For simplicity, we'll use basic embeddings (you might want to use a proper embedding model)
            # In production, use sentence-transformers or OpenAI embeddings
            vectors = []
            for i, doc in enumerate(documents):
                # Simple hash-based vector (replace with proper embeddings)
                vector = [hash(word) % 1000 / 1000.0 for word in doc.split()[:10]]
                vector.extend([0.0] * (384 - len(vector)))  # Pad to 384 dimensions
                vectors.append(vector[:384])

            points = [
                PointStruct(
                    id=doc_id,
                    vector=vector,
                    payload={"text": doc, **meta}
                )
                for doc_id, vector, doc, meta in zip(ids, vectors, documents, metadata)
            ]

            self.client.upsert(collection_name=collection_name, points=points)
            print(f"✅ Added {len(documents)} documents to {collection_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to add documents: {e}")
            return False

    def search(self, collection_name: str, query: str, limit: int = 5) -> List[Dict]:
        """Search Qdrant collection"""
        if not self.client:
            return []

        try:
            # Simple query vector (replace with proper embeddings)
            query_vector = [hash(word) % 1000 / 1000.0 for word in query.split()[:10]]
            query_vector.extend([0.0] * (384 - len(query_vector)))
            query_vector = query_vector[:384]

            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit
            )

            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "text": hit.payload.get("text", ""),
                    "metadata": {k: v for k, v in hit.payload.items() if k != "text"}
                }
                for hit in results
            ]
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []

    def list_collections(self) -> List[str]:
        """List Qdrant collections"""
        if not self.client:
            return []

        try:
            collections = self.client.get_collections()
            return [c.name for c in collections.collections]
        except Exception as e:
            print(f"❌ Failed to list collections: {e}")
            return []

    def delete_collection(self, name: str) -> bool:
        """Delete Qdrant collection"""
        if not self.client:
            return False

        try:
            self.client.delete_collection(name)
            print(f"✅ Deleted collection: {name}")
            return True
        except Exception as e:
            print(f"❌ Failed to delete collection: {e}")
            return False


class ChromaVectorDB(VectorDatabase):
    """ChromaDB-based vector database (fallback)"""

    def __init__(self, persist_dir: str = "./chroma_db"):
        self.persist_dir = persist_dir
        self.client = None
        self.collection_name = "liam_rag_collection"

    def initialize(self) -> bool:
        """Initialize ChromaDB connection"""
        if not CHROMA_AVAILABLE:
            print("ChromaDB not available")
            return False

        try:
            import os
            os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'
            os.environ['ANONYMIZED_TELEMETRY'] = 'false'
            os.environ['CHROMA_TELEMETRY_IMPL'] = 'none'
            os.environ['CHROMA_POSTHOG_DISABLED'] = 'true'
            
            settings = Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
            self.client = chromadb.PersistentClient(path=self.persist_dir, settings=settings)
            print(f"✅ Connected to ChromaDB at {self.persist_dir}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to ChromaDB: {e}")
            return False

    def create_collection(self, name: str) -> bool:
        """Create ChromaDB collection"""
        if not self.client:
            return False

        try:
            self.client.get_or_create_collection(name)
            print(f"✅ Created ChromaDB collection: {name}")
            return True
        except Exception as e:
            print(f"❌ Failed to create collection: {e}")
            return False

    def add_documents(self, collection_name: str, documents: List[str], metadata: List[Dict], ids: List[str]) -> bool:
        """Add documents to ChromaDB collection"""
        if not self.client:
            return False

        try:
            collection = self.client.get_collection(collection_name)
            collection.add(
                documents=documents,
                metadatas=metadata,
                ids=ids
            )
            print(f"✅ Added {len(documents)} documents to {collection_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to add documents: {e}")
            return False

    def search(self, collection_name: str, query: str, limit: int = 5) -> List[Dict]:
        """Search ChromaDB collection"""
        if not self.client:
            return []

        try:
            collection = self.client.get_collection(collection_name)
            results = collection.query(
                query_texts=[query],
                n_results=limit
            )

            response = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    response.append({
                        "id": results['ids'][0][i] if results['ids'] else f"doc_{i}",
                        "score": results['distances'][0][i] if results['distances'] else 0.0,
                        "text": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {}
                    })

            return response
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []

    def list_collections(self) -> List[str]:
        """List ChromaDB collections"""
        if not self.client:
            return []

        try:
            collections = self.client.list_collections()
            return [c.name for c in collections]
        except Exception as e:
            print(f"❌ Failed to list collections: {e}")
            return []

    def delete_collection(self, name: str) -> bool:
        """Delete ChromaDB collection"""
        if not self.client:
            return False

        try:
            self.client.delete_collection(name)
            print(f"✅ Deleted collection: {name}")
            return True
        except Exception as e:
            print(f"❌ Failed to delete collection: {e}")
            return False


def get_vector_db() -> VectorDatabase:
    """Factory function to get the appropriate vector database"""

    # Try Qdrant first (preferred for self-hosted)
    qdrant_url = os.environ.get('QDRANT_URL', 'http://localhost:6333')
    if QDRANT_AVAILABLE:
        db = QdrantVectorDB(qdrant_url)
        if db.initialize():
            print("🎯 Using Qdrant as vector database")
            return db

    # Fallback to ChromaDB
    if CHROMA_AVAILABLE:
        db = ChromaVectorDB("./chroma_db")
        if db.initialize():
            print("📁 Using ChromaDB as vector database")
            return db

    # Last resort - mock database
    print("⚠️  No vector database available, using mock implementation")
    return None


# Global vector database instance
_vector_db = None

def init_vector_db() -> bool:
    """Initialize the vector database"""
    global _vector_db
    _vector_db = get_vector_db()

    if _vector_db:
        # Create default collection
        _vector_db.create_collection("liam_rag_collection")
        return True

    return False

def get_vector_database() -> Optional[VectorDatabase]:
    """Get the initialized vector database"""
    return _vector_db


if __name__ == "__main__":
    # Test the vector database
    if init_vector_db():
        db = get_vector_database()
        if db:
            print("✅ Vector database initialized successfully")
            collections = db.list_collections()
            print(f"📚 Available collections: {collections}")
        else:
            print("❌ Failed to get vector database")
    else:
        print("❌ Failed to initialize vector database")

