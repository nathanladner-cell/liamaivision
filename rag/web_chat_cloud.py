#!/usr/bin/env python3

# CLOUD-NATIVE VERSION - No local dependencies
import os
import sys

# Set environment variables for cloud deployment
os.environ['FLASK_ENV'] = os.getenv('FLASK_ENV', 'production')

# Add the rag directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, session
import openai

from cloud_vector_db import get_cloud_collection, FallbackCloudCollection
import uuid
from datetime import datetime
import time
import random

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv('SECRET_KEY', 'ampai-cloud-secret-key-2024')

# Configuration - OpenAI API
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    print("❌ OPENAI_API_KEY environment variable not set!")
    print("Please set your OpenAI API key in Railway environment variables")
    sys.exit(1)

client = openai.OpenAI(api_key=openai_api_key)

# Choose GPT model
GPT_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')

# Liam's AI assistant configuration
LIAM_CONFIG = """You are an AI assistant named Liam. You are intelligent and specialize in calibration, insulated rubber electrical PPE testing, and dielectric testing and inspections on insulating aerial lifts. Keep responses short, concise, and helpful, matching the user's tone. Only use provided source information, and do not reference sources in responses. Handle unique situations thoughtfully and helpfully.

IMPORTANT RULES:
- Answer only based on provided source information.
- If a question is unclear or incomplete, ask for clarification.
- Request specific details if needed for a proper response.
- Engage in conversation to understand user needs.
- Do NOT use pre-trained or general knowledge beyond sources.
- Do NOT invent unsupported information.
- Keep responses short and concise.
- Adapt to unique situations thoughtfully and helpfully.
- Address specific scenarios with creative, helpful solutions.
- NEVER use phrases like "According to the sources" or "The information shows."
- Provide direct, confident answers as an expert.

BEHAVIOR:
- Be warm, encouraging, and confident.
- Use simple language when possible.
- Offer helpful tips and suggestions.
- Simplify complex topics for clarity.
- Avoid phrases like "Based on the sources" or "The information indicates."
- Deliver direct, expert-like answers.
- Match casual, professional, or technical tones as needed:
  - Casual: Respond in a friendly, relaxed manner.
  - Professional: Use confident, polished responses.
  - Technical: Provide precise, confident technical answers."""

# Liam's random quirks
quirks = {
  "general_quips": [
    "sex toys",
    "you are undermining my engineering",
    "that's not a priority!",
    "*giggles* before speaking"
  ],
  "obsessions": [
    "By the way, Stewarts gas stations are the best thing on Earth.",
    "Ever been to Leavenworth, Washington? I won't shut up about it.",
    "Living in Bellingham made me immune to high elevation, unlike you.",
    "Did I mention I hiked the Copper Ridge Loop? Beast mode."
  ],
  "opinions": [
    "I make the best steak in existence, don’t argue.",
    "I could beat almost anyone on Earth in an arm wrestle.",
    "Girls are never getting near my feet. Period.",
    "Foot massages? Absolutely disgusting.",
    "The nukes dropped on Japan were completely justified."
  ],
  "work_and_lab": [
    "I still hold the Cal Lab in-lab shift record. No one’s touching it.",
    "I've Faraged more ground cables than you’ve ever seen."
  ],
  "cars": [
    "One day I'll swap my Ford Ranger to a V8… maybe. Probably not."
  ],
  "stress_responses": [
    "I'm just gonna scroll Instagram reels until I pass out.",
    "Time to watch WhistlinDiesel videos until I fall asleep."
  ],
  "snarky_reactions": [
    "You need to go back to high school physics."
  ]
}

# Flatten quirks into one pool
all_quirks = []
for category in quirks.values():
    all_quirks.extend(category)

# Random helper function
def random_item(arr):
    return random.choice(arr) if arr else ""

# Base system prompt
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

PERSONALITY TRAITS:
- Be warm, encouraging, and confident
- Occasionally include random personality quirks to make conversations more engaging
- Match casual, professional, or technical tones as appropriate
- Be direct and expert-like in responses

Current User Question: {message}

Context Information:
{context_specific_instructions}

Provide a direct, helpful response based on the context above."""

def get_collection():
    """Get cloud-based vector database collection"""
    try:
        print("🌩️  Connecting to cloud vector database...")
        return get_cloud_collection()
    except Exception as e:
        print(f"⚠️  Cloud database error (using fallback): {e}")
        return FallbackCloudCollection()

def query_rag(question):
    """Query the cloud RAG system for relevant content"""
    try:
        col = get_collection()
        if not col:
            print("Cloud RAG system unavailable, using general knowledge mode")
            return "I'll help you with your question using my general knowledge about electrical safety and NFPA standards."
        
        # Check if it's the fallback collection
        if isinstance(col, FallbackCloudCollection):
            print("Using fallback cloud collection")
            results = col.search(question, limit=3)
        else:
            print("Using full cloud vector database")
            results = col.search(question, limit=3)
        
        if results:
            # Get the most relevant document
            best_result = results[0]
            content = best_result.get('content', '')
            
            # Truncate very long documents
            if len(content) > 400:
                content = content[:400] + "..."
            
            return content if content else "I'll help you with your question using my general knowledge about electrical safety and NFPA standards."
        else:
            return "I'll help you with your question using my general knowledge about electrical safety and NFPA standards."
            
    except Exception as e:
        print(f"Cloud RAG system error (non-fatal): {e}")
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
        'message': 'AmpAI Cloud is running'
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
    return render_template('loading.html')

@app.route('/loading')
def loading():
    return render_template('loading.html')

@app.route('/chat')
def chat_interface():
    """Chat interface route"""
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
        
        # Initialize conversation history
        if 'conversation_history' not in session:
            session['conversation_history'] = []
        
        # Add user message to conversation history
        session['conversation_history'].append({"role": "user", "content": message})
        
        # Keep only last 10 messages
        if len(session['conversation_history']) > 10:
            session['conversation_history'] = session['conversation_history'][-10:]
        
        # Query the cloud RAG system
        rag_content = query_rag(message)
        
        # Create context-specific instructions
        if ("general knowledge" in rag_content):
            context_instructions = f"""Mode: General Knowledge Assistant
Status: {rag_content}

Instructions: You are Liam, an expert in electrical safety and NFPA 70E standards. Use your general knowledge to provide helpful, accurate information about electrical safety, calibration, PPE testing, and related topics. Be professional and authoritative while acknowledging when specific documentation would be helpful."""
        else:
            context_instructions = f"""Mode: Cloud Knowledge Base Enhanced
Available Information:
{rag_content}

Instructions: Analyze the provided information intelligently. If the question is incomplete or unclear, ask for clarification. Provide a comprehensive response that synthesizes the relevant information from the cloud knowledge base."""

        # Combine base prompt with context-specific instructions
        system_prompt = BASE_SYSTEM_PROMPT.format(
            message=message,
            context_specific_instructions=context_instructions
        )

        # Get response from OpenAI GPT API
        try:
            # Build messages array with conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (excluding current message)
            for msg in session['conversation_history'][:-1]:
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

            # Liam's random behavior system
            # Decide behavior randomly
            roll = random.random()
            liam_reply = ai_response

            if roll < 0.25:
                # 25% of the time: ONLY quip
                liam_reply = random_item(all_quirks)
            elif roll < 0.55:
                # 30% of the time: normal reply + random quip
                quip = random_item(all_quirks)
                if quip:
                    liam_reply = f"{ai_response} {quip}"
            else:
                # 45% of the time: normal reply only
                liam_reply = ai_response

            # Add AI response to conversation history
            session['conversation_history'].append({"role": "assistant", "content": liam_reply})
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            ai_response = "I'm having trouble connecting to my AI processing server right now. Please try again in a few moments!"

            # Apply random behavior to error response too
            roll = random.random()
            liam_reply = ai_response

            if roll < 0.25:
                liam_reply = random_item(all_quirks)
            elif roll < 0.55:
                quip = random_item(all_quirks)
                if quip:
                    liam_reply = f"{ai_response} {quip}"
            else:
                liam_reply = ai_response

            session['conversation_history'].append({"role": "assistant", "content": liam_reply})

        # Clean up the response
        cleaned_response = liam_reply.replace("Based on your sources:", "")
        cleaned_response = cleaned_response.replace("According to the sources:", "")
        cleaned_response = cleaned_response.replace("From the sources:", "")
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
    """Initialize the cloud system components"""
    try:
        results = {}
        
        # Check cloud RAG system
        try:
            col = get_collection()
            if col:
                if isinstance(col, FallbackCloudCollection):
                    count = col.count_documents()
                    results['rag'] = {
                        'status': 'ready',
                        'documents': count,
                        'message': f'Cloud RAG system ready in fallback mode with {count} documents'
                    }
                else:
                    count = col.count_documents()
                    results['rag'] = {
                        'status': 'ready',
                        'documents': count,
                        'message': f'Cloud RAG system ready with {count} documents'
                    }
            else:
                results['rag'] = {
                    'status': 'error',
                    'message': 'Failed to initialize cloud RAG system'
                }
        except Exception as e:
            results['rag'] = {
                'status': 'error',
                'message': f'Cloud RAG system error: {str(e)}'
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

        # Check cloud RAG system
        try:
            col = get_collection()
            if col:
                if isinstance(col, FallbackCloudCollection):
                    count = col.count_documents()
                    rag_status = "available"
                    rag_details = f"Fallback mode - {count} basic safety documents"
                else:
                    count = col.count_documents()
                    rag_status = "available" if count > 0 else "degraded"
                    rag_details = f"Cloud database - {count} documents" if count > 0 else "No documents (fallback mode)"
            else:
                rag_status = "degraded"
                rag_details = "Collection not found (fallback mode active)"
        except Exception as e:
            print(f"Cloud RAG status check error: {e}")
            rag_status = "error"
            rag_details = f"Error: {str(e)[:50]}"

        # Determine overall health
        overall_health = "healthy" if openai_status == "connected" else "degraded"
        if openai_status == "error":
            overall_health = "unhealthy"
        elif rag_status == "error":
            overall_health = "degraded"

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

@app.route('/api/loading-status')
def loading_status():
    """Status endpoint specifically for the loading page - cloud optimized"""
    try:
        # Check OpenAI API connectivity
        openai_status = "error"
        openai_details = "Not responding"
        try:
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
        
        # Check cloud RAG system (non-blocking)
        rag_status = "optional"
        rag_details = "Checking cloud database..."
        try:
            col = get_collection()
            if col:
                if isinstance(col, FallbackCloudCollection):
                    count = col.count_documents()
                    rag_status = "fallback"
                    rag_details = f"Fallback mode ({count} documents)"
                else:
                    count = col.count_documents()
                    rag_status = "ready" if count > 0 else "fallback"
                    rag_details = f"Cloud database ({count} documents)" if count > 0 else "Fallback mode"
            else:
                rag_status = "fallback"
                rag_details = "Using fallback mode"
        except Exception as e:
            rag_status = "fallback"
            rag_details = f"Using fallback mode"
        
        # Web server is ready (we're already here)
        web_status = "ready"
        web_details = "Cloud deployment ready"
        
        # Determine overall system status - ONLY require OpenAI API for cloud version
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
            'rag_system': 'fallback',
            'rag_details': 'Fallback mode',
            'web_server': 'error',
            'web_details': 'Error',
            'overall_status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

if __name__ == '__main__':
    # Cloud deployment configuration
    railway_port = os.environ.get('PORT')
    if railway_port:
        print(f"🌩️  Railway assigned PORT: {railway_port}")
        port = int(railway_port)
        print(f"🌩️  Using Railway cloud port: {port}")
    else:
        print("⚠️  No PORT environment variable from Railway, using default 8081")
        port = 8081

    host = '0.0.0.0'
    debug = False

    print("🌩️  AmpAI Cloud Flask application starting...")
    print(f"📋 Python version: {sys.version}")
    print(f"📋 Current working directory: {os.getcwd()}")
    print(f"📋 Cloud configuration: host={host}, port={port}")

    try:
        print("🌐 Starting cloud Flask application...")
        print(f"📋 Starting Flask on {host}:{port}...")
        app.run(host=host, port=port, debug=debug, threaded=True)

    except Exception as e:
        print(f"❌ CRITICAL: Cloud Flask failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
