# 🚀 Document Q&A MCP Server (with Validation Agent)

A Python-based **Model Context Protocol (MCP)** server for document-based question answering using OpenAI models.  
Upload documents, ask questions, and receive answers **only when they are fully verified against the source documents**.

> 🛡️ Answers are surfaced **only after an AI Validation Agent confirms they are 100% grounded in document content**, dramatically reducing hallucinations and increasing trust.

---

## 🌟 Highlights

- ✅ MCP-compliant architecture
- 📄 Supports PDF, TXT, Markdown
- 🧠 Semantic search with embeddings
- 🛡️ AI Validation Agent (hallucination filtering)
- 📚 Source attribution + confidence scoring
- ⚡ Production-ready async server

---

## 🎯 Key Features

- **📤 Web File Upload**  
  Drag & drop documents via a browser interface

- **🔍 Semantic Retrieval**  
  Vector search using OpenAI embeddings and cosine similarity

- **🤖 AI-Powered Answers**  
  Responses generated strictly from document context

- **🛡️ Validation Agent (Core Feature)**  
  - Verifies answers against retrieved document chunks  
  - Blocks speculative or weakly supported responses  
  - Returns answers **only when fully verified**

- **📊 Confidence Scores**  
  Confidence is returned only after successful validation

- **🏗️ MCP Compliant**  
  Standard protocol for connecting AI models with external data

---

## 🛡️ Zero-Hallucination Guarantee

If the system cannot confidently verify an answer using the document content, it responds with:

> **“The document does not contain sufficient verified information to answer this question.”**

No guesses. No assumptions. No hallucinations.

---
Answer Flow
---

User Question
     ↓
Semantic Retrieval (Top-K Chunks)
     ↓
LLM Answer Generation
     ↓
🛡️ Validation Agent
     ├─ ❌ Not Verified → Response Blocked
     └─ ✅ Verified → Answer Returned
     
---
System Architecture

---
┌─────────────────┐        HTTP/UI        ┌─────────────────┐
│   Web Browser   │ ◄──────────────────► │   Web Server    │
│                 │                      │                 │
│ • Upload Docs   │                      │ • REST / MCP    │
│ • Ask Questions │                      │ • Session Mgmt  │
│ • View Results  │                      └─────────────────┘
└─────────────────┘                               │
                                                  ▼
                                      ┌────────────────────────┐
                                      │  Document Q&A MCP Core  │
                                      │                        │
                                      │  ┌──────────────────┐  │
                                      │  │ DocumentLoader   │  │
                                      │  └──────────────────┘  │
                                      │  ┌──────────────────┐  │
                                      │  │ Chunker          │  │
                                      │  └──────────────────┘  │
                                      │  ┌──────────────────┐  │
                                      │  │ Embedding Store  │  │
                                      │  └──────────────────┘  │
                                      │  ┌──────────────────┐  │
                                      │  │ Query Handler    │  │
                                      │  └──────────────────┘  │
                                      │  ┌──────────────────┐  │
                                      │  │ 🛡 Validation    │  │
                                      │  │    Agent         │  │
                                      │  └──────────────────┘  │
                                      └────────────────────────┘


## ⚡ Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key"

# Start the server
python web_server.py

# Open in browser
http://localhost:8000



