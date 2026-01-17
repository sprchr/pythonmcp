#!/usr/bin/env python3
"""
Setup script for Document Q&A MCP Server
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="document-qa-mcp-server",
    version="1.0.0",
    author="MCP Developer",
    description="MCP server for document-based question answering using OpenAI API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["document_qa_server"],
    install_requires=[
        "openai>=1.0.0",
        "numpy>=1.24.0",
        "PyPDF2>=3.0.0",
        "python-dotenv>=1.0.0",
        "scikit-learn>=1.3.0",
        "mcp>=0.1.0"
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        "console_scripts": [
            "document-qa-server=document_qa_server:main",
        ],
    },
)