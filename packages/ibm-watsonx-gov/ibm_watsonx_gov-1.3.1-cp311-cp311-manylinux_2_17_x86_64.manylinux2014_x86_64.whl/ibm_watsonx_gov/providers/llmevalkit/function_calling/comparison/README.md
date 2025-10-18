# Function Call Comparison Framework

A framework for evaluating and comparing function call predictions against ground truth data. This module provides multiple comparison strategies to handle different evaluation scenarios, from exact matching to semantic analysis using LLM judges.

## Overview

The Function Call Comparison Framework enables precise evaluation of tool calls in LLM applications. It supports various comparison strategies and provides detailed analysis of both function names and parameters.

## Features

- **Multiple Comparison Strategies**: Exact match, fuzzy string matching, LLM-based semantic analysis, and code-based programmatic evaluation
- **Parameter Analysis**: Detailed comparison of individual parameters with type normalization and default value handling
- **Tool Specification Support**: Integration with OpenAI-format tool specifications for context-aware comparisons
- **Async Support**: Full asynchronous operation for high-performance evaluations
- **Custom Instructions**: Specialized evaluation logic for domain-specific requirements
- **Batch Processing**: Efficient comparison of multiple tool calls
- **Comprehensive Reporting**: Detailed results with explanations and confidence scores

## Comparison Strategies

### 1. Exact Match
Performs precise structural comparison with optional type normalization.

```python
from llmevalkit.function_calling.comparison import ComparisonStrategy, ComparisonConfig, ComparisonPipeline

config = ComparisonConfig(strategy=ComparisonStrategy.EXACT_MATCH)
pipeline = ComparisonPipeline(config=config)
```

### 2. Fuzzy String Matching
Uses string similarity algorithms for near-match detection.

```python
config = ComparisonConfig(
    strategy=ComparisonStrategy.FUZZY_STRING,
    string_similarity_threshold=0.8
)
```

### 3. LLM Judge
Employs language models for semantic understanding and context-aware evaluation.

```python
from llmevalkit.llm import get_llm

llm_client = get_llm("watsonx.output_val")(model_name="meta-llama/llama-3-3-70b-instruct")
config = ComparisonConfig(strategy=ComparisonStrategy.LLM_JUDGE)
pipeline = ComparisonPipeline(config=config, llm_client=llm_client)
```

### 4. Code Agent
Uses programmatic analysis through code generation and execution for complex evaluations.

```python
config = ComparisonConfig(strategy=ComparisonStrategy.CODE_AGENT)
pipeline = ComparisonPipeline(config=config, llm_client=llm_client)
```

### 5. Hybrid Strategy
Combines multiple strategies and selects the best result based on confidence scores.

```python
config = ComparisonConfig(strategy=ComparisonStrategy.HYBRID)
pipeline = ComparisonPipeline(config=config, llm_client=llm_client)
```

## Basic Usage

### Simple Comparison

```python
import json
from llmevalkit.function_calling.comparison import ComparisonStrategy, ComparisonConfig, ComparisonPipeline

# Configure comparison strategy
config = ComparisonConfig(strategy=ComparisonStrategy.EXACT_MATCH)
pipeline = ComparisonPipeline(config=config)

# Define tool calls
predicted_call = {
    "function": {
        "name": "send_email",
        "arguments": {
            "to": "user@example.com",
            "subject": "Project Update",
            "body": "The project is complete."
        }
    }
}

ground_truth_call = {
    "function": {
        "name": "send_email", 
        "arguments": {
            "to": "user@example.com",
            "subject": "Project Update",
            "body": "The project is complete."
        }
    }
}

# Perform comparison
result = pipeline.compare(predicted_call, ground_truth_call)

print(f"Overall Score: {result.overall_score}")
print(f"Function Match: {result.function_name_match}")
print(f"Parameters Evaluated: {len(result.parameter_results)}")
```

### Advanced LLM-Based Comparison

```python
from llmevalkit.llm import get_llm
from llmevalkit.function_calling.comparison import ComparisonStrategy, ComparisonConfig, ComparisonPipeline

# Initialize LLM client
llm_client = get_llm("watsonx.output_val")(model_name="meta-llama/llama-3-3-70b-instruct")

# Configure LLM Judge strategy
config = ComparisonConfig(
    strategy=ComparisonStrategy.LLM_JUDGE,
    string_similarity_threshold=0.8,
    numeric_tolerance=0.01
)

pipeline = ComparisonPipeline(config=config, llm_client=llm_client)

# Tool specification for context
tool_spec = {
    "type": "function",
    "function": {
        "name": "book_flight",
        "description": "Book a flight for passengers",
        "parameters": {
            "type": "object", 
            "properties": {
                "departure_city": {"type": "string"},
                "arrival_city": {"type": "string"},
                "departure_date": {"type": "string", "format": "date"},
                "passenger_count": {"type": "integer"}
            },
            "required": ["departure_city", "arrival_city", "departure_date"]
        }
    }
}

# Semantic comparison with context
result = await pipeline.compare_async(
    predicted_call=predicted_call,
    ground_truth_call=ground_truth_call,
    tool_specs=[tool_spec]
)
```

## Custom Instructions

For specialized evaluation scenarios, provide custom instructions to guide the comparison logic:

```python
custom_instructions = """
When comparing dates, treat relative terms like "tomorrow" and "yesterday" 
as equivalent to their absolute date representations. Consider timezone 
context when evaluating time-sensitive parameters.
"""

config = ComparisonConfig(strategy=ComparisonStrategy.LLM_JUDGE)
pipeline = ComparisonPipeline(config=config, llm_client=llm_client)

result = await pipeline.compare_async(
    predicted_call=predicted_call,
    ground_truth_call=ground_truth_call,
    custom_instructions=custom_instructions
)
```

## Batch Processing

Process multiple comparisons efficiently:

```python
comparisons = [
    {
        "predicted_call": predicted_call_1,
        "ground_truth_call": ground_truth_call_1
    },
    {
        "predicted_call": predicted_call_2, 
        "ground_truth_call": ground_truth_call_2
    }
]

results = await pipeline.batch_compare_async(comparisons)
summary = pipeline.get_comparison_summary(results)

print(f"Average Score: {summary['average_score']}")
print(f"Success Rate: {summary['success_rate']}")
```

## Configuration Options

### ComparisonConfig Parameters

- `strategy`: Comparison strategy to use
- `string_similarity_threshold`: Threshold for fuzzy matching (0.0-1.0)
- `numeric_tolerance`: Tolerance for numeric comparisons
- `normalize_types`: Enable type normalization (string "123" ↔ int 123)
- `weight_function_name`: Weight given to function name matching
- `weight_parameters`: Weight given to parameter matching
- `parameter_weights`: Custom weights for specific parameters

### Strategy-Specific Configuration

```python
config = ComparisonConfig(
    strategy=ComparisonStrategy.FUZZY_STRING,
    string_similarity_threshold=0.8,
    numeric_tolerance=0.01,
    normalize_types=True,
    strategy_config={
        "enable_semantic_matching": True,
        "case_sensitive": False
    }
)
```

## Result Analysis

### ToolCallComparisonResult

The main result object containing:

- `overall_score`: Combined score (0.0-1.0)
- `function_name_match`: Boolean function name match result
- `function_name_score`: Function name similarity score
- `parameter_results`: List of individual parameter comparisons
- `overall_explanation`: Human-readable explanation
- `strategy_used`: Strategy or strategies employed
- `metadata`: Additional evaluation metadata

### ParameterComparisonResult

Individual parameter comparison details:

- `parameter_name`: Name of the compared parameter
- `predicted_value`: Value from predicted call
- `ground_truth_value`: Value from ground truth
- `score`: Parameter similarity score (0.0-1.0) 
- `is_match`: Boolean match result
- `explanation`: Detailed comparison explanation
- `confidence`: Confidence in the evaluation

## Error Handling

The framework provides robust error handling with fallback strategies:

```python
try:
    result = await pipeline.compare_async(predicted_call, ground_truth_call)
except Exception as e:
    print(f"Comparison failed: {e}")
    # Framework automatically falls back to simpler strategies when possible
```

## Installation Requirements

### Core Dependencies
```bash
pip install llmevalkit
```

### Optional Dependencies

For Code Agent functionality:
```bash
pip install langgraph langchain-core langchain-experimental
```

For specific LLM providers:
```bash
pip install ibm-watsonx-ai  # For Watson LLM
pip install openai         # For OpenAI models
```

## Examples

See the `examples/function_calling/comparison/` directory for comprehensive examples:

- `basic_examples.py`: Core functionality demonstrations
- `llm_judge_examples.py`: LLM-based semantic comparisons  
- `custom_instructions_examples.py`: Specialized evaluation scenarios
- `custom_schema_examples.py`: Custom response format examples
- `code_agent_demo.py`: Programmatic analysis examples

## Best Practices

1. **Choose Appropriate Strategy**: Use exact match for structured data, LLM judge for semantic understanding
2. **Provide Tool Specifications**: Include tool specs for better context and default value handling
3. **Use Custom Instructions**: Provide domain-specific guidance for specialized scenarios
4. **Batch Processing**: Use async batch operations for large-scale evaluations
5. **Error Handling**: Implement proper error handling and fallback strategies
6. **Performance Monitoring**: Monitor LLM API usage and response times in production

## Contributing

This module is part of the LLMEvalKit framework. For contributions and issues, please refer to the main project repository.
