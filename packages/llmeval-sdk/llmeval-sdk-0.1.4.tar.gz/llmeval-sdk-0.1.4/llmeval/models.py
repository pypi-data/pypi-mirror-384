"""Data models for the evaluAte SDK."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class EvalRequest(BaseModel):
    """Request model for running an evaluation."""
    
    model: str = Field(..., description="Model identifier")
    prompt: str = Field(..., description="Input prompt")
    expected: Optional[str] = Field(None, description="Expected output")
    judge_model: Optional[str] = Field(None, description="Judge model")
    criteria: Optional[str] = Field(None, description="Custom criteria")


class JudgeResult(BaseModel):
    """Judge evaluation result."""
    
    judge_model: str
    verdict: str
    reasoning: Optional[str] = None
    confidence: Optional[float] = None


class EvalResult(BaseModel):
    """Result of a single evaluation."""
    
    id: str
    status: str
    model: Optional[str] = None
    prompt: Optional[str] = None
    model_output: Optional[str] = None
    expected: Optional[str] = None
    judge_result: Optional[JudgeResult] = None
    timestamp: Optional[str] = None
    latency_ms: Optional[int] = None
    judge_latency_ms: Optional[int] = None
    total_latency_ms: Optional[int] = None
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        """Check if the evaluation passed."""
        if self.judge_result:
            return self.judge_result.verdict == "Pass"
        return self.status == "passed"

    @property
    def judge_verdict(self) -> Optional[str]:
        """Get the judge verdict if available."""
        return self.judge_result.verdict if self.judge_result else None

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "EvalResult":
        """Create EvalResult from API response."""
        result_data = data.get("result", {})
        
        judge_result = None
        if result_data.get("judge_result"):
            judge_result = JudgeResult(**result_data["judge_result"])
        
        return cls(
            id=data["id"],
            status=data["status"],
            model=result_data.get("model"),
            prompt=result_data.get("prompt"),
            model_output=result_data.get("model_output"),
            expected=result_data.get("expected"),
            judge_result=judge_result,
            timestamp=result_data.get("timestamp"),
            latency_ms=result_data.get("latency_ms"),
            judge_latency_ms=result_data.get("judge_latency_ms"),
            total_latency_ms=result_data.get("total_latency_ms"),
            error=data.get("error"),
        )


class BatchEvalResult(BaseModel):
    """Result of a batch evaluation."""
    
    batch_id: str
    status: str
    total: int
    completed: int
    passed: int
    failed: int
    average_model_latency_ms: int
    average_judge_latency_ms: int
    results: List[EvalResult]

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate as percentage."""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "BatchEvalResult":
        """Create BatchEvalResult from API response."""
        results = [EvalResult.from_api_response(r) for r in data["results"]]
        
        return cls(
            batch_id=data["batch_id"],
            status=data["status"],
            total=data["total"],
            completed=data["completed"],
            passed=data["passed"],
            failed=data["failed"],
            average_model_latency_ms=data["average_model_latency_ms"],
            average_judge_latency_ms=data["average_judge_latency_ms"],
            results=results,
        )


class HistoryEntry(BaseModel):
    """A single entry in the evaluation history."""
    
    id: str
    status: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None
    model_output: Optional[str] = None
    expected: Optional[str] = None
    judge_model: Optional[str] = None
    judge_verdict: Optional[str] = None
    judge_reasoning: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str


class HistoryResponse(BaseModel):
    """Response containing evaluation history."""
    
    results: List[HistoryEntry]


class ExperimentResponse(BaseModel):
    """Response for experiment creation/retrieval."""
    
    id: str
    name: str
    status: str
    created_at: str


class ModelsResponse(BaseModel):
    """Response containing available models."""
    
    models: List[str]
