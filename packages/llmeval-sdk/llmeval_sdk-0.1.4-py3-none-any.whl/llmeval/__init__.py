"""
LLM Evaluation Framework Python SDK

A Python client for the evaluAte LLM evaluation framework.
"""

__version__ = "0.1.0"

from .client import EvalClient
from .models import EvalRequest, EvalResult, BatchEvalResult, JudgeResult
from .exceptions import EvalError, APIError, ConnectionError

__all__ = [
    "EvalClient",
    "EvalRequest",
    "EvalResult",
    "BatchEvalResult",
    "JudgeResult",
    "EvalError",
    "APIError",
    "ConnectionError",
]
