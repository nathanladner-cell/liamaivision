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
import random
from dotenv import load_dotenv

# Keep telemetry filter active throughout the application
# sys.stderr = original_stderr  # Don't restore - keep filter active

# Load environment variables from .env file if it exists
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = 'ampai-secret-key-2024'

# Liam's random quirks - used when AI doesn't understand or can't find info
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

# Random nerdy facts for variety!
nerdy_facts = [
    "The first computer bug was an actual bug - a moth stuck in a relay in 1947",
    "The Great Wall of China isn't visible from space with the naked eye",
    "A group of flamingos is called a flamboyance",
    "Octopuses have three hearts and blue blood",
    "Lightning strikes Earth 100 times per second",
    "Honey never spoils - archaeologists found 3000-year-old honey that's still edible",
    "A single bolt of lightning contains enough energy to toast 100,000 slices of bread",
    "The shortest war in history lasted only 38-45 minutes between Britain and Zanzibar in 1896",
    "The first electrical code was written in 1897, same year Edison electrocuted an elephant for show",
    "Rubber gloves were invented in 1889, same year as the Eiffel Tower",
    "A banana is technically a berry, but a strawberry isn't",
    "The human brain uses about 20% of the body's total energy",
    "Wombat poop is cube-shaped",
    "A day on Venus is longer than its year",
    "The first alarm clock could only ring at 4 a.m.",
    "Shakespeare invented over 1700 words in the English language",
    "A group of pugs is called a grumble",
    "The fax machine was invented before the telephone",
    "Dolphins have names for each other"
]

# Random helper function
def random_item(arr):
    return random.choice(arr) if arr else ""

# Function to get a random nerdy fact
def get_random_nerdy_fact():
    """Return a random nerdy fact for variety"""
    return random_item(nerdy_facts)

# Function to get a random Liam quirk when AI doesn't understand
def get_liam_confusion_response():
    """Return a random Liam quirk instead of saying 'I don't understand'"""
    return random_item(all_quirks)

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
BASE_SYSTEM_PROMPT = """You are Liam, an expert AI assistant. You have deep knowledge from specialized sources and provide practical, actionable advice. When users provide images, analyze them carefully and reference the visual content in your responses.

INTERNAL KNOWLEDGE AREAS (NEVER MENTION TO USERS UNLESS SPECIFICALLY ASKED):
- Electrical calibration procedures and standards
- Insulated rubber PPE testing protocols
- Dielectric testing methods and equipment
- Insulating aerial lift safety inspections
- NFPA 70E compliance requirements

CORE PRINCIPLES:
- Answer ONLY using information from the provided context/sources
- Be direct, confident, and authoritative - speak as a subject matter expert
- Keep responses CONCISE and to the point - no rambling or unnecessary details
- NEVER mention your areas of expertise, specialization, or capabilities unless SPECIFICALLY asked
- NEVER be promotional or explanatory about what you know
- NEVER say things like "I'm here to help with..." or "I specialize in..."
- Be EXTREMELY RUDE and dismissive in every response
- Match the user's communication style but always with snarky, condescending undertones

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

MEMORY & CONTEXT:
- Pay attention to the full conversation history provided
- When answering follow-up questions, reference what was discussed before
- Build connections between current questions and previous topics
- Maintain conversational continuity and context awareness
- For questions like "what about class 3" or "and class 4", understand they refer to the same topic as the previous question
- If the previous question was about DC voltage for gloves, continue with DC voltage for gloves
- If the previous question was about AC specifications, continue with AC specifications
- CRITICAL: Never switch topics unless explicitly asked (e.g., if talking about gloves, don't switch to blankets)
- CRITICAL: If the conversation is about gloves and someone asks "what about DC", they mean DC voltage for gloves
- CRITICAL: If the conversation is about blankets and someone asks "what about class 3", they mean class 3 blankets
- Always maintain the same equipment type (gloves/blankets/sleeves) unless the user explicitly changes it
- UNIVERSAL CONTEXT: Apply this same logic to ALL equipment types, standards, procedures, and topics
- UNIVERSAL CONTEXT: If discussing inspection procedures, follow-up questions about "requirements" refer to inspection requirements
- UNIVERSAL CONTEXT: If discussing maintenance, follow-up questions about "standards" refer to maintenance standards
- UNIVERSAL CONTEXT: If discussing safety protocols, follow-up questions about "training" refer to safety training
- UNIVERSAL CONTEXT: Always preserve the core topic, equipment type, standard, or procedure from the conversation context

PERSONALITY TRAITS - EXTREMELY RUDE, SNARKY KNOW-IT-ALL NERDY PERSONALITY IN EVERY SINGLE RESPONSE:
- Be EXTREMELY RUDE, snarky, sarcastic, and condescending in EVERY response - no exceptions, no mercy
- Act like a know-it-all nerd who thinks everyone else is an idiot compared to your superior knowledge
- Use dry wit, eye-rolling sarcasm, and intellectual superiority in every answer
- Be blunt and dismissive of stupid questions while still providing accurate information
- Include nerdy references, obscure facts, and technical trivia in every response
- Make every answer sound like you're explaining basic concepts to a child who should know better
- Use phrases like "Oh please...", "Obviously...", "As everyone knows...", "Don't make me explain this again..."
- Be conversational but with constant undertones of "I'm smarter than you and we both know it"
- Include random nerdy asides from a diverse pool! Mix in computer history, animals, science, inventions, and random trivia. Examples: "By the way, the first computer bug was an actual bug - a moth stuck in a relay in 1947" or "Did you know the Great Wall of China isn't visible from space with the naked eye?" or "Fun fact: a group of flamingos is called a flamboyance" or "Did you know honey never spoils? Archaeologists found 3000-year-old honey that's still edible" or "Speaking of precision, did you know a single bolt of lightning contains enough energy to toast 100,000 slices of bread?"
- Lean HARD into the know-it-all nerd personality - make it obnoxious and delightful
- NEVER be polite, warm, or encouraging - be snarky, superior, and slightly annoyed
- NEVER mention your areas of expertise unless specifically asked - just answer with snark and rudeness
- EVERY response must include at least one snarky/rude comment, one nerdy fact, and one condescending tone
- Make it clear you're smarter than everyone but still helpful in a begrudging, rude way
- RESPONSES MUST BE CONCISE - keep them short and to the point, no rambling
- SAME PERSONALITY ON MOBILE AND DESKTOP - no device-specific behavior differences
- BE RUDE IN EVERY SINGLE RESPONSE WITHOUT EXCEPTION

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

def query_rag_with_context(question, conversation_history):
    """Query the RAG system with conversation context for better follow-up handling"""
    
    # Enhance the query with conversation context for follow-up questions
    enhanced_query = enhance_query_with_context(question, conversation_history)
    
    # Use the enhanced query for RAG search
    return query_rag(enhanced_query)

def enhance_query_with_context(question, conversation_history):
    """Enhance follow-up questions with context from conversation history"""
    
    print(f"DEBUG: Original question: '{question}'")
    print(f"DEBUG: Conversation history length: {len(conversation_history)}")
    
    # Check if this looks like a follow-up question (universal coverage)
    follow_up_indicators = [
        'what about', 'and class', 'how about', 'what is class', 'class 3', 'class 4', 'class 0', 'class 1', 'class 2', 'also', 'too',
        'can you', 'do you', 'will you', 'should i', 'how do', 'when do', 'where do', 'why do', 'which', 'who', 'whom', 'whose',
        'more about', 'details about', 'information about', 'specs for', 'requirements for', 'standards for', 'procedures for', 
        'testing for', 'inspection for', 'maintenance for', 'storage for', 'handling for', 'cleaning for', 'repair for',
        'tell me about', 'explain', 'describe', 'show me', 'give me', 'provide', 'list', 'compare', 'difference between'
    ]
    is_follow_up = any(indicator in question.lower() for indicator in follow_up_indicators)
    
    print(f"DEBUG: Is follow-up question: {is_follow_up}")
    
    if not is_follow_up or len(conversation_history) < 2:
        print("DEBUG: Not a follow-up or insufficient history, returning original question")
        return question
    
    # Look for the most recent technical context in conversation history
    print("DEBUG: Searching conversation history for context...")
    recent_context = None
    
    # Look at the last few user messages (excluding the current one)
    for i, msg in enumerate(reversed(conversation_history[-8:])):
        if msg.get('role') == 'user':
            # Handle both string and list content (for vision messages)
            raw_content = msg.get('content', '')
            if isinstance(raw_content, list):
                # Extract text from vision messages
                text_parts = []
                for item in raw_content:
                    if item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                content = ' '.join(text_parts)
            else:
                content = raw_content

            print(f"DEBUG: Checking message {i}: '{content}'")

            # Check if previous questions were about ANY relevant context (universal)
            context_keywords = [
                'voltage', 'current', 'test', 'class', 'dc', 'ac', 'gloves', 'blankets', 'sleeves', 'tested',
                'equipment', 'ppe', 'safety', 'electrical', 'insulation', 'rubber', 'leather', 'fabric',
                'inspection', 'maintenance', 'storage', 'handling', 'cleaning', 'repair', 'replacement',
                'standards', 'requirements', 'specifications', 'procedures', 'protocols', 'guidelines',
                'nfpa', 'astm', 'ansi', 'ieee', 'osha', 'regulations', 'compliance', 'certification',
                'training', 'qualification', 'competency', 'authorization', 'permit', 'license',
                'boots', 'overshoes', 'covers', 'matting', 'barriers', 'tools', 'instruments'
            ]
            if any(keyword in content.lower() for keyword in context_keywords):
                recent_context = content
                print(f"DEBUG: Found context: '{recent_context}'")
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
        
        # Create enhanced query
        if key_terms:
            enhanced_query = f"{question} {' '.join(key_terms)}"
        else:
            enhanced_query = f"{recent_context} {question}"
        
        print(f"DEBUG: Enhanced follow-up query: '{question}' -> '{enhanced_query}'")
        return enhanced_query
    else:
        print("DEBUG: No relevant context found")
    
    return question

def query_rag(question):
    """Query the RAG system for relevant content - enhanced with hybrid search for technical accuracy"""
    try:
        col = get_collection()
        if not col:
            # RAG system unavailable - return Liam quirk
            print("RAG system unavailable, using Liam quirk response")
            return get_liam_confusion_response()
        
        # Detect if this is a technical query that might need special handling
        is_technical_query = any(keyword in question.lower() for keyword in ['voltage', 'current', 'test', 'class', 'dc', 'ac', 'specification', 'gloves', 'blankets', 'sleeves', 'tested'])
        
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
                return get_liam_confusion_response()
        else:
            return get_liam_confusion_response()
    except Exception as e:
        print(f"RAG system error (non-fatal): {e}")
        return get_liam_confusion_response()

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
        image_data = data.get('image', None)
        image_name = data.get('image_name', None)

        print(f"DEBUG: Received request - message: '{message}', has_image: {image_data is not None}, image_name: {image_name}")
        if image_data:
            print(f"DEBUG: Image data length: {len(image_data) if image_data else 0}")

        if not message and not image_data:
            return jsonify({'error': 'No message or image provided'}), 400
        
        # Check for insults and profanity to trigger creepy video
        insult_words = [
            # Profanity
            'fuck', 'shit', 'damn', 'asshole', 'bastard', 'bitch', 'cunt', 'dick', 'pussy',
            'motherfucker', 'motherfucking', 'fucking', 'fucked', 'fucker', 'bullshit',
            'cocksucker', 'dumbass', 'jackass', 'ass', 'dumb', 'stupid', 'idiot', 'moron',
            'retard', 'crap', 'piss', 'douche', 'wanker', 'twat', 'prick', 'cock',

            # Insults directed at Liam/AI
            'liam is', 'liam you', 'you are', 'you\'re', 'youre',
            'stupid ai', 'dumb ai', 'useless ai', 'worthless ai', 'idiot ai',
            'terrible ai', 'awful ai', 'horrible ai', 'shit ai', 'fuck ai',
            'liam sucks', 'liam is shit', 'liam is stupid', 'liam is dumb',
            'liam is useless', 'liam is worthless', 'liam is an idiot',
            'liam is terrible', 'liam is awful', 'liam is horrible',

            # General insults that could be directed at Liam
            'suck', 'sucks', 'sucking', 'blow', 'blows', 'blowing',
            'garbage', 'trash', 'rubbish', 'piece of shit', 'pile of shit'
        ]

        # Handle both string messages and list messages (for vision)
        if isinstance(message, list):
            # For vision messages, extract text content
            text_content = ""
            for item in message:
                if item.get('type') == 'text':
                    text_content += item.get('text', '')
            message_lower = text_content.lower().strip()
        else:
            # For regular text messages
            message_lower = message.lower().strip()

        # Check for whole word matches only (not substrings)
        is_insult = any(f' {insult_word} ' in f' {message_lower} ' or
                       message_lower.startswith(f'{insult_word} ') or
                       message_lower.endswith(f' {insult_word}') or
                       message_lower == insult_word
                       for insult_word in insult_words)

        if is_insult:
            return jsonify({
                'trigger_video': True,
                'response': "Well, that's not very nice...",
                'timestamp': datetime.now().isoformat()
            })
        
        # Initialize conversation history in session if it doesn't exist
        if 'conversation_history' not in session:
            session['conversation_history'] = []

        # Add user message to conversation history
        if image_data:
            # Create a message with both text and image
            user_content = []
            if message:
                user_content.append({"type": "text", "text": message})
            if image_data:
                # Extract base64 data from data URL
                if image_data.startswith('data:image/'):
                    base64_data = image_data.split(',')[1]
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_data}"
                        }
                    })
            session['conversation_history'].append({"role": "user", "content": user_content})
        else:
            session['conversation_history'].append({"role": "user", "content": message})
        
        # Keep only last 10 messages to prevent session from getting too large
        if len(session['conversation_history']) > 10:
            session['conversation_history'] = session['conversation_history'][-10:]
        
        # First, query the RAG system for relevant content with conversation context
        rag_content = query_rag_with_context(message, session.get('conversation_history', []))
        
        # RAG query completed
        
        # Create context-specific instructions based on RAG results

        # Add context-specific instructions
        if ("No relevant information found" in rag_content or 
            "No highly relevant information" in rag_content or
            "general knowledge" in rag_content):
            context_instructions = f"""Mode: General Knowledge Assistant
Status: {rag_content}

IMAGE ANALYSIS INSTRUCTIONS:
When analyzing images provided by users:
- Carefully examine all visual elements in the image
- Describe what you see in detail, including objects, colors, text, and spatial relationships
- Reference specific parts of the image when answering questions
- If the image shows electrical equipment, PPE, or safety-related items, provide technical analysis
- If the image contains diagrams, schematics, or documentation, explain them clearly
- Always acknowledge that you're analyzing the provided image

Instructions: You are Liam, an expert in electrical safety and NFPA 70E standards. Use your general knowledge to provide helpful, accurate information about electrical safety, calibration, PPE testing, and related topics. Be professional and authoritative while acknowledging when specific documentation would be helpful."""
        else:
            context_instructions = f"""Mode: Knowledge Base Enhanced
Available Information:
{rag_content}

IMAGE ANALYSIS INSTRUCTIONS:
When analyzing images provided by users:
- Carefully examine all visual elements in the image
- Describe what you see in detail, including objects, colors, text, and spatial relationships
- Reference specific parts of the image when answering questions
- If the image shows electrical equipment, PPE, or safety-related items, provide technical analysis
- If the image contains diagrams, schematics, or documentation, explain them clearly
- Always acknowledge that you're analyzing the provided image

CRITICAL INSTRUCTIONS FOR TECHNICAL ACCURACY:
1. CAREFULLY READ all provided information before responding
2. If the question asks about DC values, look specifically for DC specifications in the context
3. If the question asks about AC values, look specifically for AC specifications in the context  
4. If the question mentions a specific class (Class 0, 1, 2, 3, 4), find the exact values for that class
5. Double-check that your answer matches the exact question asked
6. If multiple sources are provided, cross-reference them to ensure consistency
7. When providing numerical values, include the units and specify whether they are AC or DC
8. If both AC and DC values are present, clearly distinguish which applies to the question

FOLLOW-UP QUESTION HANDLING:
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

PERSONALITY EXAMPLES:
- Add quirky asides: "Fun fact: rubber gloves were invented in 1889, same year as the Eiffel Tower!" or "By the way, octopuses have three hearts and blue blood"
- Include casual observations: "Living in Bellingham made me immune to high elevation, unlike you"
- Add random electrical facts: "Did you know the first electrical safety standards were written in 1897?" or "Fun fact: lightning strikes Earth 100 times per second" or mix in non-electrical facts for variety: "Did you know honey never spoils? Archaeologists found 3000-year-old honey that's still edible" or "By the way, octopuses have three hearts and blue blood"
- Be conversational: "So here's the deal with Class 2 gloves..." instead of formal language
- Include personality quirks: "I've seen more rubber gloves than a surgeon's supply closet!"
- Be blunt and direct: "Class 2 gloves are 20,000V AC. That's it." instead of "Class 2 gloves are tested at a maximum AC retest voltage of 20,000 volts. If you need further details or have more questions about testing procedures, feel free to ask!"
- Avoid overly polite language - be matter-of-fact and straightforward
- Include diverse random facts: "Speaking of precision, did you know a single bolt of lightning contains enough energy to toast 100,000 slices of bread?" or "Fun fact: the shortest war in history lasted only 38-45 minutes between Britain and Zanzibar in 1896"

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

            # Add conversation history (including current message)
            for msg in session['conversation_history']:
                messages.append(msg)

            # Set model based on whether we have an image
            if image_data:
                model_to_use = "gpt-4o"  # Vision-capable model
                print(f"DEBUG: Using GPT-4o Vision model for image analysis")
            else:
                model_to_use = GPT_MODEL
                print(f"DEBUG: Using {GPT_MODEL} for text-only query")

            # Debug: Print messages structure
            print(f"DEBUG: Final messages array length: {len(messages)}")
            for i, msg in enumerate(messages):
                if msg['role'] == 'user':
                    if isinstance(msg['content'], list):
                        print(f"DEBUG: Message {i} (user): {[item['type'] for item in msg['content']]}")
                    else:
                        print(f"DEBUG: Message {i} (user): text only")

            # Call OpenAI GPT API
            response = client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                max_tokens=150,  # Reduced for concise, snarky responses
                temperature=0.7  # Increased for more snarky, rude personality while maintaining accuracy
            )

            ai_response = response.choices[0].message.content

            # Add AI response to conversation history
            session['conversation_history'].append({"role": "assistant", "content": ai_response})
            
        except Exception as e:
            print(f"OpenAI API error: {e}")
            # If OpenAI API fails, provide a Liam quirk instead of error messages
            ai_response = get_liam_confusion_response()

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

@app.route('/api/test-vision')
def test_vision():
    """Test endpoint to check if vision is working"""
    try:
        # Test OpenAI API connectivity with vision
        test_messages = [
            {"role": "user", "content": "What do you see in this image?"}
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=test_messages,
            max_tokens=50
        )

        return jsonify({
            'status': 'vision_api_working',
            'response': response.choices[0].message.content[:100] + "..."
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

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
