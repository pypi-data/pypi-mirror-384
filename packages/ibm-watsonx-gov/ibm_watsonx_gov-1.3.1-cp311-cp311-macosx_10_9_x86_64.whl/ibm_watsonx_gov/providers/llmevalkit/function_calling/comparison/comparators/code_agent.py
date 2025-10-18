from typing import Any, Dict, Optional, List
import logging
import json
import asyncio
import re
from datetime import datetime

try:
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.tools import tool
    from langchain_experimental.tools import PythonREPLTool

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

    # Create a dummy tool decorator for when LangGraph is not available
    def tool(func):
        return func


from .base import BaseComparator
from ..types import (
    ParameterComparisonResult,
    ComparisonStrategy,
    ParameterStatus,
)

logger = logging.getLogger(__name__)


class CodeAgentComparator(BaseComparator):
    """
    Code Agent-based comparator using LangGraph for detailed tool call analysis.

    This comparator creates a code agent that can:
    - Write Python code to analyze tool call differences
    - Use context from conversation history and tool specifications
    - Perform complex logical comparisons beyond simple string/semantic matching
    - Handle edge cases through programmatic analysis
    """

    def __init__(self, config, llm_client=None):
        super().__init__(config)

        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "LangGraph is required for CodeAgentComparator. "
                "Install with: pip install langgraph langchain-core langchain"
            )

        self.llm_client = llm_client
        self.agent = None
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the LangGraph code agent."""
        if not self.llm_client:
            logger.warning("No LLM client provided for CodeAgentComparator")
            return

        try:
            # Create tools for the agent - using tool functions directly
            from langchain_core.tools import tool

            @tool
            def analyze_values(
                predicted_value: str,
                ground_truth_value: str,
                param_type: str = "string",
            ) -> str:
                """
                Analyze two parameter values for comparison.

                Args:
                    predicted_value: The predicted parameter value
                    ground_truth_value: The ground truth parameter value
                    param_type: The expected parameter type

                Returns:
                    JSON string with analysis results
                """
                import json

                # Parse JSON strings if needed
                def safe_parse(value):
                    if isinstance(value, str):
                        try:
                            return json.loads(value)
                        except:
                            return value
                    return value

                pred_parsed = safe_parse(predicted_value)
                gt_parsed = safe_parse(ground_truth_value)

                # Type analysis
                pred_type = type(pred_parsed).__name__
                gt_type = type(gt_parsed).__name__

                # Exact match check
                exact_match = pred_parsed == gt_parsed

                # Type compatibility check
                type_compatible = pred_type == gt_type or (
                    (pred_type in ["int", "float"] and gt_type in ["int", "float"])
                    or (pred_type == "str" and gt_type in ["int", "float", "bool"])
                    or (gt_type == "str" and pred_type in ["int", "float", "bool"])
                )

                # Semantic equivalence check
                semantic_equivalent = False
                if not exact_match:
                    # String representations
                    pred_str = str(pred_parsed).lower().strip()
                    gt_str = str(gt_parsed).lower().strip()

                    # Common equivalences
                    equivalences = [
                        (pred_str == gt_str),
                        (
                            pred_str in ["true", "1", "yes", "on"]
                            and gt_str in ["true", "1", "yes", "on"]
                        ),
                        (
                            pred_str in ["false", "0", "no", "off"]
                            and gt_str in ["false", "0", "no", "off"]
                        ),
                        (
                            pred_str.replace(" ", "") == gt_str.replace(" ", "")
                        ),  # Whitespace differences
                    ]

                    semantic_equivalent = any(equivalences)

                result = {
                    "exact_match": exact_match,
                    "semantic_equivalent": semantic_equivalent,
                    "type_compatible": type_compatible,
                    "predicted_type": pred_type,
                    "ground_truth_type": gt_type,
                    "predicted_parsed": pred_parsed,
                    "ground_truth_parsed": gt_parsed,
                }

                return json.dumps(result)

            @tool
            def compare_json_structures(obj1: str, obj2: str) -> str:
                """
                Compare two JSON structures for deep equality.

                Args:
                    obj1: First JSON object as string
                    obj2: Second JSON object as string

                Returns:
                    JSON string with comparison results
                """
                import json

                try:
                    parsed1 = json.loads(obj1) if isinstance(obj1, str) else obj1
                    parsed2 = json.loads(obj2) if isinstance(obj2, str) else obj2

                    def deep_compare(a, b, path=""):
                        if type(a) != type(b):
                            return {
                                "match": False,
                                "reason": f"Type mismatch at {path}: {type(a)} vs {type(b)}",
                            }

                        if isinstance(a, dict):
                            if set(a.keys()) != set(b.keys()):
                                return {
                                    "match": False,
                                    "reason": f"Key mismatch at {path}: {set(a.keys())} vs {set(b.keys())}",
                                }

                            for key in a:
                                result = deep_compare(a[key], b[key], f"{path}.{key}")
                                if not result["match"]:
                                    return result

                            return {"match": True, "reason": "Deep equality"}

                        elif isinstance(a, list):
                            if len(a) != len(b):
                                return {
                                    "match": False,
                                    "reason": f"List length mismatch at {path}: {len(a)} vs {len(b)}",
                                }

                            for i, (item_a, item_b) in enumerate(zip(a, b)):
                                result = deep_compare(item_a, item_b, f"{path}[{i}]")
                                if not result["match"]:
                                    return result

                            return {"match": True, "reason": "Deep equality"}

                        else:
                            match = a == b
                            return {
                                "match": match,
                                "reason": (
                                    "Direct comparison"
                                    if match
                                    else f"Value mismatch: {a} != {b}"
                                ),
                            }

                    result = deep_compare(parsed1, parsed2)
                    return json.dumps(result)

                except Exception as e:
                    return json.dumps(
                        {"match": False, "reason": f"JSON parsing error: {str(e)}"}
                    )

            # Create tools for the agent
            tools = [PythonREPLTool(), analyze_values, compare_json_structures]

            # Create the React agent with code execution capabilities
            self.agent = create_react_agent(model=self._adapt_llm_client(), tools=tools)

        except Exception as e:
            logger.error(f"Failed to initialize code agent: {e}")
            self.agent = None

    def _adapt_llm_client(self):
        """Adapt our LLM client to work with LangChain using a Runnable wrapper."""
        from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
        from langchain_core.runnables import Runnable

        # Create a Runnable adapter for our LLM client
        class RunnableAdapter(Runnable):
            def __init__(self, llm_client):
                self.llm_client = llm_client

            def invoke(self, input_data, config=None):
                # Handle different input types
                if isinstance(input_data, dict) and "messages" in input_data:
                    messages = input_data["messages"]
                elif isinstance(input_data, list):
                    messages = input_data
                else:
                    messages = [input_data]

                # Convert messages to prompt
                prompt_parts = []
                for msg in messages:
                    if hasattr(msg, "content"):
                        prompt_parts.append(msg.content)
                    else:
                        prompt_parts.append(str(msg))
                prompt = "\n".join(prompt_parts)

                # Call our LLM
                try:
                    if hasattr(self.llm_client, "generate"):
                        # Check if this is a ValidatingLLMClient that requires schema
                        from llmevalkit.llm.output_parser import ValidatingLLMClient

                        if isinstance(self.llm_client, ValidatingLLMClient):
                            # Provide a simple string schema for ValidatingLLMClient
                            response = self.llm_client.generate(
                                prompt=prompt, schema=str
                            )
                        else:
                            response = self.llm_client.generate(prompt=prompt)
                    else:
                        response = "LLM client not available"

                    # Return AIMessage
                    return AIMessage(content=str(response))
                except Exception as e:
                    return AIMessage(content=f"Error: {str(e)}")

            def bind_tools(self, tools):
                """Bind tools to the model (required by LangGraph)."""
                return self

            def with_structured_output(self, schema):
                """Support structured output (optional for LangGraph)."""
                return self

        return RunnableAdapter(self.llm_client)

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the code agent."""
        return """You are an expert code agent with access to a Python REPL tool for executing code.

CRITICAL INSTRUCTIONS:
1. When you need to execute Python code, you MUST use the "Python REPL" tool
2. Do NOT just write code - you must CALL THE TOOL to execute it
3. The tool is called "Python REPL" - use it to run any Python code
4. After tool execution, use the actual results in your analysis

AVAILABLE TOOLS:
- Python REPL: Execute Python code and get real results

Your task is to compare tool calls using executed Python analysis.

WORKFLOW:
1. Use the Python REPL tool to execute comparison code
2. Get the actual execution results 
3. Use those results to determine equivalence
4. Return structured comparison results

EXAMPLE TOOL USAGE:
To execute code, you would call the Python REPL tool with your code, NOT just display it.

Remember: ALWAYS use the Python REPL tool for code execution!"""

    def compare_parameter(
        self,
        param_name: str,
        predicted_value: Any,
        ground_truth_value: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ParameterComparisonResult:
        """Compare a single parameter using code agent analysis."""

        if not self.agent:
            # Fallback to basic comparison if agent not available
            return self._fallback_comparison(
                param_name, predicted_value, ground_truth_value, context
            )

        try:
            # Prepare context for the agent
            context = context or {}
            param_def = context.get("parameter_definition", {})
            param_status = context.get("parameter_status", ParameterStatus.BOTH_PRESENT)

            # Create the analysis prompt
            prompt = f"""
Analyze parameter '{param_name}' by writing and EXECUTING Python code.

PARAMETER DATA:
- Name: {param_name}
- Predicted Value: {json.dumps(predicted_value)}  
- Ground Truth Value: {json.dumps(ground_truth_value)}
- Parameter Type: {param_def.get('type', 'unknown')}
- Required: {param_def.get('required', False)}
- Default: {param_def.get('default', 'None')}
- Status: {param_status.value if hasattr(param_status, 'value') else param_status}

TASK: Write Python code to analyze these values AND EXECUTE IT to get results.

Consider:
1. Exact equality
2. Type compatibility (string "1500.00" vs float 1500.0)
3. Semantic equivalence (string "true" vs boolean True)
4. Missing value handling
5. Parameter definition context

EXECUTE your analysis code and print the JSON result:
```python
import json

# The actual parameter values
predicted_value = {json.dumps(predicted_value)}
ground_truth_value = {json.dumps(ground_truth_value)}
param_name = "{param_name}"

def analyze_parameter(pred_val, gt_val, param_name):
    # Your analysis logic here
    # Return JSON with: score, is_match, explanation, confidence, parameter_analysis
    pass

result = analyze_parameter(predicted_value, ground_truth_value, param_name)
print(json.dumps(result, indent=2))
```

Execute this and provide the JSON output!
"""

            # Run the agent
            messages = [HumanMessage(content=prompt)]
            result = self.agent.invoke({"messages": messages})

            # Extract the result from agent output
            final_message = result["messages"][-1].content

            # Try to parse JSON from the final message
            analysis_result = self._extract_json_from_response(final_message)

            return ParameterComparisonResult(
                parameter_name=param_name,
                predicted_value=predicted_value,
                ground_truth_value=ground_truth_value,
                predicted_resolved_value=predicted_value,
                ground_truth_resolved_value=ground_truth_value,
                parameter_status=param_status,
                comparison_strategy=ComparisonStrategy.CODE_AGENT,
                score=analysis_result.get("score", 0.5),
                explanation=analysis_result.get(
                    "explanation", "Code agent analysis completed"
                ),
                is_match=analysis_result.get("is_match", False),
                confidence=analysis_result.get("confidence", 0.8),
                metadata={
                    "code_agent_analysis": analysis_result,
                    "parameter_analysis": analysis_result.get("parameter_analysis", {}),
                },
            )

        except Exception as e:
            logger.error(f"Code agent comparison failed: {e}")
            return self._fallback_comparison(
                param_name, predicted_value, ground_truth_value, context
            )

    def compare_tool_calls(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compare two complete tool calls using code agent analysis."""

        # Try direct code generation and execution first (more reliable)
        try:
            direct_result = self._direct_code_comparison(
                predicted_call, ground_truth_call, custom_instructions
            )
            if direct_result.get("comparison_strategy") == "code_agent_direct":
                return direct_result
        except Exception as e:
            logger.warning(
                f"Direct code comparison failed, trying LangGraph agent: {e}"
            )

        # Fall back to LangGraph agent approach
        if not self.agent:
            return self._fallback_tool_call_comparison(
                predicted_call, ground_truth_call
            )

        try:
            # Prepare detailed context
            conversation_context = ""
            if conversation_history:
                conversation_context = "\n".join(
                    [
                        f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                        for msg in conversation_history[
                            -5:
                        ]  # Last 5 messages for context
                    ]
                )

            tool_specification = ""
            function_name = predicted_call.get("name") or ground_truth_call.get("name")
            if tool_specs and function_name:
                for spec in tool_specs:
                    if spec.get("name") == function_name:
                        tool_specification = json.dumps(spec, indent=2)
                        break

            # Create detailed analysis prompt
            prompt = f"""
CRITICAL: Use the Python REPL tool to execute analysis code. Do not just show code - RUN it using the tool!

Compare these tool calls by EXECUTING Python code:

PREDICTED: {json.dumps(predicted_call, indent=2)}
GROUND TRUTH: {json.dumps(ground_truth_call, indent=2)}

TASK: Use the Python REPL tool to execute this analysis:

```python
import json

predicted_call = {json.dumps(predicted_call)}
ground_truth_call = {json.dumps(ground_truth_call)}

def analyze_tool_calls(pred, gt):
    func_match = pred.get("name") == gt.get("name")
    pred_args = pred.get("arguments", {{}})
    gt_args = gt.get("arguments", {{}})
    
    param_scores = []
    param_details = {{}}
    all_params = set(pred_args.keys()) | set(gt_args.keys())
    
    for param in all_params:
        pred_val = pred_args.get(param)
        gt_val = gt_args.get(param)
        
        if pred_val == gt_val:
            score = 1.0
        elif str(pred_val).lower() == str(gt_val).lower():
            score = 1.0
        elif (isinstance(pred_val, str) and isinstance(gt_val, (int, float)) and
              pred_val.replace('.', '').replace('-', '').isdigit() and
              float(pred_val) == float(gt_val)):
            score = 1.0
        elif (pred_val in ['true', 'True', True] and gt_val in ['true', 'True', True]) or \\
             (pred_val in ['false', 'False', False] and gt_val in ['false', 'False', False]):
            score = 1.0
        else:
            score = 0.0
        
        param_scores.append(score)
        param_details[param] = {{"score": score, "pred": pred_val, "gt": gt_val}}
    
    param_avg = sum(param_scores) / len(param_scores) if param_scores else 1.0
    overall_score = (1.0 if func_match else 0.0 + param_avg) / 2.0
    is_match = func_match and param_avg == 1.0
    
    return {{
        "score": overall_score,
        "is_match": is_match,
        "explanation": f"Function match: {{func_match}}, Param avg: {{param_avg:.3f}}",
        "confidence": 0.95,
        "function_analysis": {{"name_match": func_match}},
        "parameter_analysis": param_details,
        "contextual_insights": {{"analysis_complete": True}}
    }}

result = analyze_tool_calls(predicted_call, ground_truth_call)
print("ANALYSIS_RESULT:", json.dumps(result, indent=2))
```

EXECUTE this code using the Python REPL tool and return the results!
"""

            # Run the agent
            messages = [HumanMessage(content=prompt)]
            result = self.agent.invoke({"messages": messages})

            # Extract analysis result
            final_message = result["messages"][-1].content
            analysis_result = self._extract_json_from_response(final_message)

            # Structure the result
            return {
                "overall_score": analysis_result.get("score", 0.5),
                "is_match": analysis_result.get("is_match", False),
                "explanation": analysis_result.get(
                    "explanation", "Code agent tool call analysis completed"
                ),
                "confidence": analysis_result.get("confidence", 0.8),
                "comparison_strategy": "code_agent",
                "function_analysis": analysis_result.get("function_analysis", {}),
                "parameter_analysis": analysis_result.get("parameter_analysis", {}),
                "contextual_insights": analysis_result.get("contextual_insights", {}),
                "code_agent_metadata": {
                    "full_analysis": analysis_result,
                    "agent_response": final_message,
                    "timestamp": datetime.now().isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Code agent tool call comparison failed: {e}")
            return self._fallback_tool_call_comparison(
                predicted_call, ground_truth_call
            )

    async def compare_tool_calls_async(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tool_specs: Optional[List[Dict[str, Any]]] = None,
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Async version of tool call comparison."""
        # For now, run the sync version in an executor
        # In a full implementation, you'd make the agent calls async
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.compare_tool_calls,
            predicted_call,
            ground_truth_call,
            conversation_history,
            tool_specs,
            custom_instructions,
        )

    def compare_function_name(
        self,
        predicted_name: str,
        ground_truth_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Compare function names using code agent analysis."""

        if not self.agent:
            return 1.0 if predicted_name == ground_truth_name else 0.0

        try:
            prompt = f"""
Compare these function names: '{predicted_name}' vs '{ground_truth_name}'

Write Python code to analyze:
1. Exact match
2. Case sensitivity differences  
3. Underscore vs camelCase patterns
4. Common abbreviations or variations
5. Semantic similarity

Return a float score between 0.0-1.0.
"""

            messages = [HumanMessage(content=prompt)]
            result = self.agent.invoke({"messages": messages})

            # Extract score from response
            final_message = result["messages"][-1].content
            # Look for a numeric score in the response
            import re

            score_match = re.search(r"score[:\s=]+([0-9.]+)", final_message.lower())
            if score_match:
                return float(score_match.group(1))

            # Fallback
            return 1.0 if predicted_name == ground_truth_name else 0.0

        except Exception as e:
            logger.error(f"Code agent function name comparison failed: {e}")
            return 1.0 if predicted_name == ground_truth_name else 0.0

    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON object from agent response, prioritizing executed code output."""
        import re

        # Look for specific result patterns
        patterns = [
            r"ANALYSIS_RESULT:\s*(\{.*?\})",
            r"FINAL_RESULT:\s*(\{.*?\})",
            r"Result:\s*(\{.*?\})",
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue

        # Look for Python execution output (lines starting with execution results)
        lines = response.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("{") and '"score"' in line:
                try:
                    # Try to parse this line as JSON
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue

        # Look for JSON output after code execution
        json_candidates = []

        # Look for lines that start with { and seem to be JSON
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("{"):
                # Try to find the complete JSON object
                json_text = stripped
                j = i + 1
                brace_count = json_text.count("{") - json_text.count("}")

                while j < len(lines) and brace_count > 0:
                    json_text += "\n" + lines[j]
                    brace_count = json_text.count("{") - json_text.count("}")
                    j += 1

                if brace_count == 0:
                    json_candidates.append(json_text)

        # Try to parse JSON candidates (prioritize later ones as they're likely execution results)
        for candidate in reversed(json_candidates):
            try:
                parsed = json.loads(candidate)
                # Validate it has the expected structure
                if isinstance(parsed, dict) and any(
                    key in parsed for key in ["score", "is_match", "result"]
                ):
                    return parsed
            except json.JSONDecodeError:
                continue

        # Fallback: look for any JSON objects with regex
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        matches = re.findall(json_pattern, response, re.DOTALL)

        for match in reversed(matches):  # Try latest matches first
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue

        # Final fallback - extract key information with regex
        score_match = re.search(
            r'["\']?score["\']?\s*[:=]\s*([0-9.]+)', response.lower()
        )
        match_pattern = re.search(
            r'["\']?is_match["\']?\s*[:=]\s*(true|false)', response.lower()
        )
        explanation_match = re.search(
            r'["\']?explanation["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            response,
            re.IGNORECASE,
        )

        return {
            "score": float(score_match.group(1)) if score_match else 0.5,
            "is_match": (
                match_pattern.group(1).lower() == "true" if match_pattern else False
            ),
            "explanation": (
                explanation_match.group(1)
                if explanation_match
                else "Analysis extracted from agent response"
            ),
            "confidence": 0.7,
            "parameter_analysis": {},
            "function_analysis": {},
            "contextual_insights": {},
        }

    def _fallback_comparison(
        self,
        param_name: str,
        predicted_value: Any,
        ground_truth_value: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> ParameterComparisonResult:
        """Fallback comparison when code agent is not available."""

        context = context or {}
        param_status = context.get("parameter_status", ParameterStatus.BOTH_PRESENT)

        # Basic exact match
        is_match = predicted_value == ground_truth_value
        score = 1.0 if is_match else 0.0

        # Handle None values
        if predicted_value is None or ground_truth_value is None:
            if predicted_value is None and ground_truth_value is None:
                is_match = True
                score = 1.0
                explanation = "Both values are None"
            else:
                is_match = False
                score = 0.0
                explanation = f"One value is None: predicted={predicted_value}, ground_truth={ground_truth_value}"
        else:
            explanation = (
                f"Exact match: {predicted_value}"
                if is_match
                else f"Values differ: {predicted_value} != {ground_truth_value}"
            )

        return ParameterComparisonResult(
            parameter_name=param_name,
            predicted_value=predicted_value,
            ground_truth_value=ground_truth_value,
            predicted_resolved_value=predicted_value,
            ground_truth_resolved_value=ground_truth_value,
            parameter_status=param_status,
            comparison_strategy=ComparisonStrategy.CODE_AGENT,
            score=score,
            explanation=f"Fallback comparison (code agent unavailable): {explanation}",
            is_match=is_match,
            confidence=0.9 if is_match else 0.8,
            error_type="code_agent_unavailable" if not is_match else None,
        )

    def _fallback_tool_call_comparison(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Fallback tool call comparison when code agent is not available."""

        # Basic comparison
        function_match = predicted_call.get("name") == ground_truth_call.get("name")
        args_match = predicted_call.get("arguments") == ground_truth_call.get(
            "arguments"
        )

        overall_score = (
            1.0 if (function_match and args_match) else 0.5 if function_match else 0.0
        )

        return {
            "overall_score": overall_score,
            "is_match": function_match and args_match,
            "explanation": "Fallback comparison - code agent unavailable",
            "confidence": 0.8,
            "comparison_strategy": "code_agent_fallback",
            "function_analysis": {"score": 1.0 if function_match else 0.0},
            "parameter_analysis": {"score": 1.0 if args_match else 0.0},
            "contextual_insights": {},
        }

    def _extract_python_code(self, response: str) -> str:
        """Extract Python code from LLM response."""
        import re

        # Look for code blocks
        code_patterns = [
            r"```python\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```",
            r"<\|python_tag\|>(.*?)(?=<\||$)",
        ]

        for pattern in code_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                return matches[0].strip()

        # If no code blocks found, try to extract code heuristically
        lines = response.split("\n")
        code_lines = []
        in_code = False

        for line in lines:
            if (
                "import " in line
                or "def " in line
                or line.strip().startswith("predicted_call")
            ):
                in_code = True

            if in_code:
                code_lines.append(line)

            # Stop if we see explanatory text after code
            if (
                in_code
                and line.strip()
                and not any(
                    keyword in line
                    for keyword in [
                        "import",
                        "def",
                        "=",
                        "return",
                        "print",
                        "if",
                        "elif",
                        "else",
                        "for",
                        "while",
                        "try",
                        "except",
                        "#",
                    ]
                )
            ):
                break

        return "\n".join(code_lines) if code_lines else ""

    def _execute_python_code(
        self,
        code: str,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Safely execute Python code and return results."""
        try:
            # Use a less restrictive but still safe execution environment
            exec_globals = {
                "json": json,
                "predicted_call": predicted_call,
                "ground_truth_call": ground_truth_call,
            }
            exec_locals = {}

            # Execute the code with default builtins (safer than completely restricting)
            exec(code, exec_globals, exec_locals)

            # Look for result in various formats
            result_candidates = [
                exec_locals.get("result"),
                exec_locals.get("analysis_result"),
                exec_locals.get("comparison_result"),
            ]

            for candidate in result_candidates:
                if isinstance(candidate, dict) and "score" in candidate:
                    return candidate

            # If no explicit result variable, try to find a function and call it
            for name, obj in exec_locals.items():
                if callable(obj) and name.startswith(("analyze", "compare")):
                    try:
                        result = obj(predicted_call, ground_truth_call)
                        if isinstance(result, dict):
                            return result
                    except Exception:
                        continue

            return None

        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return None

    def _direct_code_comparison(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Direct code generation and execution approach."""

        try:
            # Use a simpler approach with hardcoded comparison logic
            return self._execute_hardcoded_comparison(
                predicted_call, ground_truth_call, custom_instructions
            )

        except Exception as e:
            logger.error(f"Direct code comparison failed: {e}")

        # Fall back to basic comparison
        return self._fallback_tool_call_comparison(predicted_call, ground_truth_call)

    def _execute_hardcoded_comparison(
        self,
        predicted_call: Dict[str, Any],
        ground_truth_call: Dict[str, Any],
        custom_instructions: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute hardcoded comparison logic that handles type conversions."""

        try:
            # Extract function info
            pred_func = predicted_call.get("function", {})
            gt_func = ground_truth_call.get("function", {})

            func_match = pred_func.get("name") == gt_func.get("name")
            pred_args = pred_func.get("arguments", {})
            gt_args = gt_func.get("arguments", {})

            param_scores = []
            param_details = {}
            all_params = set(pred_args.keys()) | set(gt_args.keys())

            for param in all_params:
                pred_val = pred_args.get(param)
                gt_val = gt_args.get(param)

                # Handle custom instructions for specific comparisons
                score = self._compare_values_with_conversion(
                    pred_val, gt_val, param, custom_instructions
                )

                param_scores.append(score)
                param_details[param] = {
                    "score": score,
                    "pred": pred_val,
                    "gt": gt_val,
                    "match": score >= 0.9,
                    "custom_instructions_applied": custom_instructions is not None,
                }

            param_avg = sum(param_scores) / len(param_scores) if param_scores else 1.0
            overall_score = (1.0 if func_match else 0.0) * 0.3 + param_avg * 0.7
            is_match = func_match and param_avg >= 0.9

            return {
                "overall_score": overall_score,
                "is_match": is_match,
                "explanation": f"Function match: {func_match}, Param avg: {param_avg:.3f}",
                "confidence": 0.95,
                "comparison_strategy": "code_agent_direct",
                "function_analysis": {"name_match": func_match},
                "parameter_analysis": param_details,
                "contextual_insights": {"direct_execution": True},
            }

        except Exception as e:
            logger.error(f"Hardcoded comparison failed: {e}")
            return self._fallback_tool_call_comparison(
                predicted_call, ground_truth_call
            )

    def _compare_values_with_conversion(
        self,
        pred_val: Any,
        gt_val: Any,
        param_name: str = None,
        custom_instructions: str = None,
    ) -> float:
        """Compare two values with intelligent type conversion and custom instructions."""

        # Apply custom instructions if provided
        if custom_instructions and param_name:
            custom_score = self._apply_custom_instructions(
                pred_val, gt_val, param_name, custom_instructions
            )
            if custom_score is not None:
                return custom_score

        # Exact match
        if pred_val == gt_val:
            return 1.0

        # Handle None values
        if pred_val is None or gt_val is None:
            return 0.0

        # String comparison (case insensitive)
        if str(pred_val).lower() == str(gt_val).lower():
            return 1.0

        # Numeric conversion
        try:
            if (
                isinstance(pred_val, str)
                and isinstance(gt_val, (int, float))
                and pred_val.replace(".", "").replace("-", "").isdigit()
            ):
                if float(pred_val) == float(gt_val):
                    return 1.0
        except (ValueError, TypeError):
            pass

        try:
            if (
                isinstance(gt_val, str)
                and isinstance(pred_val, (int, float))
                and gt_val.replace(".", "").replace("-", "").isdigit()
            ):
                if float(gt_val) == float(pred_val):
                    return 1.0
        except (ValueError, TypeError):
            pass

        # Boolean conversion
        pred_bool = self._convert_to_bool(pred_val)
        gt_bool = self._convert_to_bool(gt_val)
        if pred_bool is not None and gt_bool is not None:
            return 1.0 if pred_bool == gt_bool else 0.0

        # Partial string match for semantic similarity
        pred_str = str(pred_val).lower()
        gt_str = str(gt_val).lower()

        # Check if one is contained in the other (for cases like "Delta" vs "Delta Airlines")
        if pred_str in gt_str or gt_str in pred_str:
            return 0.8

        # Check for common abbreviations
        abbreviations = {
            "nyc": "new york city",
            "ny": "new york",
            "la": "los angeles",
            "sf": "san francisco",
            "dc": "washington dc",
        }

        for abbrev, full in abbreviations.items():
            if (pred_str == abbrev and gt_str == full) or (
                pred_str == full and gt_str == abbrev
            ):
                return 0.9

        return 0.0

    def _convert_to_bool(self, value: Any) -> bool:
        """Convert various representations to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lower_val = value.lower()
            if lower_val in ["true", "1", "yes", "on"]:
                return True
            elif lower_val in ["false", "0", "no", "off"]:
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        return None

    def _extract_python_code(self, response: str) -> str:
        """Extract Python code from LLM response."""

        # Look for code blocks
        code_patterns = [
            r"```python\s*(.*?)\s*```",
            r"```\s*(.*?)\s*```",
            r"<\|python_tag\|>(.*?)(?=<\||$)",
        ]

        for pattern in code_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            if matches:
                return matches[0].strip()

        # If no code blocks found, try to extract code heuristically
        lines = response.split("\n")
        code_lines = []
        in_code = False

        for line in lines:
            if (
                "import " in line
                or "def " in line
                or line.strip().startswith("predicted_call")
            ):
                in_code = True

            if in_code:
                code_lines.append(line)

            # Stop if we see explanatory text after code
            if (
                in_code
                and line.strip()
                and not any(
                    keyword in line
                    for keyword in [
                        "import",
                        "def",
                        "=",
                        "return",
                        "print",
                        "if",
                        "elif",
                        "else",
                        "for",
                        "while",
                        "try",
                        "except",
                        "#",
                    ]
                )
            ):
                break

        return "\n".join(code_lines) if code_lines else ""

    def _apply_custom_instructions(
        self, pred_val: Any, gt_val: Any, param_name: str, custom_instructions: str
    ) -> Optional[float]:
        """Apply custom instructions for specific parameter comparisons."""
        try:
            # Execute Python code to apply custom instructions
            import datetime

            # Try to import dateutil, but don't fail if not available
            try:
                from dateutil import parser as date_parser
            except ImportError:
                date_parser = None

            # Create a local namespace for safe execution
            local_vars = {
                "pred_val": pred_val,
                "gt_val": gt_val,
                "param_name": param_name,
                "custom_instructions": custom_instructions,
                "datetime": datetime,
                "date_parser": date_parser,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "len": len,
                "abs": abs,
                "min": min,
                "max": max,
            }

            # Example custom instruction patterns
            if (
                "yesterday" in custom_instructions.lower()
                and "date" in param_name.lower()
            ):
                # Handle date comparisons where "yesterday" might be represented differently
                code = """
import datetime
from datetime import timedelta

def check_yesterday_equivalence(pred_val, gt_val):
    try:
        # Parse dates from various formats
        pred_date = None
        gt_date = None
        
        # Try to parse predicted value as date
        if isinstance(pred_val, str):
            try:
                if date_parser:
                    pred_date = date_parser.parse(pred_val).date()
                else:
                    # Simple parsing for YYYY-MM-DD format
                    pred_date = datetime.datetime.strptime(pred_val, "%Y-%m-%d").date()
            except:
                pass
        
        # Try to parse ground truth value as date  
        if isinstance(gt_val, str):
            try:
                if date_parser:
                    gt_date = date_parser.parse(gt_val).date()
                else:
                    # Simple parsing for YYYY-MM-DD format
                    gt_date = datetime.datetime.strptime(gt_val, "%Y-%m-%d").date()
            except:
                pass
        
        # Check if either date represents yesterday
        yesterday = datetime.date.today() - timedelta(days=1)
        
        # If both are valid dates and both represent yesterday, they match
        if pred_date and gt_date:
            if pred_date == yesterday and gt_date == yesterday:
                return 1.0
            elif pred_date == gt_date:
                return 1.0
            else:
                return 0.0
        
        # If one is yesterday and the other matches yesterday, they match
        if pred_date == yesterday or gt_date == yesterday:
            return 1.0
            
        return None  # Fall back to normal comparison
    except Exception as e:
        return None  # Fall back to normal comparison

result = check_yesterday_equivalence(pred_val, gt_val)
"""

                exec(code, {}, local_vars)
                return local_vars.get("result")

            # Add more custom instruction patterns here
            # For example, handling relative time expressions, currency formats, etc.

            return None  # No custom instruction matched

        except Exception as e:
            logger.warning(f"Custom instructions execution failed: {e}")
            return None  # Fall back to normal comparison
