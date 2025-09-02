#!/usr/bin/env python3
"""
Cloud Vector Database Module
Uses Pinecone for fully cloud-based vector storage and retrieval
No local dependencies - everything runs in the cloud
"""

import os
import json
import requests
from typing import List, Dict, Optional
import openai

try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

class CloudVectorDB:
    """Cloud-based vector database using Pinecone"""
    
    def __init__(self):
        self.pc = None
        self.index = None
        self.index_name = "ampai-knowledge"
        self.dimension = 1536  # OpenAI ada-002 embedding dimension
        self.openai_client = None
        
    def initialize(self) -> bool:
        """Initialize Pinecone connection"""
        if not PINECONE_AVAILABLE:
            print("❌ Pinecone client not available")
            return False
            
        # Get API keys from environment
        pinecone_api_key = os.getenv('PINECONE_API_KEY')
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not pinecone_api_key:
            print("❌ PINECONE_API_KEY not set")
            return False
            
        if not openai_api_key:
            print("❌ OPENAI_API_KEY not set")
            return False
            
        try:
            # Initialize Pinecone
            self.pc = Pinecone(api_key=pinecone_api_key)
            
            # Initialize OpenAI for embeddings
            self.openai_client = openai.OpenAI(api_key=openai_api_key)
            
            # Check if index exists, create if not
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                print(f"🔄 Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                print(f"✅ Created Pinecone index: {self.index_name}")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            print(f"✅ Connected to Pinecone index: {self.index_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize Pinecone: {e}")
            return False
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error getting embedding: {e}")
            return []
    
    def add_documents(self, documents: List[str], metadata: List[Dict], ids: List[str]) -> bool:
        """Add documents to the cloud vector database"""
        if not self.index:
            return False
            
        try:
            vectors = []
            for i, (doc, meta, doc_id) in enumerate(zip(documents, metadata, ids)):
                embedding = self.get_embedding(doc)
                if embedding:
                    vectors.append({
                        "id": doc_id,
                        "values": embedding,
                        "metadata": {
                            **meta,
                            "content": doc[:1000]  # Store first 1000 chars in metadata
                        }
                    })
            
            if vectors:
                self.index.upsert(vectors=vectors)
                print(f"✅ Added {len(vectors)} documents to cloud database")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error adding documents: {e}")
            return False
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar documents in the cloud database"""
        if not self.index:
            return []
            
        try:
            query_embedding = self.get_embedding(query)
            if not query_embedding:
                return []
                
            results = self.index.query(
                vector=query_embedding,
                top_k=limit,
                include_metadata=True
            )
            
            documents = []
            for match in results.matches:
                if match.score > 0.7:  # Only return relevant matches
                    documents.append({
                        "content": match.metadata.get("content", ""),
                        "metadata": match.metadata,
                        "score": match.score
                    })
            
            return documents
            
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return []
    
    def count_documents(self) -> int:
        """Get total number of documents in the database"""
        if not self.index:
            return 0
            
        try:
            stats = self.index.describe_index_stats()
            return stats.total_vector_count
        except Exception as e:
            print(f"Error getting document count: {e}")
            return 0
    
    def delete_all(self) -> bool:
        """Delete all documents from the index"""
        if not self.index:
            return False
            
        try:
            self.index.delete(delete_all=True)
            print("✅ Deleted all documents from cloud database")
            return True
        except Exception as e:
            print(f"❌ Error deleting documents: {e}")
            return False

class FallbackCloudCollection:
    """Fallback collection with basic electrical safety information for cloud mode"""
    
    def __init__(self):
        self.documents = [
            "Electrical safety is paramount in any workplace. Always follow NFPA 70E standards for safe electrical work practices.",
            "Personal protective equipment (PPE) must be rated for the electrical hazards present. Use insulated gloves, sleeves, and blankets as required.",
            "Before working on electrical equipment, always verify it is de-energized using proper lockout/tagout procedures.",
            "Arc flash hazards can cause severe burns. Always wear appropriate arc-rated clothing and face protection.",
            "Grounding equipment must be tested regularly to ensure proper conductivity and safety.",
            "Insulated tools and equipment should be visually inspected and electrically tested before each use.",
            "Qualified electrical workers must be properly trained and demonstrate competence in electrical safety procedures.",
            "Electrical panels and equipment rooms should be kept clean and clear of obstructions."
        ]
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Simple keyword-based search for fallback mode"""
        query_lower = query.lower()
        relevant_docs = []
        
        keywords = ['electrical', 'safety', 'nfpa', 'ppe', 'gloves', 'grounding', 'arc', 'flash', 'insulated', 'testing']
        
        for i, doc in enumerate(self.documents):
            if any(keyword in query_lower for keyword in keywords) or any(keyword in doc.lower() for keyword in keywords):
                relevant_docs.append({
                    "content": doc,
                    "metadata": {
                        "source": "fallback_safety",
                        "category": "General Safety",
                        "chunk_index": i
                    },
                    "score": 0.8
                })
        
        return relevant_docs[:limit]
    
    def count_documents(self) -> int:
        return len(self.documents)

def load_sources_from_github() -> List[Dict]:
    """Load source documents from GitHub repository"""
    sources = []
    
    # GitHub raw file URLs for your source files
    github_base = "https://raw.githubusercontent.com/nathanladner-cell/Liam/main/sources/"
    source_files = [
        "nfpa70e.jsonl",
        "cal_gloves_sleeves.jsonl", 
        "cal_grounds.jsonl",
        "cal_blankets.jsonl",
        "cal_livelinetools.jsonl"
    ]
    
    for filename in source_files:
        try:
            url = github_base + filename
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"📥 Loading {filename} from GitHub...")
                lines = response.text.strip().split('\n')
                
                for line in lines:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if 'content' in data:
                                sources.append({
                                    "content": data['content'],
                                    "metadata": {
                                        "source": data.get('source', filename),
                                        "title": data.get('title', 'N/A'),
                                        "category": data.get('category', 'N/A'),
                                        "tags": ', '.join(data.get('tags', [])) if data.get('tags') else 'N/A'
                                    },
                                    "id": data.get('id', f"{filename}_{len(sources)}")
                                })
                        except json.JSONDecodeError:
                            continue
                            
                print(f"✅ Loaded {len([s for s in sources if filename in s['id']])} documents from {filename}")
            else:
                print(f"⚠️  Could not load {filename} from GitHub (status: {response.status_code})")
                
        except Exception as e:
            print(f"⚠️  Error loading {filename}: {e}")
    
    print(f"📚 Total documents loaded from GitHub: {len(sources)}")
    return sources

def initialize_cloud_database() -> CloudVectorDB:
    """Initialize and populate the cloud vector database"""
    db = CloudVectorDB()
    
    if not db.initialize():
        print("❌ Failed to initialize cloud database")
        return None
    
    # Check if database already has documents
    doc_count = db.count_documents()
    if doc_count > 0:
        print(f"✅ Cloud database already has {doc_count} documents")
        return db
    
    # Load sources from GitHub and populate database
    print("🔄 Loading sources from GitHub and populating cloud database...")
    sources = load_sources_from_github()
    
    if sources:
        documents = [s['content'] for s in sources]
        metadata = [s['metadata'] for s in sources]
        ids = [s['id'] for s in sources]
        
        if db.add_documents(documents, metadata, ids):
            final_count = db.count_documents()
            print(f"✅ Cloud database populated with {final_count} documents")
        else:
            print("❌ Failed to populate cloud database")
    else:
        print("⚠️  No sources loaded from GitHub")
    
    return db

# Global database instance
cloud_db = None

def get_cloud_collection():
    """Get or initialize the cloud database collection"""
    global cloud_db
    
    if cloud_db is None:
        cloud_db = initialize_cloud_database()
    
    return cloud_db if cloud_db else FallbackCloudCollection()
