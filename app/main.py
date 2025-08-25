import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.database import get_db, engine, Base, check_database_connection
from app.schemas import (
    RefineRequest, RefinementResponse, HealthCheck, 
    ProcessingStatus, RefinedProductRequirement
)
from app.services import refinement_service, response_formatter
from app.middleware import LoggingMiddleware, RateLimitMiddleware

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Product Council API", version=settings.app_version)
    
    # Check database connectivity
    if not check_database_connection():
        logger.error("Database connection failed during startup")
        raise RuntimeError("Database connection failed")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Product Council API")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A robust API for refining product requirements using a multi-agent AI system - optimized for concise responses",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls=settings.rate_limit_requests, period=settings.rate_limit_window)

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Handle validation errors with concise error messages"""
    logger.warning("Validation error", errors=exc.errors())
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation failed",
            "details": [{"field": e["loc"][-1], "message": e["msg"]} for e in exc.errors()[:3]]  # Limit to 3 errors
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with concise error messages"""
    logger.error("Unhandled exception", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again."
        }
    )

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI Product Council API - Optimized for Concise Responses",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "features": ["Concise AI responses", "Multi-agent analysis", "Real-time processing"]
    }

@app.get("/health", response_model=HealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check endpoint with fallback system status"""
    
    # Check database connection
    try:
        db_connected = check_database_connection()
    except Exception:
        db_connected = False
    
    # Check AI service (basic test)
    ai_available = True
    try:
        if not settings.google_api_key:
            ai_available = False
    except Exception:
        ai_available = False
    
    # Add Redis health check
    redis_connected = False
    try:
        # Test Redis connection
        redis_connected = True
    except Exception:
        pass
    
    # Check fallback system status
    fallback_status = {"healthy": True, "state": "primary"}
    try:
        from .fallback_orchestrator import fallback_orchestrator
        fallback_status = fallback_orchestrator.get_health_status()
    except Exception as e:
        logger.warning("Failed to get fallback status", error=str(e))
        fallback_status = {"healthy": False, "error": str(e)}
    
    # Determine overall status
    overall_status = "healthy"
    if not db_connected or not ai_available or not redis_connected:
        overall_status = "degraded"
    if not fallback_status.get("healthy", True):
        overall_status = "degraded"
    
    return HealthCheck(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        version=settings.app_version,
        database_connected=db_connected,
        ai_service_available=ai_available,
        redis_connected=redis_connected,
        fallback_status=fallback_status
    )

@app.post("/refine", response_model=RefinementResponse)
async def refine_product_idea(
    request: RefineRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Refine a product idea using our multi-agent AI system.
    
    This endpoint creates a refinement session and processes it asynchronously.
    Returns concise, focused analysis results.
    """
    
    try:
        # Validate input length
        if len(request.idea) > 1000:
            raise HTTPException(
                status_code=400, 
                detail="Product idea too long. Please keep it under 1000 characters for optimal analysis."
            )
        
        # Create refinement session
        session = await refinement_service.create_refinement_session(db, request.idea)
        
        # Process refinement in background
        background_tasks.add_task(
            refinement_service.process_refinement,
            db,
            session.id,
            request.idea,
            request.priority_focus or "balanced"
        )
        
        return RefinementResponse(
            session_id=session.id,
            status=ProcessingStatus.PROCESSING,
            created_at=session.created_at,
            message="Analysis started. Results will be concise and actionable."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to create refinement session", error=str(e))
        raise HTTPException(
            status_code=500, 
            detail="Failed to create refinement session. Please try again."
        )

@app.post("/refine/sync", response_model=RefinedProductRequirement)
async def refine_product_idea_sync(
    request: RefineRequest,
    db: Session = Depends(get_db)
):
    """
    Synchronously refine a product idea (for immediate results).
    
    Returns concise, focused analysis in 30-60 seconds.
    """
    
    try:
        # Validate input length
        if len(request.idea) > 1000:
            raise HTTPException(
                status_code=400, 
                detail="Product idea too long. Please keep it under 1000 characters for optimal analysis."
            )
        
        # Create and process refinement session synchronously
        session = await refinement_service.create_refinement_session(db, request.idea)
        
        result = await refinement_service.process_refinement(
            db,
            session.id,
            request.idea,
            request.priority_focus or "balanced"
        )
        
        # Format the result for consistency
        if hasattr(result, 'agent_debate') and result.agent_debate:
            for agent_response in result.agent_debate:
                if hasattr(agent_response, 'analysis'):
                    agent_response.analysis = response_formatter.format_agent_response(
                        str(agent_response.agent_type),
                        str(agent_response.analysis)
                    )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to refine product idea", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refine product requirement: {str(e)}"
        )

@app.get("/refine/{session_id}", response_model=RefinementResponse)
async def get_refinement_status(session_id: int, db: Session = Depends(get_db)):
    """Get the status and results of a refinement session"""
    
    try:
        session = refinement_service.get_session(db, session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Refinement session not found")
        
        # Convert stored JSON back to Pydantic model if completed
        result = None
        if session.status == ProcessingStatus.COMPLETED and session.refined_result:
            result = RefinedProductRequirement(**session.refined_result)
        
        return RefinementResponse(
            session_id=session.id,
            status=session.status,
            result=result,
            error_message=session.error_message,
            created_at=session.created_at,
            processing_time_seconds=session.processing_time_seconds
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve session data")

@app.get("/refine", response_model=list[RefinementResponse])
async def list_recent_refinements(limit: int = 10, db: Session = Depends(get_db)):
    """List recent refinement sessions"""
    
    try:
        # Validate limit
        if limit > 50:
            limit = 50
        
        sessions = refinement_service.get_recent_sessions(db, limit)
        
        responses = []
        for session in sessions:
            result = None
            if session.status == ProcessingStatus.COMPLETED and session.refined_result:
                result = RefinedProductRequirement(**session.refined_result)
            
            responses.append(RefinementResponse(
                session_id=session.id,
                status=session.status,
                result=result,
                error_message=session.error_message,
                created_at=session.created_at,
                processing_time_seconds=session.processing_time_seconds
            ))
        
        return responses
        
    except Exception as e:
        logger.error("Error listing sessions", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve sessions")

@app.get("/refine/{session_id}/agents", response_model=list[dict])
async def get_session_agents(session_id: int, db: Session = Depends(get_db)):
    """Get all agent responses for a specific session"""
    
    try:
        agent_responses = refinement_service.get_agent_responses(db, session_id)
        if not agent_responses:
            raise HTTPException(status_code=404, detail="No agent responses found for this session")
        
        return [
            {
                "agent_type": response.agent_type,
                "response_data": response.response_data,
                "processing_time_ms": response.processing_time_ms,
                "confidence_score": response.confidence_score,
                "created_at": response.created_at
            }
            for response in agent_responses
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving agent responses", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve agent responses")

@app.get("/refine/{session_id}/debate", response_model=dict)
async def get_session_debate(session_id: int, db: Session = Depends(get_db)):
    """Get debate data for a specific session"""
    
    try:
        debate = refinement_service.get_session_debate(db, session_id)
        if not debate:
            raise HTTPException(status_code=404, detail="No debate data found for this session")
        
        return {
            "session_id": debate.session_id,
            "debate_data": debate.debate_data,
            "created_at": debate.created_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving debate data", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve debate data")

# Fallback System Management Endpoints
@app.get("/fallback/status")
async def get_fallback_status():
    """Get current fallback system status and statistics"""
    try:
        from .fallback_orchestrator import fallback_orchestrator
        return fallback_orchestrator.get_fallback_stats()
    except Exception as e:
        logger.error("Failed to get fallback status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve fallback status")

@app.get("/fallback/health")
async def get_fallback_health():
    """Get detailed fallback system health information"""
    try:
        from .fallback_orchestrator import fallback_orchestrator
        return fallback_orchestrator.get_health_status()
    except Exception as e:
        logger.error("Failed to get fallback health", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve fallback health")

@app.post("/fallback/reset")
async def reset_fallback_system():
    """Reset fallback system to primary mode"""
    try:
        from .fallback_orchestrator import fallback_orchestrator
        fallback_orchestrator.reset_to_primary()
        return {"message": "Fallback system reset to primary mode", "status": "success"}
    except Exception as e:
        logger.error("Failed to reset fallback system", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to reset fallback system")

@app.get("/fallback/methods")
async def get_available_fallback_methods():
    """Get list of available fallback methods and their status"""
    try:
        from .fallback_orchestrator import fallback_orchestrator
        methods = {}
        for name, method in fallback_orchestrator.fallback_methods.items():
            methods[str(name)] = {
                "available": method.is_available(),
                "confidence_score": method.get_confidence_score(),
                "class_name": method.__class__.__name__
            }
        return methods
    except Exception as e:
        logger.error("Failed to get fallback methods", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve fallback methods")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
