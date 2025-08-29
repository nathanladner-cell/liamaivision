#!/usr/bin/env python3
"""
Production-ready llama.cpp server starter for Railway deployment
"""
import os
import subprocess
import sys
import time
import requests
from pathlib import Path

def start_llama_server():
    """Start the llama.cpp server with production settings"""
    
    # Model path
    model_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "Llama-3.2-3B-Instruct-Q6_K.gguf")
    
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        return False
    
    print(f"🚀 Starting llama.cpp server with model: {model_path}")
    
    # Get optimal thread count
    import multiprocessing
    threads = multiprocessing.cpu_count()
    
    # llama.cpp server command
    cmd = [
        "llama-server",
        "--model", model_path,
        "--host", "0.0.0.0",
        "--port", "8000",
        "--ctx-size", "4096",
        "--threads", str(threads),
        "--log-format", "text",
        "--timeout", "600",  # 10 minutes timeout
        "--cont-batching",   # Enable continuous batching for better performance
        "--parallel", "1",   # Number of parallel sequences
        "--batch-size", "512"
    ]
    
    print(f"📋 Command: {' '.join(cmd)}")
    
    try:
        # Start the server
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for server to be ready
        print("⏳ Waiting for server to start...")
        for i in range(60):  # Wait up to 60 seconds
            try:
                response = requests.get("http://localhost:8000/v1/models", timeout=2)
                if response.status_code == 200:
                    print("✅ llama.cpp server is ready!")
                    return True
            except requests.RequestException:
                pass
            
            print(f"   Waiting... ({i+1}/60)")
            time.sleep(1)
        
        print("❌ Server failed to start within timeout")
        process.terminate()
        return False
        
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

if __name__ == "__main__":
    success = start_llama_server()
    sys.exit(0 if success else 1)
