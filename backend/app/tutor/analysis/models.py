from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AnalysisContext(BaseModel):
    problem_title: str
    problem_description: str
    constraints: List[str] = []
    examples: List[Dict[str, Any]] = []
    code: str
    language: str
    execution_result: Optional[Dict[str, Any]] = None
    previous_attempts: List[Dict[str, Any]] = []
    learner_profile: Optional[Dict[str, Any]] = None
    tutor_state: Optional[Dict[str, Any]] = None

class AnalysisResult(BaseModel):
    syntax: Dict[str, Any] = {"valid": True, "errors": []}
    execution: Dict[str, Any] = {"status": "passed", "tests_run": 0, "tests_passed": 0, "failures": []}
    complexity: Dict[str, Any] = {"time": "O(n^2)", "space": "O(1)", "confidence": 0.0}
    patterns: List[Dict[str, Any]] = []  # e.g., [{"name": "nested_iteration", "confidence": 0.9}]
    signals: List[Dict[str, Any]] = []   # e.g., [{"type": "repeated_lookup", "confidence": 0.8, "evidence": "..."}]
    warnings: List[str] = []
    analysis_metadata: Dict[str, Any] = {}
