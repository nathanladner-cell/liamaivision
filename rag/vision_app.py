#!/usr/bin/env python3

import os
import sys
import uuid
from flask import Flask, render_template, request, jsonify, session
import openai
from google.cloud import vision
from google.oauth2 import service_account
import base64
import json
from dotenv import load_dotenv
import tempfile
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
app.secret_key = 'vision-app-secret-key-2024'

# OpenAI API setup
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    logger.warning("⚠️ OPENAI_API_KEY environment variable not set!")
    logger.warning("The app will start but vision analysis will not work")
    logger.warning("Please set OPENAI_API_KEY in your .env file")
    client = None
else:
    client = openai.OpenAI(api_key=openai_api_key)

# Google Cloud Vision API setup
GOOGLE_CLOUD_VISION_API_KEY = os.getenv('GOOGLE_CLOUD_VISION_API_KEY')

if GOOGLE_CLOUD_VISION_API_KEY:
    try:
        # Try Google AI Studio key first
        os.environ['GOOGLE_API_KEY'] = GOOGLE_CLOUD_VISION_API_KEY
        vision_client = vision.ImageAnnotatorClient()
        logger.info("✅ Google Cloud Vision API initialized with API key")
    except Exception as e:
        logger.warning(f"⚠️ Google Cloud Vision API setup with API key failed: {e}")
        logger.warning("Note: Google Cloud Vision typically requires service account JSON, not API key")
        vision_client = None
else:
    logger.warning("⚠️ Google Cloud Vision API key not configured")
    vision_client = None

# GPT model for vision
VISION_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')

@app.route('/')
def index():
    """Main vision form page"""
    return render_template('vision_form.html')

@app.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    """Analyze uploaded image for glove label information"""
    try:
        data = request.json
        image_data = data.get('image')

        if not image_data:
            return jsonify({'error': 'No image data provided'}), 400

        # Extract base64 data
        if image_data.startswith('data:image/'):
            base64_data = image_data.split(',')[1]
        else:
            base64_data = image_data

        # Decode base64 image
        image_bytes = base64.b64decode(base64_data)

        # Extract text using Google Cloud Vision (if available)
        vision_text = ""
        if vision_client:
            vision_text = extract_text_with_google_vision(image_bytes)

        # Use OpenAI Vision for analysis
        if client is None:
            return jsonify({
                'success': False,
                'error': 'OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.',
                'extracted_text': vision_text
            }), 400

            analysis_result = analyze_with_openai_vision(image_bytes, vision_text)

        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'extracted_text': vision_text
        })

    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

def extract_text_with_google_vision(image_bytes):
    """Extract text from image using Google Cloud Vision API"""
    try:
        if not vision_client:
            return ""

        # Create vision image object
        image = vision.Image(content=image_bytes)

        # Perform text detection
        response = vision_client.text_detection(image=image)

        if response.error.message:
            logger.warning(f"Google Vision API error: {response.error.message}")
            return ""

        # Extract text from response
        texts = response.text_annotations
        if texts:
            return texts[0].description.strip()

        return ""

    except Exception as e:
        logger.error(f"Google Vision text extraction error: {e}")
        return ""

def analyze_with_openai_vision(image_bytes, vision_text=""):
    """Analyze image with OpenAI Vision to extract glove information"""

    if client is None:
        return {
            'manufacturer': '',
            'class': '',
            'size': '',
            'color': '',
            'confidence': 'low',
            'error': 'OpenAI API key not configured'
        }

    # Save image to temporary file for OpenAI API
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
        temp_file.write(image_bytes)
        temp_file_path = temp_file.name

    try:
        # Read image file for OpenAI
        with open(temp_file_path, 'rb') as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        # Create prompt for glove label analysis
        system_prompt = """You are an expert at analyzing electrical safety equipment labels, specifically insulated rubber electrical gloves.

Analyze the provided image and extract the following information from any visible labels or markings:
- Manufacturer: The company that made the gloves
- Class: The electrical protection class (00, 0, 1, 2, 3, 4)
- Size: The glove size (7, 8, 9, 10, 11, 12, etc.)
- Color: The glove color (red, yellow, black, etc.)

Look for:
- ASTM ratings (D120, F496, etc.)
- Voltage ratings and classifications
- Manufacturer logos or names
- Size markings
- Color identification
- Any other relevant safety information

Return the information in JSON format with these exact keys:
{
  "manufacturer": "extracted manufacturer name",
  "class": "extracted class (00, 0, 1, 2, 3, 4)",
  "size": "extracted size number",
  "color": "extracted color",
  "confidence": "high/medium/low",
  "additional_info": "any other relevant details"
}

If any field cannot be determined, use an empty string. Be precise and only extract information that is clearly visible in the image."""

        user_prompt = f"""Please analyze this image of an electrical glove label and extract the manufacturer, class, size, and color information.

{f"Additional text extracted from image: {vision_text}" if vision_text else ""}

Provide the information in the specified JSON format."""

        # Call OpenAI Vision API
        response = client.chat.completions.create(
            model=VISION_MODEL,
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
            max_tokens=1000,
            temperature=0.1  # Low temperature for consistent extraction
        )

        result_text = response.choices[0].message.content

        # Try to parse JSON response
        try:
            # Clean the response to extract JSON
            result_text = result_text.strip()

            # Remove markdown code blocks if present
            if result_text.startswith('```json'):
                result_text = result_text[7:]
            if result_text.endswith('```'):
                result_text = result_text[:-3]

            result_text = result_text.strip()

            # Parse JSON
            analysis = json.loads(result_text)

            # Validate required fields
            required_fields = ['manufacturer', 'class', 'size', 'color']
            for field in required_fields:
                if field not in analysis:
                    analysis[field] = ""

            # Add confidence if missing
            if 'confidence' not in analysis:
                analysis['confidence'] = 'medium'

            return analysis

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {result_text}")
            # Return a basic structure if JSON parsing fails
            return {
                'manufacturer': '',
                'class': '',
                'size': '',
                'color': '',
                'confidence': 'low',
                'error': f'Failed to parse analysis: {str(e)}'
            }

    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@app.route('/api/save-analysis', methods=['POST'])
def save_analysis():
    """Save the analysis results for later reference"""
    try:
        data = request.json
        analysis_id = str(uuid.uuid4())

        # Store analysis in session (in production, you'd save to database)
        if 'analyses' not in session:
            session['analyses'] = []

        analysis_record = {
            'id': analysis_id,
            'timestamp': data.get('timestamp'),
            'manufacturer': data.get('manufacturer', ''),
            'class': data.get('class', ''),
            'size': data.get('size', ''),
            'color': data.get('color', ''),
            'confidence': data.get('confidence', 'medium')
        }

        session['analyses'].append(analysis_record)
        session.modified = True

        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'message': 'Analysis saved successfully'
        })

    except Exception as e:
        logger.error(f"Save analysis error: {e}")
        return jsonify({'error': f'Failed to save analysis: {str(e)}'}), 500

@app.route('/api/get-analyses', methods=['GET'])
def get_analyses():
    """Retrieve saved analyses"""
    try:
        analyses = session.get('analyses', [])
        return jsonify({
            'success': True,
            'analyses': analyses
        })

    except Exception as e:
        logger.error(f"Get analyses error: {e}")
        return jsonify({'error': f'Failed to retrieve analyses: {str(e)}'}), 500

@app.route('/health')
def health():
    """Basic health check"""
    return jsonify({
        'status': 'ok',
        'service': 'vision-app',
        'openai_available': bool(client),
        'google_vision_available': bool(vision_client)
    })

@app.route('/api/status')
def api_status():
    """Railway health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'vision-app',
        'message': 'Vision app is running',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    logger.info("🚀 Vision App starting...")
    logger.info(f"📋 Configuration: host={host}, port={port}, debug={debug}")
    logger.info(f"📋 OpenAI Vision: {'✅' if openai_api_key else '❌'}")
    logger.info(f"📋 Google Vision: {'✅' if vision_client else '❌'}")
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        logger.info("🌐 Running on Railway deployment")
    else:
        logger.info(f"🌐 Open browser to: http://localhost:{port}")

    app.run(host=host, port=port, debug=debug, threaded=True)
