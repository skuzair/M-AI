import re
from backend.app.tutor.analysis.analyzer import CodeAnalyzer
from backend.app.tutor.analysis.models import AnalysisContext

class PatternAnalyzer(CodeAnalyzer):
    """Analyzes code to detect design pattern signals (e.g. repeated lookup, two pointers)."""
    
    def analyze(self, context: AnalysisContext) -> dict:
        code = context.code
        lang = context.language.lower()
        
        signals = []
        patterns = []
        
        # 1. Repeated Lookup Pattern
        # Look for nested index referencing (like nums[i] and nums[j] inside nested loops)
        has_nested = False
        if "python" in lang:
            if re.search(r'(for|while)\s+.*:\s*\n\s+(for|while)\s+.*:', code):
                has_nested = True
        else:
            if re.search(r'for\s*\(.*\)\s*\{\s*[^}]*for\s*\(.*\)', code, re.DOTALL):
                has_nested = True
                
        if has_nested:
            signals.append({
                "type": "repeated_lookup",
                "confidence": 0.85,
                "evidence": "Nested iteration pattern scans array elements repeatedly."
            })
            
        # 2. Dual Pointers Pattern
        # Look for variables initialized to start/end index and a while loop comparing them
        has_pointers = False
        if "python" in lang:
            if re.search(r'\b(left|l|low|i)\s*=\s*\d+', code) and re.search(r'\b(right|r|high|j)\s*=\s*(len|range|-1)', code) and "while" in code:
                has_pointers = True
        else:
            if re.search(r'\b(left|l|low|i)\s*=\s*\d+', code) and re.search(r'\b(right|r|high|j)\s*=\s*\w+', code) and "while" in code:
                has_pointers = True
                
        if has_pointers:
            patterns.append({
                "name": "two_pointers",
                "confidence": 0.85
            })
            signals.append({
                "type": "two_pointers_traversal",
                "confidence": 0.85,
                "evidence": "Variables indicating pointers at different parts of the list moving concurrently."
            })
            
        # 3. Hash Map Lookup Pattern
        # Look for dictionary insertion or retrieval or membership check
        has_hash = False
        if "python" in lang:
            if ".get(" in code or "dict(" in code:
                has_hash = True
            # Check for 'in' statement that is not a loop
            if "in " in code and not re.search(r'for\s+\w+\s+in', code):
                has_hash = True
        else:
            if "new Map" in code or "new Set" in code or ".has(" in code or ".get(" in code or "seen[" in code:
                has_hash = True
                
        if has_hash:
            patterns.append({
                "name": "hash_map_lookup",
                "confidence": 0.90
            })
            signals.append({
                "type": "hash_lookup",
                "confidence": 0.90,
                "evidence": "Detected lookup/membership checks utilizing dictionaries or sets."
            })
            
        return {
            "signals": signals,
            "patterns": patterns
        }
