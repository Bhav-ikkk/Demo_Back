from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from .config import settings

# Add connection pooling for PostgreSQL
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RefinementSession(Base):
    __tablename__ = "refinement_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    original_idea = Column(Text, nullable=False)
    refined_result = Column(JSON, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)
    
    # Add relationships
    agent_responses = relationship("AgentResponse", back_populates="session", cascade="all, delete-orphan")
    debates = relationship("AgentDebate", back_populates="session", cascade="all, delete-orphan")

class AgentResponse(Base):
    __tablename__ = "agent_responses"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("refinement_sessions.id"))
    agent_type = Column(String(50), nullable=False)
    response_data = Column(JSON, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    confidence_score = Column(Integer, nullable=True)  # Store as percentage (0-100)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Add relationship
    session = relationship("RefinementSession", back_populates="agent_responses")

class AgentDebate(Base):
    __tablename__ = "agent_debates"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("refinement_sessions.id"))
    debate_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Add relationship
    session = relationship("RefinementSession", back_populates="debates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)
