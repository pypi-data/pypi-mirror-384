from .base import BaseComparator
from .exact_match import ExactMatchComparator
from .fuzzy_string import FuzzyStringComparator
from .llm_judge import LLMJudgeComparator
from .hybrid import HybridComparator

# Optional code agent comparator (requires LangGraph)
try:
    from .code_agent import CodeAgentComparator

    _code_agent_available = True
except ImportError:
    _code_agent_available = False

    # Create placeholder class to avoid import errors
    class CodeAgentComparator:
        def __init__(self):
            raise ImportError(
                "Code Agent dependencies not available. Install: pip install langgraph langchain-core langchain-experimental"
            )


__all__ = [
    "BaseComparator",
    "ExactMatchComparator",
    "FuzzyStringComparator",
    "LLMJudgeComparator",
    "CodeAgentComparator",
    "HybridComparator",
]
