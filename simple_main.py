#!/usr/bin/env python3
"""
Simple Railway entry point for vision app
"""
import os
import sys

# Add rag directory to Python path
rag_path = os.path.join(os.path.dirname(__file__), 'rag')
sys.path.insert(0, rag_path)

print("🚀 Simple Railway Vision App - Starting...")
print(f"📁 Working directory: {os.getcwd()}")
print(f"📁 Rag path: {rag_path}")
print(f"📁 Python path: {sys.path}")

try:
    # Import vision_app directly
    import vision_app
    print("✅ Successfully imported vision_app module")
    
    # Get the Flask app
    app = vision_app.app
    print("✅ Successfully got Flask app instance")
    
    # Configure for Railway
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"📋 Configuration: host={host}, port={port}, debug={debug}")
    
    # Test the health endpoint before starting
    with app.test_client() as client:
        try:
            response = client.get('/api/status')
            print(f"✅ Health check test: {response.status_code} - {response.get_json()}")
        except Exception as e:
            print(f"⚠️ Health check test failed: {e}")
    
    # Start the app
    print("🌐 Starting Flask app...")
    print(f"🌐 Health check will be available at: http://{host}:{port}/health")
    print(f"🌐 API status will be available at: http://{host}:{port}/api/status")
    print(f"🌐 Main app will be available at: http://{host}:{port}/")
    
    # Add startup delay for Railway
    import time
    print("⏳ Waiting 2 seconds before starting server...")
    time.sleep(2)
    
    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📁 Contents of current directory:")
    print(os.listdir('.'))
    if os.path.exists('rag'):
        print("📁 Contents of rag directory:")
        print(os.listdir('rag'))
    sys.exit(1)
except Exception as e:
    print(f"❌ Startup error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
