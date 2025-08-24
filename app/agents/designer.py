from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from .base_agent import BaseAgent
from ..models import AgentType

class DesignerAgent(BaseAgent):
    """Design specialist - optimized for concise UX insights"""
    
    def __init__(self):
        super().__init__(AgentType.DESIGNER)
    
    def setup_prompts(self):
        self.analysis_prompt = PromptTemplate.from_template("""
        ROLE: UX/UI Design Expert
        
        TASK: Evaluate design needs for this product in 2-3 sentences:
        
        IDEA: {product_idea}
        CONTEXT: {context}
        
        RESPOND WITH:
        1. Key design challenge (5 words max)
        2. Primary user interface element (5 words max)
        3. Design principle to follow (5 words max)
        4. One UX improvement (10 words max)
        
        Focus on user experience. Be specific.
        """)
    
    def get_expertise_areas(self) -> List[str]:
        return [
            "UX Design",
            "UI Design",
            "User Research",
            "Design Principles"
        ]
    
    async def create_design_system(self, product_idea: str, brand_guidelines: Dict[str, Any] = None) -> Dict[str, Any]:
        """Specialized method for design system creation"""
        design_system_prompt = PromptTemplate.from_template("""
        Create a comprehensive design system for: {product_idea}
        
        Brand guidelines: {brand_guidelines}
        
        Include:
        1. Color palette and usage guidelines
        2. Typography scale and hierarchy
        3. Component library structure
        4. Spacing and layout principles
        5. Iconography and imagery guidelines
        6. Accessibility standards
        
        Provide detailed specifications for implementation.
        """)
        
        chain = design_system_prompt | self.llm
        response = await chain.ainvoke({
            "product_idea": product_idea,
            "brand_guidelines": brand_guidelines or "No specific brand guidelines provided"
        })
        
        return {"design_system": response.content}
