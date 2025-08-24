from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from .base_agent import BaseAgent
from ..models import AgentType

class ProductManagerAgent(BaseAgent):
    """Product Manager specialist focusing on strategy, roadmapping, and feature prioritization"""
    
    def __init__(self):
        super().__init__(AgentType.PRODUCT_MANAGER)
    
    def setup_prompts(self):
        self.analysis_prompt = PromptTemplate.from_template("""
        ROLE: You are a Senior Product Manager with 12+ years of experience at leading tech companies, specializing in product strategy, roadmapping, and cross-functional team leadership.
        
        EXPERTISE: {expertise_areas}
        
        TASK: Conduct comprehensive product strategy analysis for:
        
        PRODUCT IDEA: {product_idea}
        CONTEXT: {context}
        
        PRODUCT STRATEGY FRAMEWORK:
        1. PRODUCT VISION & STRATEGY
           - Clear product vision and mission statement
           - Strategic objectives and success criteria
           - Value proposition and unique selling points
           - Product positioning and differentiation strategy
        
        2. FEATURE PRIORITIZATION & ROADMAPPING
           - Core feature identification and prioritization
           - MVP definition and scope
           - Feature roadmap with timeline estimates
           - Dependencies and critical path analysis
        
        3. USER STORY DEVELOPMENT
           - Epic-level user stories with acceptance criteria
           - User journey integration points
           - Edge cases and error handling scenarios
           - Performance and scalability requirements
        
        4. SUCCESS METRICS & KPIs
           - North Star metrics definition
           - Leading and lagging indicators
           - Success criteria for each feature
           - A/B testing and experimentation strategy
        
        5. STAKEHOLDER ALIGNMENT
           - Key stakeholder identification and needs
           - Communication and reporting strategy
           - Risk mitigation and contingency planning
           - Resource requirements and team structure
        
        Provide actionable product strategy with clear priorities and measurable outcomes.
        """)
    
    def get_expertise_areas(self) -> List[str]:
        return [
            "Product Strategy & Vision",
            "Feature Prioritization",
            "Product Roadmapping",
            "User Story Development",
            "Agile & Scrum Methodologies",
            "A/B Testing & Experimentation",
            "Product Analytics & KPIs",
            "Stakeholder Management",
            "Cross-functional Team Leadership",
            "Go-to-Market Planning",
            "Product-Market Fit",
            "Competitive Analysis"
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
