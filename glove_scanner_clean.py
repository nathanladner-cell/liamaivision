#!/usr/bin/env python3
"""
CLEAN Glove Scanner - NO BULLSHIT VERSION
"""
import os
import logging
from flask import Flask, request, jsonify, render_template_string
import openai
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client - Get from environment variable
API_KEY = os.getenv('OPENAI_API_KEY')
if not API_KEY:
    print("❌ OPENAI_API_KEY environment variable not set!")
    print("Please set it in your Railway project Variables section")
    API_KEY = None

try:
    client = openai.OpenAI(api_key=API_KEY)
    print("✅ OpenAI client initialized successfully")
    logger.info("✅ OpenAI client initialized")
except Exception as e:
    print(f"❌ Failed to initialize OpenAI client: {e}")
    client = None

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Electrical Glove Label Scanner</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }
        .header h1 { font-size: 24px; margin-bottom: 8px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .form-content { padding: 30px 20px; }
        .form-group { margin-bottom: 20px; }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
            font-size: 14px;
        }
        .form-group input {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .camera-btn {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 16px 24px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin: 20px 0;
            transition: transform 0.2s, box-shadow 0.3s;
        }
        .camera-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }
        .camera-section { text-align: center; margin: 20px 0; }
        #video {
            width: 100%;
            max-width: 400px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .button-row { display: flex; gap: 10px; margin-top: 15px; }
        .btn-capture { flex: 1; background: #28a745; }
        .btn-cancel { flex: 1; background: #dc3545; }
        .loading {
            text-align: center;
            color: #667eea;
            font-weight: 600;
            padding: 20px;
            font-size: 16px;
        }
        .loading::after {
            content: '';
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #667eea;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 1s linear infinite;
            margin-left: 10px;
            vertical-align: middle;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .hidden { display: none; }
        .error-message {
            background: #f8d7da;
            color: #721c24;
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
            border: 1px solid #f5c6cb;
        }
        .success-message {
            background: #d4edda;
            color: #155724;
            padding: 12px;
            border-radius: 6px;
            margin: 10px 0;
            border: 1px solid #c3e6cb;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧤 Electrical Glove Label Scanner</h1>
            <p>Take a photo of your insulated electrical glove label to automatically extract information</p>
        </div>
        
        <div class="form-content">
            <form id="gloveForm">
                <div class="form-group">
                    <label for="manufacturer">Manufacturer:</label>
                    <input type="text" id="manufacturer" name="manufacturer" placeholder="e.g., Ansell, Honeywell">
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
                    <label for="color">Color:</label>
                    <input type="text" id="color" name="color" placeholder="e.g., Red, Yellow, Black">
                </div>
                
                <button type="button" class="camera-btn" id="cameraBtn" onclick="startCamera()">
                    📷 Scan Glove Label
                </button>
                
                <div id="cameraSection" class="camera-section hidden">
                    <video id="video" autoplay playsinline></video>
                    <div class="button-row">
                        <button type="button" class="camera-btn btn-capture" onclick="capturePhoto()">📸 Capture</button>
                        <button type="button" class="camera-btn btn-cancel" onclick="stopCamera()">❌ Cancel</button>
                    </div>
                </div>
                
                <div id="loading" class="loading hidden">Analyzing image</div>
                <div id="errorMessage" class="error-message hidden"></div>
                <div id="successMessage" class="success-message hidden"></div>
            </form>
        </div>
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
            
            setTimeout(() => {
                errorDiv.classList.add('hidden');
                successDiv.classList.add('hidden');
            }, 5000);
        }
        
        async function startCamera() {
            const cameraBtn = document.getElementById('cameraBtn');
            cameraBtn.disabled = true;
            cameraBtn.textContent = '📷 Starting Camera...';
            
            try {
                const constraints = {
                    video: {
                        facingMode: { ideal: 'environment' },
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    }
                };
                
                stream = await navigator.mediaDevices.getUserMedia(constraints);
                const video = document.getElementById('video');
                video.srcObject = stream;
                
                video.onloadedmetadata = () => {
                    document.getElementById('cameraSection').classList.remove('hidden');
                    cameraBtn.disabled = false;
                    cameraBtn.textContent = '📷 Scan Glove Label';
                };
                
            } catch (err) {
                console.error('Camera error:', err);
                let errorMessage = 'Camera access failed. ';
                
                if (err.name === 'NotAllowedError') {
                    errorMessage += 'Please allow camera access and try again.';
                } else if (err.name === 'NotFoundError') {
                    errorMessage += 'No camera found on this device.';
                } else {
                    errorMessage += err.message || 'Unknown error occurred.';
                }
                
                showMessage(errorMessage, true);
                cameraBtn.disabled = false;
                cameraBtn.textContent = '📷 Scan Glove Label';
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
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('manufacturer').value = result.data.manufacturer || '';
                    document.getElementById('class').value = result.data.class || '';
                    document.getElementById('size').value = result.data.size || '';
                    document.getElementById('color').value = result.data.color || '';
                    
                    showMessage('✅ Analysis complete! Form fields have been filled.', false);
                } else {
                    showMessage('❌ Analysis failed: ' + (result.error || 'Unknown error'), true);
                }
            } catch (err) {
                console.error('Analysis error:', err);
                showMessage('❌ Error analyzing image: ' + err.message, true);
            }
            
            document.getElementById('loading').classList.add('hidden');
        }
        
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            document.getElementById('cameraBtn').disabled = true;
            document.getElementById('cameraBtn').textContent = '❌ Camera Not Supported';
            showMessage('Camera is not supported on this browser or device.', true);
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

@app.route('/api/status')
def status():
    """Status check"""
    openai_test = False
    if client:
        try:
            client.models.list()
            openai_test = True
        except Exception as e:
            print(f"OpenAI test failed: {e}")
            openai_test = False

    return jsonify({
        'status': 'ok',
        'service': 'clean-glove-scanner',
        'openai_available': bool(client),
        'openai_test_passed': openai_test,
        'timestamp': '2025-09-08T22:05:00.000000'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'
    
    print("=" * 50)
    print("🚀 CLEAN GLOVE SCANNER STARTUP")
    print("=" * 50)
    print(f"📋 Port: {port}")
    print(f"📋 Host: {host}")
    print(f"📋 OpenAI Available: {bool(client)}")
    print("=" * 50)
    
    try:
        print("🌐 Starting Flask server...")
        app.run(host=host, port=port, debug=False, threaded=True)
    except Exception as e:
        print(f"❌ Failed to start Flask server: {e}")
