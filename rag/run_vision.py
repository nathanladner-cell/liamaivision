#!/usr/bin/env python3
"""
Startup script for LiamVision
"""

import os
import sys
from pathlib import Path

def main():
    """Main startup function"""

    # Change to the script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    print("🚀 Starting LiamVision")
    print("=" * 60)

    # Check if vision_app.py exists
    if not Path("vision_app.py").exists():
        print("❌ Error: vision_app.py not found")
        print("Please make sure you're running this from the rag/ directory")
        sys.exit(1)

    # Check if .env exists
    if not Path(".env").exists():
        print("⚠️  .env file not found")
        print("The app may not work without proper API keys")
        print("Consider running: python setup_vision.py")
        print()

    # Set environment variables
    port = os.environ.get('PORT', '5000')
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print("📋 Configuration:"    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print()

    # Check API keys
    if os.getenv('OPENAI_API_KEY'):
        print("✅ OpenAI API key is configured")
    else:
        print("❌ OpenAI API key not found - app will not work")

    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS') and os.getenv('GOOGLE_PROJECT_ID'):
        print("✅ Google Cloud Vision is configured")
    else:
        print("⚠️  Google Cloud Vision not configured (optional)")

    print()
    print("🌐 Starting Flask application...")

    # Import and run the app
    try:
        from vision_app import app

        print(f"📋 Starting server at http://{host}:{port}")
        print("📋 Press Ctrl+C to stop")
        print()

        app.run(host=host, port=int(port), debug=debug)

    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
