#!/usr/bin/env python3
"""
Script to check OpenAI account status and billing
"""
import os
from openai import OpenAI

def check_account_status():
    """Check OpenAI account status and usage"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        return

    client = OpenAI(api_key=api_key)

    try:
        # Try to list models (this will fail if account has issues)
        models = client.models.list()
        print("✅ OpenAI API connection successful!")
        print(f"Available models: {len(models.data)}")

        # Try a simple completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        print("✅ Chat completion successful!")
        print(f"Response: {response.choices[0].message.content}")

    except Exception as e:
        error_msg = str(e).lower()
        if "insufficient_quota" in error_msg or "quota" in error_msg:
            print("❌ INSUFFICIENT QUOTA ERROR")
            print("Your OpenAI account needs billing setup.")
            print()
            print("To fix this:")
            print("1. Go to: https://platform.openai.com/usage")
            print("2. Click 'Set up paid account' or 'Add payment method'")
            print("3. Add a credit card or payment method")
            print("4. Start with $5-10 credit to test")
            print()
            print("Note: New accounts often need manual approval for API access.")
        elif "invalid_api_key" in error_msg:
            print("❌ INVALID API KEY")
            print("Please check your API key is correct.")
        else:
            print(f"❌ API Error: {e}")

if __name__ == "__main__":
    print("🔍 Checking OpenAI Account Status")
    print("-" * 40)
    check_account_status()
