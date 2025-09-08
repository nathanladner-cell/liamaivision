#!/bin/bash

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY environment variable is not set!"
    echo "Please set it with: export OPENAI_API_KEY=your_api_key_here"
    exit 1
fi

# Run the minimal vision app
python3 minimal_vision.py
