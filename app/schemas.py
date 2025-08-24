from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentFeedback(BaseModel):
    agent_name: str = Field(description="Name of the AI agent providing the feedback")
    feedback: str = Field(description="The detailed feedback or analysis from the agent")
    processing_time_ms: Optional[int] = Field(description="Time taken by this agent in milliseconds")
    confidence_score: Optional[float] = Field(ge=0, le=1, description="Agent's confidence in the feedback")

class RefinedProductRequirement(BaseModel):
    refined_requirement: str = Field(description="The final, detailed, and actionable product requirement")
    key_changes_summary: List[str] = Field(description="A bulleted list summarizing the most critical changes made to the original idea")
    user_stories: List[str] = Field(description="Clear, structured user stories in the format 'As a [user], I want [action], so that [benefit]'")
    technical_tasks: List[str] = Field(description="A list of high-level technical tasks for the development team")
    agent_debate: List[AgentFeedback] = Field(description="A log of the conversation and feedback from each agent")
    priority_score: Optional[int] = Field(ge=1, le=10, description="Priority score from 1-10")
    estimated_effort: Optional[str] = Field(description="Estimated development effort (Small/Medium/Large/XL)")
    risk_assessment: Optional[str] = Field(description="Key risks and mitigation strategies")

class RefineRequest(BaseModel):
    idea: str = Field(min_length=10, max_length=5000, description="The product idea to refine")
    priority_focus: Optional[str] = Field(
        description="Specific area to focus on (technical, market, user, balanced)",
        pattern="^(technical|market|user|balanced)$"  # Changed from regex to pattern
    )
    
    @validator('idea')
    def validate_idea(cls, v):
        if not v.strip():
            raise ValueError('Product idea cannot be empty or just whitespace')
        return v.strip()

class RefinementResponse(BaseModel):
    session_id: int
    status: ProcessingStatus
    result: Optional[RefinedProductRequirement] = None
    error_message: Optional[str] = None
    created_at: datetime
    processing_time_seconds: Optional[int] = None

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str
    database_connected: bool
    ai_service_available: bool
