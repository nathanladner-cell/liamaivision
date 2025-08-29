# 🤖 AmpAI - AI-Powered Electrical Safety Assistant

AmpAI is an intelligent RAG (Retrieval-Augmented Generation) system designed to provide expert guidance on electrical safety standards, calibration procedures, and insulated rubber PPE testing. Built with Flask, ChromaDB, and llama.cpp.

## 🌟 Features

- **🔍 Intelligent Q&A**: Ask questions about NFPA 70E, electrical safety, and calibration procedures
- **📚 Knowledge Base**: Comprehensive database of electrical safety standards and procedures
- **🚀 Real-time Responses**: Fast AI-powered responses using locally-hosted Llama 3.2 3B model
- **📱 Modern Web Interface**: Clean, responsive chat interface with loading animations
- **📄 File Upload**: Upload PDF, TXT, or JSONL files to expand the knowledge base
- **🔄 Auto-Reindexing**: Automatic knowledge base updates when new sources are added

## 🏗️ Architecture

- **Frontend**: Modern HTML/CSS/JavaScript chat interface
- **Backend**: Flask web server with REST API
- **AI Model**: Llama 3.2 3B Instruct (GGUF format) via llama.cpp
- **Vector Database**: ChromaDB for semantic search and retrieval
- **Knowledge Sources**: JSONL files containing electrical safety standards

## 🚀 Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

### One-Click Deployment
1. Click the Railway button above
2. Connect your GitHub account
3. Wait for deployment (10-15 minutes)
4. Access your deployed app!

### Manual Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## 🛠️ Local Development

### Prerequisites
- Python 3.8+
- Git
- 4GB+ RAM (for AI model)

### Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/ampAI.git
cd ampAI

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download the AI model
python3 download_model.py

# Build llama.cpp (if not using Docker)
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc) llama-server
cd ../..

# Initialize RAG system
cd rag
python3 rag_simple.py reindex

# Start the llama.cpp server (in one terminal)
python3 start_llama_server.py

# Start the web interface (in another terminal)
python3 web_chat.py
```

Visit `http://localhost:8081` to access the application.

## 📚 Knowledge Base

The system includes knowledge about:
- **NFPA 70E**: Electrical safety in the workplace
- **Calibration Standards**: Insulated rubber PPE testing procedures  
- **ASTM Standards**: Blankets, gloves, and protective equipment
- **Live Line Tools**: Testing and maintenance procedures
- **Grounding Equipment**: Safety and testing protocols

## 🔧 Configuration

### Environment Variables
- `PORT`: Web server port (default: 8081)
- `FLASK_DEBUG`: Debug mode (default: false)
- `MODEL_PATH`: Path to GGUF model file
- `SOURCES_DIR`: Directory containing knowledge sources
- `SECRET_KEY`: Flask secret key for sessions

### Adding Knowledge Sources
1. Place JSONL, TXT, or PDF files in the `sources/` directory
2. Use the web interface to upload files, or
3. Run `python3 rag_simple.py reindex` to manually reindex

## 🐳 Docker

```bash
# Build the image
docker build -t ampai .

# Run the container
docker run -p 8081:8081 ampai
```

## 📊 System Requirements

### Minimum
- **RAM**: 4GB
- **CPU**: 2 cores
- **Storage**: 5GB
- **Network**: 1GB (for model download)

### Recommended
- **RAM**: 8GB
- **CPU**: 4+ cores
- **Storage**: 10GB
- **Network**: Unlimited

## 🔐 Security

- The system provides information for educational purposes only
- Always consult qualified professionals for electrical work
- Ensure proper access controls in production environments
- Regular security updates recommended

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🚨 Disclaimer

This system provides information about electrical safety standards for educational and reference purposes only. Always follow proper safety procedures and consult qualified professionals for electrical work. The developers are not responsible for any damages or injuries resulting from the use of this information.

## 📞 Support

- 📖 Check the [Deployment Guide](DEPLOYMENT.md)
- 🐛 Report issues on GitHub
- 💬 Ask questions in GitHub Discussions
- 📧 Contact: [your-email@domain.com]

---

Built with ❤️ for electrical safety professionals
