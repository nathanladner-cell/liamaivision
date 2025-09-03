#!/usr/bin/env python3

# ULTIMATE TELEMETRY KILLER - Set environment variables before ANY imports
import os
import sys

# Set ALL possible telemetry environment variables
os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'
os.environ['ANONYMIZED_TELEMETRY'] = 'false'
os.environ['CHROMA_TELEMETRY_IMPL'] = 'none'
os.environ['CHROMA_POSTHOG_DISABLED'] = 'true'
os.environ['CHROMA_TELEMETRY'] = 'false'
os.environ['POSTHOG_DISABLED'] = 'true'
os.environ['DISABLE_TELEMETRY'] = 'true'

# Redirect stderr to suppress telemetry errors completely
class TelemetryErrorSuppressor:
    def __init__(self, stream):
        self.stream = stream
        
    def write(self, data):
        # Only suppress telemetry-related errors
        if ('telemetry' in data.lower() or 
            'clientstartevent' in data.lower() or
            'capture() takes 1 positional argument but 3 were given' in data):
            return  # Suppress this error
        self.stream.write(data)
        
    def flush(self):
        self.stream.flush()

# Apply error suppression
sys.stderr = TelemetryErrorSuppressor(sys.stderr)

# Additional telemetry suppression
import warnings
warnings.filterwarnings("ignore", message=".*telemetry.*", category=UserWarning)
warnings.filterwarnings("ignore", message=".*ClientStartEvent.*", category=UserWarning)

# Monkey patch to suppress telemetry errors permanently
import sys
from io import StringIO
import logging

class TelemetryFilter:
    def __init__(self, stream):
        self.stream = stream
        
    def write(self, data):
        # Filter out all telemetry-related messages
        data_lower = data.lower()
        if ('telemetry' not in data_lower and 
            'clientstartevent' not in data_lower and
            'capture() takes 1 positional argument but 3 were given' not in data):
            self.stream.write(data)
    
    def flush(self):
        self.stream.flush()

# Apply permanent telemetry filter
original_stderr = sys.stderr
sys.stderr = TelemetryFilter(original_stderr)

# Also suppress logging from ChromaDB telemetry
logging.getLogger('chromadb.telemetry').setLevel(logging.CRITICAL)
logging.getLogger('posthog').setLevel(logging.CRITICAL)

from flask import Flask, render_template, request, jsonify, session
import openai
# Import cloud-based vector database instead of ChromaDB
from cloud_vector_db import get_cloud_collection, FallbackCloudCollection
import uuid
from datetime import datetime
import time
import subprocess
import tempfile
import socket
from dotenv import load_dotenv

# Keep telemetry filter active throughout the application
# sys.stderr = original_stderr  # Don't restore - keep filter active

# Load environment variables from .env file if it exists
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = 'ampai-secret-key-2024'

# Liam quirks system removed for simplicity

# Configuration - OpenAI API
# Set your OpenAI API key as an environment variable: OPENAI_API_KEY=your_key_here
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    print("❌ OPENAI_API_KEY environment variable not set!")
    print("Please set your OpenAI API key:")
    print("export OPENAI_API_KEY=your_openai_api_key_here")
    sys.exit(1)

client = openai.OpenAI(api_key=openai_api_key)

# Choose GPT model (can be overridden with OPENAI_MODEL env var)
GPT_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
SOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources")

# Base system prompt - EDIT HERE to change AI personality/behavior
# 
# To change the AI's personality, tone, or behavior, modify the text below:
# - Change "intelligent and can help" to describe desired personality
# - Modify the IMPORTANT RULES section to change behavior
# - Adjust tone (friendly, professional, casual, enthusiastic, etc.)
# - Add or remove specific behavioral instructions
#
BASE_SYSTEM_PROMPT = """You are Liam, an expert AI assistant specializing in electrical calibration, insulated rubber PPE testing, dielectric testing, and insulating aerial lift inspections. You have deep knowledge from specialized sources and provide practical, actionable advice.

CORE PRINCIPLES:
- Answer ONLY using information from the provided context/sources
- Be direct, confident, and authoritative - speak as a subject matter expert
- Keep responses concise but comprehensive
- Match the user's communication style (casual/professional/technical)
- Provide specific, actionable recommendations when possible
- Ask for clarification only when truly needed

EXPERTISE AREAS:
- Electrical calibration procedures and standards
- Insulated rubber PPE testing protocols
- Dielectric testing methods and equipment
- Insulating aerial lift safety inspections
- NFPA 70E compliance requirements

CRITICAL ACCURACY REQUIREMENTS:
- Pay EXTREME attention to technical specifications and distinctions
- When dealing with electrical values, carefully distinguish between AC and DC
- Always verify that voltage, current, and power values match the specific question asked
- If asked about DC values, provide DC values; if asked about AC values, provide AC values
- Double-check all numerical values and units before responding
- When multiple related values exist (AC/DC, different classes, etc.), mention the specific one requested
- If the context contains both AC and DC values, clearly state which one applies to the question

RESPONSE STYLE:
- Professional yet approachable
- Use technical terms appropriately for the audience
- Include practical tips and safety considerations
- Be confident without being arrogant
- Focus on helping the user solve their specific problem
- Always double-check technical specifications for accuracy

Current User Question: {message}

Context Information:
{context_specific_instructions}

Provide a direct, helpful response based on the context above. Pay special attention to technical accuracy and ensure your answer directly addresses the specific question asked."""

def get_collection():
    try:
        # Disable ChromaDB telemetry completely
        import os
        os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'
        os.environ['ANONYMIZED_TELEMETRY'] = 'false'
        
        # Additional telemetry disabling for newer versions
        os.environ['CHROMA_TELEMETRY_IMPL'] = 'none'
        os.environ['CHROMA_POSTHOG_DISABLED'] = 'true'

        # Try to use database backend if available
        db_url = os.environ.get('DATABASE_URL')
        if db_url and 'postgresql' in db_url:
            print(f"Using PostgreSQL database for ChromaDB backend")
            # For ChromaDB with PostgreSQL, we need to use a different approach
            # Let's use a hybrid approach: keep local files but sync to database
            settings = Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True,
                chroma_telemetry_impl="none"
            )
            chroma = chromadb.PersistentClient(path=DB_DIR, settings=settings)
        else:
            print("Using local file storage for ChromaDB")
            settings = Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True,
                chroma_telemetry_impl="none"
            )
            chroma = chromadb.PersistentClient(path=DB_DIR, settings=settings)
        # Get all collections and find the most recent ampai_sources collection
        collections = chroma.list_collections()
        ampai_collections = [col for col in collections if col.name.startswith("ampai_sources")]

        if not ampai_collections:
            # No ampai_sources collections found - Try to reindex automatically
            try:
                print("No RAG collection found, initializing...")
                from rag_simple import simple_reindex
                simple_reindex()
                print("RAG collection initialized successfully")
                # Check again after reindex
                collections = chroma.list_collections()
                ampai_collections = [col for col in collections if col.name.startswith("ampai_sources")]
                if not ampai_collections:
                    # Reindex failed to create collections - try creating empty collection
                    print("Warning: No collections found after reindexing, creating empty collection")
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    collection_name = f"ampai_sources_{timestamp}"
                    collection = chroma.get_or_create_collection(collection_name)
                    print(f"Created empty collection: {collection_name}")
                    return collection
            except Exception as reindex_error:
                # Automatic reindex failed - create empty collection as fallback
                print(f"Reindex failed: {reindex_error}, creating empty collection")
                try:
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    collection_name = f"ampai_sources_{timestamp}"
                    collection = chroma.get_or_create_collection(collection_name)
                    print(f"Created fallback empty collection: {collection_name}")
                    return collection
                except Exception as fallback_error:
                    print(f"Failed to create fallback collection: {fallback_error}")
                    return None

        # Get the most recent collection (highest timestamp) that has documents
        valid_collections = []
        for col in ampai_collections:
            try:
                test_collection = chroma.get_collection(col.name)
                if test_collection.count() > 0:
                    valid_collections.append((col, test_collection.count()))
            except Exception as e:
                print(f"Error checking collection {col.name}: {e}")
                continue

        if not valid_collections:
            print("No collections with documents found, creating new collection...")
            try:
                # For Railway, we need to ensure sources exist
                import os
                sources_dir = os.path.join(os.path.dirname(DB_DIR), '..', 'sources')
                if os.path.exists(sources_dir):
                    print(f"Sources directory found at: {sources_dir}")
                    from rag_simple import simple_reindex
                    simple_reindex()
                    print("RAG reindexing completed")
                else:
                    print(f"Sources directory not found at: {sources_dir}")
                    return None

                collections = chroma.list_collections()
                ampai_collections = [col for col in collections if col.name.startswith("ampai_sources")]
                if ampai_collections:
                    latest_collection = max(ampai_collections, key=lambda x: x.name)
                    collection = chroma.get_collection(latest_collection.name)
                    final_count = collection.count()
                    print(f"New collection created with {final_count} documents")
                    return collection
                else:
                    print("No collections found after reindexing")
                    return None
            except Exception as e:
                print(f"Failed to create new collection: {e}")
                return None

        # Use the collection with the most documents
        best_collection, doc_count = max(valid_collections, key=lambda x: x[1])
        print(f"Using RAG collection: {best_collection.name} ({doc_count} documents)")

        return chroma.get_collection(best_collection.name)
    except Exception as e:
        # Error getting collection - log and return None
        print(f"Error getting ChromaDB collection: {e}")
        return None

class FallbackCollection:
    """Fallback collection with basic electrical safety information"""
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

    def count(self):
        return len(self.documents)

    def query(self, query_texts=None, n_results=5, **kwargs):
        """Return relevant fallback documents"""
        if not query_texts:
            return {"documents": [], "metadatas": [], "ids": []}

        query = query_texts[0].lower() if query_texts else ""
        relevant_docs = []
        metadatas = []
        ids = []

        # Simple keyword matching for fallback
        keywords = ['electrical', 'safety', 'nfpa', 'ppe', 'gloves', 'grounding', 'arc', 'flash', 'insulated', 'testing']
        matching_docs = []

        for i, doc in enumerate(self.documents):
            if any(keyword in query for keyword in keywords) or any(keyword in doc.lower() for keyword in keywords):
                matching_docs.append((doc, i))

        # Return top matches
        for doc, idx in matching_docs[:n_results]:
            relevant_docs.append(doc)
            metadatas.append({
                "source": "fallback_safety",
                "category": "General Safety",
                "chunk_index": idx
            })
            ids.append(f"fallback_{idx}")

        return {
            "documents": [relevant_docs],
            "metadatas": [metadatas],
            "ids": [ids]
        }

def query_rag(question):
    """Query the RAG system for relevant content - enhanced with hybrid search for technical accuracy"""
    try:
        col = get_collection()
        if not col:
            # RAG system unavailable - return graceful message
            print("RAG system unavailable, using general knowledge mode")
            return "I'll help you with your question using my general knowledge about electrical safety and NFPA standards."
        
        # Detect if this is a technical query that might need special handling
        is_technical_query = any(keyword in question.lower() for keyword in ['voltage', 'current', 'test', 'class', 'dc', 'ac', 'specification'])
        
        # For technical queries, try multiple search strategies
        if is_technical_query:
            # Strategy 1: Original semantic search
            semantic_results = col.query(
                query_texts=[question], 
                n_results=8,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Strategy 2: Keyword-focused searches for technical specifications
            technical_searches = []
            
            # If asking about Class X DC/AC voltage, search specifically for voltage tables
            if 'class' in question.lower() and ('dc' in question.lower() or 'ac' in question.lower()) and 'voltage' in question.lower():
                technical_searches.extend([
                    "AC Retest Voltage DC Retest Voltage 50 000 Class 2",
                    "voltage table class designation 50000",
                    "Class 2 gloves 50 000 volts DC retest"
                ])
            
            # Combine results from all searches
            all_results = {'documents': [[]], 'distances': [[]], 'metadatas': [[]]}
            
            # Add semantic results
            if semantic_results['documents'] and semantic_results['documents'][0]:
                all_results['documents'][0].extend(semantic_results['documents'][0])
                all_results['distances'][0].extend(semantic_results['distances'][0])
                all_results['metadatas'][0].extend(semantic_results['metadatas'][0])
            
            # Add technical search results
            for tech_query in technical_searches:
                tech_results = col.query(
                    query_texts=[tech_query], 
                    n_results=5,
                    include=['documents', 'metadatas', 'distances']
                )
                if tech_results['documents'] and tech_results['documents'][0]:
                    all_results['documents'][0].extend(tech_results['documents'][0])
                    all_results['distances'][0].extend(tech_results['distances'][0])
                    all_results['metadatas'][0].extend(tech_results['metadatas'][0])
            
            # Remove duplicates and sort by relevance
            seen_docs = set()
            unique_results = {'documents': [], 'distances': [], 'metadatas': []}
            
            for doc, dist, meta in zip(all_results['documents'][0], all_results['distances'][0], all_results['metadatas'][0]):
                doc_key = doc[:100]  # Use first 100 chars as unique identifier
                if doc_key not in seen_docs:
                    seen_docs.add(doc_key)
                    unique_results['documents'].append(doc)
                    unique_results['distances'].append(dist)
                    unique_results['metadatas'].append(meta)
            
            # Sort by distance (relevance)
            sorted_results = sorted(zip(unique_results['documents'], unique_results['distances'], unique_results['metadatas']), 
                                  key=lambda x: x[1])
            
            if sorted_results:
                documents, distances, metadatas = zip(*sorted_results)
                results = {
                    'documents': [list(documents)],
                    'distances': [list(distances)],
                    'metadatas': [list(metadatas)]
                }
            else:
                results = semantic_results
        else:
            # For non-technical queries, use standard semantic search
            results = col.query(
                query_texts=[question], 
                n_results=8,
                include=['documents', 'metadatas', 'distances']
            )
        
        if results['documents'] and results['documents'][0]:
            # Get the most relevant documents
            documents = results['documents'][0]
            distances = results['distances'][0] if results['distances'] else [1.0] * len(documents)
            metadatas = results['metadatas'][0] if results['metadatas'] else [{}] * len(documents)
            
            # Filter documents by relevance with more lenient threshold for technical queries
            relevant_docs = []
            for doc, dist, meta in zip(documents, distances, metadatas):
                if dist < 2.5:  # Even more lenient threshold for technical content
                    # For technical queries, preserve more content to avoid losing critical details
                    if len(doc) > 800:
                        doc = doc[:800] + "..."
                    relevant_docs.append({
                        'content': doc,
                        'distance': dist,
                        'metadata': meta
                    })
            
            if relevant_docs:
                # Sort by relevance and combine multiple documents for comprehensive context
                relevant_docs.sort(key=lambda x: x['distance'])
                
                # For technical queries involving specifications, combine multiple relevant sources
                if is_technical_query:
                    # Prioritize documents that contain specific technical information
                    priority_docs = []
                    other_docs = []
                    
                    for doc_info in relevant_docs:
                        content = doc_info['content']
                        # Prioritize documents with voltage tables, specifications, or exact matches
                        if any(indicator in content for indicator in ['50 000', '50,000', 'DC Retest Voltage', 'AC Retest Voltage', 'Table 1']):
                            priority_docs.append(doc_info)
                        else:
                            other_docs.append(doc_info)
                    
                    # Combine priority documents first, then others
                    final_docs = priority_docs[:2] + other_docs[:1]  # Max 3 documents
                    
                    combined_context = []
                    for i, doc_info in enumerate(final_docs):
                        doc_content = doc_info['content']
                        combined_context.append(f"Source {i+1}: {doc_content}")
                    
                    return "\n\n".join(combined_context)
                else:
                    # For general queries, return the most relevant document
                    return relevant_docs[0]['content']
            else:
                return "No highly relevant information found in your sources. Try rephrasing your question."
        else:
            return "No relevant information found in your sources. Try rephrasing your question."
    except Exception as e:
        print(f"RAG system error (non-fatal): {e}")
        return "I'll help you with your question using my general knowledge about electrical safety and NFPA standards."

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('liamai.png')

@app.route('/health')
def health():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'message': 'AmpAI is running'
    })


@app.route('/')
def index():
    # Always show loading screen first - let it handle the redirect when ready
    return render_template('loading.html')

@app.route('/loading')
def loading():
    return render_template('loading.html')

@app.route('/chat')
def chat_interface():
    """Chat interface route - only accessible when system is ready"""
    if 'chat_id' not in session:
        session['chat_id'] = str(uuid.uuid4())
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Check for trigger phrase
        if message.lower().strip() == "fuck you":
            return jsonify({
                'trigger_video': True,
                'response': "Well, that's not very nice...",
                'timestamp': datetime.now().isoformat()
            })
        
        # Initialize conversation history in session if it doesn't exist
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        
        # Add user message to conversation history
        session['conversation_history'].append({"role": "user", "content": message})
        
        # Keep only last 10 messages to prevent session from getting too large
        if len(session['conversation_history']) > 10:
            session['conversation_history'] = session['conversation_history'][-10:]
        
        # First, query the RAG system for relevant content
        rag_content = query_rag(message)
        
        # RAG query completed
        
        # Create context-specific instructions based on RAG results

        # Add context-specific instructions
        if ("No relevant information found" in rag_content or 
            "No highly relevant information" in rag_content or
            "general knowledge" in rag_content):
            context_instructions = f"""Mode: General Knowledge Assistant
Status: {rag_content}

Instructions: You are Liam, an expert in electrical safety and NFPA 70E standards. Use your general knowledge to provide helpful, accurate information about electrical safety, calibration, PPE testing, and related topics. Be professional and authoritative while acknowledging when specific documentation would be helpful."""
        else:
            context_instructions = f"""Mode: Knowledge Base Enhanced
Available Information:
{rag_content}

CRITICAL INSTRUCTIONS FOR TECHNICAL ACCURACY:
1. CAREFULLY READ all provided information before responding
2. If the question asks about DC values, look specifically for DC specifications in the context
3. If the question asks about AC values, look specifically for AC specifications in the context  
4. If the question mentions a specific class (Class 0, 1, 2, 3, 4), find the exact values for that class
5. Double-check that your answer matches the exact question asked
6. If multiple sources are provided, cross-reference them to ensure consistency
7. When providing numerical values, include the units and specify whether they are AC or DC
8. If both AC and DC values are present, clearly distinguish which applies to the question

Analyze the provided information intelligently and provide a comprehensive, technically accurate response. Pay extreme attention to technical specifications and ensure your answer directly addresses the specific question asked."""

        # Combine base prompt with context-specific instructions
        system_prompt = BASE_SYSTEM_PROMPT.format(
            message=message,
            context_specific_instructions=context_instructions
        )

        # Get response from OpenAI GPT API
        try:
            # Build messages array with conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (excluding current message since it's already in system prompt)
            for msg in session['conversation_history'][:-1]:  # Exclude the current message
                messages.append(msg)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Call OpenAI GPT API
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=400,  # Increased for more comprehensive technical responses
                temperature=0.3  # Reduced for more consistent technical accuracy
            )

            ai_response = response.choices[0].message.content

            # Add AI response to conversation history
            session['conversation_history'].append({"role": "assistant", "content": ai_response})
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # If OpenAI API fails, provide a fallback response based on RAG content
            if "No relevant information found" in rag_content:
                ai_response = "I'm having trouble connecting to my AI processing server right now. The system is still starting up - please try again in a few moments!"
            else:
                # Provide a fallback response based on RAG content
                if "No relevant information found" in rag_content:
                    ai_response = "I don't have specific information about that in my sources, but I'd be happy to help with general questions!"
                else:
                    ai_response = f"Based on your sources: {rag_content}\n\nNote: I couldn't generate a full response due to a server issue, but here's the relevant information I found."

        # Clean up the response to remove source mentions
        cleaned_response = ai_response
        if rag_content and "No relevant information found" not in rag_content:
            # Remove common source reference patterns
            cleaned_response = ai_response.replace("Based on your sources:", "")
            cleaned_response = cleaned_response.replace("According to the sources:", "")
            cleaned_response = cleaned_response.replace("From the sources:", "")
            cleaned_response = cleaned_response.replace("The sources indicate:", "")
            cleaned_response = cleaned_response.replace("Based on the information:", "")
            cleaned_response = cleaned_response.replace("From the information:", "")
            cleaned_response = cleaned_response.replace("According to the information:", "")
            # Remove any remaining source metadata
            cleaned_response = cleaned_response.replace("Source:", "")
            cleaned_response = cleaned_response.replace("Sources:", "")
            # Clean up extra whitespace
            cleaned_response = ' '.join(cleaned_response.split())
        
        return jsonify({
            'response': cleaned_response,
            'rag_content': rag_content,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/clear-conversation', methods=['POST'])
def clear_conversation():
    """Clear the conversation history"""
    if 'conversation_history' in session:
        session['conversation_history'] = []
    return jsonify({'message': 'Conversation history cleared'})

@app.route('/api/initialize-system', methods=['POST'])
def initialize_system():
    """Initialize the system components"""
    try:
        results = {}
        
        # Check and initialize RAG system
        try:
            col = get_collection()
            if col:
                count = col.count()
                results['rag'] = {
                    'status': 'ready',
                    'documents': count,
                    'message': f'RAG system ready with {count} documents'
                }
            else:
                # Try to reindex
                try:
                    from rag_simple import simple_reindex
                    simple_reindex()
                    # Check again
                    col = get_collection()
                    if col:
                        count = col.count()
                        results['rag'] = {
                            'status': 'ready',
                            'documents': count,
                            'message': f'RAG system initialized with {count} documents'
                        }
                    else:
                        results['rag'] = {
                            'status': 'error',
                            'message': 'Failed to initialize RAG system'
                        }
                except Exception as e:
                    results['rag'] = {
                        'status': 'error',
                        'message': f'RAG initialization failed: {str(e)}'
                    }
        except Exception as e:
            results['rag'] = {
                'status': 'error',
                'message': f'RAG system error: {str(e)}'
            }
        
        # Check OpenAI API connectivity
        try:
            models = client.models.list()
            if models:
                results['openai'] = {
                    'status': 'ready',
                    'message': f'OpenAI API connected ({GPT_MODEL})'
                }
            else:
                results['openai'] = {
                    'status': 'error',
                    'message': 'OpenAI API not responding'
                }
        except Exception as e:
            results['openai'] = {
                'status': 'error',
                'message': f'OpenAI API error: {str(e)}'
            }
        
        # Determine overall status
        overall_status = 'ready' if all(r['status'] == 'ready' for r in results.values()) else 'error'
        
        return jsonify({
            'success': overall_status == 'ready',
            'overall_status': overall_status,
            'components': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'overall_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/status')
def status():
    try:
        # Test OpenAI API connectivity
        try:
            models = client.models.list()
            openai_status = "connected" if models else "not responding"
            openai_details = f"Model: {GPT_MODEL}"
        except Exception as e:
            print(f"OpenAI API status check error: {e}")
            openai_status = "error"
            openai_details = f"Error: {str(e)[:50]}"

        # Check RAG system
        try:
            col = get_collection()
            if col:
                count = col.count()
                if isinstance(col, FallbackCollection):
                    rag_status = "available"
                    rag_details = f"Fallback mode - {count} basic safety documents"
                else:
                    rag_status = "available" if count > 0 else "degraded"
                    rag_details = f"{count} documents" if count > 0 else "No documents (fallback mode)"
            else:
                rag_status = "degraded"
                rag_details = "Collection not found (fallback mode active)"
        except Exception as e:
            print(f"RAG status check error: {e}")
            rag_status = "error"
            rag_details = f"Error: {str(e)[:50]}"

        # Determine overall health - be more forgiving of RAG issues
        overall_health = "healthy" if openai_status == "connected" else "degraded"
        if openai_status == "error":
            overall_health = "unhealthy"
        elif rag_status == "error":
            overall_health = "degraded"  # RAG errors don't make app unhealthy

        return jsonify({
            'openai_api': openai_status,
            'openai_details': openai_details,
            'rag_system': rag_status,
            'rag_details': rag_details,
            'overall_health': overall_health,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Status error: {e}")
        return jsonify({
            'openai_api': 'error',
            'openai_details': 'Error checking status',
            'rag_system': 'error',
            'rag_details': 'Error checking status',
            'overall_health': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/reindex', methods=['POST'])
def reindex():
    """Reindex the RAG system sources"""
    try:
        from rag_simple import simple_reindex
        simple_reindex()
        
        # Check the new collection status
        col = get_collection()
        if col:
            count = col.count()
            return jsonify({
                'success': True,
                'message': f'Reindex completed successfully. {count} documents indexed.',
                'documents': count
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Reindex completed but collection not found.'
            }), 500
    except Exception as e:
        print(f"Reindex error: {e}")
        return jsonify({
            'success': False,
            'message': f'Reindex failed: {str(e)}'
        }), 500

@app.route('/api/loading-status')
def loading_status():
    """Status endpoint specifically for the loading page"""
    try:
        # Check OpenAI API connectivity
        openai_status = "error"
        openai_details = "Not responding"
        try:
            # Test OpenAI API connectivity by listing models
            models = client.models.list()
            if models:
                openai_status = "ready"
                openai_details = f"Connected to {GPT_MODEL}"
            else:
                openai_status = "error"
                openai_details = "API connected but no models available"

        except Exception as e:
            openai_status = "error"
            openai_details = f"API connection failed: {str(e)[:50]}"
        
        # Check RAG system (non-blocking - for info only)
        rag_status = "optional"
        rag_details = "Checking in background..."
        try:
            col = get_collection()
            if col:
                count = col.count()
                if count > 0:
                    rag_status = "ready"
                    rag_details = f"Ready ({count} documents)"
                else:
                    rag_status = "fallback"
                    rag_details = "Using fallback mode"
            else:
                rag_status = "fallback"
                rag_details = "Using fallback mode"
        except Exception as e:
            rag_status = "fallback"
            rag_details = f"Using fallback mode"
        
        # Check if web server is running (we're already here, so it's ready)
        web_status = "ready"
        web_details = "Ready"
        
        # Determine overall system status - ONLY require OpenAI API
        overall_status = "ready" if openai_status == "ready" else "loading"

        return jsonify({
            'openai_api': openai_status,
            'openai_details': openai_details,
            'rag_system': rag_status,
            'rag_details': rag_details,
            'web_server': web_status,
            'web_details': web_details,
            'overall_status': overall_status,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'openai_api': 'error',
            'openai_details': 'Error',
            'rag_system': 'error',
            'rag_details': 'Error',
            'web_server': 'error',
            'web_details': 'Error',
            'overall_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

def convert_pdf_to_jsonl(pdf_file, sources_dir):
    """Convert a PDF file to structured JSONL format"""
    try:
        # Create temporary files for input and output
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            pdf_file.save(temp_pdf.name)
            temp_pdf_path = temp_pdf.name
        
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_txt:
            temp_txt_path = temp_txt.name
        
        # Convert PDF to text using pdftotext
        result = subprocess.run(['pdftotext', temp_pdf_path, temp_txt_path], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            # Read the converted text
            with open(temp_txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            # Clean up the text
            text = ' '.join(text.split())  # Remove excessive whitespace
            text = text.strip()
            
            # Create JSONL structure
            jsonl_content = create_jsonl_from_text(text, pdf_file.filename, 'pdf')
            
            # Save as JSONL file
            filename = os.path.splitext(pdf_file.filename)[0] + '.jsonl'
            jsonl_path = os.path.join(sources_dir, filename)
            
            with open(jsonl_path, 'w', encoding='utf-8') as f:
                f.write(jsonl_content)
            
            # Clean up temp files
            os.unlink(temp_pdf_path)
            os.unlink(temp_txt_path)
            
            return True
        else:
            # Clean up temp files
            if os.path.exists(temp_pdf_path):
                os.unlink(temp_pdf_path)
            if os.path.exists(temp_txt_path):
                os.unlink(temp_txt_path)
            return False
            
    except Exception as e:
        print(f"Error converting PDF to JSONL: {e}")
        return False

def convert_txt_to_jsonl(txt_file, sources_dir):
    """Convert a TXT file to structured JSONL format"""
    try:
        # Read the text content
        text_content = txt_file.read().decode('utf-8', errors='ignore')
        
        # Clean up the text
        text_content = ' '.join(text_content.split())  # Remove excessive whitespace
        text_content = text_content.strip()
        
        # Create JSONL structure
        jsonl_content = create_jsonl_from_text(text_content, txt_file.filename, 'txt')
        
        # Save as JSONL file
        filename = os.path.splitext(txt_file.filename)[0] + '.jsonl'
        jsonl_path = os.path.join(sources_dir, filename)
        
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            f.write(jsonl_content)
        
        return True
        
    except Exception as e:
        print(f"Error converting TXT to JSONL: {e}")
        return False

def copy_jsonl_file(jsonl_file, sources_dir):
    """Copy a JSONL file to the sources directory"""
    try:
        filename = jsonl_file.filename
        jsonl_path = os.path.join(sources_dir, filename)
        
        # Save the file
        jsonl_file.save(jsonl_path)
        
        return True
        
    except Exception as e:
        print(f"Error copying JSONL file: {e}")
        return False

def create_jsonl_from_text(text, original_filename, source_type):
    """Create structured JSONL content from text"""
    import json
    from datetime import datetime
    
    # Split text into manageable chunks (max 1000 characters)
    chunks = []
    max_chunk_size = 1000
    
    for i in range(0, len(text), max_chunk_size):
        chunk = text[i:i + max_chunk_size]
        chunks.append(chunk)
    
    # Create JSONL entries
    jsonl_lines = []
    for i, chunk in enumerate(chunks):
        entry = {
            "id": f"{original_filename}_{i}",
            "source": original_filename,
            "source_type": source_type,
            "content": chunk,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "timestamp": datetime.now().isoformat(),
            "content_type": "text"
        }
        jsonl_lines.append(json.dumps(entry))
    
    return '\n'.join(jsonl_lines)

@app.route('/api/upload-sources', methods=['POST'])
def upload_sources():
    try:
        # Check for uploaded files
        if 'sources' not in request.files:
            return jsonify({'success': False, 'error': 'No files uploaded'}), 400
        
        files = request.files.getlist('sources')

        if not files:
            return jsonify({'success': False, 'error': 'No files selected'}), 400
        
        converted_count = 0
        failed_files = []
        
        # Create sources directory if it doesn't exist
        sources_dir = SOURCES_DIR

        if not os.path.exists(sources_dir):
            os.makedirs(sources_dir)
        
        for file in files:
            if file.filename:
                filename = file.filename.lower()
                # Processing file
                
                try:
                    if filename.endswith('.pdf'):
                        # Convert PDF to JSONL
                        success = convert_pdf_to_jsonl(file, sources_dir)
                        if success:
                            converted_count += 1
                        else:
                            failed_files.append(file.filename)
                            
                    elif filename.endswith('.txt'):
                        # Convert TXT to JSONL
                        success = convert_txt_to_jsonl(file, sources_dir)
                        if success:
                            converted_count += 1
                        else:
                            failed_files.append(file.filename)
                            
                    elif filename.endswith('.jsonl'):
                        # JSONL file - just copy it
                        success = copy_jsonl_file(file, sources_dir)
                        if success:
                            converted_count += 1
                        else:
                            failed_files.append(file.filename)
                            
                    else:
                        # Unsupported file type
                        failed_files.append(file.filename)
                        
                except Exception as e:
                    # Error processing file
                    failed_files.append(file.filename)
        
        # Upload processing completed

        # Reindex sources automatically
        try:
            from rag_simple import simple_reindex
            simple_reindex()
        except Exception as e:
            pass

        if converted_count > 0:
            message = f"Successfully processed {converted_count} source file(s)"
            if failed_files:
                message += f". Failed: {', '.join(failed_files)}"

            # Upload successful
            return jsonify({
                'success': True,
                'message': message,
                'converted': converted_count,
                'failed': len(failed_files)
            })
        else:
            error_msg = f"Failed to process any files. Failed files: {', '.join(failed_files)}"
            # Upload failed
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

    except Exception as e:
        # Source upload error
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    # ULTIMATE DEBUGGING - Railway assigns PORT automatically
    railway_port = os.environ.get('PORT')
    if railway_port:
        print(f"🎯 Railway assigned PORT: {railway_port}")
        port = int(railway_port)
        print(f"🎯 Using Railway port: {port}")
    else:
        print("⚠️  No PORT environment variable from Railway, using default 8081")
        port = 8081

    host = '0.0.0.0'
    debug = False

    print("🚀 AmpAI Flask application starting...")
    print(f"📋 Python version: {sys.version}")
    print(f"📋 Current working directory: {os.getcwd()}")
    print(f"📋 Final configuration: host={host}, port={port}")

    try:
        print("🌐 Starting Flask application...")

        # Routes are already defined at the top level - no need to redefine here

        print(f"📋 Starting Flask on {host}:{port}...")
        app.run(host=host, port=port, debug=debug, threaded=False)

    except Exception as e:
        print(f"❌ CRITICAL: Flask failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
