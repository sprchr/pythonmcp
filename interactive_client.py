#!/usr/bin/env python3
"""
Interactive client for Document Q&A MCP Server

This provides a simple command-line interface to interact with the running server.
"""

import asyncio
import json
import os
from document_qa_server import DocumentQAServer, handle_mcp_request


class InteractiveClient:
    """Interactive client for the Document Q&A MCP Server."""
    
    def __init__(self):
        """Initialize the client with the server."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.server = DocumentQAServer(api_key)
        
    async def run(self):
        """Run the interactive client."""
        print("🚀 Document Q&A MCP Server - Interactive Client")
        print("=" * 60)
        print("Commands:")
        print("  load <file_path>     - Load a document")
        print("  ask <question>       - Ask a question")
        print("  status              - Check server status")
        print("  help                - Show this help")
        print("  quit                - Exit client")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n📝 Enter command: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if user_input.lower() in ['help', 'h']:
                    self.show_help()
                    continue
                
                # Parse command
                parts = user_input.split(' ', 1)
                command = parts[0].lower()
                
                if command == 'load':
                    if len(parts) < 2:
                        print("❌ Usage: load <file_path>")
                        continue
                    await self.load_document(parts[1])
                    
                elif command == 'ask':
                    if len(parts) < 2:
                        print("❌ Usage: ask <question>")
                        continue
                    await self.ask_question(parts[1])
                    
                elif command == 'status':
                    await self.show_status()
                    
                else:
                    print(f"❌ Unknown command: {command}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    async def load_document(self, file_path: str):
        """Load a document into the server."""
        print(f"📄 Loading document: {file_path}")
        
        request = {
            "method": "load_document",
            "params": {"file_path": file_path}
        }
        
        response = await handle_mcp_request(self.server, request)
        
        if response.get("status") == "success":
            metadata = response.get("metadata", {})
            print(f"✅ Document loaded successfully!")
            print(f"   📊 Content length: {metadata.get('content_length', 'N/A')} characters")
            print(f"   🧩 Number of chunks: {metadata.get('num_chunks', 'N/A')}")
            print(f"   📚 Total chunks in store: {metadata.get('total_chunks_in_store', 'N/A')}")
        else:
            print(f"❌ Failed to load document: {response.get('message', 'Unknown error')}")
    
    async def ask_question(self, question: str):
        """Ask a question to the server."""
        print(f"❓ Question: {question}")
        
        request = {
            "method": "ask_question",
            "params": {"question": question}
        }
        
        response = await handle_mcp_request(self.server, request)
        
        if response.get("status") == "success":
            answer = response.get("answer", "No answer provided")
            confidence = response.get("confidence", 0)
            sources = response.get("sources", [])
            
            print(f"💡 Answer: {answer}")
            print(f"🎯 Confidence: {confidence:.3f}")
            
            if sources:
                print("📚 Sources:")
                for source in sources:
                    file_name = os.path.basename(source.get("file", "Unknown"))
                    similarity = source.get("similarity_score", 0)
                    print(f"   - {file_name} (similarity: {similarity:.3f})")
        else:
            print(f"❌ Error: {response.get('answer', 'Unknown error')}")
    
    async def show_status(self):
        """Show server status."""
        request = {
            "method": "get_status",
            "params": {}
        }
        
        response = await handle_mcp_request(self.server, request)
        
        print("📊 Server Status:")
        print(f"   Status: {response.get('status', 'Unknown')}")
        print(f"   Total chunks: {response.get('total_chunks', 0)}")
        
        loaded_docs = response.get('loaded_documents', [])
        if loaded_docs:
            print("   📚 Loaded documents:")
            for doc in loaded_docs:
                print(f"     - {os.path.basename(doc)}")
        else:
            print("   📚 No documents loaded")
        
        formats = response.get('supported_formats', [])
        print(f"   🔧 Supported formats: {', '.join(formats)}")
    
    def show_help(self):
        """Show help information."""
        print("\n📖 Available Commands:")
        print("  load <file_path>     - Load a PDF, TXT, or Markdown document")
        print("  ask <question>       - Ask a question about loaded documents")
        print("  status              - Show server status and loaded documents")
        print("  help                - Show this help message")
        print("  quit                - Exit the client")
        print("\n💡 Examples:")
        print("  load document.pdf")
        print("  ask What is the main topic of this document?")
        print("  status")


async def main():
    """Main entry point."""
    client = InteractiveClient()
    await client.run()


if __name__ == "__main__":
    asyncio.run(main())