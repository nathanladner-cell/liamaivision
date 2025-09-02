#!/usr/bin/env python3
import chromadb
from chromadb.config import Settings
import os

DB_DIR = os.path.join(os.path.dirname(__file__), 'chroma_db')
print(f"Checking database at: {DB_DIR}")

try:
    chroma = chromadb.PersistentClient(path=DB_DIR, settings=Settings(anonymized_telemetry=True))

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
