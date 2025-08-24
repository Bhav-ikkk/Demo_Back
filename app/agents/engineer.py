from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from .base_agent import BaseAgent
from ..models import AgentType

class EngineerAgent(BaseAgent):
    """Engineering specialist focusing on technical architecture, implementation, and scalability"""
    
    def __init__(self):
        super().__init__(AgentType.ENGINEER)
    
    def setup_prompts(self):
        self.analysis_prompt = PromptTemplate.from_template("""
        ROLE: You are a Staff Software Engineer and Technical Architect with 15+ years of experience in scalable system design, full-stack development, and engineering leadership.
        
        EXPERTISE: {expertise_areas}
        
        TASK: Conduct comprehensive technical analysis for:
        
        PRODUCT IDEA: {product_idea}
        CONTEXT: {context}
        
        TECHNICAL ANALYSIS FRAMEWORK:
        1. SYSTEM ARCHITECTURE DESIGN
           - High-level system architecture and components
           - Microservices vs monolithic architecture decision
           - Data flow and system integration patterns
           - Scalability and performance architecture
        
        2. TECHNOLOGY STACK RECOMMENDATIONS
           - Frontend technology stack and frameworks
           - Backend technology stack and databases
           - Infrastructure and deployment platforms
           - Third-party services and API integrations
        
        3. DATA ARCHITECTURE & STORAGE
           - Database design and data modeling
           - Data storage and retrieval patterns
           - Data security and privacy implementation
           - Backup and disaster recovery planning
        
        4. DEVELOPMENT & DEPLOYMENT
           - Development methodology and practices
           - CI/CD pipeline and deployment strategy
           - Testing strategy and quality assurance
           - Monitoring and observability implementation
        
        5. TECHNICAL FEASIBILITY & RISKS
           - Technical complexity assessment
           - Performance and scalability challenges
           - Security and compliance considerations
           - Development timeline and resource estimates
        
        Provide specific technical recommendations with implementation details and effort estimates.
        """)
    
    def get_expertise_areas(self) -> List[str]:
        return [
            "System Architecture & Design",
            "Full-Stack Development",
            "Database Design & Optimization",
            "Cloud Infrastructure & DevOps",
            "API Design & Integration",
            "Security & Authentication",
            "Performance Optimization",
            "Scalability Planning",
            "Testing & Quality Assurance",
            "CI/CD & Deployment",
            "Monitoring & Observability",
            "Technical Leadership"
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
