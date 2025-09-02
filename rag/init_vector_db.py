#!/usr/bin/env python3
"""
Vector Database Initialization Script
Sets up the vector database with RAG collections and documents
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.append('.')

from vector_db import get_vector_database, init_vector_db
from rag_simple import read_text


def load_source_documents():
    """Load all source documents from the sources directory"""
    sources_dir = Path('../sources')

    if not sources_dir.exists():
        print(f"❌ Sources directory not found: {sources_dir}")
        return []

    documents = []
    metadatas = []
    ids = []

    # Process each JSONL file
    for jsonl_file in sources_dir.glob('*.jsonl'):
        print(f"📖 Processing {jsonl_file.name}...")

        try:
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    if line.strip():
                        try:
                            entry = json.loads(line.strip())
                            if 'content' in entry:
                                # Clean and truncate content if too long
                                content = entry['content'].strip()
                                if len(content) > 1000:
                                    content = content[:1000] + "..."

                                documents.append(content)
                                metadatas.append({
                                    'source': entry.get('source', jsonl_file.name),
                                    'chunk_index': entry.get('chunk_index', line_num),
                                    'total_chunks': entry.get('total_chunks', 1),
                                    'title': entry.get('title', 'N/A'),
                                    'category': entry.get('category', 'N/A')
                                })
                                ids.append(f"{jsonl_file.stem}_{line_num}")
                        except json.JSONDecodeError as e:
                            print(f"⚠️  Skipping malformed JSON line {line_num} in {jsonl_file.name}: {e}")
                            continue

        except Exception as e:
            print(f"❌ Error processing {jsonl_file.name}: {e}")
            continue

    print(f"✅ Loaded {len(documents)} documents from {len(list(sources_dir.glob('*.jsonl')))} files")
    return documents, metadatas, ids


def initialize_vector_database():
    """Initialize the vector database and populate with documents"""

    print("🚀 Initializing Vector Database for Liam AI Assistant")
    print("=" * 60)

    # Initialize the vector database
    if not init_vector_db():
        print("❌ Failed to initialize vector database")
        return False

    db = get_vector_database()
    if not db:
        print("❌ No vector database available")
        return False

    collection_name = "liam_rag_collection"

    # Create collection
    if not db.create_collection(collection_name):
        print(f"❌ Failed to create collection: {collection_name}")
        return False

    # Load source documents
    print("\n📚 Loading source documents...")
    documents, metadatas, ids = load_source_documents()

    if not documents:
        print("❌ No documents found to index")
        return False

    # Add documents to collection
    print(f"\n💾 Indexing {len(documents)} documents...")
    if db.add_documents(collection_name, documents, metadatas, ids):
        print("✅ Successfully indexed all documents!")

        # Verify the collection
        collections = db.list_collections()
        print(f"📋 Available collections: {collections}")

        return True
    else:
        print("❌ Failed to index documents")
        return False


def test_vector_database():
    """Test the vector database functionality"""

    print("\n🧪 Testing Vector Database...")

    db = get_vector_database()
    if not db:
        print("❌ No vector database available for testing")
        return False

    collection_name = "liam_rag_collection"

    # Test search
    test_queries = [
        "electrical safety",
        "NFPA 70E",
        "calibration procedures",
        "insulated gloves"
    ]

    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        results = db.search(collection_name, query, limit=2)

        if results:
            print(f"✅ Found {len(results)} results:")
            for i, result in enumerate(results[:2]):
                print(f"  {i+1}. Score: {result.get('score', 'N/A'):.3f}")
                print(f"     Text: {result.get('text', '')[:100]}...")
        else:
            print("❌ No results found")

    return True


if __name__ == "__main__":
    print("Liam AI Assistant - Vector Database Setup")
    print("=" * 50)

    # Initialize database
    if initialize_vector_database():
        print("\n✅ Vector database setup completed successfully!")

        # Test the database
        test_vector_database()

        print("\n🎉 Setup complete! Your vector database is ready.")
        print("\nNext steps:")
        print("1. Start the web application: python3 web_chat.py")
        print("2. Open http://localhost:8081 in your browser")
        print("3. Test the RAG functionality with electrical safety questions")

    else:
        print("\n❌ Vector database setup failed!")
        print("Please check the error messages above and try again.")
        sys.exit(1)

