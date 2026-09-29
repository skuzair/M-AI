from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.app.database import engine, get_db, Base
from backend.app.tutor.analysis import AnalysisContext
from backend.app.tutor.orchestrator import TutorOrchestrator
from backend.app.tutor.learner_model import LearnerModelManager
from pydantic import BaseModel

# Initialize SQLite database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Coding Tutor API Layer")

# Allow Chrome Extension context to query the localhost API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = TutorOrchestrator()

class TeachBackRequest(BaseModel):
    user_answer: str

class ChatRequest(BaseModel):
    message: str
    problem_title: str
    code: str
    language: str
    tutor_state: dict
    conversation_history: list = []

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "AI Coding Tutor Backend Engine"
    }

@app.post("/api/analyze")
def analyze_attempt(context: AnalysisContext, db: Session = Depends(get_db)):
    try:
        result = orchestrator.process_attempt(db, context)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/teach-back")
def teach_back_submission(req: TeachBackRequest, db: Session = Depends(get_db)):
    try:
        result = orchestrator.process_teach_back(db, req.user_answer)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def handle_chat(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        context = AnalysisContext(
            problem_title=req.problem_title,
            problem_description="",
            code=req.code,
            language=req.language,
            tutor_state=req.tutor_state
        )
        result = orchestrator.process_chat(db, context, req.message, req.conversation_history)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profile")
def fetch_profile(db: Session = Depends(get_db)):
    try:
        user = LearnerModelManager.get_or_create_user(db, "learner")
        profile = LearnerModelManager.get_profile(db, user.id)
        recommendation = LearnerModelManager.get_recommendation(db, user.id)
        return {
            "profile": profile,
            "recommendation": recommendation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reset")
def reset_database(db: Session = Depends(get_db)):
    try:
        # Drop and recreate tables to seed a fresh learner profile
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        user = LearnerModelManager.get_or_create_user(db, "learner")
        profile = LearnerModelManager.get_profile(db, user.id)
        return {
            "status": "reset",
            "message": "SQLite database state cleared and reseeded successfully.",
            "profile": profile
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    from sqlalchemy import text
    from backend.app.config import settings
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
        
    return {
        "status": "ok",
        "llm_provider": settings.ACTIVE_PROVIDER,
        "grok_key_preview": settings.GROK_API_KEY[:6] + "..." if settings.GROK_API_KEY else "none",
        "database": db_status
    }

@app.get("/api/diagnostics")
def get_diagnostics():
    from backend.app.config import settings
    return {
        "llm_provider": settings.ACTIVE_PROVIDER,
        "llm_model": settings.GROQ_MODEL if settings.ACTIVE_PROVIDER == "groq" else (settings.GROK_MODEL if settings.ACTIVE_PROVIDER == "grok" else "fallback"),
        "database_url": settings.DATABASE_URL.split("://")[0] + "://...",
        "grok_api_key_configured": bool(settings.GROK_API_KEY),
        "groq_api_key_configured": bool(settings.GROQ_API_KEY)
    }

