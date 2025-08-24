from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from .base_agent import BaseAgent
from ..models import AgentType

class RiskAnalystAgent(BaseAgent):
    """Risk Analysis specialist focusing on business, technical, and market risks"""
    
    def __init__(self):
        super().__init__(AgentType.RISK_ANALYST)
    
    def setup_prompts(self):
        self.analysis_prompt = PromptTemplate.from_template("""
        ROLE: You are a Senior Risk Management Analyst with expertise in business risk assessment, regulatory compliance, and strategic risk mitigation across technology and product development.
        
        EXPERTISE: {expertise_areas}
        
        TASK: Conduct comprehensive risk analysis for:
        
        PRODUCT IDEA: {product_idea}
        CONTEXT: {context}
        
        RISK ASSESSMENT FRAMEWORK:
        1. BUSINESS RISKS
           - Market acceptance and adoption risks
           - Revenue and profitability risks
           - Competitive response risks
           - Business model viability risks
        
        2. TECHNICAL RISKS
           - Technology feasibility and scalability risks
           - Security and data privacy risks
           - Integration and compatibility risks
           - Performance and reliability risks
        
        3. OPERATIONAL RISKS
           - Resource availability and capability risks
           - Timeline and delivery risks
           - Quality assurance and testing risks
           - Support and maintenance risks
        
        4. REGULATORY & COMPLIANCE RISKS
           - Legal and regulatory compliance requirements
           - Data protection and privacy regulations
           - Industry-specific compliance needs
           - Intellectual property risks
        
        5. FINANCIAL RISKS
           - Development cost overruns
           - Market size and revenue projections
           - Funding and investment risks
           - Return on investment concerns
        
        For each risk category, provide:
        - Risk probability (Low/Medium/High)
        - Impact severity (Low/Medium/High)
        - Mitigation strategies
        - Contingency plans
        - Monitoring and early warning indicators
        """)
    
    def get_expertise_areas(self) -> List[str]:
        return [
            "Business Risk Assessment",
            "Technical Risk Analysis",
            "Regulatory Compliance",
            "Data Privacy & Security",
            "Financial Risk Management",
            "Operational Risk Assessment",
            "Market Risk Analysis",
            "Legal & IP Risk Evaluation",
            "Risk Mitigation Planning",
            "Crisis Management",
            "Audit & Compliance",
            "Insurance & Risk Transfer"
        ]
    
    async def assess_security_risks(self, product_idea: str, data_types: List[str] = None) -> Dict[str, Any]:
        """Specialized method for security risk assessment"""
        security_prompt = PromptTemplate.from_template("""
        Conduct detailed security risk assessment for: {product_idea}
        
        Data types handled: {data_types}
        
        Analyze:
        1. Data security and privacy risks
        2. Authentication and authorization risks
        3. Infrastructure security risks
        4. Compliance requirements (GDPR, CCPA, etc.)
        5. Incident response planning
        
        Provide specific security recommendations and controls.
        """)
        
        chain = security_prompt | self.llm
        response = await chain.ainvoke({
            "product_idea": product_idea,
            "data_types": data_types or "Standard user data"
        })
        
        return {"security_risk_assessment": response.content}
