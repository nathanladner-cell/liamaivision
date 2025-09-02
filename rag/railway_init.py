#!/usr/bin/env python3
"""
Railway-specific initialization script for vector database
Ensures ChromaDB is properly set up before the web app starts
"""

import os
import sys
import time

def initialize_for_railway():
    """Initialize the vector database for Railway deployment"""

    print("🚂 Railway Vector Database Initialization")
    print("=" * 50)

    # Set environment variables for Railway
    os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'
    os.environ['ANONYMIZED_TELEMETRY'] = 'false'

    try:
        # Check if sources directory exists
        sources_dir = os.path.join(os.path.dirname(__file__), '..', 'sources')
        if not os.path.exists(sources_dir):
            print(f"❌ Sources directory not found: {sources_dir}")
            return False

        print(f"✅ Sources directory found: {sources_dir}")

        # Count source files
        jsonl_files = [f for f in os.listdir(sources_dir) if f.endswith('.jsonl')]
        print(f"📚 Found {len(jsonl_files)} source files: {jsonl_files}")

        if not jsonl_files:
            print("❌ No JSONL source files found")
            return False

        # Import and initialize ChromaDB
        import chromadb
        from chromadb.config import Settings

        db_dir = os.path.join(os.path.dirname(__file__), 'chroma_db')
        os.makedirs(db_dir, exist_ok=True)

        print(f"📊 Initializing ChromaDB at: {db_dir}")

        settings = Settings(anonymized_telemetry=False)
        chroma = chromadb.PersistentClient(path=db_dir, settings=settings)

        # Check existing collections
        collections = chroma.list_collections()
        existing_collections = [c.name for c in collections]
        print(f"📋 Existing collections: {existing_collections}")

        # Look for collections with documents
        valid_collections = []
        for col_name in existing_collections:
            if col_name.startswith('ampai_sources'):
                try:
                    collection = chroma.get_collection(col_name)
                    count = collection.count()
                    if count > 0:
                        valid_collections.append((col_name, count))
                        print(f"✅ Found collection with {count} documents: {col_name}")
                except Exception as e:
                    print(f"⚠️  Error checking collection {col_name}: {e}")

        if valid_collections:
            # Use the collection with most documents
            best_collection = max(valid_collections, key=lambda x: x[1])
            print(f"🎯 Using existing collection: {best_collection[0]} ({best_collection[1]} documents)")
            return True

        # No valid collections found, create new one
        print("🔄 No valid collections found, creating new collection...")

        from rag_simple import simple_reindex
        print("🏗️  Running reindex process...")
        simple_reindex()

        # Verify the new collection
        time.sleep(2)  # Give it a moment
        collections = chroma.list_collections()
        new_collections = [c.name for c in collections if c.name.startswith('ampai_sources')]

        if new_collections:
            latest_collection = max(new_collections)
            collection = chroma.get_collection(latest_collection)
            count = collection.count()
            print(f"✅ New collection created: {latest_collection} ({count} documents)")
            return True
        else:
            print("❌ Failed to create new collection")
            return False

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = initialize_for_railway()
    if success:
        print("\n🎉 Railway initialization completed successfully!")
        print("The vector database is ready for the web application.")
        sys.exit(0)
    else:
        print("\n❌ Railway initialization failed!")
        print("The web application may not function properly.")
        sys.exit(1)
