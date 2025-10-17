import asyncio
import json
from typing import List, Optional, Dict, Any, Callable
from urllib.parse import urljoin
import requests
import websockets

from .models import (
    EvalRequest,
    EvalResult,
    BatchEvalResult,
    ExperimentResponse,
    HistoryResponse,
    ModelsResponse,
)
from .exceptions import APIError, ConnectionError, EvalError


class EvalClient:
    """Client for the evaluAte LLM evaluation framework."""

    def __init__(self, base_url: str = "http://127.0.0.1:8080", timeout: int = 120):
        """
        Initialize the EvalClient.

        Args:
            base_url: Base URL of the evaluAte server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api/v1"
        self.timeout = timeout
        self.session = requests.Session()

    def _make_request(
        self, method: str, endpoint: str, **kwargs
    ) -> requests.Response:
        """Make an HTTP request to the API."""
        url = urljoin(self.api_url + "/", endpoint)
        
        try:
            response = self.session.request(
                method, url, timeout=self.timeout, **kwargs
            )
            
            # --- FIX 1: Proactively check for structured server errors (e.g., 400 Bad Request) ---
            if not response.ok:
                try:
                    # Attempt to parse the server's structured error body (EvalResponse)
                    error_data = response.json()
                    error_msg = error_data.get("error")

                    if error_msg:
                        # If a specific error message is present, raise our custom APIError immediately.
                        # This cleanly captures the error message and prevents the messy exception chain.
                        raise APIError(f"API error: {error_msg}", status_code=response.status_code)

                except (ValueError, AttributeError):
                    # Ignore if the response wasn't structured JSON, let raise_for_status handle it.
                    pass

            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            raise ConnectionError(f"Request to {url} timed out after {self.timeout}s")
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Failed to connect to {url}: {str(e)}")
        except requests.exceptions.HTTPError as e:
            # This block handles generic HTTP errors not caught by the proactive check.
            try:
                error_data = e.response.json()
                error_msg = error_data.get("error", str(e))
            except (ValueError, AttributeError):
                error_msg = str(e)
            
            raise APIError(f"API error: {error_msg}", status_code=e.response.status_code)

    def health_check(self) -> Dict[str, Any]:
        """Check if the server is healthy."""
        response = self._make_request("GET", "health")
        return response.json()

    def get_models(self) -> List[str]:
        """Get list of available models."""
        response = self._make_request("GET", "models")
        return ModelsResponse(**response.json()).models

    def run_eval(
        self,
        model: str,
        prompt: str,
        expected: Optional[str] = None,
        judge_model: Optional[str] = None,
        criteria: Optional[str] = None,
    ) -> EvalResult:
        """Run a single evaluation."""
        request = EvalRequest(
            model=model,
            prompt=prompt,
            expected=expected,
            judge_model=judge_model,
            criteria=criteria,
        )
        
        # --- FIX 2: Catch APIError and correctly convert to EvalError ---
        try:
            response = self._make_request(
                "POST", "evals/run", json=request.dict(exclude_none=True)
            )
        except APIError as e:
            # CORRECT: Access the message via e.args[0]
            # Strip the "API error: " prefix added in _make_request for a cleaner final error message.
            clean_msg = e.args[0].replace("API error: ", "")
            raise EvalError(clean_msg)
        # --- END FIX 2 ---
        
        data = response.json()
        
        if data.get("status") == "error":
            # Handles cases where the server returns 200 but the inner status is 'error'
            raise EvalError(data.get("error", "Unknown evaluation error"))
        
        return EvalResult.from_api_response(data)

    def run_batch(
        self,
        evals: List[Dict[str, Any]],
        max_workers: Optional[int] = None,
    ) -> BatchEvalResult:
        """Run multiple evaluations in parallel."""
        response = self._make_request("POST", "evals/batch", json=evals)
        data = response.json()
        return BatchEvalResult.from_api_response(data)

    def get_eval(self, eval_id: str) -> Dict[str, Any]:
        """Get a specific evaluation by ID."""
        response = self._make_request("GET", f"evals/{eval_id}")
        return response.json()

    def get_history(self) -> HistoryResponse:
        """Get evaluation history."""
        response = self._make_request("GET", "evals/history")
        return HistoryResponse(**response.json())

    def create_experiment(
        self,
        name: str,
        description: Optional[str] = None,
        eval_ids: Optional[List[str]] = None,
    ) -> ExperimentResponse:
        """Create a new experiment."""
        data = {
            "name": name,
            "description": description,
            "eval_ids": eval_ids or [],
        }
        response = self._make_request("POST", "experiments", json=data)
        return ExperimentResponse(**response.json())

    def get_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """Get experiment details."""
        response = self._make_request("GET", f"experiments/{experiment_id}")
        return response.json()

    def stream_evals(
        self,
        callback: Callable[[Dict[str, Any]], None],
        url: Optional[str] = None,
    ):
        """Stream real-time evaluation updates via WebSocket."""
        ws_url = url or self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/api/v1/ws"
        
        asyncio.run(self._stream_evals_async(ws_url, callback))

    async def _stream_evals_async(
        self, ws_url: str, callback: Callable[[Dict[str, Any]], None]
    ):
        """Internal async WebSocket handler."""
        try:
            async with websockets.connect(ws_url) as websocket:
                print(f"Connected to WebSocket: {ws_url}")
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        callback(data)
                    except json.JSONDecodeError:
                        print(f"Failed to parse message: {message}")
        except Exception as e:
            raise ConnectionError(f"WebSocket connection failed: {str(e)}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.session.close()

    def close(self):
        """Close the session."""
        self.session.close()
