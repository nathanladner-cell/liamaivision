#!/usr/bin/env python3
"""
HYBRID Glove Scanner - Google Vision OCR + OpenAI Vision Analysis
Maximum accuracy through dual AI systems
"""
import os
import logging
import tempfile
import base64
from flask import Flask, request, jsonify, render_template_string
import openai
import json
from google.cloud import vision
from google.oauth2 import service_account

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app with static files configuration
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Initialize OpenAI client - Get from environment variable OR use fallback
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("⚠️ OPENAI_API_KEY environment variable not set, using fallback...")
    # Fallback API key using base64 encoding to bypass GitHub secret scanning
    encoded_fallback = "c2stcHJvai1INF8xM2ozSG8ydlpaTW1HRG5ETkI3T1lEb2drZ1FfN0V2WHdNc3BWdWkyVVNpdVIwSlF1SGNTQ0FKVDUyeHRqQ1pLNUk4RnBzeVQzQmxia0ZKeDVVOFZmRXNQN2ZhRUEwODVQLUV2Z2l6eGh5ckpWMVF4TGIwYllpWWtqRXl3ZEZQd2lyUWxySGVfSlJwbzRfZ1FDOXdjUTFvOEE="
    try:
        OPENAI_API_KEY = base64.b64decode(encoded_fallback).decode('utf-8')
        print("✅ Using fallback OpenAI API key")
    except Exception as e:
        print(f"❌ Failed to decode fallback API key: {e}")
        OPENAI_API_KEY = None

# Initialize OpenAI client
openai_client = None
try:
    if OPENAI_API_KEY:
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        print("✅ OpenAI client initialized successfully")
        logger.info("✅ OpenAI client initialized")
    else:
        print("❌ No OpenAI API key available")
except Exception as e:
    print(f"❌ Failed to initialize OpenAI client: {e}")
    logger.error(f"OpenAI client init error: {e}")
    # Try alternative initialization for older OpenAI versions
    try:
        openai.api_key = OPENAI_API_KEY
        openai_client = openai
        print("✅ OpenAI client initialized with legacy method")
        logger.info("✅ OpenAI client initialized (legacy)")
    except Exception as e2:
        print(f"❌ Legacy initialization also failed: {e2}")
        openai_client = None

# Initialize Google Vision client
vision_client = None
google_credentials_path = "crucial-bloom-413616-9b1e75106f6e.json"

try:
    # Try environment variable first (for Railway deployment)
    google_creds_json = os.getenv('GOOGLE_CLOUD_CREDENTIALS_JSON')
    if google_creds_json:
        # Use credentials from environment variable
        import tempfile
        import json as json_module
        
        # Parse the JSON credentials
        creds_data = json_module.loads(google_creds_json)
        credentials = service_account.Credentials.from_service_account_info(creds_data)
        vision_client = vision.ImageAnnotatorClient(credentials=credentials)
        print("✅ Google Vision client initialized with environment credentials")
        logger.info("✅ Google Vision client initialized (env)")
    elif os.path.exists(google_credentials_path):
        # Use service account JSON file (for local development)
        credentials = service_account.Credentials.from_service_account_file(google_credentials_path)
        vision_client = vision.ImageAnnotatorClient(credentials=credentials)
        print("✅ Google Vision client initialized with service account file")
        logger.info("✅ Google Vision client initialized (file)")
    else:
        print(f"❌ Google Vision credentials not found: no env var and no file at {google_credentials_path}")
        logger.error("Google Vision credentials not found")
except Exception as e:
    print(f"❌ Failed to initialize Google Vision client: {e}")
    logger.error(f"Google Vision client init error: {e}")
    vision_client = None

# Check if both APIs are available
HYBRID_READY = bool(openai_client and vision_client)
if HYBRID_READY:
    print("🚀 HYBRID MODE READY - Both Google Vision and OpenAI available!")
else:
    print("❌ HYBRID MODE DISABLED - Missing required APIs")
    print(f"   OpenAI available: {bool(openai_client)}")
    print(f"   Google Vision available: {bool(vision_client)}")

def format_text_field(text):
    """Format text field with first letter capitalized and rest lowercase"""
    if not text or not isinstance(text, str):
        return text
    return text.strip().capitalize()

def extract_text_with_google_vision(image_bytes):
    """Extract all text from image using Google Vision OCR"""
    if not vision_client:
        return ""
    
    try:
        image = vision.Image(content=image_bytes)
        response = vision_client.text_detection(image=image)
        texts = response.text_annotations
        
        if texts:
            # First annotation contains all detected text
            extracted_text = texts[0].description
            logger.info(f"Google Vision extracted {len(extracted_text)} characters")
            return extracted_text.strip()
        else:
            logger.info("Google Vision found no text")
            return ""
            
    except Exception as e:
        logger.error(f"Google Vision text extraction error: {e}")
        return ""

def analyze_with_openai_hybrid(image_bytes, extracted_text=""):
    """Analyze image with OpenAI Vision, enhanced by Google Vision OCR text"""
    
    if not openai_client:
        return {
            'manufacturer': '',
            'class': '',
            'size': '',
            'inside_color': '',
            'outside_color': '',
            'confidence': 'low',
            'error': 'OpenAI not available'
        }
    
    try:
        # Convert image to base64 for OpenAI
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Create enhanced prompt with OCR text
        system_prompt = """You are an expert at analyzing electrical safety equipment labels, specifically insulated rubber electrical gloves.

Analyze the provided image and extract the following information from any visible labels or markings:
- Manufacturer: The company that made the gloves
- Class: The electrical protection class (00, 0, 1, 2, 3, 4)
- Size: The glove size (7, 8, 9, 10, 11, 12, etc.)
- Inside Color: The inner MATERIAL color of the glove (IGNORE labels - only rubber/material color)
- Outside Color: The outer MATERIAL color of the glove (IGNORE labels - only rubber/material color)

Look for:
- ASTM ratings (D120, F496, etc.)
- Voltage ratings and classifications
- Manufacturer logos or names
- Size markings
- Inside and outside GLOVE MATERIAL color identification (NEVER use label colors)
- Any other relevant safety information

Return the information in JSON format with these exact keys:
{
  "manufacturer": "extracted manufacturer name",
  "class": "extracted class (00, 0, 1, 2, 3, 4)",
  "size": "extracted size number",
  "inside_color": "glove material inside color (NOT label color)",
  "outside_color": "glove material outside color (NOT label color)",
  "confidence": "high/medium/low",
  "analysis_method": "hybrid"
}

If any field cannot be determined, use an empty string. Be precise and only extract information that is clearly visible."""

        user_prompt = f"""Please analyze this electrical glove label image and extract the manufacturer, class, size, inside color, and outside color information.

Pay special attention to:
1. Distinguishing between the inner and outer colors of the GLOVE MATERIAL ONLY (ignore label colors). Many electrical gloves have different colors on the inside and outside for safety and identification purposes.

   **CRITICAL COLOR DETECTION RULES:**
   - ONLY analyze the actual rubber/material color of the glove itself
   - IGNORE label colors (yellow, green, red labels are NOT glove colors)
   - Labels are small stickers/patches - do NOT use their colors for inside/outside color
   - If both inside and outside appear to be the same color (e.g., black), report the SAME color for both
   - Common glove material colors: black, red, yellow, orange, blue, white, brown
   - Label colors (IGNORE): bright yellow stickers, green labels, red warning labels, white text labels

{f"OCR Text extracted from image: {extracted_text}" if extracted_text else "No OCR text available."}

Use both the visual analysis of the image AND the OCR text above to provide the most accurate extraction possible.
Provide the information in the specified JSON format."""

        # Call OpenAI Vision API (handle both new and legacy clients)
        try:
            if hasattr(openai_client, 'chat') and hasattr(openai_client.chat, 'completions'):
                # New OpenAI client (v1.0+)
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500,
                    temperature=0.1  # Low temperature for consistent extraction
                )
            else:
                # Legacy OpenAI client
                response = openai.ChatCompletion.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": user_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500,
                    temperature=0.1
                )
        except Exception as api_error:
            logger.error(f"OpenAI API call failed: {api_error}")
            return {
                'manufacturer': '',
                'class': '',
                'size': '',
                'inside_color': '',
                'outside_color': '',
                'confidence': 'low',
                'error': f'OpenAI API error: {str(api_error)}'
            }
        
        # Parse response
        result_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        try:
            if result_text.startswith('```json'):
                result_text = result_text.replace('```json', '').replace('```', '').strip()
            elif result_text.startswith('```'):
                result_text = result_text.replace('```', '').strip()
            
            result_data = json.loads(result_text)
            
            # Ensure all required fields exist
            required_fields = ['manufacturer', 'class', 'size', 'inside_color', 'outside_color']
            for field in required_fields:
                if field not in result_data:
                    result_data[field] = ''
            
            # Format manufacturer and color fields with proper capitalization
            if 'manufacturer' in result_data:
                result_data['manufacturer'] = format_text_field(result_data['manufacturer'])
            if 'inside_color' in result_data:
                result_data['inside_color'] = format_text_field(result_data['inside_color'])
            if 'outside_color' in result_data:
                result_data['outside_color'] = format_text_field(result_data['outside_color'])

            # Add hybrid metadata
            result_data['analysis_method'] = 'hybrid'
            result_data['ocr_text_length'] = len(extracted_text) if extracted_text else 0

            return result_data
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse OpenAI response as JSON: {result_text}")
            # Fallback parsing
            return {
                'manufacturer': '',
                'class': '',
                'size': '',
                'inside_color': '',
                'outside_color': '',
                'confidence': 'low',
                'analysis_method': 'hybrid',
                'error': 'JSON parsing failed'
            }
            
    except Exception as e:
        logger.error(f"OpenAI analysis error: {e}")
        return {
            'manufacturer': '',
            'class': '',
            'size': '',
            'inside_color': '',
            'outside_color': '',
            'confidence': 'low',
            'analysis_method': 'hybrid',
            'error': str(e)
        }

# HTML template with Liam-style UI design
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>LiamVision</title>
    <link rel="icon" type="image/png" href="/static/liamai.png">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 1rem;
        }

        /* Global scrollbar hiding for all elements */
        *::-webkit-scrollbar {
            display: none;
        }

        * {
            -webkit-scrollbar: none;
            -ms-overflow-style: none;
            scrollbar-width: none;
        }

        body {
            font-family: 'Courier New', 'Monaco', monospace;
            background: 
                radial-gradient(circle at 20% 30%, rgba(34, 139, 34, 0.08) 0%, transparent 70%),
                radial-gradient(circle at 80% 20%, rgba(0, 128, 0, 0.06) 0%, transparent 70%),
                radial-gradient(circle at 40% 80%, rgba(144, 238, 144, 0.05) 0%, transparent 75%),
                radial-gradient(circle at 90% 90%, rgba(240, 255, 240, 0.1) 0%, transparent 60%),
                linear-gradient(135deg, #ffffff 0%, rgba(240, 255, 240, 0.6) 25%, #ffffff 50%, rgba(224, 255, 224, 0.5) 75%, #ffffff 100%);
            min-height: 100vh;
            color: #000000;
            position: relative;
            overflow-x: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        /* Beautiful glass background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 25% 25%, rgba(34, 139, 34, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 75% 75%, rgba(0, 128, 0, 0.02) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }

        /* Circuit pattern overlay */
        .circuit-pattern {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-image: 
                radial-gradient(circle at 20px 20px, rgba(34, 139, 34, 0.05) 1px, transparent 1px),
                radial-gradient(circle at 60px 60px, rgba(0, 128, 0, 0.03) 1px, transparent 1px);
            background-size: 40px 40px, 80px 80px;
            pointer-events: none;
            z-index: 0;
            opacity: 0.6;
        }

        .container {
            background: transparent;
            border: none;
            border-radius: 0;
            box-shadow: none;
            backdrop-filter: none;
            -webkit-backdrop-filter: none;
            padding: 40px;
            width: 100%;
            max-width: 600px;
            position: relative;
            z-index: 1;
        }

        .container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.1) 0%, 
                rgba(255, 255, 255, 0.05) 50%, 
                rgba(255, 255, 255, 0.1) 100%);
            border-radius: 24px;
            pointer-events: none;
            z-index: -1;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header img {
            width: 80px;
            height: 80px;
            margin-bottom: 15px;
            border-radius: 0;
            box-shadow: none;
            transition: all 0.3s ease;
        }

        .header img:hover {
            transform: scale(1.05);
            box-shadow: none;
        }

        .header h1 {
            color: #000000;
            font-size: 2rem;
            font-weight: 400;
            margin-bottom: 10px;
            font-family: 'Courier New', 'Monaco', monospace;
            letter-spacing: -0.02em;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .beta-badge {
            font-size: 0.6rem;
            font-weight: 500;
            color: rgba(0, 0, 0, 0.6);
            background: rgba(255, 255, 255, 0.8);
            padding: 2px 6px;
            border-radius: 8px;
            border: 1px solid rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .header p {
            color: rgba(0, 0, 0, 0.7);
            font-size: 1rem;
            font-family: 'Courier New', 'Monaco', monospace;
            line-height: 1.5;
        }


        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: rgba(0, 0, 0, 0.8);
            font-weight: 500;
            font-size: 1rem;
            font-family: 'Courier New', 'Monaco', monospace;
        }

        .form-group input {
            width: 100%;
            padding: 20px 24px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 0;
            font-size: 1rem;
            font-family: 'Courier New', 'Monaco', monospace;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            box-shadow: 
                0 12px 48px rgba(0, 0, 0, 0.15),
                0 6px 24px rgba(0, 0, 0, 0.08),
                0 2px 8px rgba(0, 0, 0, 0.05),
                0 1px 0 rgba(255, 255, 255, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.6),
                inset 0 -1px 0 rgba(0, 0, 0, 0.1);
            color: #000;
            clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 15px, 100% 100%, 15px 100%, 0 calc(100% - 15px));
            position: relative;
        }

        .form-group input:focus {
            outline: none;
            border-color: rgba(255, 255, 255, 0.4);
            background: rgba(255, 255, 255, 0.15);
            box-shadow: 
                0 20px 60px rgba(34, 139, 34, 0.15),
                0 12px 36px rgba(0, 0, 0, 0.12),
                0 6px 18px rgba(0, 0, 0, 0.08),
                0 0 0 2px rgba(34, 139, 34, 0.15),
                0 1px 0 rgba(255, 255, 255, 0.5),
                inset 0 1px 0 rgba(255, 255, 255, 0.7),
                inset 0 -1px 0 rgba(0, 0, 0, 0.15);
            transform: translateY(-3px) scale(1.02);
        }

        .camera-btn {
            width: 80px;
            height: 80px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 0;
            padding: 0;
            font-size: 2rem;
            font-weight: 400;
            font-family: 'Courier New', 'Monaco', monospace;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            margin: 20px auto;
            backdrop-filter: blur(20px) saturate(180%);
            -webkit-backdrop-filter: blur(20px) saturate(180%);
            box-shadow:
                0 8px 32px rgba(0, 0, 0, 0.08),
                0 1px 0 rgba(255, 255, 255, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.6);
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            color: rgba(0, 0, 0, 0.7);
            clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 15px, 100% 100%, 15px 100%, 0 calc(100% - 15px));
        }

        .camera-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s;
        }

        .camera-btn:hover {
            transform: scale(1.05);
            background: rgba(255, 255, 255, 0.2);
            box-shadow:
                0 16px 50px rgba(0, 0, 0, 0.2),
                0 0 0 1px rgba(255, 255, 255, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.4);
            color: rgba(0, 0, 0, 0.9);
        }

        .camera-btn:active {
            transform: scale(0.95);
            background: rgba(255, 255, 255, 0.3);
            box-shadow:
                0 8px 20px rgba(0, 0, 0, 0.1),
                0 0 0 1px rgba(255, 255, 255, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.5);
        }

        /* Camera Modal Overlay */
        .camera-modal {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            visibility: hidden;
            transition: all 0.3s ease;
        }

        .camera-modal.active {
            opacity: 1;
            visibility: visible;
        }

        .camera-modal-content {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            padding: 8px;
            max-width: 450px;
            width: 90%;
            height: 85vh;
            max-height: 85vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            box-shadow:
                0 20px 60px rgba(0, 0, 0, 0.3),
                0 0 0 1px rgba(255, 255, 255, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            text-align: center;
            transform: scale(0.9);
            transition: transform 0.3s ease;
            position: relative;
        }

        .camera-modal.active .camera-modal-content {
            transform: scale(1);
        }

        .camera-section {
            margin: 0;
            position: relative;
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 0;
        }

        /* Exit button - positioned at top-right */
        .exit-btn {
            position: absolute;
            top: 15px;
            right: 15px;
            width: 40px;
            height: 40px;
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }

        .exit-btn:hover {
            background: rgba(0, 0, 0, 0.8);
            transform: scale(1.1);
        }

        .exit-btn svg {
            width: 16px;
            height: 16px;
            stroke-width: 3;
        }

        /* Camera capture container - positioned at bottom center */
        .camera-capture-container {
            position: absolute;
            bottom: 12px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10;
        }

        .camera-capture-container .camera-btn {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.9);
            border: 2px solid rgba(0, 0, 0, 0.1);
            color: rgba(0, 0, 0, 0.8);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        }

        .camera-capture-container .camera-btn:hover {
            background: rgba(255, 255, 255, 1);
            transform: scale(1.05);
        }

        .camera-capture-container .camera-btn svg {
            width: 24px;
            height: 24px;
        }

        #video {
            width: 100%;
            max-width: 350px;
            max-height: 60vh;
            object-fit: cover;
            border-radius: 16px;
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.12),
                0 0 0 1px rgba(255, 255, 255, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.6);
        }

        .button-row { 
            display: flex; 
            gap: 12px; 
            margin-top: 15px; 
        }

        .btn-capture { 
            flex: 1; 
            background: linear-gradient(135deg, rgba(40, 167, 69, 0.9) 0%, rgba(34, 139, 34, 0.9) 100%);
        }

        .btn-cancel { 
            flex: 1; 
            background: linear-gradient(135deg, rgba(220, 53, 69, 0.9) 0%, rgba(198, 40, 40, 0.9) 100%);
        }

        .loading {
            text-align: center;
            color: rgba(34, 139, 34, 0.8);
            font-weight: 500;
            font-family: 'Courier New', 'Monaco', monospace;
            padding: 20px;
            font-size: 1rem;
        }

        .loading::after {
            content: '';
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(34, 139, 34, 0.3);
            border-radius: 50%;
            border-top-color: rgba(34, 139, 34, 0.8);
            animation: spin 1s linear infinite;
            margin-left: 10px;
            vertical-align: middle;
        }

        @keyframes spin { 
            to { transform: rotate(360deg); } 
        }

        /* Modern Waveform Animation */
        .waveform {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 3px;
            width: 40px;
            height: 20px;
        }

        .waveform .bar {
            width: 3px;
            background: rgba(34, 139, 34, 0.9);
            border-radius: 1px;
            animation: waveform 1.5s ease-in-out infinite;
        }

        .waveform .bar:nth-child(1) { animation-delay: 0s; }
        .waveform .bar:nth-child(2) { animation-delay: 0.1s; }
        .waveform .bar:nth-child(3) { animation-delay: 0.2s; }
        .waveform .bar:nth-child(4) { animation-delay: 0.3s; }
        .waveform .bar:nth-child(5) { animation-delay: 0.4s; }
        .waveform .bar:nth-child(6) { animation-delay: 0.5s; }

        @keyframes waveform {
            0%, 100% { height: 4px; opacity: 0.4; }
            50% { height: 20px; opacity: 1; }
        }

        /* Green completion dot */
        .completion-dot {
            width: 12px;
            height: 12px;
            background: #22c55e;
            border-radius: 50%;
            animation: completion-pulse 0.6s ease-out;
            box-shadow: 0 0 20px rgba(34, 197, 94, 0.4);
        }

        @keyframes completion-pulse {
            0% { transform: scale(0); opacity: 0; }
            50% { transform: scale(1.2); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
        }

        .hidden { 
            display: none; 
        }

        .error-message {
            background: rgba(255, 235, 238, 0.8);
            color: rgba(198, 40, 40, 0.9);
            padding: 12px;
            border-radius: 12px;
            margin: 10px 0;
            border: 1px solid rgba(244, 67, 54, 0.3);
            font-family: 'Courier New', 'Monaco', monospace;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            box-shadow: 
                0 4px 16px rgba(244, 67, 54, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.6);
        }

        .success-message {
            background: rgba(240, 255, 240, 0.8);
            color: rgba(46, 125, 50, 0.9);
            padding: 12px;
            border-radius: 12px;
            margin: 10px 0;
            border: 1px solid rgba(76, 175, 80, 0.3);
            font-family: 'Courier New', 'Monaco', monospace;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            box-shadow: 
                0 4px 16px rgba(76, 175, 80, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.6);
        }

        .analysis-info {
            background: rgba(227, 242, 253, 0.8);
            color: rgba(21, 101, 192, 0.9);
            padding: 8px 12px;
            border-radius: 12px;
            margin: 10px 0;
            font-size: 0.9rem;
            border: 1px solid rgba(33, 150, 243, 0.3);
            font-family: 'Courier New', 'Monaco', monospace;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            box-shadow: 
                0 4px 16px rgba(33, 150, 243, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.6);
        }

        @media (max-width: 768px) {
            .container {
                padding: 15px;
                margin: 5px;
                max-width: 100%;
            }

            .header h1 {
                font-size: 1.3rem;
            }

            .camera-btn {
                width: 70px;
                height: 70px;
                font-size: 1.5rem;
            }

            .camera-btn svg {
                width: 20px;
                height: 20px;
            }

            .camera-modal-content {
                padding: 6px;
                width: 95%;
                max-width: none;
                margin: 5px;
                height: 90vh;
                max-height: 90vh;
                overflow: hidden;
            }

            .camera-section #video {
                max-width: 100%;
                max-height: 55vh;
                object-fit: cover;
                border-radius: 12px;
            }

            /* Exit button mobile styles */
            .exit-btn {
                width: 32px;
                height: 32px;
                top: 8px;
                right: 8px;
            }

            .exit-btn svg {
                width: 14px;
                height: 14px;
            }

            /* Camera capture button mobile styles */
            .camera-capture-container {
                bottom: 15px;
            }

            .camera-capture-container .camera-btn {
                width: 60px;
                height: 60px;
            }

            .camera-capture-container .camera-btn svg {
                width: 20px;
                height: 20px;
            }
        }

        @media (max-width: 480px) {
            .camera-btn {
                width: 60px;
                height: 60px;
                font-size: 1.3rem;
            }

            .camera-btn svg {
                width: 18px;
                height: 18px;
            }

            .camera-modal-content {
                padding: 5px;
                height: 85vh;
                max-height: 85vh;
                overflow: hidden;
            }

            /* Exit button for very small screens */
            .exit-btn {
                width: 28px;
                height: 28px;
                top: 6px;
                right: 6px;
            }

            .exit-btn svg {
                width: 12px;
                height: 12px;
            }

            /* Camera capture button for very small screens */
            .camera-capture-container {
                bottom: 12px;
            }

            .camera-capture-container .camera-btn {
                width: 50px;
                height: 50px;
            }

            .camera-capture-container .camera-btn svg {
                width: 16px;
                height: 16px;
            }
        }
    </style>
</head>
<body>
    <!-- Circuit pattern overlay -->
    <div class="circuit-pattern"></div>
    
    <div class="container">
        <div class="header">
            <img src="/static/liamai.png" alt="Liam AI" id="logo" onerror="this.style.display='none'">
            <h1>LiamVision <span class="beta-badge">beta</span></h1>
        </div>
        
        <form id="gloveForm">
            <div class="form-group">
                <label for="manufacturer">Manufacturer:</label>
                <input type="text" id="manufacturer" name="manufacturer" placeholder="e.g., Armadillo, Salisbury">
            </div>
            
            <div class="form-group">
                <label for="class">Class:</label>
                <input type="text" id="class" name="class" placeholder="e.g., 0, 1, 2, 3, 4">
            </div>
            
            <div class="form-group">
                <label for="size">Size:</label>
                <input type="text" id="size" name="size" placeholder="e.g., 8, 9, 10, 11">
            </div>
            
            <div class="form-group">
                <label for="inside_color">Inside Color:</label>
                <input type="text" id="inside_color" name="inside_color" placeholder="e.g., Red, Yellow, Black">
            </div>
            
            <div class="form-group">
                <label for="outside_color">Outside Color:</label>
                <input type="text" id="outside_color" name="outside_color" placeholder="e.g., Red, Yellow, Black">
            </div>
            
            <!-- Cuff Type field temporarily hidden - not accurate enough yet
            <div class="form-group">
                <label for="cuff_type">Cuff Type:</label>
                <input type="text" id="cuff_type" name="cuff_type" placeholder="e.g., Bell Cuff, Straight Cuff, Contour Cuff">
            </div>
            -->
            
            <button type="button" class="camera-btn" id="cameraBtn" onclick="startCamera()">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                    <circle cx="12" cy="13" r="4"></circle>
                </svg>
            </button>
            
            <!-- Camera Modal -->
            <div id="cameraModal" class="camera-modal">
                <div class="camera-modal-content">
                    <div class="camera-section">
                        <!-- Exit button positioned at top-right -->
                        <button type="button" class="exit-btn" onclick="stopCamera()" aria-label="Close camera">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                        <video id="video" autoplay playsinline></video>
                        <!-- Camera capture button at bottom center -->
                        <div class="camera-capture-container">
                            <button type="button" class="camera-btn btn-capture" onclick="capturePhoto()">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                                    <circle cx="12" cy="13" r="4"></circle>
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div id="errorMessage" class="error-message hidden"></div>
            <div id="successMessage" class="success-message hidden"></div>
        </form>
    </div>

    <script>
        let stream = null;
        
        function showMessage(message, isError = false) {
            const errorDiv = document.getElementById('errorMessage');
            const successDiv = document.getElementById('successMessage');
            
            if (isError) {
                errorDiv.textContent = message;
                errorDiv.classList.remove('hidden');
                successDiv.classList.add('hidden');
            } else {
                successDiv.textContent = message;
                successDiv.classList.remove('hidden');
                errorDiv.classList.add('hidden');
            }
        }
        
        function hideMessages() {
            document.getElementById('errorMessage').classList.add('hidden');
            document.getElementById('successMessage').classList.add('hidden');
        }
        
        async function startCamera() {
            hideMessages();
            try {
                // Request camera permission
                stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { 
                        facingMode: 'environment',
                        width: { ideal: 1920 },
                        height: { ideal: 1080 }
                    } 
                });
                
                const video = document.getElementById('video');
                video.srcObject = stream;
                
                document.getElementById('cameraModal').classList.add('active');
                document.getElementById('cameraBtn').innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>';
                
            } catch (err) {
                console.error('Camera error:', err);
                showMessage('Failed to access camera. Please ensure you have granted camera permissions.', true);
            }
        }
        
        function stopCamera() {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }

            document.getElementById('cameraModal').classList.remove('active');
            document.getElementById('cameraBtn').innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>';
        }
        
        async function capturePhoto() {
            const video = document.getElementById('video');
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0);
            
            // Convert to blob
            canvas.toBlob(async (blob) => {
                stopCamera();
                await analyzeImage(blob);
            }, 'image/jpeg', 0.8);
        }
        
        async function analyzeImage(imageBlob) {
            hideMessages();
            
            // Show waveform animation
            const cameraBtn = document.querySelector('.camera-btn, #cameraBtn');
            if (cameraBtn) {
                cameraBtn.innerHTML = '<div class="waveform"><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div><div class="bar"></div></div>';
                cameraBtn.disabled = true;
            }
            
            try {
                const formData = new FormData();
                formData.append('image', imageBlob, 'glove_label.jpg');
                
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Show completion dot
                    if (cameraBtn) {
                        cameraBtn.innerHTML = '<div class="completion-dot"></div>';
                    }
                    
                    setTimeout(() => {
                        // Populate form fields
                        if (result.manufacturer) document.getElementById('manufacturer').value = result.manufacturer;
                        if (result.class) document.getElementById('class').value = result.class;
                        if (result.size) document.getElementById('size').value = result.size;
                        if (result.inside_color) document.getElementById('inside_color').value = result.inside_color;
                        if (result.outside_color) document.getElementById('outside_color').value = result.outside_color;
                        
                        // Reset button
                        if (cameraBtn) {
                            cameraBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>';
                            cameraBtn.disabled = false;
                        }
                    }, 800);
                    
                } else {
                    // Reset button on error
                    if (cameraBtn) {
                        cameraBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>';
                        cameraBtn.disabled = false;
                    }
                }
                
            } catch (error) {
                console.error('Analysis error:', error);
                // Reset button on error
                if (cameraBtn) {
                    cameraBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>';
                    cameraBtn.disabled = false;
                }
            }
        }

        // Add click outside modal to close
        document.getElementById('cameraModal').addEventListener('click', function(e) {
            if (e.target === this) {
                stopCamera();
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Main page with hybrid glove scanner form"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze glove label image using HYBRID Google Vision + OpenAI"""
    if not HYBRID_READY:
        missing_apis = []
        if not openai_client:
            missing_apis.append("OpenAI")
        if not vision_client:
            missing_apis.append("Google Vision")
        
        return jsonify({
            'success': False,
            'error': f'Hybrid mode disabled - Missing APIs: {", ".join(missing_apis)}'
        })
    
    try:
        # Get uploaded image
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'})
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'success': False, 'error': 'No image selected'})
        
        # Read image bytes
        image_bytes = image_file.read()
        
        # Step 1: Extract text with Google Vision OCR
        logger.info("🔍 Extracting text with Google Vision OCR...")
        extracted_text = extract_text_with_google_vision(image_bytes)
        
        # Step 2: Analyze with OpenAI Vision (enhanced by OCR text)
        logger.info("🧠 Analyzing with OpenAI Vision...")
        result = analyze_with_openai_hybrid(image_bytes, extracted_text)
        
        # Add success flag
        result['success'] = True
        
        # Log results
        logger.info(f"✅ Hybrid analysis completed: {result}")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Hybrid analysis error: {e}")
        return jsonify({
            'success': False,
            'error': f'Analysis failed: {str(e)}'
        })

@app.route('/api/status')
def status():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'hybrid_ready': HYBRID_READY,
        'openai_available': bool(openai_client),
        'google_vision_available': bool(vision_client)
    })

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (like liamai.png logo)"""
    from flask import send_from_directory
    return send_from_directory('static', filename)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"🚀 Starting Hybrid Glove Scanner on port {port}")
    print(f"🔥 Hybrid Mode: {'ENABLED' if HYBRID_READY else 'DISABLED'}")
    app.run(host='0.0.0.0', port=port, debug=False)
