import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # xAI Grok Settings
    GROK_API_KEY: str = ""
    GROK_API_URL: str = "https://api.xai.com/v1"
    GROK_MODEL: str = "grok-2"
    
    # Groq Settings
    GROQ_API_KEY: str = ""
    GROQ_API_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.1-8b-instant"  # Stable, fast model on Groq supporting JSON mode
    
    DATABASE_URL: str = "sqlite:///./tutor.db"
    ACTIVE_PROVIDER: str = "fallback"  # 'grok', 'groq', or 'fallback'

    model_config = SettingsConfigDict(
        env_file=("backend/.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Check if keys are provided and auto-detect provider
if settings.GROK_API_KEY.startswith("gsk_"):
    # User provided a Groq key in the GROK_API_KEY field
    settings.GROQ_API_KEY = settings.GROK_API_KEY
    settings.ACTIVE_PROVIDER = "groq"
elif settings.GROQ_API_KEY:
    settings.ACTIVE_PROVIDER = "groq"
elif settings.GROK_API_KEY:
    settings.ACTIVE_PROVIDER = "grok"
else:
    settings.ACTIVE_PROVIDER = "fallback"

# Logging setup for development visibility
print(f"[Config] Selected Active LLM Provider: {settings.ACTIVE_PROVIDER}")
if settings.ACTIVE_PROVIDER == "groq":
    print(f"[Config] Using Groq Model: {settings.GROQ_MODEL}")
elif settings.ACTIVE_PROVIDER == "grok":
    print(f"[Config] Using Grok Model: {settings.GROK_MODEL}")
