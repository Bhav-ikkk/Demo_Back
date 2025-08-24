from typing import List, Dict, Any
from langchain.prompts import PromptTemplate
from .base_agent import BaseAgent
from ..models import AgentType

class RiskAnalystAgent(BaseAgent):
    """Risk Analysis specialist - optimized for concise risk assessment"""
    
    def __init__(self):
        super().__init__(AgentType.RISK_ANALYST)
    
    def setup_prompts(self):
        self.analysis_prompt = PromptTemplate.from_template("""
        ROLE: Risk Management Expert
        
        TASK: Assess risks for this product in 2-3 sentences:
        
        IDEA: {product_idea}
        CONTEXT: {context}
        
        RESPOND WITH:
        1. Highest risk factor (5 words max)
        2. Risk probability (Low/Medium/High)
        3. Mitigation strategy (10 words max)
        4. Risk score (1-10)
        
        Be direct. Focus on actionable risks.
        """)
    
    def get_expertise_areas(self) -> List[str]:
        return [
            "Risk Assessment",
            "Mitigation Planning",
            "Probability Analysis",
            "Risk Scoring"
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
