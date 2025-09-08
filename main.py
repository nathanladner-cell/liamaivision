#!/usr/bin/env python3
"""
Railway main entry point - cannot be ignored
"""
import sys
import os

# Add rag directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag'))

# Import and run the vision app
try:
    # Direct import from rag directory
    from vision_app import app
    print("✅ Successfully imported vision app directly")
except ImportError as e:
    print(f"❌ Failed to import vision app directly: {e}")
    # Try importing the start module
    try:
        from start import app
        print("✅ Successfully imported vision app via start.py")
    except ImportError as e2:
        print(f"❌ All import attempts failed: {e2}")
        print("📁 Directory contents:")
        import os
        print(os.listdir('.'))
        if os.path.exists('rag'):
            print("📁 rag/ contents:")
            print(os.listdir('rag'))
        sys.exit(1)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print("🚀 Railway Vision App - Starting...")
    print(f"📋 Configuration: host={host}, port={port}, debug={debug}")
    print(f"📋 Environment: {list(os.environ.keys())}")
    print(f"📋 Current working directory: {os.getcwd()}")
    print(f"📋 Python path: {sys.path}")

    try:
        print("🌐 Starting Flask app...")
        app.run(host=host, port=port, debug=debug, threaded=True)
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
