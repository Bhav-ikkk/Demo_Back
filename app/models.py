from enum import Enum
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class AgentType(str, Enum):
    PRODUCT_MANAGER = "product_manager"
    ENGINEER = "engineer"
    DESIGNER = "designer"
    MARKET_RESEARCHER = "market_researcher"
    RISK_ANALYST = "risk_analyst"
    CUSTOMER_RESEARCHER = "customer_researcher"

class SessionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentResponseModel(BaseModel):
    agent_type: AgentType
    analysis: Dict[str, Any]
    recommendations: List[str]
    concerns: List[str]
    confidence_score: float
    reasoning: str
    supporting_data: Optional[Dict[str, Any]] = None

class ProductAnalysisRequest(BaseModel):
    product_idea: str
    target_market: Optional[str] = None
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    specific_focus: Optional[List[str]] = None

class ProductAnalysisResponse(BaseModel):
    session_id: int
    status: SessionStatus
    agent_responses: List[AgentResponseModel]
    debates: List[Dict[str, Any]]
    critic_analysis: Any
    processing_time: Optional[float] = None
    created_at: datetime
