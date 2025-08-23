import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime

from .config import settings
from .database import get_db, engine, Base
from .schemas import (
    RefineRequest, RefinementResponse, HealthCheck, 
    ProcessingStatus, RefinedProductRequirement
)
from .services import refinement_service
from .middleware import LoggingMiddleware, RateLimitMiddleware

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
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Product Council API")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A robust API for refining product requirements using a multi-agent AI system",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls=settings.rate_limit_requests, period=settings.rate_limit_window)

@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI Product Council API",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check endpoint"""
    
    # Check database connection
    try:
        db.execute("SELECT 1")
        db_connected = True
    except Exception:
        db_connected = False
    
    # Check AI service (basic test)
    ai_available = True
    try:
        if not settings.google_api_key:
            ai_available = False
    except Exception:
        ai_available = False
    
    return HealthCheck(
        status="healthy" if db_connected and ai_available else "degraded",
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        database_connected=db_connected,
        ai_service_available=ai_available
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
    """
    
    try:
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
            created_at=session.created_at
        )
        
    except Exception as e:
        logger.error("Failed to create refinement session", error=str(e))
        raise HTTPException(
            status_code=500, 
            detail="Failed to create refinement session"
        )

@app.post("/refine/sync", response_model=RefinedProductRequirement)
async def refine_product_idea_sync(
    request: RefineRequest,
    db: Session = Depends(get_db)
):
    """
    Synchronously refine a product idea (for immediate results).
    
    Note: This endpoint may take 30-60 seconds to complete.
    """
    
    try:
        # Create and process refinement session synchronously
        session = await refinement_service.create_refinement_session(db, request.idea)
        
        result = await refinement_service.process_refinement(
            db,
            session.id,
            request.idea,
            request.priority_focus or "balanced"
        )
        
        return result
        
    except Exception as e:
        logger.error("Failed to refine product idea", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refine product requirement: {str(e)}"
        )

@app.get("/refine/{session_id}", response_model=RefinementResponse)
async def get_refinement_status(session_id: int, db: Session = Depends(get_db)):
    """Get the status and results of a refinement session"""
    
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

@app.get("/refine", response_model=list[RefinementResponse])
async def list_recent_refinements(limit: int = 10, db: Session = Depends(get_db)):
    """List recent refinement sessions"""
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
