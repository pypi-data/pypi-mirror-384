"""Utility functions for the evaluAte SDK."""

from typing import List, Dict, Any
import pandas as pd


def results_to_dataframe(results: List[Any]) -> pd.DataFrame:
    """Convert evaluation results to a pandas DataFrame."""
    data = []
    for result in results:
        if hasattr(result, 'dict'):
            data.append(result.dict())
        else:
            data.append(result.__dict__)
    
    return pd.DataFrame(data)


def calculate_statistics(results: List[Any]) -> Dict[str, Any]:
    """Calculate statistics from evaluation results."""
    if not results:
        return {}
    
    total = len(results)
    passed = sum(1 for r in results if hasattr(r, 'passed') and r.passed)
    failed = total - passed
    
    latencies = [r.latency_ms for r in results if hasattr(r, 'latency_ms') and r.latency_ms]
    judge_latencies = [
        r.judge_latency_ms 
        for r in results 
        if hasattr(r, 'judge_latency_ms') and r.judge_latency_ms
    ]
    
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": (passed / total * 100) if total > 0 else 0,
        "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
        "avg_judge_latency_ms": sum(judge_latencies) / len(judge_latencies) if judge_latencies else 0,
        "min_latency_ms": min(latencies) if latencies else 0,
        "max_latency_ms": max(latencies) if latencies else 0,
    }
