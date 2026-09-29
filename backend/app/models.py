from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from backend.app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, default="learner")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    profile_entries = relationship("LearnerProfile", back_populates="user", cascade="all, delete-orphan")
    attempts = relationship("Attempt", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")

class LearnerProfile(Base):
    __tablename__ = "learner_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    concept = Column(String, index=True)  # e.g., 'hash_maps', 'complexity', 'arrays'
    mastery_percentage = Column(Float, default=50.0)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="profile_entries")

class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    problem_title = Column(String, index=True)
    code = Column(Text)
    language = Column(String)
    is_correct = Column(Boolean, default=False)
    time_complexity = Column(String, default="O(n^2)")
    space_complexity = Column(String, default="O(1)")
    hint_level_reached = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="attempts")

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String)  # 'user' or 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="chats")
