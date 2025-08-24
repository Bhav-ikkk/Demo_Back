from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from .base_agent import BaseAgent
from ..models import AgentType

class EngineerAgent(BaseAgent):
    """Engineering specialist - optimized for concise technical insights"""
    
    def __init__(self):
        super().__init__(AgentType.ENGINEER)
    
    def setup_prompts(self):
        self.analysis_prompt = PromptTemplate.from_template("""
        ROLE: Senior Software Engineer
        
        TASK: Assess technical feasibility in 2-3 sentences:
        
        IDEA: {product_idea}
        CONTEXT: {context}
        
        RESPOND WITH:
        1. Technical complexity (Low/Medium/High)
        2. Recommended tech stack (5 words max)
        3. Key technical challenge (5 words max)
        4. Development timeline (weeks/months)
        
        Focus on implementation. Be realistic.
        """)
    
    def get_expertise_areas(self) -> List[str]:
        return [
            "Technical Architecture",
            "System Design",
            "Development Planning",
            "Technology Selection"
        ]
    
    async def design_system_architecture(self, product_idea: str, scale_requirements: Dict[str, Any] = None) -> Dict[str, Any]:
        """Specialized method for system architecture design"""
        architecture_prompt = PromptTemplate.from_template("""
        Design comprehensive system architecture for: {product_idea}
        
        Scale requirements: {scale_requirements}
        
        Include:
        1. High-level architecture diagram
        2. Component breakdown and responsibilities
        3. Data flow and API design
        4. Infrastructure requirements
        5. Scalability and performance considerations
        6. Security architecture
        
        Provide detailed technical specifications.
        """)
        
        chain = architecture_prompt | self.llm
        response = await chain.ainvoke({
            "product_idea": product_idea,
            "scale_requirements": scale_requirements or "Standard web application scale"
        })
        
        return {"system_architecture": response.content}
