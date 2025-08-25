import time
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Optional, List
import structlog

# --- Import your actual agents and database models ---
from .database import RefinementSession, AgentResponse
from .schemas import RefinedProductRequirement, ProcessingStatus, AgentFeedback
from .agents.product_manager import ProductManagerAgent
from .agents.engineer import EngineerAgent
from .agents.market_researcher import MarketResearcherAgent
from .agents.customer_researcher import CustomerResearcherAgent
from .agents.risk_analyst import RiskAnalystAgent
from .agents.designer import DesignerAgent
from .agents.enhanced_orchestrator import EnhancedOrchestrator

logger = structlog.get_logger()

class ResponseFormatter:
    """Service to format and standardize AI responses for consistency"""
    
    @staticmethod
    def format_agent_response(agent_type: str, raw_response: str) -> str:
        """Format agent response to be concise and consistent"""
        cleaned = " ".join(raw_response.split())
        
        max_lengths = {
            "market_researcher": 250,
            "customer_researcher": 250,
            "product_manager": 250,
            "risk_analyst": 250,
            "designer": 250,
            "engineer": 250
        }
        
        max_len = max_lengths.get(agent_type.lower(), 200)
        if len(cleaned) > max_len:
            cleaned = cleaned[:max_len-3] + "..."
        
        return cleaned

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
        """Process a refinement request using REAL AI agents and store all data"""
        
        start_time = time.time()
        
        session = db.query(RefinementSession).filter(RefinementSession.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        session.status = ProcessingStatus.PROCESSING
        session.priority_focus = priority_focus
        db.commit()
        
        try:
            logger.info("Starting REAL AI agent refinement process", session_id=session_id)
            
            # --- THIS IS THE CORE FIX: CALLING THE REAL AI AGENTS ---
            result = await RefinementService._run_real_ai_agents(idea, priority_focus)
            
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
            session.status = ProcessingStatus.FAILED
            session.error_message = str(e)
            session.completed_at = datetime.utcnow()
            db.commit()
            logger.error("AI refinement failed", session_id=session_id, error=str(e))
            raise

    @staticmethod
    async def _run_real_ai_agents(idea: str, priority_focus: str) -> RefinedProductRequirement:
        """
        Orchestrates the REAL AI agents, running them in parallel for maximum speed.
        """
        # Initialize agents
        product_manager = ProductManagerAgent()
        engineer = EngineerAgent()
        market_researcher = MarketResearcherAgent()
        customer_researcher = CustomerResearcherAgent()
        risk_analyst = RiskAnalystAgent()
        designer = DesignerAgent()
        orchestrator = EnhancedOrchestrator()

        # Run independent agents in parallel
        initial_tasks = [
            product_manager.run(idea),
            market_researcher.run(idea),
            customer_researcher.run(idea),
            designer.run(idea),
        ]
        
        initial_feedbacks = await asyncio.gather(*initial_tasks)
        pm_feedback_raw, market_feedback_raw, customer_feedback_raw, designer_feedback_raw = initial_feedbacks

        # Format the responses using your ResponseFormatter
        pm_feedback = ResponseFormatter.format_agent_response("product_manager", pm_feedback_raw)
        market_feedback = ResponseFormatter.format_agent_response("market_researcher", market_feedback_raw)
        customer_feedback = ResponseFormatter.format_agent_response("customer_researcher", customer_feedback_raw)
        designer_feedback = ResponseFormatter.format_agent_response("designer", designer_feedback_raw)

        # Run dependent agents
        engineer_feedback_raw = await engineer.run(pm_feedback)
        engineer_feedback = ResponseFormatter.format_agent_response("engineer", engineer_feedback_raw)

        risk_analyst_feedback_raw = await risk_analyst.run(f"PM Feedback: {pm_feedback}\nEngineer Feedback: {engineer_feedback}")
        risk_analyst_feedback = ResponseFormatter.format_agent_response("risk_analyst", risk_analyst_feedback_raw)

        # Run the final synthesizer
        final_result = await orchestrator.run(
            idea=idea,
            pm_feedback=pm_feedback,
            engineer_feedback=engineer_feedback,
            market_feedback=market_feedback,
            customer_feedback=customer_feedback,
            risk_analyst_feedback=risk_analyst_feedback,
            designer_feedback=designer_feedback
        )
        
        return final_result

    @staticmethod
    async def _store_agent_responses(db: Session, session_id: int, agent_debate: List[AgentFeedback]):
        """Store individual agent responses in database"""
        try:
            for agent_feedback in agent_debate:
                agent_response = AgentResponse(
                    session_id=session_id,
                    agent_type=agent_feedback.agent_name,
                    response_data={"feedback": agent_feedback.feedback}, # Simplified for clarity
                    created_at=datetime.utcnow()
                )
                db.add(agent_response)
            
            db.commit()
            logger.info("Stored agent responses", session_id=session_id, count=len(agent_debate))
            
        except Exception as e:
            logger.error("Failed to store agent responses", session_id=session_id, error=str(e))
            db.rollback()
            raise
    
    # --- Other static methods (get_session, etc.) remain the same ---
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

# Global service instances
refinement_service = RefinementService()
response_formatter = ResponseFormatter()
