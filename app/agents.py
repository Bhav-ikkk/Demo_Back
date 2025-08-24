import asyncio
import time
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from .schemas import RefinedProductRequirement, AgentFeedback
from .config import settings

logger = structlog.get_logger()

class AIAgentOrchestrator:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            temperature=0.7,
            google_api_key=settings.google_api_key
        )
        self._setup_agents()
    
    def _setup_agents(self):
        """Initialize all agent prompts and chains"""
        
        # Enhanced Product Manager Agent
        self.pm_prompt = PromptTemplate.from_template("""
        ROLE: You are a world-class Senior Product Manager with 10+ years of experience at top tech companies.
        
        TASK: Analyze the following raw product idea and refine it with a focus on user value, market positioning, and strategic alignment.
        
        FOCUS AREAS:
        - Target audience identification and user personas
        - Core value proposition and unique selling points
        - User journey and experience considerations
        - Success metrics and KPIs
        - Competitive positioning
        
        PRODUCT IDEA: {idea}
        PRIORITY FOCUS: {priority_focus}
        
        Provide detailed, actionable feedback that transforms this idea into a market-ready product concept.
        """)
        
        # Enhanced Developer Agent
        self.dev_prompt = PromptTemplate.from_template("""
        ROLE: You are a pragmatic Staff Software Engineer and Technical Architect with expertise in scalable systems.
        
        TASK: Analyze the following product requirement from a technical perspective, focusing on feasibility, architecture, and implementation strategy.
        
        FOCUS AREAS:
        - Technical feasibility and complexity assessment
        - Required technology stack and architecture patterns
        - Data models and system integrations
        - Performance and scalability considerations
        - Security and compliance requirements
        - Development timeline and resource estimation
        
        PRODUCT REQUIREMENT: {requirement}
        PRIORITY FOCUS: {priority_focus}
        
        Provide technical insights that will guide the engineering team toward successful implementation.
        """)
        
        # Enhanced Market Analyst Agent
        self.market_prompt = PromptTemplate.from_template("""
        ROLE: You are a sharp Senior Market Research Analyst with deep expertise in product strategy and competitive intelligence.
        
        TASK: Analyze the following product idea for market opportunity, competitive landscape, and business viability.
        
        FOCUS AREAS:
        - Market size and growth potential
        - Competitive analysis and differentiation opportunities
        - Customer segments and go-to-market strategy
        - Revenue model and monetization potential
        - Market timing and adoption barriers
        - Risk assessment and mitigation strategies
        
        PRODUCT IDEA: {idea}
        PRIORITY FOCUS: {priority_focus}
        
        Provide market insights that will inform strategic product decisions and positioning.
        """)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _run_agent(self, agent_name: str, prompt: PromptTemplate, inputs: Dict[str, Any]) -> AgentFeedback:
        """Run a single agent with retry logic and timing"""
        start_time = time.time()
        
        try:
            logger.info(f"Running {agent_name} agent", inputs=inputs)
            
            chain = prompt | self.llm
            response = await chain.ainvoke(inputs)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return AgentFeedback(
                agent_name=agent_name,
                feedback=response.content,
                processing_time_ms=processing_time,
                confidence_score=0.85  # Could be enhanced with actual confidence scoring
            )
            
        except Exception as e:
            logger.error(f"Error in {agent_name} agent", error=str(e))
            raise
    
    async def refine_requirement(self, idea: str, priority_focus: str = "balanced") -> RefinedProductRequirement:
        """Orchestrate all agents to refine a product requirement"""
        
        try:
            # Run PM and Market agents in parallel
            pm_task = self._run_agent(
                "Product Manager", 
                self.pm_prompt, 
                {"idea": idea, "priority_focus": priority_focus}
            )
            
            market_task = self._run_agent(
                "Market Analyst", 
                self.market_prompt, 
                {"idea": idea, "priority_focus": priority_focus}
            )
            
            pm_feedback, market_feedback = await asyncio.gather(pm_task, market_task)
            
            # Run developer agent with PM feedback
            dev_feedback = await self._run_agent(
                "Senior Developer",
                self.dev_prompt,
                {"requirement": pm_feedback.feedback, "priority_focus": priority_focus}
            )
            
            # Run final synthesizer
            final_result = await self._synthesize_feedback(
                idea, pm_feedback, dev_feedback, market_feedback
            )
            
            return final_result
            
        except Exception as e:
            logger.error("Error in requirement refinement", error=str(e))
            raise
    
    async def _synthesize_feedback(
        self, 
        idea: str, 
        pm_feedback: AgentFeedback, 
        dev_feedback: AgentFeedback, 
        market_feedback: AgentFeedback
    ) -> RefinedProductRequirement:
        """Synthesize all agent feedback into final requirement"""
        
        parser = PydanticOutputParser(pydantic_object=RefinedProductRequirement)
        
        synthesizer_prompt = PromptTemplate(
            template="""
            ROLE: You are an expert Technical Program Manager and Product Strategy Lead.
            
            TASK: Synthesize the original idea and comprehensive feedback from our expert agents into a single, structured, actionable product requirement document.
            
            ORIGINAL IDEA: {idea}
            
            EXPERT FEEDBACK:
            
            PRODUCT MANAGER INSIGHTS:
            {pm_feedback}
            
            TECHNICAL ARCHITECT ANALYSIS:
            {dev_feedback}
            
            MARKET ANALYST ASSESSMENT:
            {market_feedback}
            
            SYNTHESIS REQUIREMENTS:
            - Create a refined requirement that incorporates the best insights from all agents
            - Prioritize actionable items and clear next steps
            - Include realistic user stories that drive business value
            - Provide technical tasks that are specific and measurable
            - Assess priority (1-10) and effort estimation (Small/Medium/Large/XL)
            - Identify key risks and mitigation strategies
            - Maintain the agent debate log for transparency
            
            {format_instructions}
            """,
            input_variables=["idea", "pm_feedback", "dev_feedback", "market_feedback"],
            partial_variables={"format_instructions": parser.get_format_instructions()},
        )
        
        chain = synthesizer_prompt | self.llm | parser
        
        result = await chain.ainvoke({
            "idea": idea,
            "pm_feedback": pm_feedback.feedback,
            "dev_feedback": dev_feedback.feedback,
            "market_feedback": market_feedback.feedback
        })
        
        # Add the agent debate log
        result.agent_debate = [pm_feedback, dev_feedback, market_feedback]
        
        return result

# Global orchestrator instance
orchestrator = AIAgentOrchestrator()
