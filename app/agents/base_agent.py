import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from ..config import settings
from ..models import AgentResponseModel, AgentType

logger = structlog.get_logger()

class BaseAgent(ABC):
    """Base class for all AI agents with common functionality - optimized for concise responses"""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,  # Lower temperature for more focused responses
            google_api_key=settings.google_api_key,
            max_output_tokens=500  # Limit output length for concise responses
        )
        self.setup_prompts()
    
    @abstractmethod
    def setup_prompts(self):
        """Setup agent-specific prompts - keep them concise and focused"""
        pass
    
    @abstractmethod
    def get_expertise_areas(self) -> List[str]:
        """Return list of expertise areas for this agent"""
        pass
    
    async def analyze(self, product_idea: str, context: Dict[str, Any] = None) -> AgentResponseModel:
        """Main analysis method with automatic fallback when primary API fails"""
        start_time = time.time()
        
        try:
            logger.info(f"Running {self.agent_type} analysis", product_idea=product_idea[:100])
            
            # Use fallback orchestrator for automatic fallback
            from ..fallback_orchestrator import fallback_orchestrator
            
            async def primary_analysis():
                """Primary analysis using Gemini API"""
                # Prepare inputs for the prompt
                inputs = {
                    "product_idea": product_idea,
                    "context": context or {},
                    "expertise_areas": ", ".join(self.get_expertise_areas())
                }
                
                # Run the analysis with retry
                from tenacity import retry, stop_after_attempt, wait_exponential
                
                @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
                async def retry_analysis():
                    chain = self.analysis_prompt | self.llm
                    response = await chain.ainvoke(inputs)
                    return response
                
                response = await retry_analysis()
                
                # Parse the response into structured format
                analysis_result = await self._parse_response(response.content)
                
                return AgentResponseModel(
                    agent_type=self.agent_type,
                    analysis=analysis_result["analysis"],
                    recommendations=analysis_result["recommendations"],
                    concerns=analysis_result["concerns"],
                    confidence_score=analysis_result.get("confidence_score", 0.8),
                    reasoning=analysis_result["reasoning"],
                    supporting_data=analysis_result.get("supporting_data")
                )
            
            # Execute with fallback
            response, used_fallback = await fallback_orchestrator.execute_with_fallback(
                primary_analysis, 
                str(self.agent_type), 
                product_idea, 
                context
            )
            
            processing_time = time.time() - start_time
            
            if used_fallback:
                logger.info(f"Used fallback for {self.agent_type}", 
                           fallback_method=response.reasoning.split(']')[0] if ']' in response.reasoning else 'unknown')
            
            return response
            
        except Exception as e:
            logger.error(f"Error in {self.agent_type} analysis", error=str(e))
            raise
    
    async def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured format - optimized for concise parsing"""
        try:
            # Use a concise parser prompt
            parser_prompt = PromptTemplate.from_template("""
            Parse this response into JSON format. Keep it concise:
            
            {response}
            
            Return JSON with these keys (keep values brief):
            - analysis: {"key_insight": "one sentence", "market_size": "brief estimate"}
            - recommendations: ["action 1", "action 2"] (max 3 items)
            - concerns: ["risk 1", "risk 2"] (max 2 items)
            - confidence_score: 0.0-1.0
            - reasoning: "one sentence explanation"
            - supporting_data: null or brief data point
            """)
            
            chain = parser_prompt | self.llm
            parsed_response = await chain.ainvoke({"response": response})
            
            import json
            try:
                return json.loads(parsed_response.content)
            except:
                # Fallback parsing for concise output
                return {
                    "analysis": {"summary": response[:200]},
                    "recommendations": ["Review analysis"],
                    "concerns": ["Verify details"],
                    "confidence_score": 0.7,
                    "reasoning": "Automated parsing",
                    "supporting_data": None
                }
                
        except Exception as e:
            logger.error("Error parsing agent response", error=str(e))
            return {
                "analysis": {"error": "Parsing failed"},
                "recommendations": [],
                "concerns": ["Analysis failed"],
                "confidence_score": 0.5,
                "reasoning": "Error in processing",
                "supporting_data": None
            }
