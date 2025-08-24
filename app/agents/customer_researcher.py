from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from .base_agent import BaseAgent
from ..models import AgentType

class CustomerResearcherAgent(BaseAgent):
    """Customer Research specialist - optimized for concise insights"""
    
    def __init__(self):
        super().__init__(AgentType.CUSTOMER_RESEARCHER)
    
    def setup_prompts(self):
        self.analysis_prompt = PromptTemplate.from_template("""
        ROLE: Customer Research Expert
        
        TASK: Analyze customer needs for this product in 2-3 sentences:
        
        IDEA: {product_idea}
        CONTEXT: {context}
        
        RESPOND WITH:
        1. Primary customer pain point (5 words max)
        2. Target customer segment (5 words max)
        3. Key customer need (5 words max)
        4. One customer acquisition insight (10 words max)
        
        Be specific and actionable. No fluff.
        """)
    
    def get_expertise_areas(self) -> List[str]:
        return [
            "Customer Pain Points",
            "User Research",
            "Customer Segmentation",
            "Acquisition Strategy"
        ]
    
    async def create_user_personas(self, product_idea: str, target_segments: List[str] = None) -> Dict[str, Any]:
        """Specialized method for creating detailed user personas"""
        persona_prompt = PromptTemplate.from_template("""
        Create detailed user personas for: {product_idea}
        
        Target segments: {target_segments}
        
        For each persona, include:
        1. Demographics and background
        2. Goals and motivations
        3. Pain points and frustrations
        4. Technology usage patterns
        5. Preferred communication channels
        6. Decision-making criteria
        
        Create 3-5 distinct personas with specific names and characteristics.
        """)
        
        chain = persona_prompt | self.llm
        response = await chain.ainvoke({
            "product_idea": product_idea,
            "target_segments": target_segments or "General consumer market"
        })
        
        return {"user_personas": response.content}
