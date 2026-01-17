#!/usr/bin/env python3
"""
Web server for Document Q&A MCP Server with file upload support

This creates a complete web interface with file upload functionality.
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any

from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, FileResponse, Response
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from document_qa_server import DocumentQAServer, handle_mcp_request


class WebServer:
    """Web server for Document Q&A interface."""
    
    def __init__(self):
        """Initialize the web server."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.qa_server = DocumentQAServer(api_key)
        self.upload_dir = Path("uploads")
        self.upload_dir.mkdir(exist_ok=True)
    
    async def homepage(self, request):
        """Serve the main HTML interface."""
        html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document Q&A MCP Server With Results Validated By Agent</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.2em;
        }
        .section {
            margin-bottom: 30px;
            padding: 25px;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            background-color: #fafafa;
        }
        .section h2 {
            margin-top: 0;
            color: #555;
            font-size: 1.4em;
            border-bottom: 2px solid #007cba;
            padding-bottom: 10px;
        }
        input[type="text"], textarea, input[type="file"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
            transition: border-color 0.3s;
        }
        input[type="text"]:focus, textarea:focus, input[type="file"]:focus {
            border-color: #007cba;
            outline: none;
        }
        button {
            background-color: #007cba;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            margin-top: 15px;
            margin-right: 10px;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #005a87;
        }
        button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .result {
            margin-top: 20px;
            padding: 20px;
            border-radius: 8px;
            background-color: #e8f4f8;
            border-left: 4px solid #007cba;
            color: #000;
        }
        .error {
            background-color: #ffeaea;
            border-left-color: #d63384;
            color: #000;
        }
        .success {
            background-color: #e8f5e8;
            border-left-color: #28a745;
            color: #000;
        }
        .status-info {
            background-color: #f0f9ff;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            border: 1px solid #b3d9ff;
        }
        .file-formats {
            font-size: 12px;
            color: #666;
            margin-top: 8px;
            font-style: italic;
        }
        .sources {
            margin-top: 15px;
            font-size: 13px;
            color: #000;
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
        }
        .confidence {
            font-weight: bold;
            color: #007cba;
            font-size: 14px;
        }
        .loading {
            display: none;
            color: #007cba;
            font-style: italic;
        }
        .upload-area {
            border: 2px dashed #007cba;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            background-color: #f8f9fa;
            margin-bottom: 15px;
        }
        .file-info {
            margin-top: 10px;
            font-size: 13px;
            color: #666;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .stat-item {
            background: white;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
            border: 1px solid #e0e0e0;
        }
        .stat-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #007cba;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Document Q&A MCP Server With Results Validated By Agent</h1>
        
        <div class="status-info">
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value" id="server-status">Active</div>
                    <div class="stat-label">Server Status</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="loaded-docs">0</div>
                    <div class="stat-label">Loaded Documents</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="total-chunks">0</div>
                    <div class="stat-label">Total Chunks</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📄 Upload & Load Document</h2>
            <div class="upload-area">
                <input type="file" id="file-upload" accept=".pdf,.txt,.md,.markdown" style="display: none;">
                <button onclick="document.getElementById('file-upload').click()">📁 Choose File</button>
                <div class="file-info" id="file-info">No file selected</div>
            </div>
            <div class="file-formats">Supported formats: PDF, TXT, Markdown (.md, .markdown)</div>
            <button onclick="uploadAndLoadDocument()" id="upload-btn" disabled>📤 Upload & Load Document</button>
            <div class="loading" id="upload-loading">⏳ Uploading and processing document...</div>
            <div id="load-result"></div>
        </div>
        
        <div class="section">
            <h2>❓ Ask Question</h2>
            <textarea id="question" rows="4" placeholder="Enter your question about the loaded documents..."></textarea>
            <button onclick="askQuestion()" id="ask-btn">🤔 Ask Question</button>
            <div class="loading" id="question-loading">⏳ Processing your question...</div>
            <div id="question-result"></div>
        </div>
        
        <div class="section">
            <h2>📊 Server Information</h2>
            <button onclick="updateStatus()">🔄 Refresh Status</button>
            <div id="status-result"></div>
        </div>
    </div>

    <script>
        let selectedFile = null;
        
        // File selection handler
        document.getElementById('file-upload').addEventListener('change', function(e) {
            selectedFile = e.target.files[0];
            const fileInfo = document.getElementById('file-info');
            const uploadBtn = document.getElementById('upload-btn');
            
            if (selectedFile) {
                fileInfo.textContent = `Selected: ${selectedFile.name} (${(selectedFile.size / 1024).toFixed(1)} KB)`;
                uploadBtn.disabled = false;
            } else {
                fileInfo.textContent = 'No file selected';
                uploadBtn.disabled = true;
            }
        });
        
        function showResult(elementId, content, type = 'info') {
            const element = document.getElementById(elementId);
            element.innerHTML = content;
            element.className = `result ${type}`;
        }
        
        function showLoading(elementId, show = true) {
            document.getElementById(elementId).style.display = show ? 'block' : 'none';
        }
        
        async function uploadAndLoadDocument() {
            if (!selectedFile) {
                showResult('load-result', 'Please select a file first', 'error');
                return;
            }
            
            const uploadBtn = document.getElementById('upload-btn');
            uploadBtn.disabled = true;
            showLoading('upload-loading', true);
            
            try {
                const formData = new FormData();
                formData.append('file', selectedFile);
                
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    showResult('load-result', `
                        <div style="color: #000;">
                            <strong style="color: #000;">✅ Document loaded successfully!</strong><br>
                            <strong style="color: #000;">File:</strong> <span style="color: #000;">${result.metadata.file_path}</span><br>
                            <strong style="color: #000;">Content Length:</strong> <span style="color: #000;">${result.metadata.content_length.toLocaleString()} characters</span><br>
                            <strong style="color: #000;">Chunks Created:</strong> <span style="color: #000;">${result.metadata.num_chunks}</span><br>
                            <strong style="color: #000;">Total Chunks in Store:</strong> <span style="color: #000;">${result.metadata.total_chunks_in_store}</span>
                        </div>
                    `, 'success');
                    updateStatus();
                } else {
                    showResult('load-result', `❌ ${result.message}`, 'error');
                }
            } catch (error) {
                showResult('load-result', `❌ Upload failed: ${error.message}`, 'error');
            } finally {
                uploadBtn.disabled = false;
                showLoading('upload-loading', false);
            }
        }
        
        async function askQuestion() {
            const question = document.getElementById('question').value.trim();
            if (!question) {
                showResult('question-result', 'Please enter a question', 'error');
                return;
            }
            
            const askBtn = document.getElementById('ask-btn');
            askBtn.disabled = true;
            showLoading('question-loading', true);
            
            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question: question })
                });
                
                const result = await response.json();
                
                if (result.status === 'success') {
                    let sourcesHtml = '';
                    if (result.sources && result.sources.length > 0) {
                        sourcesHtml = '<div class="sources" style="color: #000;"><strong style="color: #000;">📚 Sources:</strong><br>';
                        result.sources.forEach(source => {
                            const fileName = source.file.split('/').pop().split('\\\\').pop();
                            sourcesHtml += `<span style="color: #000;">• ${fileName} (similarity: ${source.similarity_score.toFixed(3)})</span><br>`;
                        });
                        sourcesHtml += '</div>';
                    }
                    
                    // Add validation results if available
                    let validationHtml = '';
                    if (result.validation) {
                        const val = result.validation;
                        const statusEmoji = {
                            'valid': '✅',
                            'partially_valid': '⚠️',
                            'invalid': '❌',
                            'uncertain': '❓'
                        };
                        const statusColor = {
                            'valid': '#28a745',
                            'partially_valid': '#ffc107',
                            'invalid': '#dc3545',
                            'uncertain': '#6c757d'
                        };
                        
                        validationHtml = `
                            <div class="validation-section" style="margin-top: 20px; padding: 15px; background-color: #f8f9fa; border-radius: 8px; border-left: 4px solid ${statusColor[val.validation_status] || '#6c757d'};">
                                <strong style="color: #000;">🔍 AI Agent Validation Results:</strong><br>
                                <div style="font-size: 12px; color: #666; margin-bottom: 10px;">Validated by AI Validation Agent</div>
                                <span style="font-size: 16px; font-weight: bold; color: ${statusColor[val.validation_status] || '#6c757d'};">
                                    ${statusEmoji[val.validation_status] || '❓'} Status: ${val.validation_status.toUpperCase()}
                                </span>
                                <br><br>
                                <strong style="color: #000;">Validation Score:</strong> <span style="color: #000;">${(val.overall_score * 100).toFixed(1)}%</span><br>
                                <br>
                                
                                <strong style="color: #000;">Checks:</strong><br>
                                <span style="color: #000;">• Based on Document: ${val.is_based_on_document ? '✅ Yes' : '❌ No'}</span><br>
                                <span style="color: #000;">• Accurate: ${val.is_accurate ? '✅ Yes' : '❌ No'}</span><br>
                                <span style="color: #000;">• Complete: ${val.is_complete ? '✅ Yes' : '❌ No'}</span><br>
                                <span style="color: #000;">• Hallucinations: ${val.has_hallucinations ? '❌ Detected' : '✅ None'}</span><br><br>
                                
                                <strong style="color: #000;">Feedback:</strong><br>
                                <div style="font-style: italic; color: #000; margin-top: 5px;">${val.feedback}</div>
                                
                                ${val.issues && val.issues.length > 0 ? `
                                    <br><strong style="color: #000;">⚠️ Issues Found:</strong><br>
                                    <ul style="margin: 5px 0; padding-left: 20px; color: #000;">
                                        ${val.issues.map(issue => `<li style="color: #000;">${issue}</li>`).join('')}
                                    </ul>
                                ` : ''}
                                
                                ${val.suggestions && val.suggestions.length > 0 ? `
                                    <br><strong style="color: #000;">💡 Suggestions:</strong><br>
                                    <ul style="margin: 5px 0; padding-left: 20px; color: #000;">
                                        ${val.suggestions.map(suggestion => `<li style="color: #000;">${suggestion}</li>`).join('')}
                                    </ul>
                                ` : ''}
                            </div>
                        `;
                    }
                    
                    // Add validation indicator badge
                    let validationBadge = '';
                    if (result.validation) {
                        validationBadge = '<div style="margin-bottom: 15px; padding: 10px; background-color: #e3f2fd; border-left: 4px solid #2196f3; border-radius: 4px;"><strong style="color: #1976d2;">✅ Answer Validated by AI Agent</strong> - This answer has been verified for accuracy and document grounding.</div>';
                    }
                    
                    // Build a concise paragraph summary of validation results
                    let summaryHtml = '';
                    if (result.validation) {
                        const val = result.validation;
                        summaryHtml = `
                            <div style="margin: 10px 0 15px 0; padding: 12px; background:#eef7ff; border-radius:6px; color:#000;">
                                <strong style="color:#000;">Summary:</strong>
                                <p style="margin:6px 0 0 0; color:#000;">
                                    Status: ${val.validation_status.toUpperCase()}.
                                    Validation Score: ${(val.overall_score * 100).toFixed(1)}%.
                                    Based on document: ${val.is_based_on_document ? 'Yes' : 'No'}.
                                    Accurate: ${val.is_accurate ? 'Yes' : 'No'}.
                                    Complete: ${val.is_complete ? 'Yes' : 'No'}.
                                    Hallucinations: ${val.has_hallucinations ? 'Detected' : 'None'}.
                                    Issues: ${(val.issues && val.issues.length) ? val.issues.length : 0}.
                                    Suggestions: ${(val.suggestions && val.suggestions.length) ? val.suggestions.length : 0}.
                                </p>
                            </div>
                        `;
                    }
                    
                    showResult('question-result', `
                        <div style="color: #000;">
                            ${validationBadge}
                            ${summaryHtml}
                            <strong style="color: #000;">💡 Answer:</strong><br>
                            <div style="color: #000;">${result.answer}</div><br><br>
                            ${sourcesHtml}
                            ${validationHtml}
                        </div>
                    `, 'success');
                } else {
                    showResult('question-result', `❌ ${result.answer || result.message}`, 'error');
                }
            } catch (error) {
                showResult('question-result', `❌ Question failed: ${error.message}`, 'error');
            } finally {
                askBtn.disabled = false;
                showLoading('question-loading', false);
            }
        }
        
        async function updateStatus() {
            try {
                const response = await fetch('/status');
                const result = await response.json();
                
                document.getElementById('server-status').textContent = result.status || 'Unknown';
                document.getElementById('loaded-docs').textContent = result.loaded_documents.length;
                document.getElementById('total-chunks').textContent = result.total_chunks;
                
                let statusHtml = '<strong>📊 Detailed Status:</strong><br>';
                statusHtml += `Status: ${result.status}<br>`;
                statusHtml += `Total Chunks: ${result.total_chunks}<br>`;
                
                if (result.loaded_documents.length > 0) {
                    statusHtml += '<strong>📚 Loaded Documents:</strong><br>';
                    result.loaded_documents.forEach(doc => {
                        const fileName = doc.split('/').pop().split('\\\\').pop();
                        statusHtml += `• ${fileName}<br>`;
                    });
                } else {
                    statusHtml += '📚 No documents loaded<br>';
                }
                
                statusHtml += `🔧 Supported Formats: ${result.supported_formats.join(', ')}`;
                
                showResult('status-result', statusHtml, 'info');
            } catch (error) {
                showResult('status-result', `❌ Status update failed: ${error.message}`, 'error');
            }
        }
        
        // Initialize status on page load
        window.onload = function() {
            updateStatus();
        }
        
        // Allow Enter key to submit question
        document.getElementById('question').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && e.ctrlKey) {
                askQuestion();
            }
        });
    </script>
</body>
</html>
        """
        return HTMLResponse(html_content)
    
    async def upload_file(self, request):
        """Handle file upload and document loading."""
        try:
            form = await request.form()
            file = form["file"]
            
            if not file.filename:
                return JSONResponse({
                    "status": "error",
                    "message": "No file provided"
                })
            
            # Save uploaded file
            file_path = self.upload_dir / file.filename
            content = await file.read()
            
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Load document into MCP server
            mcp_request = {
                "method": "load_document",
                "params": {"file_path": str(file_path)}
            }
            
            result = await handle_mcp_request(self.qa_server, mcp_request)
            
            return JSONResponse(result)
            
        except Exception as e:
            return JSONResponse({
                "status": "error",
                "message": f"Upload failed: {str(e)}"
            })
    
    async def ask_question(self, request):
        """Handle question asking."""
        try:
            data = await request.json()
            question = data.get("question")
            
            if not question:
                return JSONResponse({
                    "status": "error",
                    "message": "No question provided"
                })
            
            mcp_request = {
                "method": "ask_question",
                "params": {"question": question}
            }
            
            result = await handle_mcp_request(self.qa_server, mcp_request)
            
            return JSONResponse(result)
            
        except Exception as e:
            return JSONResponse({
                "status": "error",
                "message": f"Question processing failed: {str(e)}"
            })
    
    async def get_status(self, request):
        """Get server status."""
        try:
            mcp_request = {
                "method": "get_status",
                "params": {}
            }
            
            result = await handle_mcp_request(self.qa_server, mcp_request)
            
            return JSONResponse(result)
            
        except Exception as e:
            return JSONResponse({
                "status": "error",
                "message": f"Status check failed: {str(e)}"
            })
    
    async def favicon(self, request):
        """Handle favicon requests to prevent 404 errors."""
        return Response(status_code=204)  # No Content


def create_app():
    """Create the Starlette application."""
    web_server = WebServer()
    
    routes = [
        Route("/", web_server.homepage),
        Route("/favicon.ico", web_server.favicon, methods=["GET"]),
        Route("/upload", web_server.upload_file, methods=["POST"]),
        Route("/ask", web_server.ask_question, methods=["POST"]),
        Route("/status", web_server.get_status, methods=["GET"]),
    ]
    
    middleware = [
        Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    ]
    
    app = Starlette(routes=routes, middleware=middleware)
    
    return app


async def main():
    """Run the web server."""
    app = create_app()
    
    print("🚀 Starting Document Q&A Web Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🌐 Open your browser and navigate to the URL above")
    print("📄 You can upload PDF, TXT, or Markdown files")
    print("❓ Ask questions about your uploaded documents")
    print("⏹️  Press Ctrl+C to stop the server")
    
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())