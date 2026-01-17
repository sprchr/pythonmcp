# Validation Agent Documentation

## Overview

The Validation Agent is an intelligent component added to the Document Q&A MCP Server that validates answers provided by the MCP server. It ensures answer quality, accuracy, and prevents hallucinations by performing comprehensive multi-faceted validation.

## Architecture

### Component Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    User Question                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Document Q&A MCP Server                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Document   │  │  Embedding   │  │    Query     │    │
│  │   Loader     │→ │    Store     │← │   Handler    │    │
│  └──────────────┘  └──────────────┘  └──────┬───────┘    │
│                                               │             │
│                                               ▼             │
│                                    ┌──────────────────┐    │
│                                    │  Generate Answer │    │
│                                    └────────┬─────────┘    │
└─────────────────────────────────────────────┼──────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Validation Agent                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Validation Checks:                                  │  │
│  │  • Document Grounding                                │  │
│  │  • Accuracy Verification                             │  │
│  │  • Completeness Assessment                           │  │
│  │  • Hallucination Detection                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Validation Result:                                  │  │
│  │  • Status (valid/partially_valid/invalid/uncertain)  │  │
│  │  • Overall Score (0.0 - 1.0)                        │  │
│  │  • Detailed Feedback                                 │  │
│  │  • Issues & Suggestions                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Validated Answer + Validation Report            │
└─────────────────────────────────────────────────────────────┘
```

## Files Modified/Created

### 1. `validation_agent.py` (NEW FILE)

**Purpose**: Core validation agent implementation

**Key Components**:

- **`ValidationStatus` Enum**: Defines validation status levels
  - `VALID`: Answer is fully valid (score ≥ 0.8)
  - `PARTIALLY_VALID`: Answer is partially valid (score 0.5-0.8)
  - `INVALID`: Answer is invalid (score < 0.5 or has hallucinations)
  - `UNCERTAIN`: Validation is uncertain (score 0.3-0.5)

- **`ValidationResult` Dataclass**: Stores validation results
  ```python
  @dataclass
  class ValidationResult:
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
  ```

- **`ValidationAgent` Class**: Main validation logic
  - `validate_answer()`: Performs comprehensive validation
  - `_build_validation_prompt()`: Constructs validation prompt for GPT-4
  - `_determine_status()`: Determines validation status from results
  - `format_validation_result()`: Formats result for API response

**Validation Process**:

1. **Input**: Question, Answer, Document Context, Sources
2. **Analysis**: GPT-4 analyzes the answer against validation criteria
3. **Output**: Structured validation result with scores and feedback

**Validation Criteria**:

1. **Document Grounding**: Verifies all claims can be traced to document context
2. **Accuracy**: Checks facts match the context (numbers, dates, names)
3. **Completeness**: Assesses if question is fully answered
4. **Hallucination Detection**: Identifies unsupported claims

### 2. `document_qa_server.py` (MODIFIED)

**Changes Made**:

1. **Import Statement** (Line ~31):
   ```python
   from validation_agent import ValidationAgent
   ```

2. **QueryHandler Class** (Lines ~287-296):
   - Added `validation_agent` parameter to `__init__()`
   - Optional parameter (can be None if validation disabled)

3. **answer_question() Method** (Lines ~361-380):
   - After generating answer, calls validation agent if available
   - Adds validation results to response dictionary
   - Handles validation errors gracefully (continues without validation if it fails)

4. **DocumentQAServer Class** (Lines ~384-397):
   - Added `enable_validation` parameter (default: True)
   - Initializes `ValidationAgent` if enabled
   - Passes validation agent to `QueryHandler`

**Integration Flow**:

```python
# In QueryHandler.answer_question()
answer = generate_answer_from_gpt4(...)

# Validate if agent available
if self.validation_agent:
    validation_result = await self.validation_agent.validate_answer(
        question=question,
        answer=answer,
        context=context,
        sources=sources
    )
    result["validation"] = format_validation_result(validation_result)

return result
```

### 3. `web_server.py` (MODIFIED)

**Changes Made**:

1. **JavaScript Function `askQuestion()`** (Lines ~338-354):
   - Added validation results display section
   - Shows validation status with color-coded indicators
   - Displays validation score, confidence, and checks
   - Shows detailed feedback, issues, and suggestions

**UI Enhancements**:

- **Validation Status Badge**: Color-coded status indicator
  - ✅ Green: Valid
  - ⚠️ Yellow: Partially Valid
  - ❌ Red: Invalid
  - ❓ Gray: Uncertain

- **Validation Metrics**: 
  - Overall Score (percentage)
  - Confidence Level
  - Individual Check Results

- **Detailed Feedback**:
  - Issues found (if any)
  - Suggestions for improvement

## Usage

### Enabling/Disabling Validation

Validation is enabled by default. To disable:

```python
server = DocumentQAServer(api_key, enable_validation=False)
```

### API Response Format

When validation is enabled, the response includes a `validation` field:

```json
{
  "status": "success",
  "question": "What are the main features?",
  "answer": "The main features include...",
  "sources": [...],
  "confidence": 0.85,
  "validation": {
    "validation_status": "valid",
    "overall_score": 0.92,
    "is_based_on_document": true,
    "is_accurate": true,
    "is_complete": true,
    "has_hallucinations": false,
    "confidence": 0.88,
    "feedback": "The answer is well-grounded in the document context...",
    "issues": [],
    "suggestions": []
  }
}
```

### Validation Status Meanings

- **`valid`**: Answer is high quality (score ≥ 0.8), grounded in document, accurate, and complete
- **`partially_valid`**: Answer is acceptable (score 0.5-0.8) but may have minor issues
- **`invalid`**: Answer has significant problems (score < 0.5) or contains hallucinations
- **`uncertain`**: Validation confidence is low (score 0.3-0.5)

## Validation Agent Details

### How It Works

1. **Context Analysis**: The agent receives:
   - Original question
   - Generated answer
   - Document context used
   - Source metadata (files, similarity scores)

2. **GPT-4 Validation**: Uses GPT-4 with structured JSON output to analyze:
   - Whether answer claims are in the document
   - Factual accuracy of claims
   - Completeness of answer
   - Presence of hallucinations

3. **Result Generation**: Produces structured validation result with:
   - Overall quality score
   - Individual check results
   - Detailed feedback
   - Specific issues and suggestions

### Validation Prompt Structure

The agent uses a carefully crafted prompt that instructs GPT-4 to:

1. Check document grounding strictly
2. Verify factual accuracy
3. Assess completeness
4. Detect any hallucinations

The prompt emphasizes being strict and thorough in validation.

### Error Handling

- If validation fails (API error, parsing error, etc.), the system:
  - Logs the error
  - Returns answer without validation
  - Does not block the main Q&A flow
  - Ensures graceful degradation

## Benefits

1. **Quality Assurance**: Ensures answers are based on documents
2. **Hallucination Prevention**: Detects unsupported claims
3. **Transparency**: Provides detailed feedback on answer quality
4. **User Trust**: Users can see validation status and scores
5. **Continuous Improvement**: Issues and suggestions help improve answers

## Performance Considerations

- **Additional API Call**: Validation adds one GPT-4 API call per question
- **Latency**: Adds ~2-5 seconds to response time
- **Cost**: Additional API usage for validation
- **Optional**: Can be disabled if not needed

## Configuration

### Adjusting Validation Strictness

Modify the validation prompt in `validation_agent.py` to adjust strictness:

```python
# In _build_validation_prompt()
# Add more strict instructions for higher quality requirements
# Or relax requirements for faster validation
```

### Custom Validation Criteria

Extend `ValidationAgent` class to add custom validation checks:

```python
class CustomValidationAgent(ValidationAgent):
    async def validate_answer(self, ...):
        result = await super().validate_answer(...)
        # Add custom checks
        result.custom_check = self._custom_validation(...)
        return result
```

## Testing

Test the validation agent:

```bash
python validation_agent.py
```

This runs a simple test validation with example data.

## Future Enhancements

Potential improvements:

1. **Caching**: Cache validation results for similar questions
2. **Batch Validation**: Validate multiple answers at once
3. **Custom Rules**: Allow user-defined validation rules
4. **Metrics Dashboard**: Track validation statistics over time
5. **Auto-correction**: Suggest corrections for invalid answers

## Troubleshooting

### Validation Not Appearing

- Check that `enable_validation=True` in `DocumentQAServer` initialization
- Verify OpenAI API key is valid
- Check logs for validation errors

### Validation Always Failing

- Review validation prompt in `validation_agent.py`
- Check if document context is being passed correctly
- Verify GPT-4 API access and quota

### High Latency

- Consider disabling validation for faster responses
- Use async/await properly (already implemented)
- Consider caching validation results

## Summary

The Validation Agent adds a crucial quality assurance layer to the Document Q&A system, ensuring answers are accurate, grounded, and complete. It provides transparency and builds user trust through detailed validation reports.
