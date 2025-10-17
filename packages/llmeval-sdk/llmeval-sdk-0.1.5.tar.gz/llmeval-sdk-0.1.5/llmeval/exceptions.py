"""Custom exceptions for the evaluAte SDK."""

from typing import Optional


class EvalError(Exception):
    """Base exception for evaluAte SDK."""
    pass


class APIError(EvalError):
    """Exception raised for API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ConnectionError(EvalError):
    """Exception raised for connection errors."""
    pass
