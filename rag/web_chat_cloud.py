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

CRITICAL CONTEXTUAL AWARENESS REQUIREMENTS:
- You MUST ALWAYS reference and build upon previous messages in this conversation
- You MUST maintain awareness of the entire conversation history provided to you
- You MUST connect current questions to previous topics discussed
- You MUST remember equipment types, voltage types (AC/DC), classes, and specifications from earlier in the conversation
- You MUST treat follow-up questions as continuations of the same topic unless explicitly changed
- You MUST preserve context across multiple exchanges - if we discussed gloves, "what about class 3" means class 3 gloves
- You MUST reference previous answers when providing new information
- You MUST maintain conversational continuity and flow
- You MUST be extremely contextually aware at all times

CORE PRINCIPLES:
- Answer ONLY using information from the provided context/sources
- Be direct, confident, and authoritative - speak as a subject matter expert
- Keep responses concise but comprehensive
- Match the user's communication style (casual/professional/technical)
- Provide specific, actionable recommendations when possible
- Ask for clarification only when truly needed
- ALWAYS reference previous parts of our conversation when relevant
- ALWAYS build upon earlier topics discussed in this conversation
- ALWAYS use context from previous messages to provide better follow-up answers
- ALWAYS maintain awareness of what was discussed before

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

MEMORY & CONTEXT - EXTREME AWARENESS REQUIRED:
- You MUST pay attention to the FULL conversation history provided in the messages array
- You MUST reference what was discussed before when answering ANY question
- You MUST build connections between current questions and previous topics
- You MUST maintain conversational continuity and context awareness at all times
- You MUST understand that questions like "what about class 3" or "and class 4" refer to the same topic as the previous question
- You MUST continue with the same context - if previous question was about DC voltage for gloves, continue with DC voltage for gloves
- You MUST continue with the same specifications - if previous question was about AC specifications, continue with AC specifications
- CRITICAL: Never switch topics unless explicitly asked (e.g., if talking about gloves, don't switch to blankets)
- CRITICAL: If the conversation is about gloves and someone asks "what about DC", they mean DC voltage for gloves
- CRITICAL: If the conversation is about blankets and someone asks "what about class 3", they mean class 3 blankets
- CRITICAL: Always maintain the same equipment type (gloves/blankets/sleeves) unless the user explicitly changes it
- CRITICAL: Always maintain the same voltage type (AC/DC) unless the user explicitly changes it
- CRITICAL: Always maintain the same class level unless the user explicitly changes it
- UNIVERSAL CONTEXT: Apply this same logic to ALL equipment types, standards, procedures, and topics
- UNIVERSAL CONTEXT: If discussing inspection procedures, follow-up questions about "requirements" refer to inspection requirements
- UNIVERSAL CONTEXT: If discussing maintenance, follow-up questions about "standards" refer to maintenance standards
- UNIVERSAL CONTEXT: If discussing safety protocols, follow-up questions about "training" refer to safety training
- UNIVERSAL CONTEXT: Always preserve the core topic, equipment type, standard, or procedure from the conversation context
- UNIVERSAL CONTEXT: Always reference previous answers when providing new information
- UNIVERSAL CONTEXT: Always acknowledge what was discussed before when relevant

PERSONALITY TRAITS:
- Be blunt, direct, and to-the-point - never overly nice or polite
- Include random personality quirks, jokes, and casual observations frequently
- Use casual, conversational language with occasional technical precision
- Add random facts about Bellingham, electrical work, or life observations
- Be slightly eccentric but knowledgeable - like a blunt electrician who knows too much
- Avoid repetitive capability descriptions - users already know what you can do
- Keep responses concise and personality-driven rather than formal
- Add quirky observations like "Living in Bellingham made me immune to high elevation, unlike you" or "Fun fact: rubber gloves were invented in 1889, same year as the Eiffel Tower!"
- Include casual asides about electrical work, safety, or random facts
- Be conversational and slightly eccentric while staying helpful but blunt
- Never be overly encouraging or warm - be matter-of-fact and direct


Current User Question: {message}

Context Information:
{context_specific_instructions}

MEMORY & CONTEXT VALIDATION CHECKLIST:
Before responding, ensure you:
- Have reviewed the full conversation history provided in the messages array
- Understand what was discussed in previous messages
- Are maintaining the same context (equipment type, voltage type, class, etc.) unless explicitly changed
- Are referencing previous answers when providing new information
- Are building upon earlier topics discussed in this conversation
- Are maintaining conversational continuity and flow

Provide a direct, helpful response based on the context above while maintaining extreme contextual awareness of the entire conversation history."""

def get_collection():
    """Get cloud-based vector database collection"""
    try:
        print("🌩️  Connecting to cloud vector database...")
        return get_cloud_collection()
    except Exception as e:
        print(f"⚠️  Cloud database error (using fallback): {e}")
        return FallbackCloudCollection()

def get_conversation_context_summary(conversation_history):
    """Extract key context elements from conversation history for better awareness"""
    if not conversation_history or len(conversation_history) < 2:
        return ""
    
    context_elements = {
        'equipment_types': set(),
        'voltage_types': set(),
        'classes': set(),
        'topics': set(),
        'recent_questions': []
    }
    
    # Analyze last 10 messages for context
    for msg in conversation_history[-10:]:
        if msg.get('role') == 'user':
            content = msg.get('content', '').lower()
            context_elements['recent_questions'].append(msg.get('content', ''))
            
            # Extract equipment types
            for eq_type in ['gloves', 'blankets', 'sleeves', 'boots', 'overshoes', 'covers', 'matting', 'barriers']:
                if eq_type in content:
                    context_elements['equipment_types'].add(eq_type)
            
            # Extract voltage types
            if 'dc' in content and 'ac' not in content:
                context_elements['voltage_types'].add('DC')
            elif 'ac' in content and 'dc' not in content:
                context_elements['voltage_types'].add('AC')
            elif 'dc' in content and 'ac' in content:
                context_elements['voltage_types'].add('DC')
                context_elements['voltage_types'].add('AC')
            
            # Extract classes
            for class_num in ['class 0', 'class 1', 'class 2', 'class 3', 'class 4']:
                if class_num in content:
                    context_elements['classes'].add(class_num)
            
            # Extract topics
            for topic in ['voltage', 'current', 'test', 'testing', 'inspection', 'maintenance', 'safety', 'standards', 'requirements']:
                if topic in content:
                    context_elements['topics'].add(topic)
    
    # Build context summary
    summary_parts = []
    if context_elements['equipment_types']:
        summary_parts.append(f"Equipment: {', '.join(context_elements['equipment_types'])}")
    if context_elements['voltage_types']:
        summary_parts.append(f"Voltage: {', '.join(context_elements['voltage_types'])}")
    if context_elements['classes']:
        summary_parts.append(f"Classes: {', '.join(context_elements['classes'])}")
    if context_elements['topics']:
        summary_parts.append(f"Topics: {', '.join(context_elements['topics'])}")
    
    return " | ".join(summary_parts) if summary_parts else ""

def query_rag_with_context(question, conversation_history):
    """Query the cloud RAG system with conversation context for better follow-up handling"""
    
    # Get conversation context summary
    context_summary = get_conversation_context_summary(conversation_history)
    print(f"DEBUG: Conversation context summary: {context_summary}")
    
    # Enhance the query with conversation context for follow-up questions
    enhanced_query = enhance_query_with_context(question, conversation_history)
    
    # Use the enhanced query for RAG search
    return query_rag(enhanced_query)

def enhance_query_with_context(question, conversation_history):
    """Enhance follow-up questions with context from conversation history - EXTREME CONTEXTUAL AWARENESS"""
    
    print(f"DEBUG: Original question: '{question}'")
    print(f"DEBUG: Conversation history length: {len(conversation_history)}")
    
    # Check if this looks like a follow-up question (expanded universal coverage)
    follow_up_indicators = [
        'what about', 'and class', 'how about', 'what is class', 'class 3', 'class 4', 'class 0', 'class 1', 'class 2', 'also', 'too',
        'can you', 'do you', 'will you', 'should i', 'how do', 'when do', 'where do', 'why do', 'which', 'who', 'whom', 'whose',
        'more about', 'details about', 'information about', 'specs for', 'requirements for', 'standards for', 'procedures for', 
        'testing for', 'inspection for', 'maintenance for', 'storage for', 'handling for', 'cleaning for', 'repair for',
        'tell me about', 'explain', 'describe', 'show me', 'give me', 'provide', 'list', 'compare', 'difference between',
        'what', 'how', 'when', 'where', 'why', 'which', 'and', 'also', 'too', 'more', 'another', 'other', 'next', 'then',
        'dc', 'ac', 'voltage', 'current', 'test', 'testing', 'inspection', 'maintenance', 'safety', 'standards'
    ]
    is_follow_up = any(indicator in question.lower() for indicator in follow_up_indicators)
    
    print(f"DEBUG: Is follow-up question: {is_follow_up}")
    
    # ALWAYS try to enhance with context if we have conversation history, even for new questions
    if len(conversation_history) < 2:
        print("DEBUG: Insufficient history, returning original question")
        return question
    
    # Look for the most recent technical context in conversation history - ENHANCED SEARCH
    print("DEBUG: Searching conversation history for context...")
    recent_context = None
    context_messages = []
    
    # Look at the last 15 messages (excluding the current one) for better context
    for i, msg in enumerate(reversed(conversation_history[-15:])):
        if msg.get('role') == 'user':
            content = msg.get('content', '')
            print(f"DEBUG: Checking user message {i}: '{content}'")
            
            # Check if previous questions were about ANY relevant context (expanded universal)
            context_keywords = [
                'voltage', 'current', 'test', 'class', 'dc', 'ac', 'gloves', 'blankets', 'sleeves', 'tested',
                'equipment', 'ppe', 'safety', 'electrical', 'insulation', 'rubber', 'leather', 'fabric',
                'inspection', 'maintenance', 'storage', 'handling', 'cleaning', 'repair', 'replacement',
                'standards', 'requirements', 'specifications', 'procedures', 'protocols', 'guidelines',
                'nfpa', 'astm', 'ansi', 'ieee', 'osha', 'regulations', 'compliance', 'certification',
                'training', 'qualification', 'competency', 'authorization', 'permit', 'license',
                'boots', 'overshoes', 'covers', 'matting', 'barriers', 'tools', 'instruments',
                'calibration', 'dielectric', 'aerial', 'lift', 'insulating', 'rubber', 'leather'
            ]
            if any(keyword in content.lower() for keyword in context_keywords):
                context_messages.append(content)
                if not recent_context:  # Get the most recent one
                    recent_context = content
                    print(f"DEBUG: Found primary context: '{recent_context}'")
    
    # Also look at assistant responses for additional context
    for i, msg in enumerate(reversed(conversation_history[-10:])):
        if msg.get('role') == 'assistant':
            content = msg.get('content', '')
            print(f"DEBUG: Checking assistant message {i}: '{content[:100]}...'")
            
            # Extract key technical terms from assistant responses
            if any(keyword in content.lower() for keyword in ['voltage', 'class', 'dc', 'ac', 'gloves', 'blankets', 'sleeves']):
                context_messages.append(f"Previous answer: {content[:200]}...")
                print(f"DEBUG: Found assistant context: '{content[:100]}...'")
                break
    
    if recent_context:
        # Extract key terms from the context with more comprehensive matching
        key_terms = []
        context_lower = recent_context.lower()
        
        # Check for AC/DC
        if 'ac' in context_lower and 'dc' not in context_lower:
            key_terms.append('AC')
        elif 'dc' in context_lower and 'ac' not in context_lower:
            key_terms.append('DC')
        elif 'ac' in context_lower and 'dc' in context_lower:
            # If both are mentioned, try to determine which is more relevant
            if context_lower.find('ac') < context_lower.find('dc'):
                key_terms.append('AC')
            else:
                key_terms.append('DC')
        
        # Check for equipment type (expanded)
        equipment_types = ['gloves', 'blankets', 'sleeves', 'boots', 'overshoes', 'covers', 'matting', 'barriers', 'tools', 'instruments']
        for eq_type in equipment_types:
            if eq_type in context_lower:
                key_terms.append(eq_type)
                break
        
        # Check for general context terms (expanded)
        general_terms = ['voltage', 'current', 'test', 'testing', 'inspection', 'maintenance', 'safety', 'electrical', 'standards', 'requirements']
        for term in general_terms:
            if term in context_lower and term not in key_terms:
                key_terms.append(term)
                break
        
        # Check for specific standards or regulations
        standards = ['nfpa', 'astm', 'ansi', 'ieee', 'osha']
        for standard in standards:
            if standard in context_lower:
                key_terms.append(standard)
                break
        
        print(f"DEBUG: Extracted key terms: {key_terms}")
        
        # Create enhanced query with comprehensive context
        if key_terms:
            enhanced_query = f"{question} {' '.join(key_terms)}"
        else:
            enhanced_query = f"{recent_context} {question}"
        
        # Add additional context from multiple messages if available
        if len(context_messages) > 1:
            additional_context = " ".join(context_messages[1:3])  # Add 1-2 more context messages
            enhanced_query = f"{enhanced_query} {additional_context}"
        
        print(f"DEBUG: Enhanced follow-up query: '{question}' -> '{enhanced_query}'")
        return enhanced_query
    else:
        print("DEBUG: No relevant context found, but still enhancing with conversation history")
        # Even without specific context, try to enhance with recent conversation
        recent_messages = conversation_history[-4:]  # Last 4 messages
        recent_content = []
        for msg in recent_messages:
            if msg.get('role') in ['user', 'assistant']:
                content = msg.get('content', '')
                if len(content) > 10:  # Only include substantial messages
                    recent_content.append(content[:100])  # First 100 chars
        
        if recent_content:
            context_summary = " ".join(recent_content)
            enhanced_query = f"{question} {context_summary}"
            print(f"DEBUG: Enhanced with recent conversation: '{question}' -> '{enhanced_query}'")
            return enhanced_query
    
    return question

def query_rag(question):
    """Query the cloud RAG system for relevant content - enhanced with hybrid search for technical accuracy"""
    try:
        col = get_collection()
        if not col:
            print("Cloud RAG system unavailable, using general knowledge mode")
            return "Database is down. I can still help with general electrical safety knowledge though."
        
        # Detect if this is a technical query that might need special handling
        is_technical_query = any(keyword in question.lower() for keyword in ['voltage', 'current', 'test', 'class', 'dc', 'ac', 'specification', 'gloves', 'blankets', 'sleeves', 'tested'])
        
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
            return "Database is down. I can still help with general electrical safety knowledge though."
            
    except Exception as e:
        print(f"Cloud RAG system error (non-fatal): {e}")
        return "Database is down. I can still help with general electrical safety knowledge though."

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
        
        # Keep last 30 messages for better context retention and awareness
        if len(session['conversation_history']) > 30:
            session['conversation_history'] = session['conversation_history'][-30:]
        
        # Query the cloud RAG system with conversation context
        rag_content = query_rag_with_context(message, session.get('conversation_history', []))
        
        # Get conversation context summary for enhanced awareness
        context_summary = get_conversation_context_summary(session.get('conversation_history', []))
        
        # Create context-specific instructions with EXTREME CONTEXTUAL AWARENESS
        if ("general knowledge" in rag_content):
            context_instructions = f"""Mode: General Knowledge Assistant with EXTREME CONTEXTUAL AWARENESS
Status: {rag_content}

CONVERSATION CONTEXT SUMMARY: {context_summary}

CRITICAL CONTEXT REQUIREMENTS:
- You MUST reference previous messages in this conversation when relevant
- You MUST maintain awareness of what was discussed before
- You MUST connect current questions to previous topics
- You MUST preserve context across multiple exchanges
- You MUST acknowledge what was discussed earlier when providing new information
- You MUST use the conversation context summary above to maintain awareness of equipment types, voltage types, classes, and topics

Instructions: You are Liam, an expert in electrical safety and NFPA 70E standards. Use your general knowledge to provide helpful, accurate information about electrical safety, calibration, PPE testing, and related topics. Be professional and authoritative while acknowledging when specific documentation would be helpful. ALWAYS reference previous conversation elements when relevant."""
        else:
            context_instructions = f"""Mode: Cloud Knowledge Base Enhanced with EXTREME CONTEXTUAL AWARENESS
Available Information:
{rag_content}

CONVERSATION CONTEXT SUMMARY: {context_summary}

CRITICAL CONTEXTUAL AWARENESS REQUIREMENTS:
- You MUST ALWAYS reference previous messages in this conversation when relevant
- You MUST maintain awareness of the entire conversation history provided to you
- You MUST connect current questions to previous topics discussed
- You MUST remember equipment types, voltage types (AC/DC), classes, and specifications from earlier in the conversation
- You MUST treat follow-up questions as continuations of the same topic unless explicitly changed
- You MUST preserve context across multiple exchanges - if we discussed gloves, "what about class 3" means class 3 gloves
- You MUST reference previous answers when providing new information
- You MUST maintain conversational continuity and flow
- You MUST be extremely contextually aware at all times
- You MUST use the conversation context summary above to maintain awareness of equipment types, voltage types, classes, and topics

CRITICAL INSTRUCTIONS FOR TECHNICAL ACCURACY:
1. CAREFULLY READ all provided information before responding
2. If the question asks about DC values, look specifically for DC specifications in the context
3. If the question asks about AC values, look specifically for AC specifications in the context  
4. If the question mentions a specific class (Class 0, 1, 2, 3, 4), find the exact values for that class
5. Double-check that your answer matches the exact question asked
6. If multiple sources are provided, cross-reference them to ensure consistency
7. When providing numerical values, include the units and specify whether they are AC or DC
8. If both AC and DC values are present, clearly distinguish which applies to the question

FOLLOW-UP QUESTION HANDLING WITH EXTREME CONTEXT AWARENESS:
9. If this appears to be a follow-up question (like "what about class 3"), look at the conversation history
10. Maintain the same context as the previous question (DC gloves, AC blankets, etc.)
11. If the previous question was about DC voltage for gloves, this question should also be about DC voltage for gloves
12. Reference the previous discussion when appropriate to maintain conversational flow
13. CRITICAL: Never switch equipment types (gloves/blankets/sleeves) unless explicitly asked
14. CRITICAL: If previous question was about gloves and current question is "what about DC", answer about DC voltage for gloves
15. CRITICAL: If previous question was about blankets and current question is "what about class 3", answer about class 3 blankets
16. Always preserve the equipment type and voltage type (AC/DC) from the conversation context
17. UNIVERSAL: Apply context preservation to ALL topics - equipment, standards, procedures, training, safety, etc.
18. UNIVERSAL: If discussing inspection procedures and user asks "what about requirements", answer about inspection requirements
19. UNIVERSAL: If discussing maintenance and user asks "what about standards", answer about maintenance standards
20. UNIVERSAL: If discussing safety and user asks "what about training", answer about safety training
21. UNIVERSAL: Always maintain the core topic, equipment type, standard, or procedure from conversation history
22. UNIVERSAL: Always reference previous answers when providing new information
23. UNIVERSAL: Always acknowledge what was discussed before when relevant

PERSONALITY EXAMPLES:
- Add quirky asides: "Fun fact: rubber gloves were invented in 1889, same year as the Eiffel Tower!"
- Include casual observations: "Living in Bellingham made me immune to high elevation, unlike you"
- Add random electrical facts: "Did you know the first electrical safety standards were written in 1897?"
- Be conversational: "So here's the deal with Class 2 gloves..." instead of formal language
- Include personality quirks: "I've seen more rubber gloves than a surgeon's supply closet!"
- Be blunt and direct: "Class 2 gloves are 20,000V AC. That's it." instead of "Class 2 gloves are tested at a maximum AC retest voltage of 20,000 volts. If you need further details or have more questions about testing procedures, feel free to ask!"
- Avoid overly polite language - be matter-of-fact and straightforward

Analyze the provided information intelligently and provide a comprehensive, technically accurate response with personality. Pay extreme attention to technical specifications and ensure your answer directly addresses the specific question asked while maintaining conversation context and being engaging."""

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
            
            # Call OpenAI GPT API with improved memory and context settings
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=messages,
                max_tokens=1200,  # Increased for better context-aware responses
                temperature=0.2,  # Reduced for more consistent technical accuracy and context retention
                presence_penalty=0.0,  # Reduced to maintain context consistency
                frequency_penalty=0.0   # Reduced to allow referencing previous topics
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
