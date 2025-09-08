#!/usr/bin/env python3
"""
Railway main entry point - cannot be ignored
"""
import sys
import os

# Add rag directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'rag'))

# Import and run the vision app
from start import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print("🚀 Railway Vision App - Starting...")
    print(f"📋 Configuration: host={host}, port={port}, debug={debug}")

    app.run(host=host, port=port, debug=debug, threaded=True)
