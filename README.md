# 🤖 AmpAI - AI-Powered Electrical Safety Assistant

AmpAI is an intelligent RAG (Retrieval-Augmented Generation) system designed to provide expert guidance on electrical safety standards, calibration procedures, and insulated rubber PPE testing. Powered by OpenAI's GPT models and ChromaDB for advanced semantic search.

## 🌟 Features

- **🔍 Intelligent Q&A**: Ask questions about NFPA 70E, electrical safety, and calibration procedures
- **📚 Knowledge Base**: Comprehensive database of electrical safety standards and procedures
- **🚀 Real-time Responses**: Fast AI-powered responses using OpenAI GPT-4o
- **📱 Modern Web Interface**: Clean, responsive chat interface with loading animations
- **📄 File Upload**: Upload PDF, TXT, or JSONL files to expand the knowledge base
- **🔄 Auto-Reindexing**: Automatic knowledge base updates when new sources are added
- **⚡ Cloud-Powered**: No local hardware requirements - uses OpenAI's infrastructure

## 🏗️ Architecture

- **Frontend**: Modern HTML/CSS/JavaScript chat interface
- **Backend**: Flask web server with REST API
- **AI Model**: OpenAI GPT-4o (cloud-hosted)
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
- OpenAI API key (get one at https://platform.openai.com/api-keys)
- Internet connection (for OpenAI API)

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

# Set your OpenAI API key
export OPENAI_API_KEY="your_openai_api_key_here"
# Or create a .env file with: OPENAI_API_KEY=your_key_here

# Initialize RAG system
cd rag
python3 rag_simple.py reindex

# Start the web interface
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
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: GPT model to use (default: gpt-4o)
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

# Run the container (set your OpenAI API key)
docker run -p 8081:8081 -e OPENAI_API_KEY="your_openai_api_key_here" ampai
```

For production deployment, consider using Docker Compose with environment variables or secrets management.

## 📊 System Requirements

### Minimum
- **RAM**: 2GB
- **CPU**: 1 core
- **Storage**: 2GB
- **Network**: Stable internet connection

### Recommended
- **RAM**: 4GB
- **CPU**: 2+ cores
- **Storage**: 5GB
- **Network**: High-speed internet

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
# Force deployment Mon Sep  8 15:28:30 CDT 2025
