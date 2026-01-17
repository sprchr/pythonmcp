#!/usr/bin/env python3
"""
Simple Document Q&A Server - No MCP Needed

This shows what we actually need for a web-based document Q&A system.
The MCP layer is unnecessary complexity for this use case.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

import numpy as np
import openai
from PyPDF2 import PdfReader
from sklearn.metrics.pairwise import cosine_similarity
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn


@dataclass
class DocumentChunk:
    """Represents a chunk of document content with metadata."""
    content: str
    chunk_id: str
    source_file: str
    start_char: int
    end_char: int
    embedding: Optional[np.ndarray] = None


class SimpleDocumentQA:
    """Simple Document Q&A without MCP complexity."""
    
    def __init__(self, openai_api_key: str):
        """Initialize with OpenAI API key."""
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.chunks: List[DocumentChunk] = []
        self.embeddings: Optional[np.ndarray] = None
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
    
    def load_document(self, file_path: str) -> Dict[str, Any]:
        """Load and process a document."""
        try:
            # Load document content
            content = self._load_file_content(file_path)
            
            # Create chunks
            chunks = self._chunk_document(content, file_path)
            
            # Generate embeddings
            asyncio.create_task(self._add_chunks_async(chunks))
            
            return {
                "status": "success",
                "message": f"Loaded document: {file_path}",
                "chunks_created": len(chunks),
                "total_chunks": len(self.chunks) + len(chunks)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def ask_question(self, question: str) -> Dict[str, Any]:
        """Ask a question about loaded documents."""
        try:
            if not self.chunks:
                return {
                    "status": "error",
                    "answer": "No documents loaded. Please upload a document first."
                }
            
            # Find relevant chunks
            relevant_chunks = await self._search_similar_chunks(question)
            
            if not relevant_chunks:
                return {
                    "status": "success",
                    "answer": "No relevant content found in the loaded documents."
                }
            
            # Generate answer
            answer = await self._generate_answer(question, relevant_chunks)
            
            return {
                "status": "success",
                "answer": answer,
                "sources": [
                    {
                        "file": chunk.source_file,
                        "chunk_id": chunk.chunk_id,
                        "similarity": float(score)
                    }
                    for chunk, score in relevant_chunks
                ]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "answer": f"Error processing question: {str(e)}"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        loaded_files = list(set(chunk.source_file for chunk in self.chunks))
        
        return {
            "status": "active",
            "loaded_documents": loaded_files,
            "total_chunks": len(self.chunks),
            "supported_formats": [".pdf", ".txt", ".md", ".markdown"]
        }
    
    # Private methods (implementation details)
    def _load_file_content(self, file_path: str) -> str:
        """Load content from various file formats."""
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if path.suffix.lower() == '.pdf':
            reader = PdfReader(file_path)
            return "\\n".join(page.extract_text() for page in reader.pages)
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def _chunk_document(self, content: str, source_file: str) -> List[DocumentChunk]:
        """Split document into chunks."""
        chunk_size = 1000
        overlap = 200
        chunks = []
        
        # Simple chunking by paragraphs
        paragraphs = content.split('\\n\\n')
        current_chunk = ""
        chunk_id = 0
        start_pos = 0
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                # Create chunk
                chunk = DocumentChunk(
                    content=current_chunk.strip(),
                    chunk_id=f"{Path(source_file).stem}_{chunk_id}",
                    source_file=source_file,
                    start_char=start_pos,
                    end_char=start_pos + len(current_chunk)
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
                current_chunk = overlap_text + "\\n" + paragraph
                start_pos += len(current_chunk) - len(overlap_text)
                chunk_id += 1
            else:
                current_chunk += "\\n" + paragraph if current_chunk else paragraph
        
        # Add final chunk
        if current_chunk.strip():
            chunk = DocumentChunk(
                content=current_chunk.strip(),
                chunk_id=f"{Path(source_file).stem}_{chunk_id}",
                source_file=source_file,
                start_char=start_pos,
                end_char=start_pos + len(current_chunk)
            )
            chunks.append(chunk)
        
        return chunks
    
    async def _add_chunks_async(self, chunks: List[DocumentChunk]):
        """Add chunks and generate embeddings."""
        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        response = await asyncio.to_thread(
            self.openai_client.embeddings.create,
            model="text-embedding-3-small",
            input=texts
        )
        
        # Store embeddings
        for chunk, data in zip(chunks, response.data):
            chunk.embedding = np.array(data.embedding)
        
        # Add to store
        self.chunks.extend(chunks)
        
        # Rebuild embedding matrix
        if self.chunks:
            all_embeddings = [chunk.embedding for chunk in self.chunks]
            self.embeddings = np.vstack(all_embeddings)
    
    async def _search_similar_chunks(self, query: str, top_k: int = 3) -> List[Tuple[DocumentChunk, float]]:
        """Find similar chunks to query."""
        if not self.chunks or self.embeddings is None:
            return []
        
        # Generate query embedding
        response = await asyncio.to_thread(
            self.openai_client.embeddings.create,
            model="text-embedding-3-small",
            input=[query]
        )
        query_embedding = np.array(response.data[0].embedding)
        
        # Calculate similarities
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        return [(self.chunks[idx], similarities[idx]) for idx in top_indices]
    
    async def _generate_answer(self, question: str, relevant_chunks: List[Tuple[DocumentChunk, float]]) -> str:
        """Generate answer using OpenAI."""
        # Build context
        context_parts = []
        for chunk, score in relevant_chunks:
            context_parts.append(f"[Source: {chunk.source_file}]\\n{chunk.content}")
        
        context = "\\n\\n---\\n\\n".join(context_parts)
        
        # Generate answer
        response = await asyncio.to_thread(
            self.openai_client.chat.completions.create,
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """Answer questions based only on the provided context. 
                    If the context doesn't contain the information, say 'The document does not contain this information'."""
                },
                {
                    "role": "user",
                    "content": f"Context:\\n\\n{context}\\n\\nQuestion: {question}"
                }
            ],
            temperature=0.1
        )
        
        return response.choices[0].message.content


class SimpleWebServer:
    """Simple web server without MCP complexity."""
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.qa_system = SimpleDocumentQA(api_key)
    
    async def homepage(self, request):
        """Serve the main page."""
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Simple Document Q&A</title></head>
        <body>
            <h1>Simple Document Q&A (No MCP)</h1>
            <p>This version shows what we actually need - no MCP complexity!</p>
            
            <h2>Upload Document</h2>
            <input type="file" id="file-upload">
            <button onclick="uploadFile()">Upload</button>
            
            <h2>Ask Question</h2>
            <input type="text" id="question" placeholder="Enter your question">
            <button onclick="askQuestion()">Ask</button>
            
            <div id="result"></div>
            
            <script>
                async function uploadFile() {
                    const file = document.getElementById('file-upload').files[0];
                    if (!file) return;
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    document.getElementById('result').innerHTML = 
                        `<h3>Upload Result:</h3><pre>${JSON.stringify(result, null, 2)}</pre>`;
                }
                
                async function askQuestion() {
                    const question = document.getElementById('question').value;
                    if (!question) return;
                    
                    const response = await fetch('/ask', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({question})
                    });
                    
                    const result = await response.json();
                    document.getElementById('result').innerHTML = 
                        `<h3>Answer:</h3><p>${result.answer}</p>`;
                }
            </script>
        </body>
        </html>
        """)
    
    async def upload_file(self, request):
        """Handle file upload - NO MCP needed!"""
        try:
            form = await request.form()
            file = form["file"]
            
            # Save file
            file_path = self.qa_system.upload_dir / file.filename
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Load directly (no MCP protocol)
            result = self.qa_system.load_document(str(file_path))
            return JSONResponse(result)
            
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)})
    
    async def ask_question(self, request):
        """Handle questions - NO MCP needed!"""
        try:
            data = await request.json()
            question = data.get("question")
            
            # Ask directly (no MCP protocol)
            result = await self.qa_system.ask_question(question)
            return JSONResponse(result)
            
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)})


def create_simple_app():
    """Create simple app without MCP."""
    server = SimpleWebServer()
    
    routes = [
        Route("/", server.homepage),
        Route("/upload", server.upload_file, methods=["POST"]),
        Route("/ask", server.ask_question, methods=["POST"]),
    ]
    
    return Starlette(routes=routes)


if __name__ == "__main__":
    print("🚀 Simple Document Q&A Server (No MCP)")
    print("📍 http://localhost:8001")
    print("💡 This shows what we actually need!")
    
    app = create_simple_app()
    uvicorn.run(app, host="127.0.0.1", port=8001)