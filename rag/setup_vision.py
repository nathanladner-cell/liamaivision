#!/usr/bin/env python3
"""
Setup script for LiamVision
"""

import os
import sys
from pathlib import Path

def setup_vision_app():
    """Set up the vision application with required dependencies and configuration"""

    print("🚀 Setting up LiamVision")
    print("=" * 60)

    # Check if we're in the right directory
    if not Path("vision_app.py").exists():
        print("❌ Error: vision_app.py not found in current directory")
        print("Please run this script from the rag/ directory")
        return False

    # Install dependencies
    print("\n📦 Installing dependencies...")
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "vision_requirements.txt"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
        else:
            print("❌ Failed to install dependencies:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

    # Check for environment variables
    print("\n🔧 Checking environment configuration...")

    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API Key (required)',
    }

    optional_vars = {
        'GOOGLE_APPLICATION_CREDENTIALS': 'Path to Google Cloud service account JSON (optional)',
        'GOOGLE_PROJECT_ID': 'Google Cloud Project ID (optional)',
        'OPENAI_MODEL': 'OpenAI model to use (default: gpt-4o)',
        'FLASK_DEBUG': 'Enable Flask debug mode (default: False)',
    }

    # Check required variables
    missing_required = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_required.append(f"{var}: {description}")

    if missing_required:
        print("❌ Missing required environment variables:")
        for var in missing_required:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment")
        return False
    else:
        print("✅ Required environment variables are set")

    # Check optional variables
    missing_optional = []
    for var, description in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"{var}: {description}")

    if missing_optional:
        print("⚠️  Optional environment variables not set:")
        for var in missing_optional:
            print(f"   - {var}")
        print("\nThe app will work without these, but with reduced functionality")

    # Create .env template if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        print("\n📝 Creating .env template file...")
        env_template = """# OpenAI Configuration (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Google Cloud Vision Configuration (Optional)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json
# GOOGLE_PROJECT_ID=your_google_cloud_project_id

# OpenAI Model Configuration (Optional)
# OPENAI_MODEL=gpt-4o

# Flask Configuration (Optional)
# FLASK_DEBUG=False
"""
        with open(env_file, 'w') as f:
            f.write(env_template)
        print("✅ Created .env template file")
        print("   Please edit it with your actual API keys")

    # Test imports
    print("\n🧪 Testing imports...")
    try:
        import flask
        print("✅ Flask imported successfully")

        import openai
        print("✅ OpenAI imported successfully")

        try:
            from google.cloud import vision
            print("✅ Google Cloud Vision imported successfully")
        except ImportError:
            print("⚠️  Google Cloud Vision not available (optional)")

        print("✅ All core imports successful")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    print("\n" + "=" * 60)
    print("🎉 Vision app setup completed!")
    print("\nTo run the application:")
    print("1. Edit the .env file with your API keys")
    print("2. Run: python vision_app.py")
    print("3. Open http://localhost:5000 in your browser")
    print("\nFor Google Cloud Vision (optional):")
    print("- Create a Google Cloud Project")
    print("- Enable the Vision API")
    print("- Create a service account and download the JSON key")
    print("- Set GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_PROJECT_ID")

    return True

if __name__ == "__main__":
    success = setup_vision_app()
    sys.exit(0 if success else 1)
