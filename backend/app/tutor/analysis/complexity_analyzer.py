import re
from backend.app.tutor.analysis.analyzer import CodeAnalyzer
from backend.app.tutor.analysis.models import AnalysisContext

class ComplexityAnalyzer(CodeAnalyzer):
    """Guesses time and space complexity based on code structural clues."""
    
    def analyze(self, context: AnalysisContext) -> dict:
        code = context.code
        lang = context.language.lower()
        
        # Default baseline
        time_comp = "O(n)"
        space_comp = "O(1)"
        confidence = 0.60
        
        # Check for nested loops to imply O(n^2)
        has_nested_loops = False
        if "python" in lang:
            # Check for indent followed by another loop, or search standard patterns
            if re.search(r'(for|while)\s+.*:\s*\n\s+(for|while)\s+.*:', code) or re.search(r'for\s+\w+\s+in\s+range.*for\s+\w+\s+in\s+range', code):
                has_nested_loops = True
        else:
            # JS/TS style nested loops
            if re.search(r'for\s*\(.*\)\s*\{\s*[^}]*for\s*\(.*\)', code, re.DOTALL):
                has_nested_loops = True
                
        if has_nested_loops:
            time_comp = "O(n^2)"
            space_comp = "O(1)"
            confidence = 0.90
        else:
            # Check for sorting (O(n log n))
            has_sort = False
            if "python" in lang:
                if "sorted(" in code or ".sort(" in code or ".sort()" in code:
                    has_sort = True
            else:
                if ".sort(" in code or ".sort()" in code:
                    has_sort = True
                    
            if has_sort:
                time_comp = "O(n log n)"
                space_comp = "O(1)"
                confidence = 0.85
            else:
                # Check for hash map / lookup structures (implies O(n) space, O(n) time)
                has_hash = False
                if "python" in lang:
                    if re.search(r'\{\s*\}', code) or "dict(" in code or ".get(" in code or "in " in code:
                        # Ensure 'in' isn't just 'for x in'
                        if "in " in code and not re.search(r'for\s+\w+\s+in', code):
                            has_hash = True
                        if ".get(" in code or "dict(" in code or "{}" in code:
                            has_hash = True
                else:
                    if "new Map" in code or "new Set" in code or re.search(r'\{\s*\}', code) or "map.has(" in code or "set.has(" in code:
                        has_hash = True
                        
                if has_hash:
                    time_comp = "O(n)"
                    space_comp = "O(n)"
                    confidence = 0.80
                    
        return {
            "complexity": {
                "time": time_comp,
                "space": space_comp,
                "confidence": confidence
            }
        }
