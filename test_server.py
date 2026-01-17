#!/usr/bin/env python3
"""
Test script for Document Q&A MCP Server

Run basic tests to verify server functionality.
"""

import asyncio
import os
import tempfile
from document_qa_server import DocumentQAServer, handle_mcp_request


async def test_server():
    """Run comprehensive tests of the MCP server."""
    
    print("Testing Document Q&A MCP Server")
    print("=" * 40)
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("✗ OPENAI_API_KEY environment variable not set")
        return
    
    try:
        server = DocumentQAServer(api_key)
        print("✓ Server initialized successfully")
    except Exception as e:
        print(f"✗ Server initialization failed: {e}")
        return
    
    # Test 1: Server status
    print("\n1. Testing server status...")
    try:
        request = {"method": "get_status", "params": {}}
        response = await handle_mcp_request(server, request)
        assert response["status"] == "active"
        print("✓ Server status check passed")
    except Exception as e:
        print(f"✗ Server status test failed: {e}")
    
    # Test 2: Create and load test document
    print("\n2. Testing document loading...")
    
    test_content = """
# Test Document

## Section 1: Introduction
This is a test document for the Document Q&A MCP Server.
It contains information about testing and validation.

## Section 2: Features
The server supports the following features:
- PDF document processing
- Text file processing  
- Markdown file processing
- Semantic search capabilities
- Question answering with context

## Section 3: Technical Details
The system uses OpenAI embeddings for semantic search.
It chunks documents intelligently to maintain context.
The retrieval system uses cosine similarity for matching.
    """
    
    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(test_content)
        test_file_path = f.name
    
    try:
        request = {
            "method": "load_document",
            "params": {"file_path": test_file_path}
        }
        response = await handle_mcp_request(server, request)
        assert response["status"] == "success"
        assert response["metadata"]["num_chunks"] > 0
        print(f"✓ Document loaded successfully ({response['metadata']['num_chunks']} chunks)")
    except Exception as e:
        print(f"✗ Document loading test failed: {e}")
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)
    
    # Test 3: Question answering
    print("\n3. Testing question answering...")
    
    test_questions = [
        {
            "question": "What features does the server support?",
            "should_find_answer": True
        },
        {
            "question": "What embedding system is used?",
            "should_find_answer": True
        },
        {
            "question": "What is the capital of Mars?",
            "should_find_answer": False
        }
    ]
    
    for i, test_case in enumerate(test_questions, 1):
        try:
            request = {
                "method": "ask_question",
                "params": {"question": test_case["question"]}
            }
            response = await handle_mcp_request(server, request)
            
            assert response["status"] == "success"
            answer = response["answer"]
            
            if test_case["should_find_answer"]:
                # Should not contain "does not contain this information"
                if "does not contain this information" in answer.lower():
                    print(f"✗ Question {i} failed: Expected answer but got 'not found'")
                else:
                    print(f"✓ Question {i} answered correctly")
            else:
                # Should contain "does not contain this information" or similar
                if "does not contain" in answer.lower() or "not available" in answer.lower():
                    print(f"✓ Question {i} correctly identified missing information")
                else:
                    print(f"? Question {i} gave unexpected answer: {answer[:100]}...")
                    
        except Exception as e:
            print(f"✗ Question {i} test failed: {e}")
    
    # Test 4: Error handling
    print("\n4. Testing error handling...")
    
    # Test invalid file path
    try:
        request = {
            "method": "load_document",
            "params": {"file_path": "/nonexistent/file.pdf"}
        }
        response = await handle_mcp_request(server, request)
        assert response["status"] == "error"
        print("✓ Invalid file path handled correctly")
    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
    
    # Test invalid method
    try:
        request = {
            "method": "invalid_method",
            "params": {}
        }
        response = await handle_mcp_request(server, request)
        assert "error" in response
        print("✓ Invalid method handled correctly")
    except Exception as e:
        print(f"✗ Invalid method test failed: {e}")
    
    # Test missing parameters
    try:
        request = {
            "method": "ask_question",
            "params": {}  # Missing question parameter
        }
        response = await handle_mcp_request(server, request)
        assert "error" in response
        print("✓ Missing parameters handled correctly")
    except Exception as e:
        print(f"✗ Missing parameters test failed: {e}")
    
    print("\n" + "=" * 40)
    print("Testing completed!")


if __name__ == "__main__":
    asyncio.run(test_server())