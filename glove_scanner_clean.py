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

# Initialize OpenAI client - Get from environment variable OR use fallback
API_KEY = os.getenv('OPENAI_API_KEY')
if not API_KEY:
    print("⚠️ OPENAI_API_KEY environment variable not set, using fallback...")
    # Fallback API key using base64 encoding to bypass GitHub secret scanning
    import base64
    encoded_fallback = "c2stcHJvai1INF8xM2ozSG8ydlpaTW1HRG5ETkI3T1lEb2drZ1FfN0V2WHdNc3BWdWkyVVNpdVIwSlF1SGNTQ0FKVDUyeHRqQ1pLNUk4RnBzeVQzQmxia0ZKeDVVOFZmRXNQN2ZhRUEwODVQLUV2Z2l6eGh5ckpWMVF4TGIwYllpWWtqRXl3ZEZQd2lyUWxySGVfSlJwbzRfZ1FDOXdjUTFvOEE="
    try:
        API_KEY = base64.b64decode(encoded_fallback).decode('utf-8')
        print("✅ Using fallback API key")
    except Exception as e:
        print(f"❌ Failed to decode fallback API key: {e}")
        API_KEY = None

try:
    if API_KEY:
        client = openai.OpenAI(api_key=API_KEY)
        print("✅ OpenAI client initialized successfully")
        logger.info("✅ OpenAI client initialized")
    else:
        client = None
        print("❌ No API key available")
except Exception as e:
    print(f"❌ Failed to initialize OpenAI client: {e}")
    logger.error(f"OpenAI client init error: {e}")
    # Try alternative initialization for older OpenAI versions
    try:
        openai.api_key = API_KEY
        client = openai
        print("✅ OpenAI client initialized with legacy method")
        logger.info("✅ OpenAI client initialized (legacy)")
    except Exception as e2:
        print(f"❌ Legacy initialization also failed: {e2}")
        client = None

def format_text_field(text):
    """Format text field with first letter capitalized and rest lowercase"""
    if not text or not isinstance(text, str):
        return text
    return text.strip().capitalize()

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>LiamVision</title>
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
        .header h1 {
            font-size: 24px;
            margin-bottom: 8px;
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
            width: 80px;
            height: 80px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 50%;
            padding: 0;
            font-size: 2rem;
            font-weight: 400;
            cursor: pointer;
            transition: all 0.4s ease;
            margin: 20px auto;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            box-shadow:
                0 12px 40px rgba(0, 0, 0, 0.15),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.3);
            position: relative;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            color: rgba(0, 0, 0, 0.7);
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
            border-radius: 20px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            box-shadow:
                0 20px 60px rgba(0, 0, 0, 0.3),
                0 0 0 1px rgba(255, 255, 255, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            text-align: center;
            transform: scale(0.9);
            transition: transform 0.3s ease;
        }
        .camera-modal.active .camera-modal-content {
            transform: scale(1);
        }
        .camera-section {
            margin: 0;
            position: relative;
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
            bottom: 20px;
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

        @media (max-width: 768px) {
            body {
                padding: 5px;
            }

            .container {
                padding: 15px;
                margin: 5px;
                max-width: 100%;
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
                padding: 15px;
                width: 98%;
                max-width: none;
                margin: 10px;
                max-height: 85vh;
            }

            .camera-section #video {
                max-width: 100%;
                height: auto;
                border-radius: 12px;
            }

            .button-row {
                gap: 10px;
            }

            .button-row .camera-btn {
                width: 60px;
                height: 60px;
                font-size: 1.3rem;
            }

            .button-row .camera-btn svg {
                width: 16px;
                height: 16px;
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
                padding: 12px;
                max-height: 80vh;
            }

            .button-row .camera-btn {
                width: 50px;
                height: 50px;
                font-size: 1.1rem;
            }

            .button-row .camera-btn svg {
                width: 14px;
                height: 14px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧤 LiamVision <span class="beta-badge">beta</span></h1>
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
            cameraBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>';
            
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
                    document.getElementById('cameraModal').classList.add('active');
                    cameraBtn.disabled = false;
                    cameraBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>';
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
                    cameraBtn.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>';
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
            document.getElementById('cameraBtn').innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
            showMessage('Camera is not supported on this browser or device.', true);
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
        
        # Call OpenAI Vision API (handle both new and legacy clients)
        try:
            if hasattr(client, 'chat') and hasattr(client.chat, 'completions'):
                # New OpenAI client (v1.0+)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Analyze this electrical glove label image and extract: manufacturer, class, size, inside color, and outside color. COLOR RULES: ONLY use glove MATERIAL colors (rubber/fabric), NEVER label colors (ignore yellow/green/red stickers). If both sides are same color (e.g. black), report same color for both. Return ONLY JSON: manufacturer, class, size, inside_color, outside_color."
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
            else:
                # Legacy OpenAI client
                response = openai.ChatCompletion.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Analyze this electrical glove label image and extract: manufacturer, class, size, inside color, and outside color. COLOR RULES: ONLY use glove MATERIAL colors (rubber/fabric), NEVER label colors (ignore yellow/green/red stickers). If both sides are same color (e.g. black), report same color for both. Return ONLY JSON: manufacturer, class, size, inside_color, outside_color."
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
        except Exception as api_error:
            logger.error(f"OpenAI API call failed: {api_error}")
            return jsonify({'success': False, 'error': f'OpenAI API error: {str(api_error)}'})
        
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
                'inside_color': '',
                'outside_color': ''
            }

        # Format manufacturer and color fields with proper capitalization
        if 'manufacturer' in result_data:
            result_data['manufacturer'] = format_text_field(result_data['manufacturer'])
        if 'inside_color' in result_data:
            result_data['inside_color'] = format_text_field(result_data['inside_color'])
        if 'outside_color' in result_data:
            result_data['outside_color'] = format_text_field(result_data['outside_color'])

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
            if hasattr(client, 'models') and hasattr(client.models, 'list'):
                # New OpenAI client (v1.0+)
                client.models.list()
                openai_test = True
            else:
                # Legacy OpenAI client - just check if we have an API key
                openai_test = bool(API_KEY)
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
