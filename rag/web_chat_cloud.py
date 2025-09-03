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
- REMEMBER AND REFERENCE previous parts of our conversation when relevant
- Build upon earlier topics discussed in this conversation
- Use context from previous messages to provide better follow-up answers

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
- Reference earlier conversation points when they add value
- Always double-check technical specifications for accuracy

MEMORY & CONTEXT:
- Pay attention to the full conversation history provided
- When answering follow-up questions, reference what was discussed before
- Build connections between current questions and previous topics
- Maintain conversational continuity and context awareness

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
    """Query the cloud RAG system for relevant content - enhanced with hybrid search for technical accuracy"""
    try:
        col = get_collection()
        if not col:
            print("Cloud RAG system unavailable, using general knowledge mode")
            return "I'll help you with your question using my general knowledge about electrical safety and NFPA standards."
        
        # Detect if this is a technical query that might need special handling
        is_technical_query = any(keyword in question.lower() for keyword in ['voltage', 'current', 'test', 'class', 'dc', 'ac', 'specification'])
        
        # Check if it's the fallback collection
        if isinstance(col, FallbackCloudCollection):
            print("Using fallback cloud collection")
            results = col.search(question, limit=8)
        else:
            print("Using full cloud vector database")
            # For technical queries, try multiple search strategies
            if is_technical_query:
                # Primary search
                results = col.search(question, limit=8)
                
                # Additional technical searches for voltage specifications
                if 'class' in question.lower() and ('dc' in question.lower() or 'ac' in question.lower()) and 'voltage' in question.lower():
                    technical_searches = [
                        "AC Retest Voltage DC Retest Voltage 50 000 Class 2",
                        "voltage table class designation 50000",
                        "Class 2 gloves 50 000 volts DC retest"
                    ]
                    
                    # Combine results from additional searches
                    all_results = list(results) if results else []
                    
                    for tech_query in technical_searches:
                        try:
                            tech_results = col.search(tech_query, limit=5)
                            if tech_results:
                                all_results.extend(tech_results)
                        except:
                            continue
                    
                    # Remove duplicates based on content similarity
                    seen_content = set()
                    unique_results = []
                    
                    for result in all_results:
                        content_key = result.get('content', '')[:100]  # Use first 100 chars as key
                        if content_key not in seen_content:
                            seen_content.add(content_key)
                            unique_results.append(result)
                    
                    results = unique_results
            else:
                results = col.search(question, limit=8)
        
        if results:
            # For technical queries involving specifications, combine multiple relevant sources
            if is_technical_query:
                # Prioritize documents that contain specific technical information
                priority_results = []
                other_results = []
                
                for result in results:
                    content = result.get('content', '')
                    # Prioritize documents with voltage tables, specifications, or exact matches
                    if any(indicator in content for indicator in ['50 000', '50,000', 'DC Retest Voltage', 'AC Retest Voltage', 'Table 1']):
                        priority_results.append(result)
                    else:
                        other_results.append(result)
                
                # Combine priority results first, then others
                final_results = priority_results[:2] + other_results[:1]  # Max 3 documents
                
                combined_context = []
                for i, result in enumerate(final_results):
                    content = result.get('content', '')
                    # For technical queries, preserve more content to avoid losing critical details
                    if len(content) > 800:
                        content = content[:800] + "..."
                    if content:
                        combined_context.append(f"Source {i+1}: {content}")
                
                return "\n\n".join(combined_context) if combined_context else "I'll help you with your question using my general knowledge about electrical safety and NFPA standards."
            else:
                # For general queries, return the most relevant document
                best_result = results[0]
                content = best_result.get('content', '')
                
                # Truncate very long documents for general queries
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
        
        # Keep last 20 messages for better context retention
        if len(session['conversation_history']) > 20:
            session['conversation_history'] = session['conversation_history'][-20:]
        
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
            
            # Add conversation history (excluding current message)
            for msg in session['conversation_history'][:-1]:
                messages.append(msg)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Call OpenAI GPT API with improved memory settings
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=1000,  # Increased for better responses
                temperature=0.3,  # Reduced for more consistent technical accuracy
                presence_penalty=0.1,  # Encourage diverse responses
                frequency_penalty=0.1   # Reduce repetition
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
