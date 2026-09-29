from sqlalchemy.orm import Session
from backend.app.models import User, LearnerProfile, Attempt
import datetime

class LearnerModelManager:
    """Manages the learner's profile, concept mastery tracking, and recommendations."""

    @staticmethod
    def get_or_create_user(db: Session, username: str = "learner") -> User:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            user = User(username=username)
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Seed default concepts with baseline masteries
            concepts = {
                "hash_maps": 72.0,     # Preseed close to demo start state (72% -> 81%)
                "complexity": 54.0,    # Preseed close to demo start state (54% -> 64%)
                "arrays": 60.0,
                "two_pointers": 50.0
            }
            for concept, mastery in concepts.items():
                profile = LearnerProfile(
                    user_id=user.id, 
                    concept=concept, 
                    mastery_percentage=mastery
                )
                db.add(profile)
            db.commit()
            db.refresh(user)
        return user

    @staticmethod
    def get_profile(db: Session, user_id: int) -> dict:
        profiles = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).all()
        return {p.concept: round(p.mastery_percentage, 1) for p in profiles}

    @staticmethod
    def update_mastery(db: Session, user_id: int, concept: str, delta: float) -> float:
        profile = db.query(LearnerProfile).filter(
            LearnerProfile.user_id == user_id, 
            LearnerProfile.concept == concept
        ).first()
        if profile:
            profile.mastery_percentage = min(100.0, max(0.0, profile.mastery_percentage + delta))
            db.commit()
            return round(profile.mastery_percentage, 1)
        return 50.0

    @staticmethod
    def get_recommendation(db: Session, user_id: int) -> dict:
        profile = LearnerModelManager.get_profile(db, user_id)
        
        # Based on mastery levels or history, make recommendations
        # Two Sum demo path focuses on hash maps and complexity
        # If complexity is still relatively low or just updated, recommend Sliding Window
        complexity_mastery = profile.get("complexity", 50.0)
        
        if complexity_mastery < 65.0:
            return {
                "recommended_concept": "Sliding Window",
                "recommended_problem": "Longest Substring Without Repeating Characters",
                "explanation": (
                    "You successfully applied hash-based lookup, but your recent attempts still rely on "
                    "repeated traversal. Sliding Window is recommended because it builds on your current "
                    "understanding of Hash Maps while strengthening efficient single-pass array traversal."
                )
            }
        else:
            return {
                "recommended_concept": "Two Pointers",
                "recommended_problem": "Container With Most Water",
                "explanation": (
                    "To further optimize space complexity from O(N) to O(1), practicing the Two Pointers "
                    "pattern will help you traverse bounds concurrently without storing elements."
                )
            }
            
    @staticmethod
    def log_attempt(
        db: Session, 
        user_id: int, 
        problem_title: str, 
        code: str, 
        language: str, 
        is_correct: bool, 
        time_comp: str, 
        space_comp: str, 
        hint_level: int
    ) -> Attempt:
        attempt = Attempt(
            user_id=user_id,
            problem_title=problem_title,
            code=code,
            language=language,
            is_correct=is_correct,
            time_complexity=time_comp,
            space_complexity=space_comp,
            hint_level_reached=hint_level
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt
