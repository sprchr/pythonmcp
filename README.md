🚀 Document Q&A MCP Server (with Validation Agent)

A Python-based Model Context Protocol (MCP) server for document-based question answering using OpenAI models.
Upload documents, ask questions, and receive answers only when they are fully verified against the source documents — dramatically reducing hallucinations and improving trust.

✅ Answers are surfaced only when the Validation Agent confirms they are 100% grounded in document content.

🌟 What’s New
🛡️ AI Validation Agent (Key Upgrade)

This system now includes a dedicated AI Validation Agent that:

Verifies every generated answer against retrieved document chunks

Confirms factual grounding and source alignment

Blocks partial, speculative, or unverified responses

Returns answers only when confidence and validity thresholds are met

If validation fails, the system responds with:

“The document does not contain sufficient verified information to answer this question.”

🎯 Core Features

📤 Web File Upload: PDF, TXT, Markdown

🧠 Semantic Q&A: Context-aware answers powered by OpenAI

🔍 Vector Search: Embeddings with cosine similarity

🛡️ Validation Agent: Filters hallucinations before responses are returned

📚 Source Attribution: Exact document chunks used

📊 Confidence Scoring: Returned only after validation

🏗️ MCP-Compliant: Standard protocol for AI ↔ data integration

⚡ Production Ready: Async, logging, error handling

🏛️ Updated Architecture
High-Level Flow
User Question
     │
     ▼
Semantic Retrieval (Top-K Chunks)
     │
     ▼
LLM Answer Generation
     │
     ▼
🛡️ Validation Agent
     │
     ├── ❌ Not Verified → Block Response
     └── ✅ Fully Verified → Return Answer

System Architecture Diagram
┌─────────────────┐        HTTP / UI        ┌─────────────────┐
│   Web Browser   │ ◄────────────────────► │   Web Server    │
│                 │                         │                 │
│ • File Upload   │                         │ • Upload API    │
│ • Q&A Interface │                         │ • REST/MCP      │
│ • Results View  │                         │ • Session Mgmt  │
└─────────────────┘                         └─────────────────┘
                                                     │
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

🧠 Core Components (Updated)

DocumentLoader
Parses PDF, TXT, Markdown documents

DocumentChunker
Semantic chunking with overlap for context continuity

EmbeddingStore
Vector embeddings + cosine similarity search

QueryHandler
Retrieves relevant chunks and generates draft answers

ValidationAgent 🛡️

Cross-checks answers against retrieved chunks

Enforces grounding and confidence thresholds

Blocks hallucinated or weakly-supported responses

MCPServer
Exposes standardized MCP endpoints

🛡️ Validation Agent Logic (Conceptual)
if not validation_agent.verify(answer, retrieved_chunks):
    return {
        "status": "blocked",
        "message": "Answer could not be fully verified against document content."
    }


Validation criteria may include:

Direct evidence in retrieved chunks

No external or inferred knowledge

Consistent semantic alignment

Confidence score above threshold

📡 MCP Response (Validated)
{
  "status": "success",
  "answer": "Based on the document, the main features include...",
  "sources": [
    {
      "file": "document.pdf",
      "chunk_id": "chunk_03",
      "similarity_score": 0.91
    }
  ],
  "confidence": 0.91,
  "validated": true
}


If validation fails:

{
  "status": "blocked",
  "validated": false,
  "message": "The document does not contain sufficient verified information."
}

🤔 Why This Is Different from Traditional RAG
Traditional RAG	This MCP + Validation Approach
Retrieve + Generate	Retrieve → Generate → Validate
Answers always returned	Answers may be blocked
Higher hallucination risk	Hallucinations filtered
Tight coupling	MCP-standard, modular
Limited trust	High-confidence outputs
🔮 Future Extensions

Multi-agent validation (factual + semantic)

Cross-document contradiction detection

Per-answer explanation of validation outcome

Streaming partial answers with delayed validation

Plug-in validators (compliance, legal, medical)

🧠 Ideal Use Cases

Enterprise document Q&A

Legal / policy assistants

Internal knowledge bases

Compliance-heavy AI systems

Trust-first AI applications
