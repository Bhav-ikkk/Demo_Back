from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from .base_agent import BaseAgent
from ..models import AgentType

class DesignerAgent(BaseAgent):
    """Design specialist focusing on UX/UI, design systems, and user experience"""
    
    def __init__(self):
        super().__init__(AgentType.DESIGNER)
    
    def setup_prompts(self):
        self.analysis_prompt = PromptTemplate.from_template("""
        ROLE: You are a Senior Product Designer and UX Strategist with 10+ years of experience in user-centered design, design systems, and digital product design.
        
        EXPERTISE: {expertise_areas}
        
        TASK: Conduct comprehensive design analysis for:
        
        PRODUCT IDEA: {product_idea}
        CONTEXT: {context}
        
        DESIGN ANALYSIS FRAMEWORK:
        1. USER EXPERIENCE STRATEGY
           - User experience goals and principles
           - Information architecture and navigation
           - Interaction design patterns and flows
           - Accessibility and inclusive design considerations
        
        2. VISUAL DESIGN DIRECTION
           - Brand identity and visual language
           - Color palette and typography recommendations
           - UI component library requirements
           - Design system scalability planning
        
        3. INTERFACE DESIGN REQUIREMENTS
           - Key screen and component identification
           - Responsive design considerations
           - Mobile-first design approach
           - Cross-platform consistency requirements
        
        4. USABILITY & ACCESSIBILITY
           - Usability heuristics and best practices
           - WCAG compliance requirements
           - User testing and validation approach
           - Performance and loading considerations
        
        5. DESIGN PROCESS & DELIVERABLES
           - Design methodology and process recommendations
           - Required design deliverables and artifacts
           - Design review and approval workflows
           - Design-to-development handoff process
        
        Provide specific design recommendations with rationale and implementation guidance.
        """)
    
    def get_expertise_areas(self) -> List[str]:
        return [
            "User Experience (UX) Design",
            "User Interface (UI) Design",
            "Design Systems & Component Libraries",
            "Information Architecture",
            "Interaction Design",
            "Visual Design & Branding",
            "Accessibility & Inclusive Design",
            "Responsive & Mobile Design",
            "Prototyping & Wireframing",
            "User Testing & Validation",
            "Design Thinking",
            "Cross-platform Design"
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
