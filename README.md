# 🚀 Document Q&A MCP Server

A Python-based Model Context Protocol (MCP) server that provides document-based question answering using OpenAI's API. Upload documents, ask questions, and get answers based strictly on document content with zero hallucinations.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green.svg)](https://openai.com/)

## 🌟 Live Demo

**Web Interface**: Start the server and visit `http://localhost:8000`

![Document Q&A Demo](https://via.placeholder.com/800x400/007cba/ffffff?text=Document+Q%26A+MCP+Server+Demo)

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# 3. Start the web server
python web_server.py

# 4. Open http://localhost:8000 in your browser
# 5. Upload a document and start asking questions!
```

## 🎯 Features

- **📤 Web File Upload**: Drag & drop PDF, TXT, Markdown files
- **🤖 Smart Q&A**: GPT-4 powered answers based strictly on your documents  
- **🔍 Semantic Search**: OpenAI embeddings with cosine similarity
- **🚫 Zero Hallucinations**: Only answers from document content
- **📊 Real-time Dashboard**: Live status, confidence scores, source attribution
- **🏗️ MCP Compliant**: Standard protocol for AI integration
- **⚡ Production Ready**: Error handling, logging, async support

## 🏛️ Architecture

- **Multi-format Support**: PDF, TXT, and Markdown files
- **Intelligent Chunking**: Semantic document splitting with overlap
- **Vector Search**: OpenAI embeddings with cosine similarity
- **Hallucination Prevention**: Strict adherence to document content
- **MCP Compliant**: Standard protocol endpoints
- **Production Ready**: Clean architecture with error handling

## Architecture

```
┌─────────────────┐    HTTP/Upload    ┌─────────────────┐    MCP Protocol    ┌─────────────────┐
│   Web Browser   │ ◄────────────────► │   Web Server    │ ◄─────────────────► │ Document Q&A    │
│                 │                    │                 │                    │   MCP Server    │
│  • File Upload  │                    │  • File Handling│                    │                 │
│  • Q&A Interface│                    │  • HTTP Endpoints│                    │  ┌───────────┐  │
│  • Results      │                    │  • JSON API     │                    │  │DocumentLoader│  │
└─────────────────┘                    └─────────────────┘                    │  └───────────┘  │
                                                                              │  ┌───────────┐  │
                                                                              │  │ Chunker   │  │
                                                                              │  └───────────┘  │
                                                                              │  ┌───────────┐  │
                                                                              │  │Embedding  │  │
                                                                              │  │  Store    │  │
                                                                              │  └───────────┘  │
                                                                              │  ┌───────────┐  │
                                                                              │  │  Query    │  │
                                                                              │  │ Handler   │  │
                                                                              │  └───────────┘  │
                                                                              └─────────────────┘
```

The server consists of five main components:

1. **DocumentLoader**: Handles PDF, TXT, and Markdown file parsing
2. **DocumentChunker**: Intelligently splits documents into semantic chunks  
3. **EmbeddingStore**: Manages vector embeddings for similarity search
4. **QueryHandler**: Processes questions and generates context-aware answers
5. **MCPServer**: Exposes MCP-compliant endpoints

## 🚀 Usage Options

### Option 1: Web Interface (Recommended)
```bash
python web_server.py
# Visit http://localhost:8000
```

### Option 2: Interactive CLI
```bash
python interactive_client.py
```

### Option 3: Simple Version (No MCP)
```bash
python simple_document_qa.py  
# Visit http://localhost:8001
```

### Option 4: Run Tests
```bash
python test_server.py
```

## 📱 Web Interface Features

- **📤 File Upload**: Click "Choose File" or drag & drop documents
- **❓ Question Input**: Type questions in the text area  
- **📊 Live Dashboard**: Real-time status and document info
- **🎯 Confidence Scores**: See how confident the AI is in each answer
- **📚 Source Attribution**: Know exactly which document parts were used
- **⚡ Real-time Processing**: Instant feedback and results

## 📡 MCP Endpoints

### 1. Load Document

Load a document into the system for question answering.

**Request:**
```json
{
  "method": "load_document",
  "params": {
    "file_path": "/path/to/document.pdf"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully loaded document: /path/to/document.pdf",
  "metadata": {
    "file_path": "/path/to/document.pdf",
    "content_length": 15420,
    "num_chunks": 12,
    "total_chunks_in_store": 12
  }
}
```

### 2. Ask Question

Ask a question about loaded documents.

**Request:**
```json
{
  "method": "ask_question",
  "params": {
    "question": "What are the main features?"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "question": "What are the main features?",
  "answer": "Based on the document, the main features include...",
  "sources": [
    {
      "file": "/path/to/document.pdf",
      "chunk_id": "document_0",
      "similarity_score": 0.892
    }
  ],
  "confidence": 0.892
}
```

### 3. Get Status

Check server status and loaded documents.

**Request:**
```json
{
  "method": "get_status",
  "params": {}
}
```

**Response:**
```json
{
  "status": "active",
  "loaded_documents": ["/path/to/document.pdf"],
  "total_chunks": 12,
  "supported_formats": [".pdf", ".txt", ".md", ".markdown"]
}
```

## 📁 Project Structure

```
document-qa-mcp-server/
├── 📄 document_qa_server.py      # Main MCP server implementation
├── 🌐 web_server.py              # Web interface with file upload
├── 🖥️  simple_document_qa.py     # Simplified version (no MCP)
├── 💬 interactive_client.py      # CLI interface
├── 🧪 test_server.py             # Test suite
├── 📖 example_usage.py           # Usage examples
├── 📋 requirements.txt           # Dependencies
├── 📚 MCP_SERVER_DOCUMENTATION.md # Complete MCP guide
├── 🎨 web_interface.py           # Static HTML generator
└── 📄 README.md                  # This file
```

## 🔧 Configuration

### Chunking Parameters

Modify chunking behavior in `DocumentChunker`:

```python
chunker = DocumentChunker(
    chunk_size=1000,  # Target chunk size in characters
    overlap=200       # Overlap between chunks
)
```

### Retrieval Parameters

Adjust retrieval in `QueryHandler.answer_question()`:

```python
similar_chunks = await self.embedding_store.search_similar(
    question, 
    top_k=3  # Number of chunks to retrieve
)
```

### OpenAI Model Configuration

Change models in the respective methods:

```python
# Embeddings model
model="text-embedding-3-small"

# Chat completion model  
model="gpt-4"
```

## 🚨 Error Handling

The server handles common errors gracefully:

- **File not found**: Clear error with file path
- **Unsupported format**: Lists supported formats  
- **API errors**: Returns OpenAI error messages
- **No documents loaded**: Prompts to load documents first
- **Missing information**: Returns "The document does not contain this information"

## 🔮 Extending for Multiple Documents

The current architecture supports multiple documents. To extend:

1. **Document Management**: Add document metadata tracking
2. **Source Filtering**: Filter by specific documents  
3. **Cross-Document Search**: Search across all loaded documents
4. **Document Removal**: Add endpoint to remove specific documents

Example extension:

```python
async def remove_document(self, file_path: str) -> Dict[str, Any]:
    """Remove a specific document from the store."""
    self.embedding_store.chunks = [
        chunk for chunk in self.embedding_store.chunks 
        if chunk.source_file != file_path
    ]
    # Rebuild embeddings matrix...
```

## ⚡ Performance Considerations

- **Chunk Size**: Larger chunks = more context but slower search
- **Overlap**: More overlap = better context continuity but more storage
- **Top-K**: More retrieved chunks = better context but higher API costs  
- **Embedding Model**: `text-embedding-3-small` balances cost and quality

## 🔒 Security Notes

- Store API keys securely (environment variables, secrets management)
- Input validation implemented for file paths and parameters
- Consider rate limiting for production deployments
- Sanitize file paths to prevent directory traversal

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For issues and questions:
1. Check the error messages and logs
2. Verify OpenAI API key and quota
3. Ensure document formats are supported
4. Review the example usage patterns
5. Open an issue on GitHub

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/) for GPT-4 and embedding models
- [Model Context Protocol](https://github.com/modelcontextprotocol) for the MCP specification
- [Starlette](https://www.starlette.io/) for the web framework
- [scikit-learn](https://scikit-learn.org/) for cosine similarity calculations