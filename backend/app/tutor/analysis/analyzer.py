from typing import List
from backend.app.tutor.analysis.models import AnalysisContext, AnalysisResult

class CodeAnalyzer:
    """Base interface/protocol for all code analyzers."""
    def analyze(self, context: AnalysisContext) -> dict:
        raise NotImplementedError("Analyzers must implement the analyze method.")

class AnalysisPipeline:
    """Coordinates and aggregates signals from multiple CodeAnalyzers."""
    def __init__(self, analyzers: List[CodeAnalyzer]):
        self.analyzers = analyzers

    def execute(self, context: AnalysisContext) -> AnalysisResult:
        aggregated_result = AnalysisResult()
        
        for analyzer in self.analyzers:
            try:
                res = analyzer.analyze(context)
                
                # Merge syntax errors if any
                if "syntax" in res:
                    aggregated_result.syntax.update(res["syntax"])
                
                # Merge execution details
                if "execution" in res:
                    aggregated_result.execution.update(res["execution"])
                
                # Merge complexity estimation (take highest confidence or prioritize)
                if "complexity" in res:
                    current_conf = aggregated_result.complexity.get("confidence", 0.0)
                    new_conf = res["complexity"].get("confidence", 0.0)
                    if new_conf >= current_conf:
                        aggregated_result.complexity.update(res["complexity"])
                
                # Append patterns and signals
                if "patterns" in res:
                    aggregated_result.patterns.extend(res["patterns"])
                if "signals" in res:
                    aggregated_result.signals.extend(res["signals"])
                if "warnings" in res:
                    aggregated_result.warnings.extend(res["warnings"])
                if "analysis_metadata" in res:
                    aggregated_result.analysis_metadata.update(res["analysis_metadata"])
                    
            except Exception as e:
                # Graceful degradation for individual analyzers
                aggregated_result.warnings.append(f"Analyzer failed: {str(e)}")
                
        return aggregated_result
