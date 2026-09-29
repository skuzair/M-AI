from backend.app.tutor.analysis.models import AnalysisContext, AnalysisResult
from backend.app.tutor.analysis.analyzer import AnalysisPipeline
from backend.app.tutor.analysis.static_analyzer import StaticAnalyzer
from backend.app.tutor.analysis.complexity_analyzer import ComplexityAnalyzer
from backend.app.tutor.analysis.pattern_analyzer import PatternAnalyzer
from backend.app.tutor.analysis.execution_analyzer import ExecutionAnalyzer
from backend.app.tutor.analysis.adapters.base import registry

# Import adapters to ensure they auto-register in the registry
import backend.app.tutor.analysis.adapters.twosum

def run_analysis_pipeline(context: AnalysisContext) -> AnalysisResult:
    """Executes all analyzers and problem adapters against the provided context."""
    pipeline = AnalysisPipeline([
        StaticAnalyzer(),
        ComplexityAnalyzer(),
        PatternAnalyzer(),
        ExecutionAnalyzer()
    ])
    
    # Run generic analysis
    result = pipeline.execute(context)
    
    # Run adapter analysis if available
    adapter = registry.get_adapter(context)
    if adapter:
        adapter_res = adapter.analyze(context)
        if "signals" in adapter_res:
            result.signals.extend(adapter_res["signals"])
        if "patterns" in adapter_res:
            result.patterns.extend(adapter_res["patterns"])
            
    return result
