import time
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
import structlog
from .database import RefinementSession
from .agents import orchestrator
from .schemas import RefinedProductRequirement, ProcessingStatus

logger = structlog.get_logger()

class RefinementService:
    
    @staticmethod
    async def create_refinement_session(db: Session, idea: str) -> RefinementSession:
        """Create a new refinement session in the database"""
        session = RefinementSession(
            original_idea=idea,
            status=ProcessingStatus.PENDING
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info("Created refinement session", session_id=session.id)
        return session
    
    @staticmethod
    async def process_refinement(
        db: Session, 
        session_id: int, 
        idea: str, 
        priority_focus: str = "balanced"
    ) -> Optional[RefinedProductRequirement]:
        """Process a refinement request and update the database"""
        
        start_time = time.time()
        
        # Update status to processing
        session = db.query(RefinementSession).filter(RefinementSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = ProcessingStatus.PROCESSING
        db.commit()
        
        try:
            logger.info("Starting refinement process", session_id=session_id, idea_length=len(idea))
            
            # Process with AI agents
            result = await orchestrator.refine_requirement(idea, priority_focus)
            
            # Calculate processing time
            processing_time = int(time.time() - start_time)
            
            # Update session with results
            session.refined_result = result.dict()
            session.status = ProcessingStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            session.processing_time_seconds = processing_time
            
            db.commit()
            
            logger.info(
                "Refinement completed successfully", 
                session_id=session_id, 
                processing_time=processing_time
            )
            
            return result
            
        except Exception as e:
            # Update session with error
            session.status = ProcessingStatus.FAILED
            session.error_message = str(e)
            session.completed_at = datetime.utcnow()
            
            db.commit()
            
            logger.error("Refinement failed", session_id=session_id, error=str(e))
            raise
    
    @staticmethod
    def get_session(db: Session, session_id: int) -> Optional[RefinementSession]:
        """Get a refinement session by ID"""
        return db.query(RefinementSession).filter(RefinementSession.id == session_id).first()
    
    @staticmethod
    def get_recent_sessions(db: Session, limit: int = 10) -> list[RefinementSession]:
        """Get recent refinement sessions"""
        return db.query(RefinementSession).order_by(RefinementSession.created_at.desc()).limit(limit).all()

refinement_service = RefinementService()
