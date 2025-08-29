#!/usr/bin/env python3
"""
Download the AI model during deployment to avoid including it in the Git repository
"""
import os
import requests
import sys
from pathlib import Path

def download_file(url, filepath, chunk_size=8192):
    """Download a file with progress indication"""
    print(f"📥 Downloading model from {url}")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r📊 Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='', flush=True)
        
        print(f"\n✅ Model downloaded successfully: {filepath}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error downloading model: {e}")
        return False

def main():
    """Main download function"""
    # Model file path
    model_dir = os.path.join(os.path.dirname(__file__), "models")
    model_path = os.path.join(model_dir, "Llama-3.2-3B-Instruct-Q6_K.gguf")
    
    # Check if model already exists
    if os.path.exists(model_path):
        print(f"✅ Model already exists: {model_path}")
        return True
    
    # Hugging Face model URL (this is a public model)
    model_url = "https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q6_K.gguf"
    
    print(f"🚀 Downloading Llama 3.2 3B model...")
    print(f"📁 Target path: {model_path}")
    
    success = download_file(model_url, model_path)
    
    if success:
        # Verify file size
        file_size = os.path.getsize(model_path)
        print(f"📏 Downloaded file size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        
        if file_size < 1000000:  # Less than 1MB suggests download failed
            print("❌ Downloaded file seems too small, download may have failed")
            return False
        
        print("✅ Model download completed successfully!")
        return True
    
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
