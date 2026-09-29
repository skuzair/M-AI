import json
from typing import List, Dict, Any
from backend.app.tutor.analysis.adapters.base import ProblemAdapter, registry
from backend.app.tutor.analysis.models import AnalysisContext

class TwoSumAdapter(ProblemAdapter):
    """Specific adapter for the 'Two Sum' problem."""
    
    def can_handle(self, context: AnalysisContext) -> bool:
        title = context.problem_title.lower()
        return "two sum" in title
        
    def analyze(self, context: AnalysisContext) -> dict:
        code = context.code
        lang = context.language.lower()
        
        signals = []
        patterns = []
        
        # Two Sum specific misconception check (e.g. reusing the same index twice)
        # We can check if code checks nums[i] + nums[i] == target (i.e. doesn't verify i != j)
        # Or returns [i, i] if target is even and nums[i] * 2 == target.
        # This will be flagged as a signal and passed to Grok to make a diagnosis.
        if "python" in lang:
            # Check if student's loop has a single index lookup or doesn't check i != j
            # We will generate a signal if we suspect same element reuse.
            if "nums[i]" in code and "nums[j]" in code and "i !=" not in code and "j !=" not in code:
                signals.append({
                    "type": "same_element_reuse",
                    "confidence": 0.70,
                    "evidence": "Code scans pairs but does not seem to guard against reusing the same element at index i."
                })
        else:
            if "nums[i]" in code and "nums[j]" in code and "i !==" not in code and "j !==" not in code and "i !=" not in code and "j !=" not in code:
                signals.append({
                    "type": "same_element_reuse",
                    "confidence": 0.70,
                    "evidence": "Code checks indices but lacks condition to prevent i and j from pointing to the same index."
                })
                
        return {"signals": signals, "patterns": patterns}
        
    def generate_tests(self, context: AnalysisContext) -> List[Dict[str, Any]]:
        return [
            {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
            {"input": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2]},
            {"input": {"nums": [3, 3], "target": 6}, "expected": [0, 1]}
        ]
        
    def generate_execution_wrapper(self, code: str, test_cases: List[Dict[str, Any]], language: str) -> str:
        lang = language.lower()
        tc_json = json.dumps(test_cases)
        
        if "python" in lang:
            return f"""
import json
import sys

# User's Code
{code}

# Test Cases
test_cases = {tc_json}

results = []
passed_count = 0

# Try to find Solution class
try:
    sol = Solution()
except NameError:
    # Fallback if student didn't wrap in class Solution
    class SolutionWrapper:
        pass
    sol = SolutionWrapper()
    # Bind twoSum directly if defined globally
    if 'twoSum' in globals():
        sol.twoSum = globals()['twoSum']
    else:
        # Try to find any function and bind it
        funcs = [v for k, v in globals().items() if callable(v) and k != 'SolutionWrapper']
        if funcs:
            sol.twoSum = funcs[0]

for idx, tc in enumerate(test_cases):
    try:
        nums = tc['input']['nums']
        target = tc['input']['target']
        expected = tc['expected']
        
        if not hasattr(sol, 'twoSum'):
            raise AttributeError("Could not locate twoSum function in code.")
            
        actual = sol.twoSum(nums, target)
        
        # Compare sorted values (indices can be returned in any order)
        if isinstance(actual, (list, tuple)) and len(actual) == 2 and sorted(list(actual)) == sorted(expected):
            passed_count += 1
        else:
            results.append({{
                "test_index": idx,
                "input": tc['input'],
                "expected": expected,
                "actual": actual,
                "error": f"Expected {{expected}}, got {{actual}}"
            }})
    except Exception as e:
        results.append({{
            "test_index": idx,
            "input": tc['input'],
            "expected": tc['expected'],
            "actual": None,
            "error": f"Exception: {{str(e)}}"
        }})

print(json.dumps({{
    "status": "passed" if passed_count == len(test_cases) else "failed",
    "tests_run": len(test_cases),
    "tests_passed": passed_count,
    "failures": results
}}))
"""
        elif "javascript" in lang or "js" in lang:
            return f"""
const fs = require('fs');

// User's Code
{code}

// Test Cases
const testCases = {tc_json};

const results = [];
let passedCount = 0;

// Resolve twoSum function
let targetFn = null;
if (typeof twoSum === 'function') {{
    targetFn = twoSum;
}} else if (typeof Solution !== 'undefined' && typeof Solution.prototype.twoSum === 'function') {{
    const s = new Solution();
    targetFn = s.twoSum.bind(s);
}} else if (typeof Solution !== 'undefined' && typeof Solution.twoSum === 'function') {{
    targetFn = Solution.twoSum;
}} else {{
    // Search global scope for any function that might be it
    for (const key in global) {{
        if (typeof global[key] === 'function' && key !== 'gc') {{
            targetFn = global[key];
            break;
        }}
    }}
}}

testCases.forEach((tc, idx) => {{
    try {{
        const nums = tc.input.nums;
        const target = tc.input.target;
        const expected = tc.expected;
        
        if (!targetFn) {{
            throw new Error("Could not locate twoSum function in code.");
        }}
        
        const actual = targetFn(nums, target);
        
        if (Array.isArray(actual) && actual.length === 2 && 
            actual.slice().sort((a,b)=>a-b).join(',') === expected.slice().sort((a,b)=>a-b).join(',')) {{
            passedCount += 1;
        }} else {{
            results.push({{
                test_index: idx,
                input: tc.input,
                expected: expected,
                actual: actual,
                error: `Expected [${{expected}}], got [${{actual}}]`
            }});
        }}
    }} catch (e) {{
        results.push({{
            test_index: idx,
            input: tc.input,
            expected: tc.expected,
            actual: null,
            error: "Exception: " + e.message
        }});
    }}
}});

console.log(JSON.stringify({{
    status: passedCount === testCases.length ? "passed" : "failed",
    tests_run: testCases.length,
    tests_passed: passedCount,
    failures: results
}}));
"""
        return ""

# Auto register
registry.register(TwoSumAdapter())
