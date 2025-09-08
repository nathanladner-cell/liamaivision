#!/usr/bin/env python3
"""
Simple Railway entry point for minimal vision app
"""
import os
import sys

print("=" * 50)
print("🚀 MINIMAL VISION APP STARTUP")
print("=" * 50)
print(f"📋 Port: {int(os.environ.get('PORT', 8000))}")
print(f"📋 Host: 0.0.0.0")
print(f"📋 Working directory: {os.getcwd()}")

# Environment variables
print(f"📋 Environment Variables:")
for key, value in os.environ.items():
    if 'API' in key or 'KEY' in key or 'PORT' in key:
        print(f"    {key}: {value[:20]}..." if len(str(value)) > 20 else f"    {key}: {value}")
print("=" * 50)

try:
    # Import minimal_vision directly
    import minimal_vision
    print("✅ Successfully imported minimal_vision module")

    # Get the Flask app
    app = minimal_vision.app
    print("✅ Successfully got Flask app instance")

    # Configure for Railway
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"📋 Final configuration: host={host}, port={port}, debug={debug}")

    # Test the health endpoint before starting
    with app.test_client() as client:
        try:
            response = client.get('/api/status')
            print(f"✅ Health check test: {response.status_code}")
            if response.get_json():
                data = response.get_json()
                print(f"    Service: {data.get('service', 'N/A')}")
                print(f"    OpenAI Available: {data.get('openai_available', 'N/A')}")
                print(f"    Status: {data.get('status', 'N/A')}")
        except Exception as e:
            print(f"⚠️ Health check test failed: {e}")

    # Start the app
    print("🌐 Starting Flask server...")
    print(f"🌐 Health check: http://{host}:{port}/health")
    print(f"🌐 API status: http://{host}:{port}/api/status")
    print(f"🌐 Main app: http://{host}:{port}/")
    print("=" * 50)

    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("📁 Contents of current directory:")
    print(os.listdir('.'))
    sys.exit(1)
except Exception as e:
    print(f"❌ Startup error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
