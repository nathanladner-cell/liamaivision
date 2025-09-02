#!/usr/bin/env python3
"""
Setup script for OpenAI GPT + RAG integration
"""
import os
import sys
import subprocess

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")

    try:
        # Install from requirements.txt
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Dependencies installed successfully!")
            return True
        else:
            print("❌ Failed to install dependencies:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def setup_api_key():
    """Guide user through API key setup"""
    print("\n🔑 OpenAI API Key Setup")
    print("-" * 30)

    # Check if API key is already set
    current_key = os.getenv('OPENAI_API_KEY')
    if current_key:
        print(f"✅ OpenAI API key is already set (ends with: ...{current_key[-4:]})")
        return True

    print("You need an OpenAI API key to use GPT models.")
    print("1. Go to: https://platform.openai.com/api-keys")
    print("2. Create a new API key")
    print("3. Copy the API key (it starts with 'sk-')")
    print()

    api_key = input("Enter your OpenAI API key: ").strip()

    if not api_key:
        print("❌ No API key provided.")
        return False

    if not api_key.startswith('sk-'):
        print("⚠️  Warning: API key should start with 'sk-'. Please verify it's correct.")
        confirm = input("Continue anyway? (y/N): ").strip().lower()
        if confirm != 'y':
            return False

    # Set the environment variable
    os.environ['OPENAI_API_KEY'] = api_key

    print("✅ API key set for this session!")
    print("Note: You'll need to set OPENAI_API_KEY in your environment for future sessions.")
    print("You can add this to your shell profile or use:")
    print(f"export OPENAI_API_KEY={api_key}")

    return True

def test_setup():
    """Test the complete setup"""
    print("\n🧪 Testing Setup...")

    try:
        # Import required modules
        import openai
        from dotenv import load_dotenv

        # Test OpenAI API
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not set")
            return False

        client = openai.OpenAI(api_key=api_key)
        models = client.models.list()

        if models:
            print("✅ OpenAI API connection successful!")
            return True
        else:
            print("❌ OpenAI API connection failed")
            return False

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main setup process"""
    print("🚀 OpenAI GPT + RAG Setup")
    print("=" * 40)

    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)

    # Step 2: Setup API key
    if not setup_api_key():
        print("❌ Setup failed at API key configuration")
        sys.exit(1)

    # Step 3: Test setup
    if test_setup():
        print("\n" + "=" * 40)
        print("🎉 Setup completed successfully!")
        print()
        print("To start your AI assistant:")
        print("1. Make sure OPENAI_API_KEY is set in your environment")
        print("2. Run: python web_chat.py")
        print("3. Open http://localhost:8081 in your browser")
        print()
        print("Your system now uses OpenAI GPT instead of local Llama!")
    else:
        print("❌ Setup completed but tests failed")
        print("Check the error messages above and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
