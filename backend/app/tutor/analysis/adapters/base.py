from typing import List, Dict, Any, Optional
from backend.app.tutor.analysis.models import AnalysisContext

class ProblemAdapter:
    """Interface for problem-specific adapters (e.g. test generation, custom patterns)."""
    
    def can_handle(self, context: AnalysisContext) -> bool:
        """Checks if this adapter is applicable to the current problem context."""
        raise NotImplementedError()
        
    def analyze(self, context: AnalysisContext) -> dict:
        """Runs problem-specific static analysis, returning list of signals/patterns."""
        return {"signals": [], "patterns": []}
        
    def generate_tests(self, context: AnalysisContext) -> List[Dict[str, Any]]:
        """Returns structured test cases: [{'input': ..., 'expected': ...}]."""
        return []
        
    def generate_execution_wrapper(self, code: str, test_cases: List[Dict[str, Any]], language: str) -> str:
        """Generates runnable script contents (Python or JavaScript) to run test cases."""
        return ""

class ProblemAdapterRegistry:
    """Registry to manage and select problem-specific adapters."""
    def __init__(self):
        self._adapters: List[ProblemAdapter] = []
        
    def register(self, adapter: ProblemAdapter):
        self._adapters.append(adapter)
        
    def get_adapter(self, context: AnalysisContext) -> Optional[ProblemAdapter]:
        for adapter in self._adapters:
            if adapter.can_handle(context):
                return adapter
        return None

# Singleton instance
registry = ProblemAdapterRegistry()
