#!/usr/bin/env python3
"""
Test script to run after adding billing to OpenAI account
"""

import openai
from dotenv import load_dotenv
import os

load_dotenv()

def test_openai_after_billing():
    """Test OpenAI API after adding billing"""
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    print("🧪 Testing OpenAI API after adding billing...")
    
    try:
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[{'role': 'user', 'content': 'Hello! This is a test after adding billing.'}],
            max_tokens=50
        )
        
        print("✅ SUCCESS! OpenAI API is working!")
        print(f"Response: {response.choices[0].message.content}")
        print("\n🎉 Your AmpAI application will now work perfectly!")
        return True
        
    except Exception as e:
        if '429' in str(e):
            print("❌ Still getting quota error. Wait a few more minutes and try again.")
            print("If this persists, check your billing setup at:")
            print("https://platform.openai.com/settings/organization/billing")
        else:
            print(f"❌ Different error: {e}")
        return False

if __name__ == "__main__":
    test_openai_after_billing()
