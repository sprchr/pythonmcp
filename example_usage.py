#!/usr/bin/env python3
"""
Example usage of the Document Q&A MCP Server

This script demonstrates how to use the MCP server for document-based
question answering with various document formats.
"""

import asyncio
import json
import os
from document_qa_server import DocumentQAServer, handle_mcp_request


async def run_examples():
    """Run example interactions with the Document Q&A server."""
    
    # Initialize server with API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        return
    
    server = DocumentQAServer(api_key)
    
    print("Document Q&A MCP Server - Example Usage")
    print("=" * 50)
    
    # Example 1: Check server status
    print("\n1. Checking server status...")
    status_request = {
        "method": "get_status",
        "params": {}
    }
    
    response = await handle_mcp_request(server, status_request)
    print(f"Status Response: {json.dumps(response, indent=2)}")
    
    # Example 2: Load a document (you'll need to create a sample document)
    print("\n2. Loading a sample document...")
    
    # Create a sample document for testing
    sample_content = """
# Sample Document for Testing

## Introduction
This is a sample document to demonstrate the Document Q&A MCP Server capabilities.
The server can process PDF, TXT, and Markdown files to answer questions based on their content.

## Features
The Document Q&A server includes the following key features:
- Document loading from multiple formats (PDF, TXT, Markdown)
- Intelligent document chunking for optimal retrieval
- Semantic search using OpenAI embeddings
- Context-aware question answering using GPT-4
- Strict adherence to document content (no hallucinations)

## Technical Architecture
The system consists of several components:
1. DocumentLoader: Handles file format parsing
2. DocumentChunker: Splits documents into semantic chunks
3. EmbeddingStore: Manages vector embeddings for similarity search
4. QueryHandler: Processes questions and generates answers
5. MCPServer: Exposes MCP-compliant endpoints

## Usage Examples
Users can ask questions like:
- "What are the main features of this system?"
- "How does the technical architecture work?"
- "What file formats are supported?"

The system will only answer based on the loaded document content.
    """
    
    # Write sample document
    with open("sample_document.md", "w", encoding="utf-8") as f:
        f.write(sample_content)
    
    load_request = {
        "method": "load_document",
        "params": {
            "file_path": "sample_document.md"
        }
    }
    
    response = await handle_mcp_request(server, load_request)
    print(f"Load Response: {json.dumps(response, indent=2)}")
    
    # Example 3: Ask questions about the document
    print("\n3. Asking questions about the loaded document...")
    
    questions = [
        "What are the main features of the Document Q&A server?",
        "How many components are in the technical architecture?",
        "What file formats are supported?",
        "What is the capital of France?"  # This should return "not in document"
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n3.{i} Question: {question}")
        
        question_request = {
            "method": "ask_question",
            "params": {
                "question": question
            }
        }
        
        response = await handle_mcp_request(server, question_request)
        print(f"Answer: {response.get('answer', 'No answer')}")
        print(f"Confidence: {response.get('confidence', 0):.3f}")
        
        if response.get('sources'):
            print("Sources:")
            for source in response['sources']:
                print(f"  - {source['file']} (similarity: {source['similarity_score']:.3f})")
    
    # Example 4: Check final status
    print("\n4. Final server status...")
    response = await handle_mcp_request(server, status_request)
    print(f"Final Status: {json.dumps(response, indent=2)}")
    
    # Clean up
    if os.path.exists("sample_document.md"):
        os.remove("sample_document.md")
        print("\nCleaned up sample document.")


# MCP Request/Response Examples
def print_mcp_examples():
    """Print example MCP request/response payloads."""
    
    print("\nMCP Request/Response Examples")
    print("=" * 40)
    
    examples = [
        {
            "name": "Load Document",
            "request": {
                "method": "load_document",
                "params": {
                    "file_path": "/path/to/document.pdf"
                }
            },
            "response": {
                "status": "success",
                "message": "Successfully loaded document: /path/to/document.pdf",
                "metadata": {
                    "file_path": "/path/to/document.pdf",
                    "content_length": 15420,
                    "num_chunks": 12,
                    "total_chunks_in_store": 12
                }
            }
        },
        {
            "name": "Ask Question",
            "request": {
                "method": "ask_question",
                "params": {
                    "question": "What is the main topic of this document?"
                }
            },
            "response": {
                "status": "success",
                "question": "What is the main topic of this document?",
                "answer": "Based on the document content, the main topic is...",
                "sources": [
                    {
                        "file": "/path/to/document.pdf",
                        "chunk_id": "document_0",
                        "similarity_score": 0.892
                    }
                ],
                "confidence": 0.892
            }
        },
        {
            "name": "Get Status",
            "request": {
                "method": "get_status",
                "params": {}
            },
            "response": {
                "status": "active",
                "loaded_documents": ["/path/to/document.pdf"],
                "total_chunks": 12,
                "supported_formats": [".pdf", ".txt", ".md", ".markdown"]
            }
        }
    ]
    
    for example in examples:
        print(f"\n{example['name']}:")
        print("Request:")
        print(json.dumps(example['request'], indent=2))
        print("Response:")
        print(json.dumps(example['response'], indent=2))


if __name__ == "__main__":
    print_mcp_examples()
    print("\n" + "=" * 50)
    asyncio.run(run_examples())