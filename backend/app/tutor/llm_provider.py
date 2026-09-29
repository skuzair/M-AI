import httpx
import json
from typing import Dict, Any, Optional
from backend.app.config import settings

class LLMProvider:
    """Interface for LLM service providers."""
    def generate_tutor_response(self, prompt_context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()

    def generate_chat_response(self, prompt_context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError()

class GrokProvider(LLMProvider):
    """xAI Grok API Provider."""
    
    def generate_tutor_response(self, prompt_context: Dict[str, Any]) -> Dict[str, Any]:
        if not settings.GROK_API_KEY:
            raise ValueError("GROK_API_KEY environment variable is not configured.")
            
        print(f"[LLM] Querying Grok API using model {settings.GROK_MODEL}...")
        headers = {
            "Authorization": f"Bearer {settings.GROK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        system_prompt = (
            "You are Antigravity, a premium AI Coding Tutor. Your core pedagogical philosophy is to help "
            "the student understand and solve problems independently without handing them the solution directly.\n\n"
            "You will be given a JSON context containing:\n"
            "1. problem: title, description, constraints.\n"
            "2. student: skill level, weaknesses, previous attempts.\n"
            "3. code: current submission.\n"
            "4. analysis: syntax errors, test execution outcomes, static patterns, and complexity.\n"
            "5. tutor_state: mode (optimize/debug), current hint level, and previous hints.\n\n"
            "Your output MUST be a valid JSON object matching this schema:\n"
            "{\n"
            "  \"diagnosis\": {\n"
            "    \"observed_issue\": \"string describing what happens in the code (observed fact)\",\n"
            "    \"likely_conceptual_gap\": \"string representing inferred gap (e.g. hash maps, loops) with cautious language\",\n"
            "    \"reasoning\": \"explanation of your inference\",\n"
            "    \"confidence\": 0.0 to 1.0\n"
            "  },\n"
            "  \"teaching_strategy\": {\n"
            "    \"type\": \"progressive_hint\" | \"teach_back\" | \"congratulate\",\n"
            "    \"level\": integer (1 to 4)\n"
            "  },\n"
            "  \"response\": \"Your markdown response to the student, offering guidance at the current hint level without spoiling code. Explain concepts using real-world analogies where helpful.\",\n"
            "  \"learning_signal\": {\n"
            "    \"concept\": \"hash_maps\" | \"complexity\" | \"arrays\" | \"pointers\",\n"
            "    \"signal\": \"needs_practice\" | \"improving\" | \"mastered\"\n"
            "  }\n"
            "}"
        )
        
        payload = {
            "model": settings.GROK_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(prompt_context)}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(
                    f"{settings.GROK_API_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )
                res.raise_for_status()
                response_data = res.json()
                content = response_data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            print(f"[LLM] Grok call failed: {str(e)}. Falling back to DemoFallbackProvider.")
            # Fall back to DemoFallbackProvider internally on api error
            fallback = DemoFallbackProvider()
            return fallback.generate_tutor_response(prompt_context)

    def generate_chat_response(self, prompt_context: Dict[str, Any]) -> Dict[str, Any]:
        if not settings.GROK_API_KEY:
            raise ValueError("GROK_API_KEY environment variable is not configured.")
            
        print(f"[LLM] Querying Grok API for chat...")
        headers = {
            "Authorization": f"Bearer {settings.GROK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        system_prompt = (
            "You are Antigravity, a premium AI Coding Tutor. Your core pedagogical philosophy is to help "
            "the student understand concepts and fix issues themselves without handing them the solution directly.\n\n"
            "The student has asked a question in the chat: '{chat_message}'\n"
            "You will be given a JSON context containing:\n"
            "1. problem: title, description, constraints.\n"
            "2. code: current submission.\n"
            "3. analysis: syntax errors, test execution outcomes, static patterns, complexity.\n"
            "4. tutor_state: mode, current hint level.\n"
            "5. conversation_history: list of past messages.\n\n"
            "Answer the student's question concisely, using markdown. Focus on guidance and conceptual explanation. "
            "Never provide full code solutions unless requested, and even then, favor code snippets and pseudocode.\n\n"
            "Your output MUST be a valid JSON object matching this schema:\n"
            "{{\n"
            "  \"response\": \"Your markdown formatted pedagogical response to the student\"\n"
            "}}"
        )
        
        payload = {
            "model": settings.GROK_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt.format(chat_message=prompt_context.get("chat_message", ""))},
                {"role": "user", "content": json.dumps(prompt_context)}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(
                    f"{settings.GROK_API_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )
                res.raise_for_status()
                response_data = res.json()
                content = response_data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            print(f"[LLM] Grok chat failed: {str(e)}. Falling back to DemoFallbackProvider.")
            fallback = DemoFallbackProvider()
            return fallback.generate_chat_response(prompt_context)

class GroqProvider(LLMProvider):
    """Groq API Provider (OpenAI compatible wrapper)."""
    
    def generate_tutor_response(self, prompt_context: Dict[str, Any]) -> Dict[str, Any]:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")
            
        print(f"[LLM] Querying Groq API using model {settings.GROQ_MODEL}...")
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        system_prompt = (
            "You are Antigravity, a premium AI Coding Tutor. Your core pedagogical philosophy is to help "
            "the student understand and solve problems independently without handing them the solution directly.\n\n"
            "You will be given a JSON context containing:\n"
            "1. problem: title, description, constraints.\n"
            "2. student: skill level, weaknesses, previous attempts.\n"
            "3. code: current submission.\n"
            "4. analysis: syntax errors, test execution outcomes, static patterns, and complexity.\n"
            "5. tutor_state: mode (optimize/debug), current hint level, and previous hints.\n\n"
            "Your output MUST be a valid JSON object matching this schema:\n"
            "{\n"
            "  \"diagnosis\": {\n"
            "    \"observed_issue\": \"string describing what happens in the code (observed fact)\",\n"
            "    \"likely_conceptual_gap\": \"string representing inferred gap (e.g. hash maps, loops) with cautious language\",\n"
            "    \"reasoning\": \"explanation of your inference\",\n"
            "    \"confidence\": 0.0 to 1.0\n"
            "  },\n"
            "  \"teaching_strategy\": {\n"
            "    \"type\": \"progressive_hint\" | \"teach_back\" | \"congratulate\",\n"
            "    \"level\": integer (1 to 4)\n"
            "  },\n"
            "  \"response\": \"Your markdown response to the student, offering guidance at the current hint level without spoiling code. Explain concepts using real-world analogies where helpful.\",\n"
            "  \"learning_signal\": {\n"
            "    \"concept\": \"hash_maps\" | \"complexity\" | \"arrays\" | \"pointers\",\n"
            "    \"signal\": \"needs_practice\" | \"improving\" | \"mastered\"\n"
            "  }\n"
            "}"
        )
        
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(prompt_context)}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(
                    f"{settings.GROQ_API_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )
                res.raise_for_status()
                response_data = res.json()
                content = response_data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            print(f"[LLM] Groq call failed: {str(e)}. Falling back to DemoFallbackProvider.")
            # Fall back to DemoFallbackProvider internally on api error
            fallback = DemoFallbackProvider()
            return fallback.generate_tutor_response(prompt_context)

    def generate_chat_response(self, prompt_context: Dict[str, Any]) -> Dict[str, Any]:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY environment variable is not configured.")
            
        print(f"[LLM] Querying Groq API for chat...")
        headers = {
            "Authorization": f"Bearer {settings.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        system_prompt = (
            "You are Antigravity, a premium AI Coding Tutor. Your core pedagogical philosophy is to help "
            "the student understand concepts and fix issues themselves without handing them the solution directly.\n\n"
            "The student has asked a question in the chat: '{chat_message}'\n"
            "You will be given a JSON context containing:\n"
            "1. problem: title, description, constraints.\n"
            "2. code: current submission.\n"
            "3. analysis: syntax errors, test execution outcomes, static patterns, complexity.\n"
            "4. tutor_state: mode, current hint level.\n"
            "5. conversation_history: list of past messages.\n\n"
            "Answer the student's question concisely, using markdown. Focus on guidance and conceptual explanation. "
            "Never provide full code solutions unless requested, and even then, favor code snippets and pseudocode. "
            "Always keep the response under 3 paragraphs if possible.\n\n"
            "Your output MUST be a valid JSON object matching this schema:\n"
            "{{\n"
            "  \"response\": \"Your markdown formatted pedagogical response to the student\"\n"
            "}}"
        )
        
        payload = {
            "model": settings.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt.format(chat_message=prompt_context.get("chat_message", ""))},
                {"role": "user", "content": json.dumps(prompt_context)}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(
                    f"{settings.GROQ_API_URL}/chat/completions",
                    headers=headers,
                    json=payload
                )
                res.raise_for_status()
                response_data = res.json()
                content = response_data["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as e:
            print(f"[LLM] Groq chat failed: {str(e)}. Falling back to DemoFallbackProvider.")
            fallback = DemoFallbackProvider()
            return fallback.generate_chat_response(prompt_context)

class DemoFallbackProvider(LLMProvider):
    """Signal-based mock fallback provider for reliable demo behavior."""
    
    def generate_tutor_response(self, prompt_context: Dict[str, Any]) -> Dict[str, Any]:
        print("[LLM] Using DemoFallbackProvider...")
        analysis = prompt_context.get("analysis", {})
        execution = analysis.get("execution", {})
        complexity = analysis.get("complexity", {})
        signals = analysis.get("signals", [])
        tutor_state = prompt_context.get("tutor_state", {})
        
        mode = tutor_state.get("mode", "debug")
        hint_level = tutor_state.get("hint_level", 1)
        
        # Determine signals
        signal_types = [s.get("type") for s in signals]
        has_nested = "nested_iteration" in signal_types or complexity.get("time") == "O(n^2)"
        has_hash_lookup = "hash_lookup" in signal_types or complexity.get("space") == "O(n)"
        
        # 1. Execution has failed (Bugs / compilation errors)
        if execution.get("status") == "failed":
            failures = execution.get("failures", [])
            err_msg = failures[0].get("error", "") if failures else "Test case failed."
            
            # Check for specific Two Sum reuse same index misconception
            if "same_element_reuse" in signal_types:
                response_text = (
                    "It looks like your code returns indices that point to the exact same element "
                    "(e.g., repeating the index of `3` when looking for a sum of `6`).\n\n"
                    "**Analogy:** Imagine trying to form a pair of socks but just holding the same single sock in both hands.\n\n"
                    "Think about how you can check that the indices of the two elements are distinct."
                )
                gap = "Element reuse misconception (not verifying index uniqueness)"
            else:
                response_text = f"Your code failed execution with error: `{err_msg}`. Take a close look at where your loop boundaries or variables are initialized."
                gap = "Runtime boundary issue or logical error"
                
            return {
                "diagnosis": {
                    "observed_issue": "Code crashes or fails validation.",
                    "likely_conceptual_gap": gap,
                    "reasoning": f"Execution analyzer output: {err_msg}",
                    "confidence": 0.85
                },
                "teaching_strategy": {
                    "type": "progressive_hint",
                    "level": hint_level
                },
                "response": response_text,
                "learning_signal": {
                    "concept": "arrays",
                    "signal": "needs_practice"
                }
            }

        # 2. Execution passed, but code is inefficient (O(N^2)) and mode is optimize
        if execution.get("status") == "passed" and has_nested:
            if hint_level == 1:
                response_text = (
                    "Your solution checks pairs repeatedly. Before changing the code, think about "
                    "what information you could remember while traversing the array.\n\n"
                    "**Analogy:** Imagine checking a guest list by walking through the entire party to look for each name, "
                    "versus having a clipboard at the door to register names as they arrive."
                )
            elif hint_level == 2:
                response_text = (
                    "To avoid the nested scan, what if you could look up whether you've already seen "
                    "the 'complement' (i.e., `target - num`) in a single step?\n\n"
                    "Which data structure allows you to lookup values in $O(1)$ average time?"
                )
            elif hint_level == 3:
                response_text = (
                    "Try using a Hash Map (dictionary in Python, `Map` in JavaScript).\n\n"
                    "For each number `x`, calculate `complement = target - x`. If `complement` is already in your map, "
                    "you've found the solution!"
                )
            else:
                response_text = (
                    "**Step-by-step Solution Walkthrough:**\n"
                    "1. Initialize an empty dictionary `seen = {}`.\n"
                    "2. Loop through `nums` with index `i` and value `num`.\n"
                    "3. Calculate `complement = target - num`.\n"
                    "4. If `complement` is in `seen`, return `[seen[complement], i]`.\n"
                    "5. Otherwise, store `num` with its index: `seen[num] = i`."
                )
                
            return {
                "diagnosis": {
                    "observed_issue": "Nested loop creates O(n^2) runtime complexity.",
                    "likely_conceptual_gap": "Using search loops instead of index lookbehind hashes",
                    "reasoning": "Loop depth is 2, creating quadratic runtime.",
                    "confidence": 0.90
                },
                "teaching_strategy": {
                    "type": "progressive_hint",
                    "level": hint_level
                },
                "response": response_text,
                "learning_signal": {
                    "concept": "hash_maps",
                    "signal": "needs_practice"
                }
            }
            
        # 3. Execution passed and code is optimized O(n)
        if execution.get("status") == "passed" and not has_nested:
            # Check if we are waiting for a teach-back response
            teach_back_answer = prompt_context.get("teach_back_answer")
            if teach_back_answer:
                # User has submitted their explanation. Let's evaluate it!
                answer_lower = teach_back_answer.lower()
                is_satisfactory = False
                
                # Check for keywords like "O(1)", "lookup", "space", "search", "time", "dictionary"
                if "o(1)" in answer_lower or "lookup" in answer_lower or "search" in answer_lower or "constant" in answer_lower:
                    if "space" in answer_lower or "memory" in answer_lower:
                        is_satisfactory = True
                        
                if is_satisfactory:
                    feedback = (
                        "**Spot on!** By using a Hash Map, we gain $O(1)$ average time complexity "
                        "for check-ups, which completely eliminates the nested loop (bringing overall time to $O(N)$). "
                        "The trade-off is $O(N)$ space complexity since we store numbers in memory. You've mastered this concept!"
                    )
                    sig = "mastered"
                else:
                    feedback = (
                        "You're on the right track, but remember that the Hash Map lets us look up the complement "
                        "in $O(1)$ average time rather than scanning the list. The trade-off is that we need $O(N)$ "
                        "memory (space) to store those elements. What do you think about that?"
                    )
                    sig = "improving"
                    
                return {
                    "diagnosis": {
                        "observed_issue": "Teach-back response submitted.",
                        "likely_conceptual_gap": "Refining trade-offs explanation" if not is_satisfactory else "No gaps detected",
                        "reasoning": f"Student explanation evaluation: '{teach_back_answer}'",
                        "confidence": 0.90
                    },
                    "teaching_strategy": {
                        "type": "teach_back_evaluation",
                        "level": 4
                    },
                    "response": feedback,
                    "learning_signal": {
                        "concept": "complexity",
                        "signal": sig
                    }
                }
            else:
                # Trigger the teach-back question
                return {
                    "diagnosis": {
                        "observed_issue": "Correct O(n) optimized solution submitted.",
                        "likely_conceptual_gap": "Awaiting explanation of complexity trade-offs",
                        "reasoning": "Solution passed tests and is O(n) complexity. Check student's depth of learning.",
                        "confidence": 0.95
                    },
                    "teaching_strategy": {
                        "type": "teach_back",
                        "level": 4
                    },
                    "response": (
                        "**Fantastic! Your solution is correct and optimal!**\n\n"
                        "To verify your understanding: **Why does using a Hash Map reduce the time complexity from $O(n^2)$ to $O(n)$, and what is the trade-off?**"
                    ),
                    "learning_signal": {
                        "concept": "complexity",
                        "signal": "improving"
                    }
                }
                
        # Default response fallback
        return {
            "diagnosis": {
                "observed_issue": "No specific pattern matches.",
                "likely_conceptual_gap": "Algorithmic layout check",
                "reasoning": "Default system state.",
                "confidence": 0.50
            },
            "teaching_strategy": {
                "type": "progressive_hint",
                "level": hint_level
            },
            "response": "How can I help you understand this problem better? Tell me what you're thinking so far.",
            "learning_signal": {
                "concept": "arrays",
                "signal": "needs_practice"
            }
        }

    def generate_chat_response(self, prompt_context: Dict[str, Any]) -> Dict[str, Any]:
        print("[LLM] Using DemoFallbackProvider for chat...")
        question = prompt_context.get("chat_message", "").lower()
        analysis = prompt_context.get("analysis", {})
        execution = analysis.get("execution", {})
        complexity = analysis.get("complexity", {})
        signals = [s.get("type") for s in analysis.get("signals", [])]
        
        response_text = "That's an interesting question. Let's think about how we store previously traversed values to avoid checking them again. What do you think?"
        
        if "why" in question and ("o(n^2)" in question or "n^2" in question or "complexity" in question or "slow" in question):
            if "nested_iteration" in signals or complexity.get("time") == "O(n^2)":
                response_text = (
                    "Your code has two nested loops iterating over the input array. "
                    "For each element in the outer loop, you run the inner loop, which checks other elements. "
                    "This results in $O(N \\times N) = O(N^2)$ operations."
                )
            else:
                response_text = "Your current code does not have nested loops and is actually $O(N)$."
                
        elif "hashmap" in question or "hash map" in question or "dictionary" in question or "why do we need" in question:
            response_text = (
                "A Hash Map allows us to check if an element (like the complement `target - x`) exists in $O(1)$ average time "
                "by indexing elements by key, which avoids repeatedly scanning the array."
            )
            
        elif "correct" in question or "pass" in question:
            if execution.get("status") == "passed":
                response_text = "Yes, your current solution passes the test cases."
            else:
                failures = execution.get("failures", [])
                err_msg = failures[0].get("error", "logical mismatch") if failures else "Test case failed."
                response_text = f"No, your solution failed or has errors. Check the error message: `{err_msg}`."
                
        elif "optimize" in question:
            if "nested_iteration" in signals or complexity.get("time") == "O(n^2)":
                response_text = (
                    "Yes! Instead of nested loops checking all pairs ($O(N^2)$), "
                    "we can use a Hash Map to locate the complement in a single pass ($O(N)$ time)."
                )
            else:
                response_text = "Your solution is already optimized to $O(N)$ time complexity."
                
        return {
            "response": response_text
        }
