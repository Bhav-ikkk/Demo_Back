import time
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional
import structlog
from app.database import RefinementSession, AgentResponse, AgentDebate
from app.schemas import RefinedProductRequirement, ProcessingStatus, AgentFeedback

logger = structlog.get_logger()

class ResponseFormatter:
    """Service to format and standardize AI responses for consistency"""
    
    @staticmethod
    def format_agent_response(agent_type: str, raw_response: str) -> str:
        """Format agent response to be concise and consistent"""
        # Remove excessive whitespace and newlines
        cleaned = " ".join(raw_response.split())
        
        # Limit length based on agent type
        max_lengths = {
            "market_researcher": 150,
            "customer_researcher": 120,
            "product_manager": 100,
            "risk_analyst": 100,
            "designer": 80,
            "engineer": 100
        }
        
        max_len = max_lengths.get(agent_type.lower(), 100)
        if len(cleaned) > max_len:
            cleaned = cleaned[:max_len-3] + "..."
        
        return cleaned
    
    @staticmethod
    def format_final_summary(agent_responses: list, debate_outcomes: list) -> str:
        """Create a concise final summary from all responses"""
        if not agent_responses:
            return "Analysis incomplete - no agent responses available."
        
        # Extract key points from each agent
        key_points = []
        for response in agent_responses:
            if hasattr(response, 'feedback'):
                key_points.append(f"{response.agent_name}: {response.feedback[:50]}")
        
        # Create concise summary
        summary = " | ".join(key_points[:3])  # Limit to 3 key points
        
        if len(summary) > 200:
            summary = summary[:197] + "..."
        
        return summary

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
        session.priority_focus = priority_focus
        db.commit()
        
        try:
            logger.info("Starting AI agent refinement process", session_id=session_id, idea_length=len(idea))
            
            # Create mock AI responses for now (will be replaced with real AI later)
            result = await RefinementService._create_mock_ai_response(idea, priority_focus)
            
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
    async def _create_mock_ai_response(idea: str, priority_focus: str) -> RefinedProductRequirement:
        """Create a mock AI response for testing - will be replaced with real AI later"""
        
        # Create mock agent responses
        agent_debate = [
            AgentFeedback(
                agent_name="Market Researcher",
                feedback=f"Market Analysis: {idea} shows strong potential. Estimated market size: $2-5B. Key competitors identified.",
                processing_time_ms=1200,
                confidence_score=0.85
            ),
            AgentFeedback(
                agent_name="Product Manager",
                feedback=f"Product Strategy: {idea} has good product-market fit (8/10). Focus on user experience and rapid iteration.",
                processing_time_ms=800,
                confidence_score=0.90
            ),
            AgentFeedback(
                agent_name="Engineer",
                feedback=f"Technical Assessment: {idea} is technically feasible. Recommend modern web stack with cloud infrastructure.",
                processing_time_ms=950,
                confidence_score=0.80
            )
        ]
        
        return RefinedProductRequirement(
            refined_requirement=f"AI-Enhanced: {idea}",
            key_changes_summary=[
                "Enhanced user experience with intuitive design",
                "Improved technical architecture for scalability",
                "Better market positioning and differentiation"
            ],
            user_stories=[
                "As a user, I want an intuitive interface, so that I can achieve my goals efficiently",
                "As a user, I want fast performance, so that I don't waste time waiting"
            ],
            technical_tasks=[
                "Implement responsive web design with mobile-first approach",
                "Setup scalable backend with cloud infrastructure",
                "Implement proper error handling and logging"
            ],
            agent_debate=agent_debate,
            priority_score=8,
            estimated_effort="Medium",
            risk_assessment="Low to medium risk. Key risks: market competition, technical complexity. Mitigation: MVP approach, user feedback loops."
        )
    
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
                    confidence_score=int(agent_feedback.confidence_score * 100),
                    created_at=datetime.utcnow()
                )
                
                db.add(agent_response)
            
            db.commit()
            logger.info("Stored agent responses", session_id=session_id, count=len(agent_debate))
            
        except Exception as e:
            logger.error("Failed to store agent responses", session_id=session_id, error=str(e))
            db.rollback()
            raise
    
    @staticmethod
    def get_session(db: Session, session_id: int) -> Optional[RefinementSession]:
        """Get a refinement session by ID"""
        return db.query(RefinementSession).filter(RefinementSession.id == session_id).first()
    
    @staticmethod
    def get_recent_sessions(db: Session, limit: int = 10) -> list:
        """Get recent refinement sessions"""
        return db.query(RefinementSession).order_by(
            RefinementSession.created_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_agent_responses(db: Session, session_id: int) -> list:
        """Get all agent responses for a session"""
        return db.query(AgentResponse).filter(
            AgentResponse.session_id == session_id
        ).order_by(AgentResponse.created_at).all()
    
    @staticmethod
    def get_session_debate(db: Session, session_id: int) -> Optional[AgentDebate]:
        """Get debate data for a session"""
        return db.query(AgentDebate).filter(
            AgentDebate.session_id == session_id
        ).first()

# Global service instances
refinement_service = RefinementService()
response_formatter = ResponseFormatter()
