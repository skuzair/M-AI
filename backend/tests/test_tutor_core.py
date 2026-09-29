import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models import User, LearnerProfile, Attempt
from backend.app.tutor.analysis import run_analysis_pipeline, AnalysisContext
from backend.app.tutor.orchestrator import TutorOrchestrator
from backend.app.tutor.learner_model import LearnerModelManager
from backend.app.tutor.policy import TutorPolicy
from backend.app.tutor.llm_provider import DemoFallbackProvider

# Use in-memory SQLite database for test runs
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_generic_analysis_pipeline_non_twosum():
    """Verify that the analysis pipeline analyzes non-Two-Sum problems correctly."""
    # Test case: Python code for 'Reverse String' containing a nested loop (quadratic complexity)
    context = AnalysisContext(
        problem_title="Reverse String",
        problem_description="Reverse a string in place.",
        constraints=["1 <= s.length <= 10^5"],
        examples=[],
        code="""
def reverseString(s):
    # Buggy nested loop implementation resulting in quadratic runtime
    for i in range(len(s)):
        for j in range(len(s)):
            pass
""",
        language="python"
    )
    
    result = run_analysis_pipeline(context)
    
    # Assert syntax is valid
    assert result.syntax["valid"] is True
    # Assert nested loops were detected by StaticAnalyzer
    signals = [s["type"] for s in result.signals]
    assert "nested_iteration" in signals
    # Assert ComplexityAnalyzer estimated O(n^2)
    assert result.complexity["time"] == "O(n^2)"

def test_tutor_policy_transitions():
    """Verify that TutorPolicy makes pure state decisions based on correctness and complexity."""
    policy = TutorPolicy()
    
    # 1. Correct but non-optimal solution should trigger "optimize" strategy
    strategy_opt = policy.determine_strategy(
        is_correct=True,
        current_complexity="O(n^2)",
        target_complexity="O(n)",
        current_hint_level=1,
        code_changed=False
    )
    assert strategy_opt["action"] == "optimize"
    assert strategy_opt["next_hint_level"] == 1
    
    # 2. Correct and optimal solution should trigger "teach_back" strategy
    strategy_tb = policy.determine_strategy(
        is_correct=True,
        current_complexity="O(n)",
        target_complexity="O(n)",
        current_hint_level=1,
        code_changed=False
    )
    assert strategy_tb["action"] == "teach_back"
    assert strategy_tb["next_hint_level"] == 4
    
    # 3. Incorrect solution should trigger "debug" strategy
    strategy_dbg = policy.determine_strategy(
        is_correct=False,
        current_complexity="O(n^2)",
        target_complexity="O(n)",
        current_hint_level=1,
        code_changed=False
    )
    assert strategy_dbg["action"] == "debug"

def test_signal_based_fallback_non_twosum():
    """Verify that DemoFallbackProvider makes signal-based recommendations for any problem."""
    provider = DemoFallbackProvider()
    
    # Context for a generic problem "Three Sum" with quadratic nested loops
    prompt_context = {
        "analysis": {
            "execution": {"status": "passed"},
            "complexity": {"time": "O(n^2)", "space": "O(1)"},
            "signals": [{"type": "nested_iteration", "confidence": 0.95}]
        },
        "tutor_state": {
            "mode": "optimize",
            "hint_level": 1
        }
    }
    
    response = provider.generate_tutor_response(prompt_context)
    
    # Assert diagnosis is correct and not hardcoded specifically to Two Sum title
    assert response["diagnosis"]["observed_issue"] == "Nested loop creates O(n^2) runtime complexity."
    assert " O(n^2)" in response["diagnosis"]["observed_issue"]
    # Check that it suggests optimization hints
    assert "Your solution checks pairs repeatedly." in response["response"]

def test_learner_model_updates(db_session):
    """Verify that LearnerModelManager handles seeding, logging, and mastery tracking."""
    # 1. Create a user
    user = LearnerModelManager.get_or_create_user(db_session, "test_student")
    assert user.username == "test_student"
    
    # Check default seeded profiles
    profile = LearnerModelManager.get_profile(db_session, user.id)
    assert profile["hash_maps"] == 72.0
    assert profile["complexity"] == 54.0
    
    # 2. Update mastery
    new_mastery = LearnerModelManager.update_mastery(db_session, user.id, "complexity", 10.0)
    assert new_mastery == 64.0
    
    # 3. Check recommended next concept
    rec = LearnerModelManager.get_recommendation(db_session, user.id)
    assert rec["recommended_concept"] == "Sliding Window"
    
    # Increase complexity mastery to exceed recommendation threshold
    LearnerModelManager.update_mastery(db_session, user.id, "complexity", 10.0)
    rec2 = LearnerModelManager.get_recommendation(db_session, user.id)
    # Recommended concept should switch to Two Pointers
    assert rec2["recommended_concept"] == "Two Pointers"
