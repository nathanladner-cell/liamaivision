#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, session
import openai
import os
import chromadb
from chromadb.config import Settings
import uuid
from datetime import datetime
import time
import subprocess
import tempfile
import sys
import socket
from dotenv import load_dotenv

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

RESPONSE STYLE:
- Professional yet approachable
- Use technical terms appropriately for the audience
- Include practical tips and safety considerations
- Be confident without being arrogant
- Focus on helping the user solve their specific problem

Current User Question: {message}

Context Information:
{context_specific_instructions}

Provide a direct, helpful response based on the context above."""

def get_collection():
    try:
        # Try to disable all ChromaDB telemetry
        import os
        os.environ['CHROMA_TELEMETRY_ENABLED'] = 'false'
        os.environ['ANONYMIZED_TELEMETRY'] = 'false'

        # Try to use database backend if available
        db_url = os.environ.get('DATABASE_URL')
        if db_url and 'postgresql' in db_url:
            print(f"Using PostgreSQL database for ChromaDB backend")
            # For ChromaDB with PostgreSQL, we need to use a different approach
            # Let's use a hybrid approach: keep local files but sync to database
            settings = Settings(anonymized_telemetry=False)
            chroma = chromadb.PersistentClient(path=DB_DIR, settings=settings)
        else:
            print("Using local file storage for ChromaDB")
            settings = Settings(anonymized_telemetry=False)
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
                    # Reindex failed to create collections
                    print("Warning: No collections found after reindexing")
                    return None
            except Exception as reindex_error:
                # Automatic reindex failed
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

class MockCollection:
    """Mock collection for fallback when ChromaDB fails"""
    def count(self):
        return 0

    def query(self, *args, **kwargs):
        return {"documents": [], "metadatas": []}

def query_rag(question):
    """Query the RAG system for relevant content"""
    try:
        col = get_collection()
        if not col:
            # Fallback to mock collection if ChromaDB fails
            print("Using fallback mock collection due to ChromaDB issues")
            return "I apologize, but the knowledge base is currently unavailable. However, I can still help you with general questions about electrical safety standards and calibration procedures based on my training. What would you like to know?"
        
        # Use ChromaDB's default embeddings for querying
        results = col.query(
            query_texts=[question], 
            n_results=3,  # Increased back to 3 for better coverage
            include=['documents', 'metadatas', 'distances']
        )
        
        if results['documents'] and results['documents'][0]:
            # Get the most relevant documents
            documents = results['documents'][0]
            distances = results['distances'][0] if results['distances'] else [1.0] * len(documents)
            
            # Filter documents by relevance (distance < 1.5)
            relevant_docs = []
            for doc, dist in zip(documents, distances):
                if dist < 1.5:
                    # Truncate very long documents to prevent massive prompts
                    if len(doc) > 400:
                        doc = doc[:400] + "..."
                    relevant_docs.append(doc)
            
            if relevant_docs:
                # Return the most relevant document
                return relevant_docs[0]
            else:
                return "No highly relevant information found in your sources. Try rephrasing your question."
        else:
            return "No relevant information found in your sources. Try rephrasing your question."
    except Exception as e:
        print(f"Error in query_rag: {e}")
        return f"Error querying RAG system: {e}"

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

@app.route('/video/liamaicreepy.mp4')
def serve_video():
    """Serve the video file"""
    video_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'liamaicreepy.mp4')
    if os.path.exists(video_path):
        from flask import send_file
        return send_file(video_path, mimetype='video/mp4')
    else:
        return "Video not found", 404

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
        if "No relevant information found" in rag_content or "No highly relevant information" in rag_content:
            context_instructions = """Available Information:
No relevant information found in sources.

Instructions: If the question is unclear, ask for clarification. If you need more context, ask for it. Help the user understand what information you need to provide a helpful answer."""
        else:
            context_instructions = f"""Available Information:
{rag_content}

Instructions: Analyze the provided information intelligently. If the question is incomplete or unclear, ask for clarification. If you can answer based on the sources, provide a comprehensive response that synthesizes the relevant information."""

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
                max_tokens=200,
                temperature=0.7
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
        
        # Check RAG system
        rag_status = "error"
        rag_details = "Not available"
        try:
            col = get_collection()
            if col:
                count = col.count()
                if count > 0:
                    rag_status = "ready"
                    rag_details = f"Ready ({count} documents)"
                else:
                    rag_status = "error"
                    rag_details = "Empty collection"
            else:
                rag_status = "error"
                rag_details = "No collection found"
        except Exception as e:
            rag_status = "error"
            rag_details = f"Error: {str(e)[:50]}"
        
        # Check if web server is running (we're already here, so it's ready)
        web_status = "ready"
        web_details = "Ready"
        
        # Determine overall system status
        overall_status = "ready" if (openai_status == "ready" and rag_status == "ready") else "loading"

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
