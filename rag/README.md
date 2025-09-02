# AmpAI RAG System

A Retrieval-Augmented Generation (RAG) system for electrical safety and testing standards, powered by OpenAI GPT and ChromaDB.

## 🚀 Quick Start

### Prerequisites
- OpenAI API key (get one at https://platform.openai.com/api-keys)
- Python 3.8+

### Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your OpenAI API key
export OPENAI_API_KEY="your_openai_api_key_here"

# 3. Index your sources
python3 rag_simple.py reindex

# 4. Start the web interface
python3 web_chat.py
```

Visit `http://localhost:8081` to access the application.

## 🔧 System Components

### 1. **RAG Engine** (`rag_simple.py`)
- Indexes JSONL source files from `../sources/`
- Provides command-line interface for testing
- Uses ChromaDB for vector storage

### 2. **Web Interface** (`web_chat.py`)
- Flask-based chat interface on port 8081
- Integrates with RAG system for knowledge retrieval
- Connects to OpenAI API for AI responses

### 3. **OpenAI Integration**
- Uses OpenAI GPT-4o for advanced AI responses
- Cloud-hosted - no local hardware requirements
- Secure API key authentication

## 📁 Directory Structure

```
rag/
├── rag_simple.py          # RAG engine and CLI
├── web_chat.py            # Web chat interface
├── requirements.txt       # Python dependencies
├── templates/             # HTML templates
├── static/                # CSS/JS assets
└── README.md             # This file

../sources/                # JSONL source files
../chroma_db/             # ChromaDB storage
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. **"Collection ampai_sources does not exist"**
**Solution**: The collection name includes a timestamp. The system now automatically finds the latest collection.

#### 2. **"OpenAI API error"**
**Solution**: Check your API key and billing status:
```bash
# Test API connection
python3 ../test_openai_integration.py

# Check API key
echo $OPENAI_API_KEY
```

#### 3. **"RAG system not available"**
**Solution**: Reindex your sources:
```bash
python3 rag_simple.py reindex
```

#### 4. **Web server won't start**
**Solution**: Check if port 8081 is in use:
```bash
lsof -i :8081
# Kill any processes using the port
pkill -f "web_chat.py"
```

### Testing the System

#### Test RAG Retrieval
```bash
python3 rag_simple.py ask "What is NFPA 70E?"
```

#### Test Web Interface
1. Start the web server
2. Open http://localhost:8081
3. Ask a question in the chat interface

#### Check Server Status
```bash
# Check web server
curl http://localhost:8081/api/status

# Test OpenAI API connection
python3 ../test_openai_integration.py
```

## 📚 Available Knowledge Sources

The system includes knowledge from:
- **NFPA 70E**: Electrical safety standards
- **NETA ATS**: Acceptance testing specifications
- **ASTM Standards**: Insulating blankets and PPE
- **Internal Documents**: Testing procedures and guidelines

## 🔍 RAG System Features

- **Semantic Search**: Finds relevant content based on meaning
- **Context-Aware Responses**: AI responses based on retrieved knowledge
- **Multi-Source Integration**: Combines information from multiple standards
- **Real-Time Indexing**: Always up-to-date with latest sources

## 🚨 Safety Notes

- This system provides information about electrical safety standards
- Always consult qualified professionals for actual electrical work
- The system is for informational purposes only
- Follow all applicable safety codes and regulations

## 📞 Support

For issues or questions:
1. Check this README first
2. Review the troubleshooting section
3. Check server logs for error messages
4. Ensure all dependencies are installed

## 🔄 Maintenance

### Regular Tasks
- **Reindex Sources**: Run `python3 rag_simple.py reindex` when sources change
- **Monitor API Usage**: Check OpenAI usage at https://platform.openai.com/usage
- **Update API Key**: Rotate keys periodically for security
- **Clean Database**: Delete `../chroma_db/` to start fresh (will reindex on next run)

### Performance Optimization
- Adjust `n_results` in `query_rag()` function for different retrieval strategies
- Modify distance thresholds for relevance filtering
- Adjust document truncation lengths based on GPT's context window (128K tokens)
- Choose different GPT models (gpt-4o, gpt-4, gpt-3.5-turbo) for speed vs. quality trade-offs
