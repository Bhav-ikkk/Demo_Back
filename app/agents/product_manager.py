from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from .base_agent import BaseAgent
from ..models import AgentType

class ProductManagerAgent(BaseAgent):
    """Product Management specialist - optimized for concise strategy"""
    
    def __init__(self):
        super().__init__(AgentType.PRODUCT_MANAGER)
    
    def setup_prompts(self):
        self.analysis_prompt = PromptTemplate.from_template("""
        ROLE: Senior Product Manager
        
        TASK: Evaluate this product idea in 2-3 sentences:
        
        IDEA: {product_idea}
        CONTEXT: {context}
        
        RESPOND WITH:
        1. Product-market fit score (1-10)
        2. Top 3 must-have features
        3. MVP timeline estimate
        4. Key success metric
        
        Keep each point brief. Focus on execution.
        """)
    
    def get_expertise_areas(self) -> List[str]:
        return [
            "Product Strategy",
            "Feature Prioritization",
            "MVP Planning",
            "Success Metrics"
        ]
    
    async def create_product_roadmap(self, product_idea: str, timeline: str = "12 months") -> Dict[str, Any]:
        """Specialized method for creating product roadmaps"""
        roadmap_prompt = PromptTemplate.from_template("""
        Create a detailed product roadmap for: {product_idea}
        
        Timeline: {timeline}
        
        Include:
        1. MVP features and timeline
        2. Quarterly feature releases
        3. Dependencies and risks
        4. Resource requirements
        5. Success metrics for each phase
        
        Format as a structured roadmap with clear milestones.
        """)
        
        chain = roadmap_prompt | self.llm
        response = await chain.ainvoke({
            "product_idea": product_idea,
            "timeline": timeline
        })
        
        return {"product_roadmap": response.content}
