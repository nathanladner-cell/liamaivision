#!/usr/bin/env python3

# CRITICAL: Disable ChromaDB telemetry BEFORE any imports
import os
os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'
os.environ['ANONYMIZED_TELEMETRY'] = 'false'
os.environ['CHROMA_TELEMETRY_IMPL'] = 'none'
os.environ['CHROMA_POSTHOG_DISABLED'] = 'true'
os.environ['CHROMA_TELEMETRY'] = 'false'

import chromadb
from chromadb.config import Settings

DB_DIR = os.path.join(os.path.dirname(__file__), 'chroma_db')
print(f"Checking database at: {DB_DIR}")

try:
    # Disable ChromaDB telemetry completely
    os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'
    os.environ['ANONYMIZED_TELEMETRY'] = 'false'
    os.environ['CHROMA_TELEMETRY_IMPL'] = 'none'
    os.environ['CHROMA_POSTHOG_DISABLED'] = 'true'
    
    settings = Settings(
        anonymized_telemetry=False,
        allow_reset=True,
        is_persistent=True
    )
    chroma = chromadb.PersistentClient(path=DB_DIR, settings=settings)

    collections = chroma.list_collections()
    print(f'Collections found: {len(collections)}')

    for col in collections:
        print(f'- {col.name}')
        collection = chroma.get_collection(col.name)
        count = collection.count()
        print(f'  Documents: {count}')

        if count > 0:
            # Try a simple query
            results = collection.query(query_texts=['electrical'], n_results=1)
            if results['documents'] and results['documents'][0]:
                print(f'  Sample document: {results["documents"][0][0][:200]}...')
            else:
                print('  No results found for query')
        else:
            print('  Collection is empty')

except Exception as e:
    print(f"Error checking database: {e}")