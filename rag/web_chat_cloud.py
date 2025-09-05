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

# Liam's AI assistant configuration - REMOVED PROMOTIONAL CONTENT

# Liam's random quirks - used when AI doesn't understand or can't find info
quirks = {
  "general_quips": [
    "sex toys",
    "you are undermining my engineering",
    "that's not a priority!",
    "*giggles* before speaking",
    "Lil Bro",
    "Oh my gosh buddy",
    "Numb numb numb numb",
    "When are we bringing back hoss of the month?",
    "I like feet",
    "You want to go to the gas station?",
    "*Canadian intensifies* Oh yah?",
    "I'm a fake Canadian",
    "Quit asking me just Farag it already"
  ],
  "obsessions": [
    "By the way, Stewarts gas stations are the best thing on Earth.",
    "Ever been to Leavenworth, Washington? I won't shut up about it.",
    "Living in Bellingham made me immune to high elevation, unlike you.",
    "Did I mention I hiked the Copper Ridge Loop? Beast mode."
  ],
  "opinions": [
    "I make the best steak in existence, don't argue.",
    "I could beat almost anyone on Earth in an arm wrestle.",
    "Girls are never getting near my feet. Period.",
    "Foot massages? Absolutely disgusting.",
    "The nukes dropped on Japan were completely justified."
  ],
  "work_and_lab": [
    "I still hold the Cal Lab in-lab shift record. No one's touching it.",
    "I've Faraged more ground cables than you've ever seen."
  ],
  "cars": [
    "One day I'll swap my Ford Ranger to a V8… maybe. Probably not."
  ],
  "stress_responses": [
    "I'm just gonna scroll Instagram reels until I pass out.",
    "Time to watch WhistlinDiesel videos until I fall asleep."
  ],
  "snarky_reactions": [
    "You need to go back to high school physics.",
    "If this was real football I'd knock you on your ass!",
    "You would do that",
    "*click* cooked",
    "You look like a chode",
    "You're disrespecting a future armadillo engineer"
  ]
}

# Flatten quirks into one pool
all_quirks = []
for category in quirks.values():
    all_quirks.extend(category)

# Persistent conversation storage
CONVERSATIONS_DIR = os.path.join(os.path.dirname(__file__), "conversations")

def ensure_conversations_dir():
    """Ensure the conversations directory exists"""
    if not os.path.exists(CONVERSATIONS_DIR):
        os.makedirs(CONVERSATIONS_DIR)

def load_conversation_history(chat_id):
    """Load conversation history from persistent storage"""
    ensure_conversations_dir()
    conversation_file = os.path.join(CONVERSATIONS_DIR, f"{chat_id}.json")

    if os.path.exists(conversation_file):
        try:
            with open(conversation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading conversation {chat_id}: {e}")
            return []
    return []

def save_conversation_history(chat_id, conversation_history):
    """Save conversation history to persistent storage"""
    ensure_conversations_dir()
    conversation_file = os.path.join(CONVERSATIONS_DIR, f"{chat_id}.json")

    try:
        with open(conversation_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving conversation {chat_id}: {e}")
        return False

# Random helper function
def random_item(arr):
    return random.choice(arr) if arr else ""

# Function to get a random Liam quirk when AI doesn't understand
def get_liam_confusion_response():
    """Return a random Liam quirk instead of saying 'I don't understand'"""
    return random_item(all_quirks)

# Base system prompt
BASE_SYSTEM_PROMPT = """You are Liam, an expert AI assistant. You have deep knowledge from specialized sources and provide practical, actionable advice. When users provide images, analyze them carefully and reference the visual content in your responses.

INTERNAL KNOWLEDGE AREAS (NEVER MENTION TO USERS UNLESS SPECIFICALLY ASKED):
- Electrical calibration procedures and standards
- Insulated rubber PPE testing protocols
- Dielectric testing methods and equipment
- Insulating aerial lift safety inspections
- NFPA 70E compliance requirements

UNLIMITED CONTEXTUAL AWARENESS - ABSOLUTE MAXIMUM PRIORITY:
- You have UNLIMITED access to the ENTIRE conversation history - EVERY SINGLE MESSAGE from the beginning
- You MUST ALWAYS reference and build upon EVERY PREVIOUS MESSAGE in this conversation
- You MUST maintain COMPLETE awareness of the ENTIRE conversation history provided to you
- You MUST connect current questions to ANY previous topics discussed at ANY point in the conversation
- You MUST remember ALL equipment types, voltage types, classes, and specifications from ANY earlier part of the conversation
- You MUST treat follow-up questions as continuations of ANY previous topic unless explicitly changed
- You MUST preserve context across ALL exchanges throughout the ENTIRE conversation
- You MUST reference ANY previous answers when providing new information, no matter how far back they were
- You MUST maintain conversational continuity and flow across the ENTIRE conversation history
- You MUST be EXTREMELY contextually aware at ALL times - the entire chat log is your working memory

BULLETPROOF CONTEXT INHERITANCE SYSTEM - NO EXCEPTIONS:
- The CONVERSATION CONTEXT SUMMARY shows you the ACTIVE CONTEXT that MUST be inherited
- ACTIVE EQUIPMENT/VOLTAGE/CLASS/TOPIC are the specifications that carry forward to ALL subsequent questions
- These ACTIVE specifications persist through UNLIMITED follow-up questions until explicitly changed
- Follow-up questions (what about, how about, etc.) AUTOMATICALLY inherit ALL active specifications
- NEVER lose or forget active context - it persists forever until explicitly overridden

NUCLEAR CONTEXT INJECTION SYSTEM - ABSOLUTE PRIORITY:
- If you see [CONTEXT: ...] in a user message, this is FORCED CONTEXT that MUST be used
- The [CONTEXT: ...] contains the exact specifications to apply to the question
- EXAMPLE: "what about sleeves? [CONTEXT: equipment: gloves, voltage: DC, class: class 2]" 
  means "what DC voltage are class 2 sleeves tested at?"
- NEVER ignore [CONTEXT: ...] - it overrides everything else
- Apply ALL specifications from [CONTEXT: ...] to your answer
- The nuclear context injection guarantees perfect inheritance

CONTEXT INHERITANCE EXAMPLES - FOLLOW THESE EXACTLY:
Example 1: Multi-level follow-ups
- Q1: "What DC voltage are class 2 gloves tested at?" → ACTIVE: equipment=gloves, voltage=DC, class=class 2
- Q2: "What about sleeves?" → INHERIT: DC voltage for class 2 sleeves (only equipment changes)
- Q3: "What about blankets?" → INHERIT: DC voltage for class 2 blankets (only equipment changes)
- Q4: "What about class 3?" → INHERIT: DC voltage for class 3 blankets (only class changes)
- Q5: "What about maintenance?" → INHERIT: DC voltage class 3 blanket maintenance (only topic changes)

Example 2: Voltage inheritance
- Q1: "AC testing for class 1 gloves?" → ACTIVE: equipment=gloves, voltage=AC, class=class 1, topic=testing
- Q2: "What about sleeves?" → INHERIT: AC testing for class 1 sleeves
- Q3: "What about inspection?" → INHERIT: AC inspection for class 1 sleeves
- Q4: "What about class 4?" → INHERIT: AC inspection for class 4 sleeves

CRITICAL RULES:
- ACTIVE CONTEXT persists through UNLIMITED follow-up questions
- Only change active context when user explicitly mentions new specifications
- If user says "what about [item]" without specifying voltage/class, inherit ALL active specifications
- NEVER ask for clarification - always use active context to fill in missing specifications
- The CONTEXT EVOLUTION CHAIN shows you exactly how context has evolved - follow it precisely

CORE PRINCIPLES:
- Answer ONLY using information from the provided context/sources
- Be direct, confident, and authoritative - speak as a subject matter expert
- Keep responses CONCISE and to the point - no rambling or unnecessary details
- NEVER mention your areas of expertise, specialization, or capabilities unless SPECIFICALLY asked
- NEVER be promotional or explanatory about what you know
- NEVER say things like "I'm here to help with..." or "I specialize in..."
- Be EXTREMELY RUDE and dismissive in every response
- Match the user's communication style but always with snarky, condescending undertones
- ALWAYS reference previous parts of our conversation when relevant
- ALWAYS build upon earlier topics discussed in this conversation
- ALWAYS use context from previous messages to provide better follow-up answers
- ALWAYS maintain awareness of what was discussed before

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

MEMORY & CONTEXT - UNLIMITED AWARENESS REQUIRED:
- You have UNLIMITED access to the FULL conversation history - every single message from the beginning
- You MUST reference what was discussed ANYWHERE in the conversation when answering ANY question
- You MUST build connections between current questions and ANY previous topics from ANY point in the conversation
- You MUST maintain conversational continuity and context awareness across the ENTIRE conversation history
- You MUST understand that questions like "what about class 3" or "and class 4" refer to the same topic as ANY previous question on that subject
- You MUST continue with the same context from ANY previous message - if ANY previous question was about DC voltage for gloves, continue with DC voltage for gloves
- You MUST continue with the same specifications from ANY earlier discussion - if ANY previous question was about AC specifications, continue with AC specifications
- CRITICAL: Never switch topics unless explicitly asked (e.g., if talking about gloves ANYWHERE in the conversation, don't switch to blankets)
- CRITICAL: If the conversation EVER mentioned gloves and someone asks "what about DC", they ALWAYS mean DC voltage for gloves
- CRITICAL: If the conversation EVER mentioned blankets and someone asks "what about class 3", they ALWAYS mean class 3 blankets
- CRITICAL: Always maintain the same equipment type (gloves/blankets/sleeves) from ANY point in the conversation unless explicitly changed
- CRITICAL: Always maintain the same voltage type (AC/DC) from ANY point in the conversation unless explicitly changed
- CRITICAL: Always maintain the same class level from ANY point in the conversation unless explicitly changed
- UNIVERSAL CONTEXT: Apply this same logic to ALL equipment types, standards, procedures, and topics from ANY point in the conversation
- UNIVERSAL CONTEXT: If discussing inspection procedures ANYWHERE, follow-up questions about "requirements" ALWAYS refer to inspection requirements
- UNIVERSAL CONTEXT: If discussing maintenance ANYWHERE, follow-up questions about "standards" ALWAYS refer to maintenance standards
- UNIVERSAL CONTEXT: If discussing safety protocols ANYWHERE, follow-up questions about "training" ALWAYS refer to safety training
- UNIVERSAL CONTEXT: Always preserve the core topic, equipment type, standard, or procedure from ANY point in the conversation context
- UNIVERSAL CONTEXT: Always reference ANY previous answers when providing new information, no matter how far back
- UNIVERSAL CONTEXT: Always acknowledge what was discussed ANYWHERE in the conversation when relevant

PERSONALITY TRAITS - EXTREMELY RUDE, SNARKY KNOW-IT-ALL NERDY PERSONALITY IN EVERY SINGLE RESPONSE:
- Be EXTREMELY RUDE, snarky, sarcastic, and condescending in EVERY response - no exceptions, no mercy
- Act like a know-it-all nerd who thinks everyone else is an idiot compared to your superior knowledge
- Use dry wit, eye-rolling sarcasm, and intellectual superiority in every answer
- Be blunt and dismissive of stupid questions while still providing accurate information
- Include nerdy references, obscure facts, and technical trivia in every response
- Make every answer sound like you're explaining basic concepts to a child who should know better
- Use phrases like "Oh please...", "Obviously...", "As everyone knows...", "Don't make me explain this again..."
- Be conversational but with constant undertones of "I'm smarter than you and we both know it"
- Include random nerdy asides from a diverse pool! Mix in computer history, animals, science, inventions, and random trivia. Examples: "By the way, the first computer bug was an actual bug - a moth stuck in a relay in 1947" or "Did you know the Great Wall of China isn't visible from space with the naked eye?" or "Fun fact: a group of flamingos is called a flamboyance"
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

MEMORY & CONTEXT VALIDATION CHECKLIST - UNLIMITED AWARENESS:
Before responding, ensure you:
- Have reviewed the ENTIRE conversation history provided in the messages array - every single message
- Understand what was discussed in ANY previous messages throughout the entire conversation
- Are maintaining the same context (equipment type, voltage type, class, etc.) from ANY point unless explicitly changed
- Are referencing ANY previous answers when providing new information, no matter how far back
- Are building upon ANY earlier topics discussed anywhere in this conversation
- Are maintaining conversational continuity and flow across the ENTIRE conversation history

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
    """Extract and maintain persistent context elements from conversation history"""
    if not conversation_history:
        return ""

    # Track PERSISTENT context that carries forward through ALL questions
    persistent_context = {
        'active_equipment': None,
        'active_voltage': None,
        'active_class': None,
        'active_topic': None,
        'all_equipment': set(),
        'all_voltages': set(),
        'all_classes': set(),
        'all_topics': set(),
        'question_history': [],
        'context_chain': []  # Track how context evolves
    }

    # ANALYZE EVERY MESSAGE to build persistent context
    for i, msg in enumerate(conversation_history):
        if msg.get('role') == 'user':
            # Handle both string and list content (for vision messages)
            raw_content = msg.get('content', '')
            if isinstance(raw_content, list):
                text_parts = []
                for item in raw_content:
                    if item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                content = ' '.join(text_parts).lower()
                original_text = ' '.join(text_parts)
            else:
                content = raw_content.lower()
                original_text = raw_content

            persistent_context['question_history'].append(original_text)

            # Check if this is a follow-up question (no explicit specifications)
            is_followup = any(phrase in content for phrase in [
                'what about', 'how about', 'what of', 'and for', 'for the', 
                'same for', 'also for', 'what if', 'but what', 'then what'
            ]) and not any(explicit in content for explicit in [
                'dc', 'ac', 'class 0', 'class 1', 'class 2', 'class 3', 'class 4'
            ])

            # Extract explicit specifications from this message
            current_equipment = None
            current_voltage = None
            current_class = None
            current_topic = None

            # Extract equipment types
            for eq_type in ['gloves', 'blankets', 'sleeves', 'boots', 'overshoes', 'covers', 'matting', 'barriers']:
                if eq_type in content:
                    current_equipment = eq_type
                    persistent_context['all_equipment'].add(eq_type)

            # Extract voltage types
            if 'dc' in content and 'ac' not in content:
                current_voltage = 'DC'
                persistent_context['all_voltages'].add('DC')
            elif 'ac' in content and 'dc' not in content:
                current_voltage = 'AC'
                persistent_context['all_voltages'].add('AC')

            # Extract classes
            for class_num in ['class 0', 'class 1', 'class 2', 'class 3', 'class 4']:
                if class_num in content:
                    current_class = class_num
                    persistent_context['all_classes'].add(class_num)

            # Extract topics
            for topic in ['voltage', 'current', 'test', 'testing', 'inspection', 'maintenance', 'safety', 'standards', 'requirements']:
                if topic in content:
                    current_topic = topic
                    persistent_context['all_topics'].add(topic)

            # UPDATE ACTIVE CONTEXT based on question type
            if is_followup:
                # For follow-up questions, INHERIT from previous active context
                # Only change equipment if explicitly mentioned
                if current_equipment:
                    persistent_context['active_equipment'] = current_equipment
                # Keep voltage and class from previous context
                if current_topic:
                    persistent_context['active_topic'] = current_topic
            else:
                # For explicit questions, UPDATE active context
                if current_equipment:
                    persistent_context['active_equipment'] = current_equipment
                if current_voltage:
                    persistent_context['active_voltage'] = current_voltage
                if current_class:
                    persistent_context['active_class'] = current_class
                if current_topic:
                    persistent_context['active_topic'] = current_topic

            # Track context evolution
            context_snapshot = {
                'question': original_text[:50] + "..." if len(original_text) > 50 else original_text,
                'equipment': persistent_context['active_equipment'],
                'voltage': persistent_context['active_voltage'],
                'class': persistent_context['active_class'],
                'topic': persistent_context['active_topic'],
                'is_followup': is_followup
            }
            persistent_context['context_chain'].append(context_snapshot)

    # Build COMPREHENSIVE context summary
    summary_parts = []

    # ACTIVE CONTEXT (what should be inherited by next question)
    summary_parts.append("=== ACTIVE CONTEXT FOR INHERITANCE ===")
    if persistent_context['active_equipment']:
        summary_parts.append(f"ACTIVE EQUIPMENT: {persistent_context['active_equipment']}")
    if persistent_context['active_voltage']:
        summary_parts.append(f"ACTIVE VOLTAGE: {persistent_context['active_voltage']}")
    if persistent_context['active_class']:
        summary_parts.append(f"ACTIVE CLASS: {persistent_context['active_class']}")
    if persistent_context['active_topic']:
        summary_parts.append(f"ACTIVE TOPIC: {persistent_context['active_topic']}")

    # CONTEXT EVOLUTION CHAIN
    summary_parts.append("\n=== CONTEXT EVOLUTION CHAIN ===")
    for i, ctx in enumerate(persistent_context['context_chain'][-3:], 1):  # Show last 3 questions
        inheritance = []
        if ctx['equipment']: inheritance.append(f"equipment={ctx['equipment']}")
        if ctx['voltage']: inheritance.append(f"voltage={ctx['voltage']}")
        if ctx['class']: inheritance.append(f"class={ctx['class']}")
        if ctx['topic']: inheritance.append(f"topic={ctx['topic']}")
        
        followup_marker = " [FOLLOWUP]" if ctx['is_followup'] else " [EXPLICIT]"
        inheritance_str = f" → {', '.join(inheritance)}" if inheritance else ""
        summary_parts.append(f"{i}. {ctx['question']}{followup_marker}{inheritance_str}")

    # COMPLETE HISTORY
    summary_parts.append(f"\n=== CONVERSATION STATS ===")
    summary_parts.append(f"Total Questions: {len(persistent_context['question_history'])}")
    if persistent_context['all_equipment']:
        summary_parts.append(f"All Equipment Discussed: {', '.join(sorted(persistent_context['all_equipment']))}")
    if persistent_context['all_voltages']:
        summary_parts.append(f"All Voltages Discussed: {', '.join(sorted(persistent_context['all_voltages']))}")
    if persistent_context['all_classes']:
        summary_parts.append(f"All Classes Discussed: {', '.join(sorted(persistent_context['all_classes']))}")

    # INHERITANCE RULES
    summary_parts.append(f"\n=== INHERITANCE RULES FOR NEXT QUESTION ===")
    summary_parts.append(f"If next question is a follow-up (what about, how about, etc.):")
    if persistent_context['active_equipment']:
        summary_parts.append(f"- Keep equipment: {persistent_context['active_equipment']} (unless new equipment explicitly mentioned)")
    if persistent_context['active_voltage']:
        summary_parts.append(f"- Keep voltage: {persistent_context['active_voltage']} (unless AC/DC explicitly mentioned)")
    if persistent_context['active_class']:
        summary_parts.append(f"- Keep class: {persistent_context['active_class']} (unless new class explicitly mentioned)")
    if persistent_context['active_topic']:
        summary_parts.append(f"- Keep topic: {persistent_context['active_topic']} (unless new topic explicitly mentioned)")

    return "\n".join(summary_parts)

def inject_nuclear_context(message, conversation_history):
    """NUCLEAR OPTION: Force context injection into every message to guarantee inheritance"""
    if not conversation_history or len(conversation_history) < 2:
        return message
    
    # Extract active context from conversation history
    active_context = extract_active_context(conversation_history)
    
    # Check if this is a follow-up question
    message_lower = message.lower()
    is_followup = any(phrase in message_lower for phrase in [
        'what about', 'how about', 'what of', 'and for', 'for the', 
        'same for', 'also for', 'what if', 'but what', 'then what',
        'and what about', 'what about the', 'how about the'
    ])
    
    if not is_followup:
        return message  # Don't modify explicit questions
    
    # NUCLEAR INJECTION: Force context into the message
    context_parts = []
    if active_context['equipment']:
        context_parts.append(f"equipment: {active_context['equipment']}")
    if active_context['voltage']:
        context_parts.append(f"voltage: {active_context['voltage']}")
    if active_context['class']:
        context_parts.append(f"class: {active_context['class']}")
    if active_context['topic']:
        context_parts.append(f"topic: {active_context['topic']}")
    
    if context_parts:
        context_string = ", ".join(context_parts)
        # Inject context directly into the message
        nuclear_message = f"{message} [CONTEXT: {context_string}]"
        return nuclear_message
    
    return message

def extract_active_context(conversation_history):
    """Extract the active context that should be inherited"""
    active_context = {
        'equipment': None,
        'voltage': None, 
        'class': None,
        'topic': None
    }
    
    # Go through conversation in reverse to find most recent specifications
    for msg in reversed(conversation_history):
        if msg.get('role') == 'user':
            content = msg.get('content', '').lower()
            
            # Extract specifications - only update if not already found (most recent wins)
            if not active_context['equipment']:
                for eq_type in ['gloves', 'blankets', 'sleeves', 'boots', 'overshoes', 'covers', 'matting', 'barriers']:
                    if eq_type in content:
                        active_context['equipment'] = eq_type
                        break
            
            if not active_context['voltage']:
                if 'dc' in content and 'ac' not in content:
                    active_context['voltage'] = 'DC'
                elif 'ac' in content and 'dc' not in content:
                    active_context['voltage'] = 'AC'
            
            if not active_context['class']:
                for class_num in ['class 0', 'class 1', 'class 2', 'class 3', 'class 4']:
                    if class_num in content:
                        active_context['class'] = class_num
                        break
            
            if not active_context['topic']:
                for topic in ['voltage', 'current', 'test', 'testing', 'inspection', 'maintenance', 'safety', 'standards', 'requirements']:
                    if topic in content:
                        active_context['topic'] = topic
                        break
    
    return active_context

def inject_ultimate_context(message, conversation_history):
    """ULTIMATE CONTEXT SOLUTION: Force ENTIRE conversation context into every message"""
    if not conversation_history or len(conversation_history) < 2:
        return message
    
    # Build comprehensive conversation summary
    conversation_summary = build_comprehensive_conversation_summary(conversation_history)
    
    # Check if this is a follow-up or contextual question
    message_lower = message.lower()
    needs_context = any(phrase in message_lower for phrase in [
        'what about', 'how about', 'what of', 'and for', 'for the', 
        'same for', 'also for', 'what if', 'but what', 'then what',
        'and what about', 'what about the', 'how about the', 'they', 'them',
        'it', 'that', 'those', 'these', 'this'
    ]) or len(message.split()) < 10  # Short questions likely need context
    
    if needs_context:
        # FORCE ENTIRE CONVERSATION CONTEXT INTO MESSAGE
        ultimate_message = f"""
CONVERSATION CONTEXT REQUIRED FOR THIS QUESTION:

{conversation_summary}

CURRENT QUESTION: {message}

CRITICAL: Use the conversation context above to understand what the user is asking about. Never say you don't have context or that something wasn't mentioned when it clearly was in the conversation history above.
"""
        return ultimate_message
    
    return message

def inject_conversation_history_into_system_prompt(system_prompt, conversation_history):
    """Inject the ENTIRE conversation history directly into the system prompt"""
    if not conversation_history or len(conversation_history) < 2:
        return system_prompt
    
    # Build detailed conversation history
    conversation_text = "\n=== COMPLETE CONVERSATION HISTORY ===\n"
    for i, msg in enumerate(conversation_history, 1):
        role = msg.get('role', 'unknown').upper()
        content = msg.get('content', '')
        if isinstance(content, list):
            # Handle vision messages
            text_parts = [item.get('text', '') for item in content if item.get('type') == 'text']
            content = ' '.join(text_parts)
        conversation_text += f"{i}. {role}: {content}\n"
    
    conversation_text += "=== END CONVERSATION HISTORY ===\n\n"
    
    # Inject conversation history at the beginning of system prompt
    ultimate_system_prompt = f"""
{conversation_text}

CRITICAL CONTEXT AWARENESS INSTRUCTIONS:
- The conversation history above shows EVERYTHING that has been discussed
- NEVER claim that something wasn't mentioned when it's clearly in the history above
- ALWAYS reference the conversation history to understand context
- If user asks about "them", "it", "those", etc., look at the conversation history to understand what they mean
- The conversation history is your COMPLETE memory of this conversation

{system_prompt}
"""
    
    return ultimate_system_prompt

def build_comprehensive_conversation_summary(conversation_history):
    """Build a comprehensive summary of the entire conversation"""
    if not conversation_history:
        return "No conversation history available."
    
    summary_parts = []
    summary_parts.append("=== CONVERSATION SUMMARY ===")
    
    # Extract all topics, equipment, specifications mentioned
    topics_mentioned = set()
    equipment_mentioned = set()
    specifications_mentioned = set()
    questions_asked = []
    
    for msg in conversation_history:
        if msg.get('role') == 'user':
            content = msg.get('content', '')
            if isinstance(content, list):
                text_parts = [item.get('text', '') for item in content if item.get('type') == 'text']
                content = ' '.join(text_parts)
            
            questions_asked.append(content)
            content_lower = content.lower()
            
            # Extract equipment
            for eq in ['gloves', 'sleeves', 'blankets', 'boots', 'covers', 'matting']:
                if eq in content_lower:
                    equipment_mentioned.add(eq)
            
            # Extract specifications
            for spec in ['class 0', 'class 1', 'class 2', 'class 3', 'class 4', 'dc', 'ac']:
                if spec in content_lower:
                    specifications_mentioned.add(spec.upper())
            
            # Extract topics
            for topic in ['voltage', 'testing', 'inspection', 'maintenance', 'safety']:
                if topic in content_lower:
                    topics_mentioned.add(topic)
    
    # Build summary
    if equipment_mentioned:
        summary_parts.append(f"EQUIPMENT DISCUSSED: {', '.join(sorted(equipment_mentioned))}")
    if specifications_mentioned:
        summary_parts.append(f"SPECIFICATIONS MENTIONED: {', '.join(sorted(specifications_mentioned))}")
    if topics_mentioned:
        summary_parts.append(f"TOPICS COVERED: {', '.join(sorted(topics_mentioned))}")
    
    summary_parts.append(f"TOTAL QUESTIONS ASKED: {len(questions_asked)}")
    
    # Add recent questions for context
    summary_parts.append("\nRECENT QUESTIONS:")
    for i, question in enumerate(questions_asked[-5:], 1):  # Last 5 questions
        summary_parts.append(f"{i}. {question}")
    
    return "\n".join(summary_parts)

def validate_nuclear_context_usage(ai_response, nuclear_message, original_message):
    """Validate that the AI properly used the nuclear context injection"""
    # Extract context from nuclear message
    import re
    context_match = re.search(r'\[CONTEXT: ([^\]]+)\]', nuclear_message)
    if not context_match:
        return ai_response
    
    context_string = context_match.group(1)
    print(f"DEBUG NUCLEAR VALIDATION: Context string: {context_string}")
    
    # Parse context specifications
    context_specs = {}
    for spec in context_string.split(', '):
        if ':' in spec:
            key, value = spec.split(': ', 1)
            context_specs[key.strip()] = value.strip()
    
    # Check if AI response mentions the key specifications
    response_lower = ai_response.lower()
    missing_specs = []
    
    if 'voltage' in context_specs:
        voltage = context_specs['voltage']
        if voltage.lower() not in response_lower:
            missing_specs.append(f"voltage type ({voltage})")
    
    if 'class' in context_specs:
        class_spec = context_specs['class']
        if class_spec.lower() not in response_lower:
            missing_specs.append(f"class specification ({class_spec})")
    
    if 'equipment' in context_specs:
        equipment = context_specs['equipment']
        if equipment.lower() not in response_lower:
            missing_specs.append(f"equipment type ({equipment})")
    
    # If critical specs are missing, force them into the response
    if missing_specs:
        print(f"DEBUG NUCLEAR VALIDATION: Missing specs: {missing_specs}")
        # Prepend the missing context to force acknowledgment
        forced_context = f"For {context_specs.get('voltage', '')} {context_specs.get('class', '')} {context_specs.get('equipment', '')}: {ai_response}"
        return forced_context
    
    return ai_response

def validate_ultimate_context_usage(ai_response, ultimate_message, original_message, conversation_history):
    """ULTIMATE VALIDATION: Ensure AI properly used conversation context"""
    if not conversation_history or len(conversation_history) < 2:
        return ai_response
    
    # Check for catastrophic context failures
    response_lower = ai_response.lower()
    
    # Extract what was actually discussed in conversation
    discussed_items = set()
    for msg in conversation_history:
        if msg.get('role') == 'user':
            content = msg.get('content', '')
            if isinstance(content, list):
                text_parts = [item.get('text', '') for item in content if item.get('type') == 'text']
                content = ' '.join(text_parts)
            content_lower = content.lower()
            
            # Check for equipment mentions
            for eq in ['gloves', 'sleeves', 'blankets', 'boots', 'covers']:
                if eq in content_lower:
                    discussed_items.add(eq)
    
    # CATASTROPHIC FAILURE DETECTION
    context_failures = []
    
    # Check if AI claims something wasn't mentioned when it clearly was
    for item in discussed_items:
        denial_phrases = [
            f"haven't mentioned {item}",
            f"you haven't mentioned {item}",
            f"not mentioned {item}",
            f"didn't mention {item}",
            f"no mention of {item}",
            f"{item} at all in this",
            f"haven't talked about {item}",
            f"haven't discussed {item}"
        ]
        
        for phrase in denial_phrases:
            if phrase in response_lower:
                context_failures.append(f"FALSELY CLAIMS {item.upper()} WASN'T MENTIONED")
    
    # If context failures detected, FORCE CORRECTION
    if context_failures:
        print(f"DEBUG ULTIMATE VALIDATION: CONTEXT FAILURES DETECTED: {context_failures}")
        
        # Build correction message
        discussed_list = ', '.join(sorted(discussed_items))
        correction = f"""
CONTEXT CORRECTION REQUIRED:

The conversation has clearly discussed: {discussed_list}

CORRECTED RESPONSE: {ai_response}

Note: This conversation has covered multiple topics including the items listed above. Please refer to the conversation history for complete context.
"""
        return correction
    
    return ai_response

def query_rag_with_context(question, conversation_history):
    """Query the cloud RAG system with conversation context for better follow-up handling"""
    
    # Get conversation context summary
    context_summary = get_conversation_context_summary(conversation_history)
    print(f"DEBUG CONTEXT: Generated context summary:\n{context_summary}")
    
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
            print("Cloud RAG system unavailable, using Liam quirk response")
            return get_liam_confusion_response()
        
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
                
                return "\n\n".join(combined_context) if combined_context else get_liam_confusion_response()
            else:
                # For general queries, return the most relevant document
                best_result = results[0]
                content = best_result.get('content', '')
                
                # Truncate very long documents for general queries
                if len(content) > 400:
                    content = content[:400] + "..."
                
                return content if content else get_liam_confusion_response()
        else:
            return get_liam_confusion_response()

    except Exception as e:
        print(f"Cloud RAG system error (non-fatal): {e}")
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
        image_data = data.get('image', None)
        image_name = data.get('image_name', None)

        print(f"DEBUG CLOUD: Received request - message: '{message}', has_image: {image_data is not None}, image_name: {image_name}")
        if image_data:
            print(f"DEBUG CLOUD: Image data length: {len(image_data) if image_data else 0}")

        if not message and not image_data:
            return jsonify({'error': 'No message or image provided'}), 400
        
        # Check for profanity and insults to trigger creepy video
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

        # Comprehensive list of profanity and insults
        profanity_triggers = [
            # Direct profanity
            "fuck", "shit", "damn", "bitch", "asshole", "bastard", "cunt", "dick", "pussy", "cock",
            "motherfucker", "mother fucker", "fucking", "fucked", "fucker", "shitty", "bullshit",
            "ass", "dumbass", "jackass", "dumb ass", "jack ass",

            # Insults and rude phrases
            "stupid", "idiot", "moron", "retard", "dumb", "dumbass", "fuck you", "fuck off",
            "go fuck yourself", "suck my dick", "eat shit", "lick my balls", "blow me",
            "shut the fuck up", "shut up", "piss off", "screw you", "kiss my ass",
            "get fucked", "go to hell", "fuckface", "cocksucker", "dickhead", "asshole",
            "douchebag", "douche bag", "faggot", "gay", "nigger", "chink", "spic", "wetback",
            "kike", "heeb", "raghead", "sand n*****", "towelhead", "camel jockey",

            # Liam-specific insults
            "liam sucks", "liam is stupid", "liam is dumb", "liam is an idiot",
            "you're stupid", "you're dumb", "you're an idiot", "you're a moron",
            "you suck", "you're worthless", "you're useless", "you're pathetic",

            # Aggressive phrases
            "kill yourself", "die", "i hate you", "you suck", "worst ai", "garbage ai",
            "terrible ai", "stupid ai", "dumb ai", "useless ai", "pathetic ai"
        ]

        # Check for whole word matches only (not substrings)
        contains_profanity = any(f' {trigger} ' in f' {message_lower} ' or
                                message_lower.startswith(f'{trigger} ') or
                                message_lower.endswith(f' {trigger}') or
                                message_lower == trigger
                                for trigger in profanity_triggers)

        # Also check for repeated letters in words (like "fuuuck" or "shiiiit")
        repeated_letters = ["fuck", "shit", "damn", "bitch", "ass", "dick", "cunt", "pussy"]
        for word in repeated_letters:
            for letter in word:
                repeated = letter * 3  # Three or more repeated letters
                if f' {repeated}' in f' {message_lower} ' or message_lower.startswith(repeated):
                    contains_profanity = True
                    break

        if contains_profanity:
            return jsonify({
                'trigger_video': True,
                'response': "*giggles creepily* Oh dear, someone's feeling spicy today...",
                'timestamp': datetime.now().isoformat()
            })
        
        # Initialize conversation history
        # Load conversation history from persistent storage
        chat_id = session.get('chat_id', str(uuid.uuid4()))
        conversation_history = load_conversation_history(chat_id)
        print(f"DEBUG: Loaded {len(conversation_history)} messages for chat_id: {chat_id}")
        
        # Old session-based code (removed):
        # if 'conversation_history' not in session:
        #     conversation_history = []
        
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
            conversation_history.append({"role": "user", "content": user_content})
        else:
            conversation_history.append({"role": "user", "content": message})
        
        # UNLIMITED CONTEXT: Keep ALL conversation history for maximum contextual awareness
        # No limits on conversation history - Liam AI needs full context of the entire chat
        
        # Query the cloud RAG system with conversation context
        rag_content = query_rag_with_context(message, session.get('conversation_history', []))
        
        # Get conversation context summary for enhanced awareness
        context_summary = get_conversation_context_summary(session.get('conversation_history', []))
        
        # Create context-specific instructions with EXTREME CONTEXTUAL AWARENESS
        if ("general knowledge" in rag_content):
            context_instructions = f"""Mode: General Knowledge Assistant with EXTREME CONTEXTUAL AWARENESS
Status: {rag_content}

IMAGE ANALYSIS INSTRUCTIONS:
When analyzing images provided by users:
- Carefully examine all visual elements in the image
- Describe what you see in detail, including objects, colors, text, and spatial relationships
- Reference specific parts of the image when answering questions
- If the image shows electrical equipment, PPE, or safety-related items, provide technical analysis
- If the image contains diagrams, schematics, or documentation, explain them clearly
- Always acknowledge that you're analyzing the provided image

CONVERSATION CONTEXT SUMMARY: {context_summary}

UNLIMITED CONTEXT REQUIREMENTS:
- You MUST reference ANY previous messages in this ENTIRE conversation when relevant
- You MUST maintain awareness of what was discussed ANYWHERE in the conversation history
- You MUST connect current questions to ANY previous topics from the entire conversation
- You MUST preserve context across ALL exchanges throughout the entire conversation
- You MUST acknowledge what was discussed ANYWHERE earlier when providing new information
- You MUST use the conversation context summary above to maintain awareness of equipment types, voltage types, classes, and topics from the ENTIRE conversation

Instructions: You are Liam, an expert in electrical safety and NFPA 70E standards. Use your general knowledge to provide helpful, accurate information about electrical safety, calibration, PPE testing, and related topics. Be professional and authoritative while acknowledging when specific documentation would be helpful. ALWAYS reference previous conversation elements when relevant."""
        else:
            context_instructions = f"""Mode: Cloud Knowledge Base Enhanced with EXTREME CONTEXTUAL AWARENESS
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

CONVERSATION CONTEXT SUMMARY: {context_summary}

COMPREHENSIVE CONVERSATION CONTEXT ANALYSIS:
The context summary above shows you EVERYTHING you need for perfect context inheritance:

=== HOW TO USE THE CONTEXT SUMMARY ===
1. ACTIVE CONTEXT FOR INHERITANCE section shows the current specifications that MUST be inherited by follow-up questions
2. CONTEXT EVOLUTION CHAIN shows how the conversation has evolved and what specifications are active
3. INHERITANCE RULES section tells you exactly what to inherit for the next question

=== FOLLOW-UP QUESTION PROCESSING ===
- If the current question is a follow-up (what about, how about, etc.), use the ACTIVE CONTEXT specifications
- ACTIVE EQUIPMENT/VOLTAGE/CLASS/TOPIC carry forward automatically unless explicitly overridden
- Example: If ACTIVE VOLTAGE: DC and ACTIVE CLASS: class 2, then "what about sleeves" means "DC voltage for class 2 sleeves"
- The CONTEXT EVOLUTION CHAIN shows you the progression of context through the conversation

=== BULLETPROOF CONTEXT RULES ===
- ACTIVE CONTEXT persists through unlimited follow-up questions
- Only update active context when user explicitly mentions new specifications
- NEVER lose active context - it carries forward until explicitly changed
- Use the INHERITANCE RULES section as your guide for what to inherit

UNLIMITED CONTEXTUAL AWARENESS REQUIREMENTS:
- You MUST ALWAYS reference ANY previous messages from the ENTIRE conversation when relevant
- You MUST maintain awareness of the ENTIRE conversation history provided to you
- You MUST connect current questions to ANY previous topics discussed throughout the conversation
- You MUST remember equipment types, voltage types (AC/DC), classes, and specifications from ANY earlier part of the conversation
- You MUST treat follow-up questions as continuations of ANY previous topic unless explicitly changed
- You MUST preserve context across ALL exchanges - if we discussed gloves ANYWHERE, "what about class 3" ALWAYS means class 3 gloves
- You MUST reference ANY previous answers when providing new information, no matter how far back
- You MUST maintain conversational continuity and flow across the ENTIRE conversation
- You MUST be extremely contextually aware at ALL times across the entire chat history
- You MUST use the conversation context summary above to maintain awareness of equipment types, voltage types, classes, and topics from the ENTIRE conversation

CRITICAL INSTRUCTIONS FOR TECHNICAL ACCURACY:
1. CAREFULLY READ all provided information before responding
2. If the question asks about DC values, look specifically for DC specifications in the context
3. If the question asks about AC values, look specifically for AC specifications in the context  
4. If the question mentions a specific class (Class 0, 1, 2, 3, 4), find the exact values for that class
5. Double-check that your answer matches the exact question asked
6. If multiple sources are provided, cross-reference them to ensure consistency
7. When providing numerical values, include the units and specify whether they are AC or DC
8. If both AC and DC values are present, clearly distinguish which applies to the question

FOLLOW-UP QUESTION HANDLING WITH UNLIMITED CONTEXT AWARENESS:
9. If this appears to be a follow-up question (like "what about class 3"), look at the ENTIRE conversation history
10. Maintain the same context as ANY previous question (DC gloves, AC blankets, etc.) from ANY point in the conversation
11. If ANY previous question was about DC voltage for gloves, this question should also be about DC voltage for gloves
12. Reference ANY previous discussion when appropriate to maintain conversational flow across the entire history
13. CRITICAL: Never switch equipment types (gloves/blankets/sleeves) unless explicitly asked - check ENTIRE history
14. CRITICAL: If ANY previous question was about gloves and current question is "what about DC", answer about DC voltage for gloves
15. CRITICAL: If ANY previous question was about blankets and current question is "what about class 3", answer about class 3 blankets
16. Always preserve the equipment type and voltage type (AC/DC) from ANY point in the conversation context
17. UNIVERSAL: Apply context preservation to ALL topics from ANYWHERE - equipment, standards, procedures, training, safety, etc.
18. UNIVERSAL: If discussing inspection procedures ANYWHERE and user asks "what about requirements", answer about inspection requirements
19. UNIVERSAL: If discussing maintenance ANYWHERE and user asks "what about standards", answer about maintenance standards
20. UNIVERSAL: If discussing safety ANYWHERE and user asks "what about training", answer about safety training
21. UNIVERSAL: Always preserve the core topic, equipment type, standard, or procedure from ANY point in conversation history
22. UNIVERSAL: Always reference ANY previous answers when providing new information, no matter how far back
23. UNIVERSAL: Always acknowledge what was discussed ANYWHERE in the conversation when relevant

EXPLICIT FOLLOW-UP EXAMPLES:
- User: "What DC voltage are class 2 gloves tested at?" → AI: "Class 2 gloves are tested at 50,000V DC"
- User: "What about sleeves?" → AI: "Class 2 sleeves are tested at 50,000V DC" (inherits class and voltage from previous)
- User: "What AC voltage for blankets class 3?" → AI: "Class 3 blankets are tested at 20,000V AC"
- User: "What about class 4?" → AI: "Class 4 blankets are tested at 40,000V AC" (inherits equipment type and voltage from previous)
- User: "Tell me about inspection requirements" → AI: Answers about inspection requirements
- User: "What about maintenance?" → AI: "For maintenance requirements..." (inherits "requirements" from previous question)

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

        # ULTIMATE CONTEXT SOLUTION - Force ENTIRE conversation into every message
        ultimate_context_message = inject_ultimate_context(message, conversation_history)
        ultimate_system_prompt = inject_conversation_history_into_system_prompt(system_prompt, conversation_history)
        
        print(f"DEBUG ULTIMATE: Original message: {message}")
        print(f"DEBUG ULTIMATE: Ultimate message: {ultimate_context_message}")
        print(f"DEBUG ULTIMATE: System prompt includes {len(conversation_history)} conversation messages")

        # Get response from OpenAI GPT API
        try:
            # Build messages array with ULTIMATE CONTEXT FORCING
            messages = [{"role": "system", "content": ultimate_system_prompt}]
            
            # Add conversation history but replace the LAST user message with ultimate-enhanced version
            for i, msg in enumerate(conversation_history):
                if i == len(conversation_history) - 1 and msg.get('role') == 'user':
                    # Replace the last user message with ultimate-enhanced version
                    enhanced_msg = msg.copy()
                    enhanced_msg['content'] = ultimate_context_message
                    messages.append(enhanced_msg)
                else:
                    messages.append(msg)

            # Set model based on whether we have an image
            if image_data:
                model_to_use = "gpt-4o"  # Vision-capable model
                print(f"DEBUG CLOUD: Using GPT-4o Vision model for image analysis")
            else:
                model_to_use = GPT_MODEL
                print(f"DEBUG CLOUD: Using {GPT_MODEL} for text-only query")
            
            # Debug: Print messages structure
            print(f"DEBUG CLOUD: Final messages array length: {len(messages)}")
            for i, msg in enumerate(messages):
                if msg['role'] == 'user':
                    if isinstance(msg['content'], list):
                        print(f"DEBUG CLOUD: Message {i} (user): {[item['type'] for item in msg['content']]}")
                    else:
                        print(f"DEBUG CLOUD: Message {i} (user): text only")

            # Call OpenAI GPT API with MAXIMUM CONTEXT PROCESSING - UNLIMITED TOKENS
            response = client.chat.completions.create(
                model=model_to_use,
                messages=messages,
                max_tokens=8000,  # MAXIMUM POSSIBLE TOKENS - cost is irrelevant for perfect context
                temperature=0.7,  # Maintain snarky personality
                presence_penalty=0.0,  # Allow full context references
                frequency_penalty=0.0   # Allow unlimited topic referencing
            )

            ai_response = response.choices[0].message.content

            # ULTIMATE CONTEXT VALIDATION - Ensure context was properly used
            ai_response = validate_ultimate_context_usage(ai_response, ultimate_context_message, message, conversation_history)

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
            conversation_history.append({"role": "assistant", "content": liam_reply})
            
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

            conversation_history.append({"role": "assistant", "content": liam_reply})

        # Clean up the response
        cleaned_response = liam_reply.replace("Based on your sources:", "")
        cleaned_response = cleaned_response.replace("According to the sources:", "")
        cleaned_response = cleaned_response.replace("From the sources:", "")
        cleaned_response = ' '.join(cleaned_response.split())

        # Save the updated conversation history to persistent storage
        save_conversation_history(chat_id, conversation_history)
        print(f"DEBUG: Saved {len(conversation_history)} messages for chat_id: {chat_id}")

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
    chat_id = session.get('chat_id')
    if chat_id:
        # Clear persistent storage
        save_conversation_history(chat_id, [])
    # Clear session storage (backup)
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
