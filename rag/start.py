#!/usr/bin/env python3
"""
Railway startup script for vision app
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the vision app
from vision_app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    host = '0.0.0.0'
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print("🚀 Starting Vision App via start.py...")
    print(f"📋 Configuration: host={host}, port={port}, debug={debug}")

    app.run(host=host, port=port, debug=debug, threaded=True)
