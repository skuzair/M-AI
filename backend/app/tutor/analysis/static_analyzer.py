import ast
import re
from backend.app.tutor.analysis.analyzer import CodeAnalyzer
from backend.app.tutor.analysis.models import AnalysisContext

class StaticAnalyzer(CodeAnalyzer):
    """Statically analyzes code to find structure patterns like nesting levels."""
    
    def analyze(self, context: AnalysisContext) -> dict:
        code = context.code
        lang = context.language.lower()
        
        result = {
            "syntax": {"valid": True, "errors": []},
            "signals": [],
            "patterns": []
        }
        
        if not code.strip():
            result["syntax"] = {"valid": False, "errors": ["Code is empty."]}
            return result

        if "python" in lang:
            try:
                tree = ast.parse(code)
                
                class LoopVisitor(ast.NodeVisitor):
                    def __init__(self):
                        self.current_depth = 0
                        self.max_depth = 0
                        self.recursion_calls = 0
                    
                    def visit_For(self, node):
                        self.current_depth += 1
                        self.max_depth = max(self.max_depth, self.current_depth)
                        self.generic_visit(node)
                        self.current_depth -= 1
                        
                    def visit_While(self, node):
                        self.current_depth += 1
                        self.max_depth = max(self.max_depth, self.current_depth)
                        self.generic_visit(node)
                        self.current_depth -= 1
                
                visitor = LoopVisitor()
                visitor.visit(tree)
                
                if visitor.max_depth >= 2:
                    result["signals"].append({
                        "type": "nested_iteration",
                        "confidence": 0.95,
                        "evidence": f"Found nested loop structure with depth {visitor.max_depth}."
                    })
                    result["patterns"].append({
                        "name": "nested_loops",
                        "confidence": 0.95
                    })
                    
            except SyntaxError as se:
                result["syntax"] = {
                    "valid": False,
                    "errors": [f"SyntaxError: {se.msg} on line {se.lineno}"]
                }
        else:
            # Basic fallback analyzer for JavaScript/other languages using simple brace depth counting
            lines = code.split('\n')
            max_depth = 0
            current_depth = 0
            for line in lines:
                cleaned = line.strip()
                # Find for or while statements
                if re.search(r'\b(for|while)\s*\(', cleaned):
                    current_depth += 1
                    max_depth = max(max_depth, current_depth)
                # Very simple indentation-based or closing brace check
                if '}' in cleaned:
                    current_depth = max(0, current_depth - cleaned.count('}'))
                    
            if max_depth >= 2:
                result["signals"].append({
                    "type": "nested_iteration",
                    "confidence": 0.85,
                    "evidence": f"Detected potential nested loops (depth {max_depth}) in code."
                })
                result["patterns"].append({
                    "name": "nested_loops",
                    "confidence": 0.85
                })
                
        return result
