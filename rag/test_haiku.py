#!/usr/bin/env python3
"""
Test script to generate a haiku about AI using OpenAI GPT
"""
import os
from openai import OpenAI

# Get API key from environment
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("❌ OPENAI_API_KEY not set")
    exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

try:
    # Corrected API call for chat completions
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Write a haiku about AI"}
        ],
        max_tokens=100,
        temperature=0.7
    )

    # Print the response
    haiku = response.choices[0].message.content
    print("🤖 AI-Generated Haiku:")
    print("-" * 30)
    print(haiku)
    print("-" * 30)

except Exception as e:
    print(f"❌ Error: {e}")
