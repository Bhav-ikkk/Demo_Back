import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from ..database import get_db, RefinementSession, AgentResponse, AgentDebate, CriticAnalysis
from ..models import SessionStatus, ProductAnalysisRequest, ProductAnalysisResponse
from .critic_orchestrator import critic_orchestrator
import structlog

logger = structlog.get_logger()

class EnhancedProductAnalysisService:
    """
    Enhanced service that integrates the Critic AI Orchestrator with database persistence
    and provides a complete product analysis workflow
    """
    
    async def create_analysis_session(
        self,
        request: ProductAnalysisRequest,
        db: Session
    ) -> ProductAnalysisResponse:
        """Create a new analysis session and run comprehensive product analysis"""
        
        # Create database session
        db_session = RefinementSession(
            original_idea=request.product_idea,
            status=SessionStatus.PROCESSING.value
        )
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        try:
            logger.info(f"Starting analysis session {db_session.id}")
            
            # Prepare context from request
            context = {
                "target_market": request.target_market,
                "budget_range": request.budget_range,
                "timeline": request.timeline,
                "specific_focus": request.specific_focus or []
            }
            
            # Run comprehensive analysis using critic orchestrator
            analysis_result = await critic_orchestrator.orchestrate_analysis(
                product_idea=request.product_idea,
                context=context,
                enable_debates=True
            )
            
            # Store agent responses in database
            await self._store_agent_responses(db_session.id, analysis_result, db)
            
            # Store critic analysis
            await self._store_critic_analysis(db_session.id, analysis_result, db)
            
            # Update session status
            db_session.status = SessionStatus.COMPLETED.value
            db_session.refined_result = {
                "overall_assessment": analysis_result.overall_assessment,
                "consensus_level": analysis_result.consensus_level,
                "final_recommendations": analysis_result.final_recommendations
            }
            db.commit()
            
            logger.info(f"Completed analysis session {db_session.id}")
            
            return ProductAnalysisResponse(
                session_id=db_session.id,
                status=SessionStatus.COMPLETED,
                agent_responses=[],  # Would be populated from database
                debates=[],  # Would be populated from database
                critic_analysis=analysis_result,
                processing_time=None,  # Would be calculated
                created_at=db_session.created_at
            )
            
        except Exception as e:
            logger.error(f"Error in analysis session {db_session.id}", error=str(e))
            
            # Update session with error
            db_session.status = SessionStatus.FAILED.value
            db_session.error_message = str(e)
            db.commit()
            
            raise
    
    async def _store_agent_responses(
        self,
        session_id: int,
        analysis_result: Any,
        db: Session
    ):
        """Store individual agent responses in database"""
        # This would store the actual agent responses
        # For now, creating placeholder entries
        pass
    
    async def _store_critic_analysis(
        self,
        session_id: int,
        analysis_result: Any,
        db: Session
    ):
        """Store critic analysis in database"""
        critic_analysis = CriticAnalysis(
            session_id=session_id,
            overall_assessment=analysis_result.overall_assessment,
            agent_performance_scores=analysis_result.agent_performance_scores,
            identified_conflicts=analysis_result.identified_conflicts,
            final_recommendations=analysis_result.final_recommendations,
            consensus_level=analysis_result.consensus_level
        )
        db.add(critic_analysis)
        db.commit()
    
    async def get_analysis_status(self, session_id: int, db: Session) -> Dict[str, Any]:
        """Get current status of an analysis session"""
        session = db.query(RefinementSession).filter(
            RefinementSession.id == session_id
        ).first()
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        return {
            "session_id": session.id,
            "status": session.status,
            "created_at": session.created_at,
            "completed_at": session.completed_at,
            "error_message": session.error_message
        }

# Global service instance
analysis_service = EnhancedProductAnalysisService()
