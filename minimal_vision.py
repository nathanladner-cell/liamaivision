#!/usr/bin/env python3
"""
Minimal vision app - ONLY what's needed for glove label scanning
"""
import os
import sys
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
import openai
import base64
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client
openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        logger.info("✅ OpenAI client initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenAI client: {e}")
        logger.warning("⚠️ OpenAI client disabled - vision analysis will not work")
        client = None
else:
    client = None
    logger.warning("⚠️ No OpenAI API key - vision analysis disabled")

# HTML template for the glove scanner
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Electrical Glove Label Scanner</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }
        .camera-btn { background: #007bff; color: white; padding: 15px 30px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; margin: 20px 0; }
        .camera-btn:hover { background: #0056b3; }
        #video { width: 100%; max-width: 400px; }
        .hidden { display: none; }
        .loading { color: #666; font-style: italic; }
    </style>
</head>
<body>
    <h1>🧤 Electrical Glove Label Scanner</h1>
    
    <form id="gloveForm">
        <div class="form-group">
            <label for="manufacturer">Manufacturer:</label>
            <input type="text" id="manufacturer" name="manufacturer">
        </div>
        
        <div class="form-group">
            <label for="class">Class:</label>
            <input type="text" id="class" name="class">
        </div>
        
        <div class="form-group">
            <label for="size">Size:</label>
            <input type="text" id="size" name="size">
        </div>
        
        <div class="form-group">
            <label for="color">Color:</label>
            <input type="text" id="color" name="color">
        </div>
        
        <button type="button" class="camera-btn" onclick="startCamera()">📷 Scan Glove Label</button>
        
        <div id="cameraSection" class="hidden">
            <video id="video" autoplay></video>
            <br>
            <button type="button" class="camera-btn" onclick="capturePhoto()">📸 Capture</button>
            <button type="button" class="camera-btn" onclick="stopCamera()">❌ Cancel</button>
        </div>
        
        <div id="loading" class="loading hidden">Analyzing image...</div>
    </form>

    <script>
        let stream = null;
        
        async function startCamera() {
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: true });
                document.getElementById('video').srcObject = stream;
                document.getElementById('cameraSection').classList.remove('hidden');
            } catch (err) {
                alert('Camera access denied or not available');
            }
        }
        
        function stopCamera() {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }
            document.getElementById('cameraSection').classList.add('hidden');
        }
        
        async function capturePhoto() {
            const video = document.getElementById('video');
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);
            
            const imageData = canvas.toDataURL('image/jpeg', 0.8);
            
            stopCamera();
            document.getElementById('loading').classList.remove('hidden');
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: imageData })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('manufacturer').value = result.data.manufacturer || '';
                    document.getElementById('class').value = result.data.class || '';
                    document.getElementById('size').value = result.data.size || '';
                    document.getElementById('color').value = result.data.color || '';
                } else {
                    alert('Analysis failed: ' + result.error);
                }
            } catch (err) {
                alert('Error analyzing image: ' + err.message);
            }
            
            document.getElementById('loading').classList.add('hidden');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Main page with glove scanner form"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze glove label image using OpenAI Vision"""
    if not client:
        return jsonify({'success': False, 'error': 'OpenAI not configured'})
    
    try:
        data = request.get_json()
        image_data = data.get('image', '')
        
        if not image_data:
            return jsonify({'success': False, 'error': 'No image provided'})
        
        # Remove data URL prefix
        if 'base64,' in image_data:
            image_data = image_data.split('base64,')[1]
        
        # Call OpenAI Vision API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this electrical glove label image and extract: manufacturer, class, size, and color. Return ONLY a JSON object with these exact keys: manufacturer, class, size, color. Use empty string if not found."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        # Parse response
        result_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        try:
            if result_text.startswith('```json'):
                result_text = result_text.replace('```json', '').replace('```', '').strip()
            elif result_text.startswith('```'):
                result_text = result_text.replace('```', '').strip()
            
            result_data = json.loads(result_text)
        except json.JSONDecodeError:
            # Fallback parsing
            result_data = {
                'manufacturer': '',
                'class': '',
                'size': '',
                'color': ''
            }
        
        return jsonify({'success': True, 'data': result_data})
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health():
    """Health check"""
    return jsonify({'status': 'ok', 'service': 'minimal-vision'})

@app.route('/api/status')
def status():
    """Status check"""
    return jsonify({
        'status': 'ok',
        'service': 'minimal-vision',
        'openai_available': bool(client),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'
    
    print("=" * 50)
    print("🚀 MINIMAL VISION APP STARTUP")
    print("=" * 50)
    print(f"📋 Port: {port}")
    print(f"📋 Host: {host}")
    print(f"📋 OpenAI Available: {bool(client)}")
    print(f"📋 Environment Variables:")
    for key, value in os.environ.items():
        if 'API' in key or 'KEY' in key or 'PORT' in key:
            print(f"    {key}: {value[:20]}..." if len(str(value)) > 20 else f"    {key}: {value}")
    print("=" * 50)
    
    try:
        print("🌐 Starting Flask server...")
        app.run(host=host, port=port, debug=False, threaded=True)
    except Exception as e:
        print(f"❌ Failed to start Flask server: {e}")
        import traceback
        traceback.print_exc()
