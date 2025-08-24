from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from .base_agent import BaseAgent
from ..models import AgentType

class MarketResearcherAgent(BaseAgent):
    """Market Research specialist - optimized for concise analysis"""
    
    def __init__(self):
        super().__init__(AgentType.MARKET_RESEARCHER)
    
    def setup_prompts(self):
        self.analysis_prompt = PromptTemplate.from_template("""
        ROLE: Senior Market Research Analyst
        
        TASK: Analyze this product idea in 2-3 sentences max:
        
        IDEA: {product_idea}
        CONTEXT: {context}
        
        RESPOND WITH:
        1. Market size estimate (one number/range)
        2. Top 2 competitors
        3. Key market risk
        4. One actionable recommendation
        
        Keep each point to 10 words or less. Be direct and specific.
        """)
    
    def get_expertise_areas(self) -> List[str]:
        return [
            "Market Sizing",
            "Competitive Analysis",
            "Risk Assessment",
            "Strategic Recommendations"
        ]
    
    async def analyze_competition(self, product_idea: str, competitors: List[str] = None) -> Dict[str, Any]:
        """Specialized method for competitive analysis - concise version"""
        competitive_prompt = PromptTemplate.from_template("""
        Analyze competition for: {product_idea}
        
        Competitors: {competitors}
        
        Return in 2 sentences:
        1. Main competitive advantage
        2. Key differentiation opportunity
        """)
        
        chain = competitive_prompt | self.llm
        response = await chain.ainvoke({
            "product_idea": product_idea,
            "competitors": competitors or "Unknown"
        })
        
        return {"competitive_analysis": response.content}
