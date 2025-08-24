from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, ForeignKey, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import structlog
from .config import settings

logger = structlog.get_logger()

# Enhanced database engine configuration
def create_database_engine():
    """Create database engine with enhanced configuration"""
    try:
        # Determine if we're using PostgreSQL or SQLite
        if settings.database_url.startswith('postgresql'):
            # PostgreSQL configuration
            engine = create_engine(
                settings.database_url,
                poolclass=QueuePool,
                pool_pre_ping=settings.database_pool_pre_ping,
                pool_recycle=settings.database_pool_recycle,
                pool_size=settings.database_pool_size,
                max_overflow=settings.database_max_overflow,
                pool_timeout=30,
                echo=settings.debug
            )
        else:
            # SQLite configuration (for development)
            engine = create_engine(
                settings.database_url,
                pool_pre_ping=settings.database_pool_pre_ping,
                pool_recycle=settings.database_pool_recycle,
                echo=settings.debug
            )
        
        logger.info("Database engine created successfully", 
                   database_url=settings.database_url.split('@')[0] + '@***' if '@' in settings.database_url else settings.database_url)
        return engine
    except Exception as e:
        logger.error("Failed to create database engine", error=str(e))
        raise

engine = create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RefinementSession(Base):
    __tablename__ = "refinement_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    original_idea = Column(Text, nullable=False)
    refined_result = Column(JSON, nullable=True)
    status = Column(String(50), default="pending", index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)
    priority_focus = Column(String(50), nullable=True)
    
    # Add relationships
    agent_responses = relationship("AgentResponse", back_populates="session", cascade="all, delete-orphan")
    debates = relationship("AgentDebate", back_populates="session", cascade="all, delete-orphan")
    
    # Add indexes for better performance
    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),
        Index('idx_priority_focus', 'priority_focus'),
    )

class AgentResponse(Base):
    __tablename__ = "agent_responses"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("refinement_sessions.id"), index=True)
    agent_type = Column(String(50), nullable=False, index=True)
    response_data = Column(JSON, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    confidence_score = Column(Integer, nullable=True)  # Store as percentage (0-100)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Add relationship
    session = relationship("RefinementSession", back_populates="agent_responses")
    
    # Add indexes for better performance
    __table_args__ = (
        Index('idx_session_agent', 'session_id', 'agent_type'),
        Index('idx_confidence_score', 'confidence_score'),
    )

class AgentDebate(Base):
    __tablename__ = "agent_debates"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("refinement_sessions.id"), index=True)
    debate_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Add relationship
    session = relationship("RefinementSession", back_populates="debates")

def get_db():
    """Enhanced database session with error handling"""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error("Database error occurred", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """Initialize database tables with error handling"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error("Failed to create database tables", error=str(e))
        raise

def check_database_connection():
    """Check database connectivity"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            connection.commit()
        return True
    except Exception as e:
        logger.error("Database connection check failed", error=str(e))
        return False

# Initialize database on import
init_database()
