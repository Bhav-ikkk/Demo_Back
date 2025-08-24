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
    Advanced AI Orchestrator that manages agent debates, identifies conflicts,
    and synthesizes comprehensive product analysis results
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,  # Lower temperature for more consistent analysis
            google_api_key=settings.google_api_key
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
        """Setup prompts for critic analysis and debate facilitation"""
        
        self.conflict_detection_prompt = PromptTemplate.from_template("""
        ROLE: You are an expert Product Strategy Analyst specializing in identifying conflicts and inconsistencies in multi-stakeholder product analysis.
        
        TASK: Analyze the following agent responses and identify significant conflicts, inconsistencies, or areas requiring debate.
        
        AGENT RESPONSES:
        {agent_responses}
        
        CONFLICT ANALYSIS CRITERIA:
        1. STRATEGIC CONFLICTS
           - Conflicting product vision or positioning
           - Disagreement on target market or customer segments
           - Different prioritization of features or requirements
        
        2. TECHNICAL CONFLICTS
           - Incompatible technical approaches or architectures
           - Conflicting feasibility assessments
           - Different risk evaluations for technical implementation
        
        3. MARKET CONFLICTS
           - Contradictory market opportunity assessments
           - Different competitive analysis conclusions
           - Conflicting go-to-market strategies
        
        4. RESOURCE CONFLICTS
           - Incompatible timeline or budget estimates
           - Different resource requirement assessments
           - Conflicting priority recommendations
        
        For each conflict identified, provide:
        - Conflict description and severity (Low/Medium/High)
        - Involved agents and their positions
        - Potential impact on product success
        - Recommended debate topics and questions
        
        Return a structured analysis of conflicts requiring resolution.
        """)
        
        self.debate_facilitation_prompt = PromptTemplate.from_template("""
        ROLE: You are a skilled Product Strategy Facilitator conducting a structured debate between expert agents to resolve conflicts and reach consensus.
        
        DEBATE TOPIC: {debate_topic}
        CONFLICT DESCRIPTION: {conflict_description}
        
        PARTICIPATING AGENTS AND POSITIONS:
        {agent_positions}
        
        FACILITATION FRAMEWORK:
        1. Present the conflict clearly and objectively
        2. Allow each agent to present their position with supporting evidence
        3. Facilitate constructive challenge and counter-arguments
        4. Identify areas of agreement and remaining disagreements
        5. Guide toward practical compromise or resolution
        
        DEBATE RULES:
        - Focus on evidence-based arguments
        - Consider business impact and feasibility
        - Seek win-win solutions where possible
        - Acknowledge trade-offs and their implications
        
        Conduct a structured debate and provide:
        - Summary of each agent's refined position
        - Areas of consensus reached
        - Remaining disagreements and trade-offs
        - Recommended resolution or compromise
        - Action items for implementation
        """)
        
        self.final_synthesis_prompt = PromptTemplate.from_template("""
        ROLE: You are a Chief Product Officer with 20+ years of experience synthesizing complex product analysis into actionable strategic recommendations.
        
        TASK: Create a comprehensive final analysis that synthesizes all agent feedback, debate outcomes, and conflict resolutions into a unified product strategy.
        
        INPUT DATA:
        ORIGINAL PRODUCT IDEA: {product_idea}
        
        AGENT ANALYSES:
        {agent_responses}
        
        DEBATE OUTCOMES:
        {debate_outcomes}
        
        SYNTHESIS FRAMEWORK:
        1. EXECUTIVE SUMMARY
           - Clear product vision and value proposition
           - Key strategic recommendations
           - Critical success factors and risks
        
        2. INTEGRATED ANALYSIS
           - Market opportunity and competitive positioning
           - Customer needs and user experience strategy
           - Technical feasibility and architecture approach
           - Risk assessment and mitigation strategies
        
        3. ACTIONABLE ROADMAP
           - Prioritized feature development plan
           - Resource requirements and timeline
           - Key milestones and success metrics
           - Go-to-market strategy and launch plan
        
        4. CONSENSUS ASSESSMENT
           - Level of agreement across agents (0-1 scale)
           - Remaining areas of uncertainty or risk
           - Recommended validation and testing approach
        
        Provide a comprehensive, actionable product strategy that balances all stakeholder perspectives.
        """)
    
    async def orchestrate_analysis(
        self, 
        product_idea: str, 
        context: Dict[str, Any] = None,
        enable_debates: bool = True
    ) -> CriticAnalysisModel:
        """
        Main orchestration method that runs all agents, facilitates debates, and synthesizes results
        """
        start_time = time.time()
        
        try:
            logger.info("Starting comprehensive product analysis", product_idea=product_idea[:100])
            
            # Phase 1: Run all agents in parallel
            agent_responses = await self._run_all_agents(product_idea, context or {})
            
            # Phase 2: Detect conflicts and facilitate debates if enabled
            debate_outcomes = []
            if enable_debates:
                conflicts = await self._detect_conflicts(agent_responses)
                if conflicts:
                    debate_outcomes = await self._facilitate_debates(conflicts, agent_responses)
            
            # Phase 3: Synthesize final analysis
            final_analysis = await self._synthesize_final_analysis(
                product_idea, agent_responses, debate_outcomes
            )
            
            processing_time = time.time() - start_time
            logger.info("Completed product analysis", processing_time=processing_time)
            
            return final_analysis
            
        except Exception as e:
            logger.error("Error in product analysis orchestration", error=str(e))
            raise
    
    async def _run_all_agents(
        self, 
        product_idea: str, 
        context: Dict[str, Any]
    ) -> List[AgentResponseModel]:
        """Run all agents in parallel and collect their responses"""
        
        logger.info("Running all agents in parallel")
        
        # Create tasks for all agents
        agent_tasks = [
            agent.analyze(product_idea, context)
            for agent in self.agents.values()
        ]
        
        # Run agents in parallel with timeout
        try:
            agent_responses = await asyncio.wait_for(
                asyncio.gather(*agent_tasks, return_exceptions=True),
                timeout=300  # 5 minute timeout
            )
            
            # Filter out exceptions and log errors
            valid_responses = []
            for i, response in enumerate(agent_responses):
                if isinstance(response, Exception):
                    agent_type = list(self.agents.keys())[i]
                    logger.error(f"Agent {agent_type} failed", error=str(response))
                else:
                    valid_responses.append(response)
            
            return valid_responses
            
        except asyncio.TimeoutError:
            logger.error("Agent analysis timed out")
            raise Exception("Agent analysis timed out after 5 minutes")
    
    async def _detect_conflicts(
        self, 
        agent_responses: List[AgentResponseModel]
    ) -> List[Dict[str, Any]]:
        """Detect conflicts between agent responses"""
        
        logger.info("Detecting conflicts between agent responses")
        
        # Format agent responses for conflict analysis
        formatted_responses = []
        for response in agent_responses:
            formatted_responses.append(f"""
            AGENT: {response.agent_type}
            ANALYSIS: {response.analysis}
            RECOMMENDATIONS: {response.recommendations}
            CONCERNS: {response.concerns}
            CONFIDENCE: {response.confidence_score}
            """)
        
        chain = self.conflict_detection_prompt | self.llm
        conflict_analysis = await chain.ainvoke({
            "agent_responses": "\n".join(formatted_responses)
        })
        
        # Parse conflict analysis (simplified - in production, use structured parsing)
        conflicts = await self._parse_conflicts(conflict_analysis.content)
        
        logger.info(f"Detected {len(conflicts)} conflicts requiring debate")
        return conflicts
    
    async def _parse_conflicts(self, conflict_text: str) -> List[Dict[str, Any]]:
        """Parse conflict analysis into structured format"""
        # Simplified parsing - in production, use more robust parsing
        try:
            # Use LLM to structure the conflicts
            parser_prompt = PromptTemplate.from_template("""
            Parse the following conflict analysis into a structured JSON format:
            
            {conflict_text}
            
            Return a JSON array where each conflict has:
            - topic: string
            - description: string
            - severity: "Low"|"Medium"|"High"
            - involved_agents: array of agent types
            - impact: string
            - debate_questions: array of strings
            """)
            
            chain = parser_prompt | self.llm
            parsed_response = await chain.ainvoke({"conflict_text": conflict_text})
            
            import json
            try:
                return json.loads(parsed_response.content)
            except:
                # Fallback if parsing fails
                return [{
                    "topic": "General Strategy Alignment",
                    "description": "Multiple agents have different strategic perspectives",
                    "severity": "Medium",
                    "involved_agents": ["product_manager", "market_researcher"],
                    "impact": "May affect product positioning and go-to-market strategy",
                    "debate_questions": ["What should be the primary value proposition?"]
                }]
                
        except Exception as e:
            logger.error("Error parsing conflicts", error=str(e))
            return []
    
    async def _facilitate_debates(
        self, 
        conflicts: List[Dict[str, Any]], 
        agent_responses: List[AgentResponseModel]
    ) -> List[Dict[str, Any]]:
        """Facilitate debates for each identified conflict"""
        
        debate_outcomes = []
        
        for conflict in conflicts:
            if conflict["severity"] in ["Medium", "High"]:
                logger.info(f"Facilitating debate on: {conflict['topic']}")
                
                # Get positions of involved agents
                agent_positions = self._extract_agent_positions(
                    conflict["involved_agents"], agent_responses
                )
                
                # Facilitate the debate
                debate_outcome = await self._conduct_debate(conflict, agent_positions)
                debate_outcomes.append(debate_outcome)
        
        return debate_outcomes
    
    def _extract_agent_positions(
        self, 
        involved_agents: List[str], 
        agent_responses: List[AgentResponseModel]
    ) -> Dict[str, str]:
        """Extract relevant positions from involved agents"""
        positions = {}
        
        for response in agent_responses:
            if response.agent_type.value in involved_agents:
                positions[response.agent_type.value] = {
                    "analysis": response.analysis,
                    "recommendations": response.recommendations,
                    "reasoning": response.reasoning
                }
        
        return positions
    
    async def _conduct_debate(
        self, 
        conflict: Dict[str, Any], 
        agent_positions: Dict[str, str]
    ) -> Dict[str, Any]:
        """Conduct a structured debate for a specific conflict"""
        
        chain = self.debate_facilitation_prompt | self.llm
        debate_result = await chain.ainvoke({
            "debate_topic": conflict["topic"],
            "conflict_description": conflict["description"],
            "agent_positions": str(agent_positions)
        })
        
        return {
            "conflict": conflict,
            "debate_outcome": debate_result.content,
            "resolution_status": "resolved"  # Could be enhanced with actual status tracking
        }
    
    async def _synthesize_final_analysis(
        self,
        product_idea: str,
        agent_responses: List[AgentResponseModel],
        debate_outcomes: List[Dict[str, Any]]
    ) -> CriticAnalysisModel:
        """Synthesize all analysis into final comprehensive result"""
        
        logger.info("Synthesizing final analysis")
        
        # Format all inputs for synthesis
        formatted_responses = [
            f"AGENT {resp.agent_type}: {resp.analysis}" 
            for resp in agent_responses
        ]
        
        formatted_debates = [
            f"DEBATE: {outcome['conflict']['topic']} - {outcome['debate_outcome']}"
            for outcome in debate_outcomes
        ]
        
        chain = self.final_synthesis_prompt | self.llm
        synthesis_result = await chain.ainvoke({
            "product_idea": product_idea,
            "agent_responses": "\n".join(formatted_responses),
            "debate_outcomes": "\n".join(formatted_debates)
        })
        
        # Calculate agent performance scores and consensus level
        agent_scores = self._calculate_agent_scores(agent_responses)
        consensus_level = self._calculate_consensus_level(agent_responses, debate_outcomes)
        
        return CriticAnalysisModel(
            overall_assessment=synthesis_result.content,
            agent_performance_scores=agent_scores,
            identified_conflicts=[outcome["conflict"] for outcome in debate_outcomes],
            final_recommendations=["Implement synthesized strategy"],  # Would be parsed from synthesis
            consensus_level=consensus_level,
            priority_actions=["Begin MVP development", "Validate market assumptions"]  # Would be parsed
        )
    
    def _calculate_agent_scores(self, agent_responses: List[AgentResponseModel]) -> Dict[AgentType, float]:
        """Calculate performance scores for each agent"""
        scores = {}
        for response in agent_responses:
            # Simple scoring based on confidence and completeness
            score = response.confidence_score * 0.7 + 0.3  # Base score + confidence
            scores[response.agent_type] = min(score, 1.0)
        return scores
    
    def _calculate_consensus_level(
        self, 
        agent_responses: List[AgentResponseModel], 
        debate_outcomes: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall consensus level across all agents"""
        if not agent_responses:
            return 0.0
        
        # Simple consensus calculation based on confidence scores and debate resolutions
        avg_confidence = sum(resp.confidence_score for resp in agent_responses) / len(agent_responses)
        
        # Reduce consensus for each unresolved conflict
        conflict_penalty = len(debate_outcomes) * 0.1
        
        return max(0.0, min(1.0, avg_confidence - conflict_penalty))

# Global orchestrator instance
critic_orchestrator = CriticAIOrchestrator()
