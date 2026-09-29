import os
import sys

# Append project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from dotenv import load_dotenv
# Load .env explicitly prior to importing settings
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.tutor.analysis import AnalysisContext
from backend.app.tutor.orchestrator import TutorOrchestrator
from backend.app.tutor.learner_model import LearnerModelManager
from backend.app.config import settings

def run_diagnostic():
    print("--- AI Coding Tutor Diagnostics ---")
    print(f"Loaded Settings: ACTIVE_PROVIDER={settings.ACTIVE_PROVIDER}")
    print(f"Grok Key Set: {bool(settings.GROK_API_KEY)} (starts with: {settings.GROK_API_KEY[:4] if settings.GROK_API_KEY else 'N/A'})")
    print(f"Groq Key Set: {bool(settings.GROQ_API_KEY)} (starts with: {settings.GROQ_API_KEY[:4] if settings.GROQ_API_KEY else 'N/A'})")
    print(f"Groq URL: {settings.GROQ_API_URL}")
    print(f"Groq Model: {settings.GROQ_MODEL}")

    # Set up in-memory DB
    engine = create_engine("sqlite:///:memory:")
    SessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Instantiate Orchestrator
    orchestrator = TutorOrchestrator()

    # 2. Construct Brute Force python attempt for Two Sum
    context = AnalysisContext(
        problem_title="Two Sum",
        problem_description="Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        constraints=["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9", "-10^9 <= target <= 10^9"],
        examples=[{"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]}],
        code="""
class Solution:
    def twoSum(self, nums, target):
        for i in range(len(nums)):
            for j in range(len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
""",
        language="python",
        tutor_state={"mode": "debug", "hint_level": 0}
    )

    print("\n[Step 1] Processing O(n^2) Brute Force Attempt...")
    res = orchestrator.process_attempt(db, context)
    
    print("\n--- Result ---")
    print(f"Correct: {res['analysis']['execution']['status']}")
    print(f"Complexity Time: {res['analysis']['complexity']['time']}")
    print(f"Detected Signals: {[s['type'] for s in res['analysis']['signals']]}")
    print(f"Tutor Mode State: {res['tutor_state']['mode']}")
    print(f"Tutor Response:\n{res['tutor_response']}\n")

    # 3. Simulate requesting next hint
    print("[Step 2] Requesting Progressive Hint...")
    context.tutor_state = {
        "mode": res["tutor_state"]["mode"],
        "hint_level": res["tutor_state"]["hint_level"] + 1
    }
    # Keep code identical
    res_hint = orchestrator.process_attempt(db, context)
    print(f"Tutor State Level: {res_hint['tutor_state']['hint_level']}")
    print(f"Tutor Response:\n{res_hint['tutor_response']}\n")

    # 4. Process O(n) Optimal Python solution
    print("[Step 3] Submitting Optimal Solution...")
    context_opt = AnalysisContext(
        problem_title="Two Sum",
        problem_description=context.problem_description,
        constraints=context.constraints,
        examples=context.examples,
        code="""
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for i, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], i]
            seen[num] = i
""",
        language="python",
        tutor_state={"mode": "optimize", "hint_level": 0}
    )
    
    res_opt = orchestrator.process_attempt(db, context_opt)
    print(f"Correct: {res_opt['analysis']['execution']['status']}")
    print(f"Complexity Time: {res_opt['analysis']['complexity']['time']}")
    print(f"Tutor Mode State: {res_opt['tutor_state']['mode']}")
    print(f"Tutor Response:\n{res_opt['tutor_response']}\n")

    # 5. Answer the teach back question
    if res_opt["tutor_state"]["mode"] == "teach_back":
        print("[Step 4] Submitting Teach-Back Answer...")
        res_tb = orchestrator.process_teach_back(db, "A hash map gives O(1) average lookup time so we only scan once. The trade-off is O(n) memory space.")
        print(f"Feedback:\n{res_tb['feedback']}\n")
        print(f"Profile Mastery: {res_tb['profile']}")
        print(f"Recommendation: {res_tb['recommendation']}")

    db.close()

if __name__ == "__main__":
    run_diagnostic()
