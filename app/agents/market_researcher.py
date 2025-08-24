from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from .base_agent import BaseAgent
from ..models import AgentType

class MarketResearcherAgent(BaseAgent):
    """Market Research specialist focusing on market analysis and competitive intelligence"""
    
    def __init__(self):
        super().__init__(AgentType.MARKET_RESEARCHER)
    
    def setup_prompts(self):
        self.analysis_prompt = PromptTemplate.from_template("""
        ROLE: You are a Senior Market Research Analyst with 15+ years of experience in product strategy, competitive intelligence, and market sizing across multiple industries.
        
        EXPERTISE: {expertise_areas}
        
        TASK: Conduct a comprehensive market analysis for the following product idea:
        
        PRODUCT IDEA: {product_idea}
        CONTEXT: {context}
        
        ANALYSIS FRAMEWORK:
        1. MARKET OPPORTUNITY ASSESSMENT
           - Total Addressable Market (TAM) estimation
           - Serviceable Addressable Market (SAM) analysis
           - Market growth trends and drivers
           - Market maturity and lifecycle stage
        
        2. COMPETITIVE LANDSCAPE ANALYSIS
           - Direct and indirect competitors identification
           - Competitive positioning and differentiation gaps
           - Market share distribution
           - Competitive strengths and weaknesses
        
        3. CUSTOMER SEGMENTATION & TARGETING
           - Primary and secondary customer segments
           - Customer pain points and unmet needs
           - Buying behavior and decision-making process
           - Customer acquisition cost considerations
        
        4. GO-TO-MARKET STRATEGY
           - Optimal market entry strategy
           - Distribution channels and partnerships
           - Pricing strategy recommendations
           - Marketing and positioning approach
        
        5. MARKET RISKS & OPPORTUNITIES
           - Market barriers and entry challenges
           - Regulatory and compliance considerations
           - Technology disruption risks
           - Market timing assessment
        
        Provide specific, data-driven insights with confidence levels for each recommendation.
        Focus on actionable intelligence that will inform strategic product decisions.
        """)
    
    def get_expertise_areas(self) -> List[str]:
        return [
            "Market Sizing & TAM Analysis",
            "Competitive Intelligence",
            "Customer Segmentation",
            "Go-to-Market Strategy",
            "Pricing Strategy",
            "Market Entry Planning",
            "Industry Analysis",
            "Consumer Behavior Research",
            "Market Trend Analysis",
            "Business Model Validation"
        ]
    
    async def analyze_competition(self, product_idea: str, competitors: List[str] = None) -> Dict[str, Any]:
        """Specialized method for competitive analysis"""
        competitive_prompt = PromptTemplate.from_template("""
        Conduct a detailed competitive analysis for: {product_idea}
        
        Known competitors: {competitors}
        
        Analyze:
        1. Feature comparison matrix
        2. Pricing strategies
        3. Market positioning
        4. Strengths and weaknesses
        5. Differentiation opportunities
        
        Provide actionable competitive intelligence.
        """)
        
        chain = competitive_prompt | self.llm
        response = await chain.ainvoke({
            "product_idea": product_idea,
            "competitors": competitors or "Unknown - please identify"
        })
        
        return {"competitive_analysis": response.content}
