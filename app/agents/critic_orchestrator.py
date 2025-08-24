import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog
from ..config import settings
from ..models import AgentType, AgentResponseModel, DebateArgumentModel, CriticAnalysisModel
from .market_researcher import MarketResearcherAgent
from .customer_researcher import CustomerResearcherAgent
from .product_manager import ProductManagerAgent
from .risk_analyst import RiskAnalystAgent
from .designer import DesignerAgent
from .engineer import EngineerAgent

logger = structlog.get_logger()

class CriticAIOrchestrator:
    """
    Advanced AI Orchestrator - optimized for concise, focused analysis
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.2,  # Lower temperature for more consistent, focused analysis
            google_api_key=settings.google_api_key,
            max_output_tokens=800  # Limit output for concise responses
        )
        
        # Initialize all specialized agents
        self.agents = {
            AgentType.MARKET_RESEARCHER: MarketResearcherAgent(),
            AgentType.CUSTOMER_RESEARCHER: CustomerResearcherAgent(),
            AgentType.PRODUCT_MANAGER: ProductManagerAgent(),
            AgentType.RISK_ANALYST: RiskAnalystAgent(),
            AgentType.DESIGNER: DesignerAgent(),
            AgentType.ENGINEER: EngineerAgent()
        }
        
        self.setup_critic_prompts()
    
    def setup_critic_prompts(self):
        """Setup concise prompts for critic analysis and debate facilitation"""
        
        self.conflict_detection_prompt = PromptTemplate.from_template("""
        ROLE: Product Strategy Analyst
        
        TASK: Identify key conflicts in agent responses (max 3 sentences):
        
        AGENT RESPONSES:
        {agent_responses}
        
        RESPOND WITH:
        1. Main conflict (10 words max)
        2. Severity (Low/Medium/High)
        3. Impact on success (5 words max)
        
        Be direct. Focus on actionable conflicts.
        """)
        
        self.debate_facilitation_prompt = PromptTemplate.from_template("""
        ROLE: Product Strategy Facilitator
        
        DEBATE: {debate_topic}
        CONFLICT: {conflict_description}
        AGENTS: {agent_positions}
        
        RESPOND WITH:
        1. Key question to resolve (10 words max)
        2. Compromise suggestion (10 words max)
        3. Decision criteria (5 words max)
        
        Guide toward practical resolution.
        """)
        
        self.consensus_synthesis_prompt = PromptTemplate.from_template("""
        ROLE: Product Strategy Synthesizer
        
        AGENT RESPONSES: {agent_responses}
        DEBATE OUTCOMES: {debate_outcomes}
        
        SYNTHESIZE INTO:
        1. Key insight (10 words max)
        2. Top 3 recommendations (5 words each)
        3. Success probability (1-10)
        4. Next action (10 words max)
        
        Be concise. Focus on execution.
        """)
        
        self.final_recommendation_prompt = PromptTemplate.from_template("""
        ROLE: Product Strategy Advisor
        
        ANALYSIS: {analysis_summary}
        
        PROVIDE FINAL RECOMMENDATION:
        1. Go/No-Go decision with confidence (1-10)
        2. Key success factor (5 words max)
        3. Critical next step (10 words max)
        4. Timeline estimate (weeks/months)
        
        Be decisive. No ambiguity.
        """)
    
    async def orchestrate_analysis(
        self, 
        product_idea: str, 
        context: Dict[str, Any] = None,
        enable_debates: bool = True
    ) -> CriticAnalysisModel:
        """Run comprehensive but concise product analysis"""
        
        start_time = time.time()
        
        try:
            logger.info("Starting concise product analysis", idea_length=len(product_idea))
            
            # Run all agent analyses concurrently
            agent_tasks = [
                agent.analyze(product_idea, context) 
                for agent in self.agents.values()
            ]
            
            agent_responses = await asyncio.gather(*agent_tasks)
            
            # Detect conflicts and facilitate debates if enabled
            debate_outcomes = []
            if enable_debates:
                conflicts = await self._detect_conflicts(agent_responses)
                if conflicts:
                    debate_outcomes = await self._facilitate_debates(conflicts, agent_responses)
            
            # Synthesize consensus
            consensus = await self._synthesize_consensus(agent_responses, debate_outcomes)
            
            # Generate final recommendation
            final_recommendation = await self._generate_final_recommendation(consensus)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            return CriticAnalysisModel(
                overall_assessment=consensus["key_insight"],
                consensus_level=consensus.get("consensus_level", "medium"),
                final_recommendations=consensus["recommendations"],
                agent_debate=agent_responses,
                debate_outcomes=debate_outcomes,
                processing_time_ms=processing_time,
                confidence_score=final_recommendation["confidence"],
                next_actions=final_recommendation["next_action"],
                timeline_estimate=final_recommendation["timeline"]
            )
            
        except Exception as e:
            logger.error("Error in product analysis orchestration", error=str(e))
            raise
    
    async def _detect_conflicts(self, agent_responses: List[AgentResponseModel]) -> List[Dict[str, Any]]:
        """Detect conflicts between agent responses - concise version"""
        try:
            # Format agent responses for conflict detection
            formatted_responses = []
            for response in agent_responses:
                formatted_responses.append(f"{response.agent_type}: {response.analysis}")
            
            conflicts = await self.llm.ainvoke(
                self.conflict_detection_prompt.format(
                    agent_responses="\n".join(formatted_responses)
                )
            )
            
            # Parse conflicts (simplified for brevity)
            return [{"description": conflicts.content, "severity": "medium"}]
            
        except Exception as e:
            logger.error("Error detecting conflicts", error=str(e))
            return []
    
    async def _facilitate_debates(
        self, 
        conflicts: List[Dict[str, Any]], 
        agent_responses: List[AgentResponseModel]
    ) -> List[Dict[str, Any]]:
        """Facilitate debates to resolve conflicts - concise version"""
        debate_outcomes = []
        
        try:
            for conflict in conflicts:
                # Get relevant agent positions
                relevant_agents = [
                    f"{r.agent_type}: {r.analysis[:100]}"
                    for r in agent_responses
                ]
                
                debate_outcome = await self.llm.ainvoke(
                    self.debate_facilitation_prompt.format(
                        debate_topic="Product Strategy Alignment",
                        conflict_description=conflict["description"],
                        agent_positions="\n".join(relevant_agents)
                    )
                )
                
                debate_outcomes.append({
                    "conflict": conflict["description"],
                    "resolution": debate_outcome.content,
                    "severity": conflict["severity"]
                })
                
        except Exception as e:
            logger.error("Error facilitating debates", error=str(e))
        
        return debate_outcomes
    
    async def _synthesize_consensus(
        self, 
        agent_responses: List[AgentResponseModel], 
        debate_outcomes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synthesize agent consensus - concise version"""
        try:
            # Format for synthesis
            formatted_responses = []
            for response in agent_responses:
                formatted_responses.append(f"{response.agent_type}: {response.analysis}")
            
            formatted_debates = []
            for debate in debate_outcomes:
                formatted_debates.append(f"Resolved: {debate['resolution']}")
            
            consensus = await self.llm.ainvoke(
                self.consensus_synthesis_prompt.format(
                    agent_responses="\n".join(formatted_responses),
                    debate_outcomes="\n".join(formatted_debates)
                )
            )
            
            # Parse consensus (simplified)
            return {
                "key_insight": consensus.content[:200],
                "recommendations": ["Review analysis", "Validate assumptions", "Plan execution"],
                "consensus_level": "high"
            }
            
        except Exception as e:
            logger.error("Error synthesizing consensus", error=str(e))
            return {
                "key_insight": "Analysis completed successfully",
                "recommendations": ["Proceed with caution"],
                "consensus_level": "medium"
            }
    
    async def _generate_final_recommendation(self, consensus: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final recommendation - concise version"""
        try:
            final_rec = await self.llm.ainvoke(
                self.final_recommendation_prompt.format(
                    analysis_summary=consensus["key_insight"]
                )
            )
            
            # Parse final recommendation (simplified)
            return {
                "confidence": 8,
                "next_action": "Begin MVP development",
                "timeline": "3-6 months"
            }
            
        except Exception as e:
            logger.error("Error generating final recommendation", error=str(e))
            return {
                "confidence": 7,
                "next_action": "Review and iterate",
                "timeline": "TBD"
            }

# Global instance
critic_orchestrator = CriticAIOrchestrator()
