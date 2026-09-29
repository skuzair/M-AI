class TutorPolicy:
    """State transition logic for the tutor, separating strategy decisions from LLM generation."""
    
    def determine_strategy(
        self, 
        is_correct: bool, 
        current_complexity: str, 
        target_complexity: str, 
        current_hint_level: int, 
        code_changed: bool
    ) -> dict:
        """
        Decides the pedagogical action and next hint level.
        
        Args:
            is_correct: If the user's code passed tests.
            current_complexity: Time complexity estimate (e.g. 'O(n^2)').
            target_complexity: Optimal time complexity (e.g. 'O(n)').
            current_hint_level: Last hint level requested (1-4).
            code_changed: True if this is a fresh/modified attempt.
            
        Returns:
            dict: { "action": "debug"|"optimize"|"teach_back"|"congratulate", "next_hint_level": int }
        """
        # If student changed their code, reset progress back to hint level 1
        if code_changed:
            next_hint_level = 1
        else:
            next_hint_level = current_hint_level

        if not is_correct:
            return {
                "action": "debug",
                "next_hint_level": next_hint_level
            }
            
        # Code is correct. Check if it's optimal.
        # Two Sum optimal is O(n). If it is O(n^2), we guide them to optimize.
        is_optimal = current_complexity == target_complexity or current_complexity == "O(n)"
        
        if is_optimal:
            return {
                "action": "teach_back",
                "next_hint_level": 4  # Teach-back uses max level
            }
        else:
            return {
                "action": "optimize",
                "next_hint_level": next_hint_level
            }
