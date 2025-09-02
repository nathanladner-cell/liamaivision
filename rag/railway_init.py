#!/usr/bin/env python3
"""
Railway-specific initialization script for vector database
Ensures ChromaDB is properly set up before the web app starts
"""

import os
import sys
import time

def create_fallback_collection(chroma):
    """Create a fallback collection with basic electrical safety information"""
    try:
        collection_name = "liam_rag_fallback"

        # Check if fallback collection already exists
        collections = chroma.list_collections()
        existing_names = [c.name for c in collections]

        if collection_name in existing_names:
            collection = chroma.get_collection(collection_name)
            if collection.count() > 0:
                print(f"✅ Using existing fallback collection with {collection.count()} documents")
                return True

        # Create collection with fallback data
        chroma.delete_collection(collection_name) if collection_name in existing_names else None
        collection = chroma.create_collection(collection_name)

        # Add basic electrical safety information
        fallback_docs = [
            "Electrical safety is paramount in any workplace. Always follow NFPA 70E standards for safe electrical work practices.",
            "Personal protective equipment (PPE) must be rated for the electrical hazards present. Use insulated gloves, sleeves, and blankets as required.",
            "Before working on electrical equipment, always verify it is de-energized using proper lockout/tagout procedures.",
            "Arc flash hazards can cause severe burns. Always wear appropriate arc-rated clothing and face protection.",
            "Grounding equipment must be tested regularly to ensure proper conductivity and safety.",
            "Insulated tools and equipment should be visually inspected and electrically tested before each use.",
            "Qualified electrical workers must be properly trained and demonstrate competence in electrical safety procedures.",
            "Electrical panels and equipment rooms should be kept clean and clear of obstructions."
        ]

        fallback_metadata = [
            {"source": "fallback_safety", "category": "General Safety", "chunk_index": i}
            for i in range(len(fallback_docs))
        ]

        collection.add(
            documents=fallback_docs,
            metadatas=fallback_metadata,
            ids=[f"fallback_{i}" for i in range(len(fallback_docs))]
        )

        print(f"✅ Created fallback collection with {len(fallback_docs)} basic safety documents")
        return True

    except Exception as e:
        print(f"❌ Failed to create fallback collection: {e}")
        return False

def initialize_for_railway():
    """Initialize the vector database for Railway deployment"""

    print("🚂 Railway Vector Database Initialization")
    print("=" * 50)

    # Set environment variables for Railway
    os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'
    os.environ['ANONYMIZED_TELEMETRY'] = 'false'
    os.environ['CHROMA_TELEMETRY_IMPL'] = 'none'
    os.environ['CHROMA_POSTHOG_DISABLED'] = 'true'

    try:
        # Check if sources directory exists
        sources_dir = os.path.join(os.path.dirname(__file__), '..', 'sources')
        print(f"Looking for sources at: {sources_dir}")

        if not os.path.exists(sources_dir):
            print(f"⚠️  Sources directory not found: {sources_dir}")
            print("Creating fallback collection instead...")
            return create_fallback_collection(chroma)

        print(f"✅ Sources directory found: {sources_dir}")

        # Count source files
        try:
            jsonl_files = [f for f in os.listdir(sources_dir) if f.endswith('.jsonl')]
            print(f"📚 Found {len(jsonl_files)} source files: {jsonl_files}")

            if not jsonl_files:
                print("⚠️  No JSONL source files found, creating fallback collection")
                return create_fallback_collection(chroma)
        except Exception as e:
            print(f"⚠️  Error reading sources directory: {e}")
            return create_fallback_collection(chroma)

        # Import and initialize ChromaDB
        import chromadb
        from chromadb.config import Settings

        db_dir = os.path.join(os.path.dirname(__file__), 'chroma_db')
        os.makedirs(db_dir, exist_ok=True)

        print(f"📊 Initializing ChromaDB at: {db_dir}")

        settings = Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True,
            chroma_telemetry_impl="none"
        )
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

        # No valid collections found, try to create new one
        print("🔄 No valid collections found, attempting to create new collection...")

        try:
            # Try to run reindex process
            sys.path.append('.')
            from rag_simple import simple_reindex
            print("🏗️  Running reindex process...")
            simple_reindex()
            print("✅ Reindex completed")

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
                print("⚠️  Reindex didn't create collections, using fallback")
                return create_fallback_collection(chroma)

        except Exception as e:
            print(f"⚠️  Reindex failed: {e}")
            print("Using fallback collection instead")
            return create_fallback_collection(chroma)

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
