from sqlalchemy.orm import Session
from backend.app.tutor.analysis import run_analysis_pipeline, AnalysisContext
from backend.app.tutor.policy import TutorPolicy
from backend.app.tutor.llm_provider import GrokProvider, GroqProvider, DemoFallbackProvider
from backend.app.tutor.learner_model import LearnerModelManager
from backend.app.config import settings
from backend.app.models import Attempt
import json

class TutorOrchestrator:
    """Orchestrates code analysis, tutoring policy, LLM prompt engineering, and learner updates."""
    
    def __init__(self):
        self.policy = TutorPolicy()
        if settings.ACTIVE_PROVIDER == "grok":
            self.llm = GrokProvider()
        elif settings.ACTIVE_PROVIDER == "groq":
            self.llm = GroqProvider()
        else:
            self.llm = DemoFallbackProvider()

    def process_attempt(self, db: Session, context: AnalysisContext) -> dict:
        # 1. Fetch user context
        user = LearnerModelManager.get_or_create_user(db, "learner")
        
        # 2. Detect if code has changed from last attempt
        last_attempt = db.query(Attempt).filter(
            Attempt.user_id == user.id,
            Attempt.problem_title == context.problem_title
        ).order_by(Attempt.created_at.desc()).first()
        
        code_changed = True
        if last_attempt and last_attempt.code.strip() == context.code.strip():
            code_changed = False
            
        # 3. Run generic + adapter analysis pipeline
        analysis_result = run_analysis_pipeline(context)
        
        # 4. Extract tutor state parameters
        tutor_state = context.tutor_state or {}
        current_mode = tutor_state.get("mode", "debug")
        current_hint_level = tutor_state.get("hint_level", 1)
        
        # 5. Consult tutoring policy
        is_correct = analysis_result.execution.get("status") == "passed"
        time_comp = analysis_result.complexity.get("time", "O(n^2)")
        space_comp = analysis_result.complexity.get("space", "O(1)")
        target_complexity = "O(n)"
        
        strategy = self.policy.determine_strategy(
            is_correct=is_correct,
            current_complexity=time_comp,
            target_complexity=target_complexity,
            current_hint_level=current_hint_level,
            code_changed=code_changed
        )
        
        action = strategy["action"]
        next_hint_level = strategy["next_hint_level"]
        
        # Map policy action back to user interface mode
        new_mode = current_mode
        if action == "optimize":
            new_mode = "optimize"
        elif action == "teach_back":
            new_mode = "teach_back"
        elif action == "debug":
            new_mode = "debug"
            
        # 6. Build structured context for LLM prompt
        profile_data = LearnerModelManager.get_profile(db, user.id)
        
        prompt_context = {
            "problem": {
                "title": context.problem_title,
                "description": context.problem_description,
                "constraints": context.constraints,
                "examples": context.examples
            },
            "student": {
                "skill_level": "intermediate",
                "known_weaknesses": ["optimization reasoning"],
                "previous_attempts": []
            },
            "code": context.code,
            "analysis": analysis_result.dict(),
            "tutor_state": {
                "mode": new_mode,
                "hint_level": next_hint_level,
                "previous_hints": []
            }
        }
        
        # 7. Query Provider
        llm_response = self.llm.generate_tutor_response(prompt_context)
        
        # 8. Log the attempt
        LearnerModelManager.log_attempt(
            db=db,
            user_id=user.id,
            problem_title=context.problem_title,
            code=context.code,
            language=context.language,
            is_correct=is_correct,
            time_comp=time_comp,
            space_comp=space_comp,
            hint_level=next_hint_level
        )
        
        # 9. Process learning signal
        learning_signal = llm_response.get("learning_signal", {})
        if learning_signal:
            concept = learning_signal.get("concept")
            sig = learning_signal.get("signal")
            if concept and sig:
                delta = 0.0
                if sig == "mastered":
                    delta = 10.0
                elif sig == "improving":
                    delta = 5.0
                elif sig == "needs_practice":
                    delta = -2.0
                
                # Apply delta to DB
                LearnerModelManager.update_mastery(db, user.id, concept, delta)
                
        # 10. Fetch updated model state and recommendations
        updated_profile = LearnerModelManager.get_profile(db, user.id)
        rec_info = LearnerModelManager.get_recommendation(db, user.id)
        
        return {
            "analysis": analysis_result.dict(),
            "tutor_response": llm_response.get("response", ""),
            "tutor_state": {
                "mode": new_mode,
                "hint_level": next_hint_level,
            },
            "diagnosis": llm_response.get("diagnosis", {}),
            "profile": updated_profile,
            "recommendation": rec_info
        }

    def process_teach_back(self, db: Session, user_answer: str) -> dict:
        user = LearnerModelManager.get_or_create_user(db, "learner")
        
        # Formulate a context mimicking a teach back step
        prompt_context = {
            "analysis": {
                "execution": {"status": "passed"},
                "complexity": {"time": "O(n)", "space": "O(n)"},
                "signals": [{"type": "hash_lookup", "confidence": 1.0}]
            },
            "tutor_state": {
                "mode": "teach_back",
                "hint_level": 4
            },
            "teach_back_answer": user_answer
        }
        
        llm_response = self.llm.generate_tutor_response(prompt_context)
        
        # Process learning signals
        learning_signal = llm_response.get("learning_signal", {})
        if learning_signal:
            concept = learning_signal.get("concept", "complexity")
            sig = learning_signal.get("signal", "improving")
            
            # Significant boost upon correct explanation
            if sig == "mastered":
                # Boost both complexity and hash maps
                LearnerModelManager.update_mastery(db, user.id, "complexity", 10.0)
                LearnerModelManager.update_mastery(db, user.id, "hash_maps", 9.0)
            elif sig == "improving":
                LearnerModelManager.update_mastery(db, user.id, "complexity", 5.0)
                
        updated_profile = LearnerModelManager.get_profile(db, user.id)
        rec_info = LearnerModelManager.get_recommendation(db, user.id)
        
        return {
            "feedback": llm_response.get("response", ""),
            "profile": updated_profile,
            "recommendation": rec_info
        }

    def process_chat(self, db: Session, context: AnalysisContext, message: str, conversation_history: list) -> dict:
        user = LearnerModelManager.get_or_create_user(db, "learner")
        
        # 1. Run generic + adapter analysis pipeline on current code
        analysis_result = run_analysis_pipeline(context)
        
        # 2. Build structured context for LLM prompt
        prompt_context = {
            "problem": {
                "title": context.problem_title,
                "description": context.problem_description,
                "constraints": context.constraints,
                "examples": context.examples
            },
            "code": context.code,
            "language": context.language,
            "analysis": analysis_result.dict(),
            "tutor_state": context.tutor_state or {},
            "chat_message": message,
            "conversation_history": conversation_history
        }
        
        # 3. Query LLM
        llm_response = self.llm.generate_chat_response(prompt_context)
        
        return {
            "response": llm_response.get("response", ""),
            "tutor_state": context.tutor_state or {}
        }
