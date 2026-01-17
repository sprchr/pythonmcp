#!/usr/bin/env python3
"""
MCP Server for Document-Based Q&A using OpenAI API

This server implements the Model Context Protocol (MCP) to provide document-based
question answering capabilities. It loads documents, creates embeddings for semantic
search, and uses OpenAI's API to generate answers strictly based on document content.

Architecture:
- DocumentLoader: Handles PDF, TXT, and Markdown file loading
- DocumentChunker: Intelligently splits documents into semantic chunks
- EmbeddingStore: Manages vector embeddings for similarity search
- QueryHandler: Processes questions and generates context-aware responses
- MCPServer: Exposes MCP-compliant endpoints
"""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

import numpy as np
import openai
from PyPDF2 import PdfReader
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from validation_agent import ValidationAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of document content with metadata."""
    content: str
    chunk_id: str
    source_file: str
    start_char: int
    end_char: int
    embedding: Optional[np.ndarray] = None


class DocumentLoader:
    """Handles loading of various document formats."""
    
    @staticmethod
    def load_document(file_path: str) -> str:
        """
        Load document content from supported file formats.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Document content as string
            
        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file doesn't exist
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        file_extension = path.suffix.lower()
        
        if file_extension == '.pdf':
            return DocumentLoader._load_pdf(file_path)
        elif file_extension in ['.txt', '.md', '.markdown']:
            return DocumentLoader._load_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    @staticmethod
    def _load_pdf(file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error reading PDF: {str(e)}")
    
    @staticmethod
    def _load_text(file_path: str) -> str:
        """Load text from plain text or markdown file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except Exception as e:
            raise ValueError(f"Error reading text file: {str(e)}")


class DocumentChunker:
    """Intelligently chunks documents for optimal retrieval."""
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize chunker with size and overlap parameters.
        
        Args:
            chunk_size: Target size for each chunk in characters
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_document(self, content: str, source_file: str) -> List[DocumentChunk]:
        """
        Split document into semantic chunks with overlap.
        
        Args:
            content: Document content to chunk
            source_file: Source file path for metadata
            
        Returns:
            List of DocumentChunk objects
        """
        # First, try to split by paragraphs for better semantic boundaries
        paragraphs = self._split_by_paragraphs(content)
        chunks = []
        current_chunk = ""
        current_start = 0
        chunk_id = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, finalize current chunk
            if len(current_chunk) + len(paragraph) > self.chunk_size and current_chunk:
                chunk = DocumentChunk(
                    content=current_chunk.strip(),
                    chunk_id=f"{Path(source_file).stem}_{chunk_id}",
                    source_file=source_file,
                    start_char=current_start,
                    end_char=current_start + len(current_chunk)
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.overlap:] if len(current_chunk) > self.overlap else current_chunk
                current_chunk = overlap_text + "\n" + paragraph
                current_start = current_start + len(current_chunk) - len(overlap_text) - len(paragraph) - 1
                chunk_id += 1
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Add final chunk if it has content
        if current_chunk.strip():
            chunk = DocumentChunk(
                content=current_chunk.strip(),
                chunk_id=f"{Path(source_file).stem}_{chunk_id}",
                source_file=source_file,
                start_char=current_start,
                end_char=current_start + len(current_chunk)
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks from {source_file}")
        return chunks
    
    def _split_by_paragraphs(self, content: str) -> List[str]:
        """Split content by paragraphs, preserving semantic boundaries."""
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', content)
        
        # Filter out empty paragraphs and strip whitespace
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs


class EmbeddingStore:
    """Manages document embeddings for semantic search."""
    
    def __init__(self, openai_client: openai.OpenAI):
        """
        Initialize embedding store with OpenAI client.
        
        Args:
            openai_client: Configured OpenAI client
        """
        self.client = openai_client
        self.chunks: List[DocumentChunk] = []
        self.embeddings: Optional[np.ndarray] = None
    
    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """
        Add document chunks and generate embeddings.
        
        Args:
            chunks: List of document chunks to add
        """
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        # Generate embeddings for all chunks
        texts = [chunk.content for chunk in chunks]
        embeddings = await self._generate_embeddings(texts)
        
        # Store embeddings in chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        # Add to store
        self.chunks.extend(chunks)
        
        # Rebuild embedding matrix
        all_embeddings = [chunk.embedding for chunk in self.chunks]
        self.embeddings = np.vstack(all_embeddings)
        
        logger.info(f"Total chunks in store: {len(self.chunks)}")
    
    async def search_similar(self, query: str, top_k: int = 3) -> List[Tuple[DocumentChunk, float]]:
        """
        Find most similar chunks to query using cosine similarity.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of (chunk, similarity_score) tuples
        """
        if not self.chunks or self.embeddings is None:
            return []
        
        # Generate query embedding
        query_embeddings = await self._generate_embeddings([query])
        query_embedding = query_embeddings[0]
        
        # Calculate similarities
        similarities = cosine_similarity([query_embedding], self.embeddings)[0]
        
        # Get top-k most similar chunks
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx]
            score = similarities[idx]
            results.append((chunk, score))
        
        logger.info(f"Found {len(results)} similar chunks for query")
        return results
    
    async def _generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """Generate embeddings using OpenAI API."""
        try:
            response = await asyncio.to_thread(
                self.client.embeddings.create,
                model="text-embedding-3-small",
                input=texts
            )
            
            embeddings = []
            for data in response.data:
                embeddings.append(np.array(data.embedding))
            
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def clear(self) -> None:
        """Clear all stored chunks and embeddings."""
        self.chunks.clear()
        self.embeddings = None
        logger.info("Cleared embedding store")


class QueryHandler:
    """Handles question answering using retrieved context."""
    
    def __init__(self, openai_client: openai.OpenAI, embedding_store: EmbeddingStore, validation_agent: Optional[ValidationAgent] = None):
        """
        Initialize query handler.
        
        Args:
            openai_client: Configured OpenAI client
            embedding_store: Embedding store for retrieval
            validation_agent: Optional validation agent for answer validation
        """
        self.client = openai_client
        self.embedding_store = embedding_store
        self.validation_agent = validation_agent
    
    async def answer_question(self, question: str, max_context_chunks: int = 3) -> Dict[str, Any]:
        """
        Answer question based on document content.
        
        Args:
            question: User's question
            max_context_chunks: Maximum number of context chunks to use
            
        Returns:
            Dictionary containing answer and metadata
        """
        # Retrieve relevant chunks
        similar_chunks = await self.embedding_store.search_similar(
            question, top_k=max_context_chunks
        )
        
        if not similar_chunks:
            return {
                "answer": "No documents have been loaded. Please load a document first.",
                "sources": []
            }
        
        # Build context from retrieved chunks
        context_parts = []
        sources = []
        
        for chunk, score in similar_chunks:
            context_parts.append(f"[Source: {chunk.source_file}]\n{chunk.content}")
            sources.append({
                "file": chunk.source_file,
                "chunk_id": chunk.chunk_id,
                "similarity_score": float(score)
            })
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Generate answer using OpenAI
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful assistant that answers questions strictly based on the provided document context. 

CRITICAL INSTRUCTIONS:
- Only answer based on the information explicitly provided in the context below
- If the context doesn't contain enough information to answer the question, respond with: "The document does not contain this information"
- Do not use your general knowledge or make assumptions beyond what's in the context
- Be precise and cite specific parts of the context when possible
- If you're uncertain, err on the side of saying the information isn't available"""
                    },
                    {
                        "role": "user",
                        "content": f"Context from documents:\n\n{context}\n\nQuestion: {question}"
                    }
                ],
                temperature=0.1,  # Low temperature for more deterministic responses
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            # Validate answer if validation agent is available
            validation_result = None
            if self.validation_agent:
                try:
                    validation_result = await self.validation_agent.validate_answer(
                        question=question,
                        answer=answer,
                        context=context,
                        sources=sources
                    )
                    logger.info(f"Answer validated. Status: {validation_result.status.value}, Score: {validation_result.overall_score:.2f}")
                except Exception as e:
                    logger.error(f"Validation failed: {str(e)}")
                    # Continue without validation if it fails
            
            result = {
                "answer": answer,
                "sources": sources
            }
            
            # Add validation results if available
            if validation_result:
                result["validation"] = self.validation_agent.format_validation_result(validation_result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "sources": sources
            }


class DocumentQAServer:
    """MCP-compliant server for document-based question answering."""
    
    def __init__(self, openai_api_key: str, enable_validation: bool = True):
        """
        Initialize the MCP server.
        
        Args:
            openai_api_key: OpenAI API key
            enable_validation: Whether to enable answer validation (default: True)
        """
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.embedding_store = EmbeddingStore(self.openai_client)
        
        # Initialize validation agent if enabled
        self.validation_agent = None
        if enable_validation:
            self.validation_agent = ValidationAgent(self.openai_client)
            logger.info("Validation Agent enabled")
        
        self.query_handler = QueryHandler(
            self.openai_client, 
            self.embedding_store,
            validation_agent=self.validation_agent
        )
        self.document_loader = DocumentLoader()
        self.document_chunker = DocumentChunker()
        
        logger.info("Document Q&A MCP Server initialized")
    
    async def load_document(self, file_path: str) -> Dict[str, Any]:
        """
        MCP endpoint: Load a document into the system.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Status and metadata about the loaded document
        """
        try:
            # Load document content
            content = self.document_loader.load_document(file_path)
            
            # Chunk the document
            chunks = self.document_chunker.chunk_document(content, file_path)
            
            # Generate and store embeddings
            await self.embedding_store.add_chunks(chunks)
            
            return {
                "status": "success",
                "message": f"Successfully loaded document: {file_path}",
                "metadata": {
                    "file_path": file_path,
                    "content_length": len(content),
                    "num_chunks": len(chunks),
                    "total_chunks_in_store": len(self.embedding_store.chunks)
                }
            }
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to load document: {str(e)}",
                "metadata": {}
            }
    
    async def ask_question(self, question: str) -> Dict[str, Any]:
        """
        MCP endpoint: Ask a question about loaded documents.
        
        Args:
            question: User's question
            
        Returns:
            Answer and supporting information
        """
        try:
            result = await self.query_handler.answer_question(question)
            
            return {
                "status": "success",
                "question": question,
                "answer": result["answer"],
                "sources": result["sources"],
                **({"validation": result["validation"]} if "validation" in result else {})
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {
                "status": "error",
                "question": question,
                "answer": f"Error processing question: {str(e)}",
                "sources": []
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        MCP endpoint: Get server status and loaded documents info.
        
        Returns:
            Server status information
        """
        loaded_files = list(set(chunk.source_file for chunk in self.embedding_store.chunks))
        
        return {
            "status": "active",
            "loaded_documents": loaded_files,
            "total_chunks": len(self.embedding_store.chunks),
            "supported_formats": [".pdf", ".txt", ".md", ".markdown"]
        }


# MCP Protocol Implementation
async def handle_mcp_request(server: DocumentQAServer, request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming MCP requests and route to appropriate endpoints.
    
    Args:
        server: DocumentQAServer instance
        request: MCP request payload
        
    Returns:
        MCP response payload
    """
    method = request.get("method")
    params = request.get("params", {})
    
    if method == "load_document":
        file_path = params.get("file_path")
        if not file_path:
            return {"error": "file_path parameter is required"}
        return await server.load_document(file_path)
    
    elif method == "ask_question":
        question = params.get("question")
        if not question:
            return {"error": "question parameter is required"}
        return await server.ask_question(question)
    
    elif method == "get_status":
        return server.get_status()
    
    else:
        return {"error": f"Unknown method: {method}"}


async def main():
    """Main server entry point for testing."""
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        logger.error("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        return
    
    # Initialize server
    server = DocumentQAServer(api_key)
    
    # Example usage
    print("Document Q&A MCP Server")
    print("======================")
    
    # Example requests
    example_requests = [
        {
            "method": "get_status",
            "params": {}
        }
    ]
    
    for request in example_requests:
        print(f"\nRequest: {json.dumps(request, indent=2)}")
        response = await handle_mcp_request(server, request)
        print(f"Response: {json.dumps(response, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())