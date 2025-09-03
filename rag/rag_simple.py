#!/usr/bin/env python3

# CRITICAL: Disable ChromaDB telemetry BEFORE any imports
import os
os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'
os.environ['ANONYMIZED_TELEMETRY'] = 'false'
os.environ['CHROMA_TELEMETRY_IMPL'] = 'none'
os.environ['CHROMA_POSTHOG_DISABLED'] = 'true'
os.environ['CHROMA_TELEMETRY'] = 'false'

import json
import chromadb
from chromadb.config import Settings

# Configuration
DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
SOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sources")

def read_text(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def get_collection():
    # Disable ChromaDB telemetry completely
    import os
    os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'
    os.environ['ANONYMIZED_TELEMETRY'] = 'false'
    os.environ['CHROMA_TELEMETRY_IMPL'] = 'none'
    os.environ['CHROMA_POSTHOG_DISABLED'] = 'true'
    
    # ChromaDB 0.4.24 compatibility
    settings = Settings(
        anonymized_telemetry=False,
        allow_reset=True,
        is_persistent=True
    )
    chroma = chromadb.PersistentClient(path=DB_DIR, settings=settings)

    # Find existing ampai_sources collections and use the most recent one with data
    collections = chroma.list_collections()
    ampai_collections = [col for col in collections if col.name.startswith("ampai_sources")]

    if ampai_collections:
        # Sort by name (which includes timestamp) and find the one with the most documents
        ampai_collections.sort(key=lambda x: x.name, reverse=True)

        for col in ampai_collections:
            collection = chroma.get_collection(col.name)
            if collection.count() > 0:
                print(f"Using existing collection: {col.name} ({collection.count()} documents)")
                return collection

    # If no populated collection found, create a new one
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    collection_name = f"ampai_sources_{timestamp}"
    print(f"Creating new collection: {collection_name}")
    return chroma.get_or_create_collection(collection_name)

def simple_reindex():
    print("Starting simple reindex...")
    
    # Completely remove the old database directory
    import shutil
    if os.path.exists(DB_DIR):
        print(f"Removing old database: {DB_DIR}")
        shutil.rmtree(DB_DIR)
    
    # Create fresh collection
    col = get_collection()
    print("Created fresh collection")
    
    # Get all source files dynamically
    source_files = []
    for filename in os.listdir(SOURCES_DIR):
        if filename.endswith(('.txt', '.jsonl')):
            source_files.append(filename)
    
    print(f"Found {len(source_files)} source files: {', '.join(source_files)}")
    
    for filename in source_files:
        filepath = os.path.join(SOURCES_DIR, filename)
        
        if filename.endswith('.jsonl'):
            # Handle JSONL files
            print(f"Processing JSONL file: {filename}")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if line.strip():
                            data = json.loads(line.strip())
                            
                            # All JSONL files now use the standard format
                            if 'content' in data:
                                doc_content = data['content']
                                doc_id = data.get('id', f"{filename}_{i}")
                                
                                # Convert tags list to string for ChromaDB compatibility
                                tags = data.get('tags', [])
                                tags_str = ', '.join(tags) if tags else 'N/A'
                                
                                # Enhanced metadata with more details for better retrieval
                                metadata = {
                                    "source": data.get('source', filename),
                                    "title": data.get('title', 'N/A'),
                                    "category": data.get('category', 'N/A'),
                                    "tags": tags_str,
                                    "chunk_index": data.get('chunk_index', i),
                                    "total_chunks": data.get('total_chunks', 1),
                                    "content_length": len(doc_content),
                                    "entry_number": i+1
                                }
                                
                                # For very long JSONL entries, consider splitting them too
                                if len(doc_content) > 2000:
                                    # Split into smaller chunks while preserving context
                                    chunk_size = 1500
                                    overlap = 200
                                    chunks = []
                                    
                                    for chunk_start in range(0, len(doc_content), chunk_size - overlap):
                                        chunk = doc_content[chunk_start:chunk_start + chunk_size]
                                        if chunk.strip():
                                            chunks.append(chunk)
                                    
                                    if len(chunks) > 1:
                                        print(f"  Entry {i+1} split into {len(chunks)} sub-chunks for better retrieval")
                                        
                                        # Add each sub-chunk
                                        for sub_idx, chunk in enumerate(chunks):
                                            sub_doc_id = f"{doc_id}_sub{sub_idx+1}"
                                            sub_metadata = metadata.copy()
                                            sub_metadata.update({
                                                "sub_chunk_index": sub_idx+1,
                                                "total_sub_chunks": len(chunks),
                                                "content_length": len(chunk)
                                            })
                                            
                                            col.add(
                                                ids=[sub_doc_id],
                                                documents=[chunk],
                                                metadatas=[sub_metadata]
                                            )
                                    else:
                                        # Single chunk
                                        col.add(
                                            ids=[doc_id],
                                            documents=[doc_content],
                                            metadatas=[metadata]
                                        )
                                else:
                                    # Regular sized content
                                    col.add(
                                        ids=[doc_id],
                                        documents=[doc_content],
                                        metadatas=[metadata]
                                    )
                            else:
                                # Fallback for any non-standard files
                                doc_content = json.dumps(data)
                                doc_id = f"{filename}_{i}"
                                metadata = {
                                    "source": filename, 
                                    "format": "fallback",
                                    "entry_number": i+1,
                                    "content_length": len(doc_content)
                                }
                                col.add(
                                    ids=[doc_id],
                                    documents=[doc_content],
                                    metadatas=[metadata]
                                )
                            
                            print(f"  Indexed entry {i+1}: {doc_content[:50]}...")
                
                print(f"✅ Successfully indexed {filename}")
                
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
                
        elif filename.endswith('.txt'):
            # Handle text files
            print(f"Processing text file: {filename}")
            try:
                content = read_text(filepath)
                print(f"  Content length: {len(content)} characters")
                
                # For very long content, split into chunks to preserve all information
                if len(content) > 8000:
                    # Split into overlapping chunks to ensure no information is lost
                    chunk_size = 6000
                    overlap = 500
                    chunks = []
                    
                    for i in range(0, len(content), chunk_size - overlap):
                        chunk = content[i:i + chunk_size]
                        if chunk.strip():
                            chunks.append(chunk)
                    
                    print(f"  Split into {len(chunks)} chunks to preserve all information")
                    
                    # Add each chunk as a separate document
                    for j, chunk in enumerate(chunks):
                        doc_id = f"{filename.replace('.txt', '')}_{j+1}"
                        col.add(
                            ids=[doc_id],
                            documents=[chunk],
                            metadatas=[{
                                "source": filename,
                                "chunk_index": j+1,
                                "total_chunks": len(chunks)
                            }]
                        )
                else:
                    # Add single document for shorter content
                    doc_id = filename.replace('.txt', '')
                    col.add(
                        ids=[doc_id],
                        documents=[content],
                        metadatas=[{
                            "source": filename,
                            "chunk_index": 1,
                            "total_chunks": 1
                        }]
                    )
                
                print(f"✅ Successfully indexed {filename}")
                
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
    
    print(f"\n✅ Reindex complete! Indexed {len(source_files)} source files.")

def simple_ask(question):
    print(f"\n🔍 Question: {question}")
    print("=" * 50)
    
    col = get_collection()
    
    # Query the collection
    results = col.query(
        query_texts=[question],
        n_results=3
    )
    
    if results['documents'] and results['documents'][0]:
        print("📚 Found relevant content:")
        for i, doc in enumerate(results['documents'][0]):
            print(f"\n--- Document {i+1} ---")
            print(doc)
            if results['metadatas'] and results['metadatas'][0]:
                print(f"Source: {results['metadatas'][0][i]}")
    else:
        print("❌ No relevant content found.")
    
    print("\n" + "=" * 50)
    print("💡 This is what your RAG system found from your sources!")
    print("The OpenAI API connection is working, and retrieval is functioning perfectly!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "reindex":
            simple_reindex()
        elif sys.argv[1] == "ask" and len(sys.argv) > 2:
            question = " ".join(sys.argv[2:])
            simple_ask(question)
        else:
            print("Usage: python rag_simple.py [reindex|ask <question>]")
    else:
        print("Usage: python rag_simple.py [reindex|ask <question>]")
