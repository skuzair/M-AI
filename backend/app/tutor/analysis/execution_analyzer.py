import os
import sys
import tempfile
import subprocess
import json
from backend.app.tutor.analysis.analyzer import CodeAnalyzer
from backend.app.tutor.analysis.models import AnalysisContext
from backend.app.tutor.analysis.adapters.base import registry

class ExecutionAnalyzer(CodeAnalyzer):
    """Executes code against test cases in a subprocess and parses outputs."""
    
    def analyze(self, context: AnalysisContext) -> dict:
        result = {
            "execution": {
                "status": "passed",
                "tests_run": 0,
                "tests_passed": 0,
                "failures": []
            }
        }
        
        # 1. Fetch adapter
        adapter = registry.get_adapter(context)
        if not adapter:
            # If no adapter exists, we cannot execute the code deterministically.
            # We return empty execution, indicating no execution occurred.
            result["execution"]["status"] = "skipped"
            return result
            
        # 2. Generate tests and wrapper script
        test_cases = adapter.generate_tests(context)
        if not test_cases:
            result["execution"]["status"] = "skipped"
            return result
            
        wrapper_code = adapter.generate_execution_wrapper(
            context.code, test_cases, context.language
        )
        if not wrapper_code:
            result["execution"]["status"] = "skipped"
            return result
            
        # 3. Determine run command
        lang = context.language.lower()
        cmd = []
        suffix = ""
        
        if "python" in lang:
            # Use current python executable to ensure environment compatibility
            cmd = [sys.executable]
            suffix = ".py"
        elif "javascript" in lang or "js" in lang:
            cmd = ["node"]
            suffix = ".js"
            # Verify if node is available on system
            try:
                subprocess.run(["node", "--version"], capture_output=True, check=True)
            except Exception:
                result["execution"] = {
                    "status": "failed",
                    "tests_run": len(test_cases),
                    "tests_passed": 0,
                    "failures": [{
                        "test_index": 0,
                        "input": {},
                        "expected": {},
                        "actual": None,
                        "error": "NodeJS runtime not found on this system. Cannot run JavaScript code."
                    }]
                }
                return result
        else:
            result["execution"]["status"] = "unsupported_language"
            return result
            
        # 4. Write to temp file and run
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                f.write(wrapper_code)
                
            # Run command with 2-second timeout to catch infinite loops
            run_res = subprocess.run(
                cmd + [temp_path],
                capture_output=True,
                text=True,
                timeout=3.0
            )
            
            if run_res.returncode == 0:
                try:
                    # The script should output JSON on the last line
                    lines = run_res.stdout.strip().split('\n')
                    json_str = lines[-1] if lines else "{}"
                    execution_info = json.loads(json_str)
                    result["execution"] = execution_info
                except Exception as je:
                    result["execution"] = {
                        "status": "failed",
                        "tests_run": len(test_cases),
                        "tests_passed": 0,
                        "failures": [{
                            "test_index": 0,
                            "input": {},
                            "expected": {},
                            "actual": None,
                            "error": f"Failed to parse test runner output. Output: {run_res.stdout}. ParseError: {str(je)}"
                        }]
                    }
            else:
                # Syntax or runtime crash prior to printing output JSON
                stderr_output = run_res.stderr or run_res.stdout
                result["execution"] = {
                    "status": "failed",
                    "tests_run": len(test_cases),
                    "tests_passed": 0,
                    "failures": [{
                        "test_index": 0,
                        "input": {},
                        "expected": {},
                        "actual": None,
                        "error": f"Runtime Crash: {stderr_output.strip()}"
                    }]
                }
                
        except subprocess.TimeoutExpired:
            result["execution"] = {
                "status": "failed",
                "tests_run": len(test_cases),
                "tests_passed": 0,
                "failures": [{
                    "test_index": 0,
                    "input": {},
                    "expected": {},
                    "actual": None,
                    "error": "Time Limit Exceeded (Infinite Loop suspected)."
                }]
            }
        except Exception as ex:
            result["execution"] = {
                "status": "failed",
                "tests_run": len(test_cases),
                "tests_passed": 0,
                "failures": [{
                    "test_index": 0,
                    "input": {},
                    "expected": {},
                    "actual": None,
                    "error": f"Execution analyzer error: {str(ex)}"
                }]
            }
        finally:
            # Clean up temp file
            try:
                os.remove(temp_path)
            except Exception:
                pass
                
        return result
