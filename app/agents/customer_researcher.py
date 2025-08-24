from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from .base_agent import BaseAgent
from ..models import AgentType

class CustomerResearcherAgent(BaseAgent):
    """Customer Research specialist focusing on user needs, personas, and behavior analysis"""
    
    def __init__(self):
        super().__init__(AgentType.CUSTOMER_RESEARCHER)
    
    def setup_prompts(self):
        self.analysis_prompt = PromptTemplate.from_template("""
        ROLE: You are a Lead User Experience Researcher and Customer Insights Specialist with deep expertise in user-centered design and behavioral psychology.
        
        EXPERTISE: {expertise_areas}
        
        TASK: Conduct comprehensive customer research and user analysis for:
        
        PRODUCT IDEA: {product_idea}
        CONTEXT: {context}
        
        RESEARCH FRAMEWORK:
        1. USER PERSONA DEVELOPMENT
           - Primary and secondary user personas
           - Demographics, psychographics, and behavioral patterns
           - User goals, motivations, and pain points
           - Technology adoption patterns and preferences
        
        2. USER JOURNEY MAPPING
           - Current state user journey analysis
           - Touchpoint identification and pain point mapping
           - Opportunity areas for improvement
           - Future state journey optimization
        
        3. NEEDS ASSESSMENT & VALIDATION
           - Functional, emotional, and social needs analysis
           - Jobs-to-be-done framework application
           - Need prioritization and validation approach
           - Unmet needs and opportunity gaps
        
        4. BEHAVIORAL ANALYSIS
           - User behavior patterns and triggers
           - Decision-making process and criteria
           - Adoption barriers and enablers
           - Usage patterns and engagement drivers
        
        5. RESEARCH METHODOLOGY RECOMMENDATIONS
           - Recommended research methods and approaches
           - Sample size and recruitment strategies
           - Key research questions and hypotheses
           - Success metrics and validation criteria
        
        Provide evidence-based insights with specific recommendations for user validation and research.
        """)
    
    def get_expertise_areas(self) -> List[str]:
        return [
            "User Persona Development",
            "Customer Journey Mapping",
            "User Needs Analysis",
            "Behavioral Psychology",
            "User Experience Research",
            "Survey Design & Analysis",
            "Interview & Focus Group Facilitation",
            "Usability Testing",
            "Customer Segmentation",
            "Jobs-to-be-Done Framework",
            "Design Thinking",
            "Customer Validation"
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
