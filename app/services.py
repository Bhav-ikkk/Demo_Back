import time
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
import structlog
from .database import RefinementSession, AgentResponse, AgentDebate
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
        """Process a refinement request using AI agents and store all data"""
        
        start_time = time.time()
        
        # Update status to processing
        session = db.query(RefinementSession).filter(RefinementSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = ProcessingStatus.PROCESSING
        db.commit()
        
        try:
            logger.info("Starting AI agent refinement process", session_id=session_id, idea_length=len(idea))
            
            # Use the AI orchestrator
            result = await orchestrator.refine_requirement(idea, priority_focus)
            
            # Calculate processing time
            processing_time = int(time.time() - start_time)
            
            # Store individual agent responses
            await RefinementService._store_agent_responses(db, session_id, result.agent_debate)
            
            # Store the final refined result
            session.refined_result = result.dict()
            session.status = ProcessingStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            session.processing_time_seconds = processing_time
            
            db.commit()
            
            logger.info(
                "AI refinement completed successfully", 
                session_id=session_id, 
                processing_time=processing_time,
                agent_count=len(result.agent_debate)
            )
            
            return result
            
        except Exception as e:
            # Update session with error
            session.status = ProcessingStatus.FAILED
            session.error_message = str(e)
            session.completed_at = datetime.utcnow()
            
            db.commit()
            
            logger.error("AI refinement failed", session_id=session_id, error=str(e))
            raise
    
    @staticmethod
    async def _store_agent_responses(db: Session, session_id: int, agent_debate: list):
        """Store individual agent responses in database"""
        try:
            for agent_feedback in agent_debate:
                # Create agent response record
                agent_response = AgentResponse(
                    session_id=session_id,
                    agent_type=agent_feedback.agent_name,
                    response_data={
                        "feedback": agent_feedback.feedback,
                        "confidence_score": agent_feedback.confidence_score,
                        "processing_time_ms": agent_feedback.processing_time_ms
                    },
                    processing_time_ms=agent_feedback.processing_time_ms,
                    confidence_score=int(agent_feedback.confidence_score * 100)  # Convert to percentage
                )
                
                db.add(agent_response)
            
            # Create debate record
            debate_record = AgentDebate(
                session_id=session_id,
                debate_data={
                    "agent_count": len(agent_debate),
                    "debate_summary": "Multi-agent analysis completed",
                    "consensus_level": "High",  # Could be calculated based on confidence scores
                    "debate_insights": [af.feedback[:200] + "..." for af in agent_debate]  # Truncated insights
                }
            )
            
            db.add(debate_record)
            db.commit()
            
            logger.info(f"Stored {len(agent_debate)} agent responses and debate data", session_id=session_id)
            
        except Exception as e:
            logger.error(f"Failed to store agent responses", session_id=session_id, error=str(e))
            # Don't fail the whole process if storage fails
            db.rollback()
    
    @staticmethod
    def get_session(db: Session, session_id: int) -> Optional[RefinementSession]:
        """Get a refinement session by ID with all related data"""
        return db.query(RefinementSession).filter(RefinementSession.id == session_id).first()
    
    @staticmethod
    def get_recent_sessions(db: Session, limit: int = 10) -> list[RefinementSession]:
        """Get recent refinement sessions with agent data"""
        return db.query(RefinementSession).order_by(RefinementSession.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_agent_responses(db: Session, session_id: int) -> list[AgentResponse]:
        """Get all agent responses for a session"""
        return db.query(AgentResponse).filter(AgentResponse.session_id == session_id).all()
    
    @staticmethod
    def get_session_debate(db: Session, session_id: int) -> Optional[AgentDebate]:
        """Get debate data for a session"""
        return db.query(AgentDebate).filter(AgentDebate.session_id == session_id).first()

refinement_service = RefinementService()
