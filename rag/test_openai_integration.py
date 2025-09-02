#!/usr/bin/env python3
"""
Test script to verify OpenAI GPT integration with RAG system
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_connection():
    """Test basic OpenAI API connectivity"""
    try:
        import openai

        # Get API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY environment variable not set!")
            print("Please set your OpenAI API key:")
            print("export OPENAI_API_KEY=your_openai_api_key_here")
            return False

        # Initialize client
        client = openai.OpenAI(api_key=api_key)

        # Test API connectivity
        models = client.models.list()
        if models:
            print("✅ OpenAI API connection successful!")
            print(f"   Available models: {len(models.data)} models found")

            # Check for GPT models
            gpt_models = [m.id for m in models.data if 'gpt' in m.id.lower()]
            if gpt_models:
                print(f"   GPT models available: {', '.join(gpt_models[:3])}{'...' if len(gpt_models) > 3 else ''}")

            return True
        else:
            print("❌ OpenAI API connected but no models available")
            return False

    except ImportError:
        print("❌ OpenAI package not installed. Run: pip install openai")
        return False
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return False

def test_rag_system():
    """Test RAG system functionality"""
    try:
        # Import the RAG functions from web_chat
        sys.path.append(os.path.dirname(__file__))
        from web_chat import get_collection, query_rag

        print("🔍 Testing RAG system...")

        # Test collection access
        collection = get_collection()
        if collection:
            count = collection.count()
            print(f"✅ RAG collection accessible with {count} documents")

            # Test a simple query
            test_query = "calibration testing"
            result = query_rag(test_query)
            if result and "No relevant information found" not in result:
                print("✅ RAG query successful")
                print(f"   Sample result: {result[:100]}...")
                return True
            else:
                print("⚠️  RAG query returned no results (this may be normal if no matching documents)")
                return True
        else:
            print("❌ Could not access RAG collection")
            return False

    except Exception as e:
        print(f"❌ RAG system error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Testing OpenAI GPT + RAG Integration")
    print("=" * 50)

    # Test OpenAI connection
    openai_ok = test_openai_connection()
    print()

    # Test RAG system
    rag_ok = test_rag_system()
    print()

    # Summary
    print("=" * 50)
    if openai_ok and rag_ok:
        print("✅ Integration test PASSED!")
        print("Your OpenAI GPT + RAG system is ready to use.")
        print()
        print("To start the web interface:")
        print("1. Set your OpenAI API key: export OPENAI_API_KEY=your_key_here")
        print("2. Run: python web_chat.py")
        print("3. Open http://localhost:8081 in your browser")
    else:
        print("❌ Integration test FAILED!")
        if not openai_ok:
            print("- OpenAI API connection issue")
        if not rag_ok:
            print("- RAG system issue")
        print()
        print("Please check the error messages above and fix any issues.")

if __name__ == "__main__":
    main()
