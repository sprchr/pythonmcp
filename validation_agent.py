#!/usr/bin/env python3
"""
Validation Agent for Document Q&A MCP Server

This agent validates answers provided by the MCP server to ensure:
1. Answers are based on document content (no hallucinations)
2. Answers are accurate and relevant to the question
3. Answers fully address the question
4. Answers don't contain unsupported claims

The agent uses GPT-4 to perform multi-faceted validation and provides
detailed feedback on answer quality.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

import openai

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status levels."""
    VALID = "valid"
    PARTIALLY_VALID = "partially_valid"
    INVALID = "invalid"
    UNCERTAIN = "uncertain"


@dataclass
class ValidationResult:
    """Result of answer validation."""
    status: ValidationStatus
    overall_score: float  # 0.0 to 1.0
    is_based_on_document: bool
    is_accurate: bool
    is_complete: bool
    has_hallucinations: bool
    feedback: str
    confidence: float
    issues: List[str]
    suggestions: List[str]


class ValidationAgent:
    """
    Agent that validates answers from the MCP server.
    
    The agent performs comprehensive validation including:
    - Document grounding check (is answer based on provided context?)
    - Accuracy verification (is the answer factually correct?)
    - Completeness check (does it fully answer the question?)
    - Hallucination detection (are there unsupported claims?)
    """
    
    def __init__(self, openai_client: openai.OpenAI):
        """
        Initialize the validation agent.
        
        Args:
            openai_client: Configured OpenAI client
        """
        self.client = openai_client
        logger.info("Validation Agent initialized")
    
    async def validate_answer(
        self,
        question: str,
        answer: str,
        context: str,
        sources: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        Validate an answer provided by the MCP server.
        
        Args:
            question: Original question asked by user
            answer: Answer provided by MCP server
            context: Document context used to generate the answer
            sources: List of source chunks with metadata
            
        Returns:
            ValidationResult with detailed validation information
        """
        logger.info(f"Validating answer for question: {question[:50]}...")
        
        try:
            # Build validation prompt
            validation_prompt = self._build_validation_prompt(
                question, answer, context, sources
            )
            
            # Get validation analysis from GPT-4
            validation_response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert validation agent that evaluates answers from a document Q&A system. 
Your task is to validate answers by checking:
1. Document Grounding: Is the answer based on the provided document context?
2. Accuracy: Are the facts in the answer correct according to the context?
3. Completeness: Does the answer fully address the question?
4. Hallucination Detection: Are there any claims not supported by the context?

You must be strict and thorough. Return ONLY a valid JSON object with the following structure (no additional text before or after):
{
    "is_based_on_document": true/false,
    "is_accurate": true/false,
    "is_complete": true/false,
    "has_hallucinations": true/false,
    "overall_score": 0.0-1.0,
    "confidence": 0.0-1.0,
    "issues": ["list of specific issues found"],
    "suggestions": ["list of suggestions for improvement"],
    "feedback": "detailed explanation of validation results"
}

IMPORTANT: Return ONLY the JSON object, nothing else."""
                    },
                    {
                        "role": "user",
                        "content": validation_prompt
                    }
                ],
                temperature=0.1
            )
            
            # Parse validation response - extract JSON from response text
            response_text = validation_response.choices[0].message.content.strip()
            
            # Try to extract JSON if there's any text before/after
            try:
                # First, try direct JSON parsing
                validation_json = json.loads(response_text)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text
                # Look for JSON object boundaries
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx + 1]
                    validation_json = json.loads(json_str)
                else:
                    raise ValueError("Could not extract JSON from validation response")
            
            # Determine validation status
            status = self._determine_status(validation_json)
            
            # Create validation result
            result = ValidationResult(
                status=status,
                overall_score=float(validation_json.get("overall_score", 0.0)),
                is_based_on_document=bool(validation_json.get("is_based_on_document", False)),
                is_accurate=bool(validation_json.get("is_accurate", False)),
                is_complete=bool(validation_json.get("is_complete", False)),
                has_hallucinations=bool(validation_json.get("has_hallucinations", False)),
                feedback=str(validation_json.get("feedback", "")),
                confidence=float(validation_json.get("confidence", 0.0)),
                issues=list(validation_json.get("issues", [])),
                suggestions=list(validation_json.get("suggestions", []))
            )
            
            logger.info(f"Validation complete. Status: {status.value}, Score: {result.overall_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error during validation: {str(e)}")
            # Return a default invalid result on error
            return ValidationResult(
                status=ValidationStatus.UNCERTAIN,
                overall_score=0.0,
                is_based_on_document=False,
                is_accurate=False,
                is_complete=False,
                has_hallucinations=True,
                feedback=f"Validation error: {str(e)}",
                confidence=0.0,
                issues=[f"Validation process failed: {str(e)}"],
                suggestions=["Please retry the validation"]
            )
    
    def _build_validation_prompt(
        self,
        question: str,
        answer: str,
        context: str,
        sources: List[Dict[str, Any]]
    ) -> str:
        """Build the validation prompt for GPT-4."""
        
        sources_info = "\n".join([
            f"- {source.get('file', 'unknown')} (similarity: {source.get('similarity_score', 0):.3f})"
            for source in sources
        ])
        
        prompt = f"""Please validate the following answer from a document Q&A system.

QUESTION:
{question}

ANSWER TO VALIDATE:
{answer}

DOCUMENT CONTEXT USED:
{context}

SOURCE INFORMATION:
{sources_info}

VALIDATION CRITERIA:
1. Document Grounding: Check if all claims in the answer can be traced back to the provided document context. 
   - If the answer says "The document does not contain this information", this is valid if true.
   - If the answer makes specific claims, verify they appear in the context.

2. Accuracy: Verify that facts stated in the answer are correct according to the context.
   - Check for contradictions between answer and context.
   - Verify numbers, dates, names, and specific details match the context.

3. Completeness: Assess if the answer fully addresses the question.
   - Does it answer all parts of the question?
   - Are there important aspects left unaddressed?

4. Hallucination Detection: Identify any information in the answer that is NOT in the context.
   - Look for made-up facts, unsupported claims, or information from general knowledge not in the document.
   - Be strict: if it's not in the context, it's a hallucination.

Provide a thorough analysis and return the results as JSON."""
        
        return prompt
    
    def _determine_status(self, validation_json: Dict[str, Any]) -> ValidationStatus:
        """
        Determine validation status based on validation results.
        
        Args:
            validation_json: JSON response from validation
            
        Returns:
            ValidationStatus enum value
        """
        overall_score = float(validation_json.get("overall_score", 0.0))
        is_based_on_document = bool(validation_json.get("is_based_on_document", False))
        has_hallucinations = bool(validation_json.get("has_hallucinations", False))
        
        # If there are hallucinations, it's invalid
        if has_hallucinations:
            return ValidationStatus.INVALID
        
        # If not based on document, it's invalid
        if not is_based_on_document:
            return ValidationStatus.INVALID
        
        # Determine status based on score
        if overall_score >= 0.8:
            return ValidationStatus.VALID
        elif overall_score >= 0.5:
            return ValidationStatus.PARTIALLY_VALID
        elif overall_score >= 0.3:
            return ValidationStatus.UNCERTAIN
        else:
            return ValidationStatus.INVALID
    
    def format_validation_result(self, result: ValidationResult) -> Dict[str, Any]:
        """
        Format validation result for API response.
        
        Args:
            result: ValidationResult object
            
        Returns:
            Dictionary formatted for JSON response
        """
        return {
            "validation_status": result.status.value,
            "overall_score": result.overall_score,
            "is_based_on_document": result.is_based_on_document,
            "is_accurate": result.is_accurate,
            "is_complete": result.is_complete,
            "has_hallucinations": result.has_hallucinations,
            "confidence": result.confidence,
            "feedback": result.feedback,
            "issues": result.issues,
            "suggestions": result.suggestions
        }


async def main():
    """Test the validation agent."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found")
        return
    
    agent = ValidationAgent(openai.OpenAI(api_key=api_key))
    
    # Example validation
    question = "What are the main features?"
    answer = "The main features include document loading, semantic search, and question answering."
    context = "The system has three main features: document loading from multiple formats, semantic search using embeddings, and context-aware question answering."
    sources = [{"file": "test.pdf", "similarity_score": 0.85}]
    
    result = await agent.validate_answer(question, answer, context, sources)
    
    print("Validation Result:")
    print(f"Status: {result.status.value}")
    print(f"Score: {result.overall_score:.2f}")
    print(f"Feedback: {result.feedback}")
    print(f"Issues: {result.issues}")
    print(f"Suggestions: {result.suggestions}")


if __name__ == "__main__":
    asyncio.run(main())
