"""
AI Response Optimization Configuration
This module contains settings and prompts optimized for concise, focused AI responses.
"""

from typing import Dict, List

# Response length limits for different agent types
AGENT_RESPONSE_LIMITS = {
    "market_researcher": {
        "max_length": 150,
        "target_length": 100,
        "key_points": 4
    },
    "customer_researcher": {
        "max_length": 120,
        "target_length": 80,
        "key_points": 4
    },
    "product_manager": {
        "max_length": 100,
        "target_length": 60,
        "key_points": 4
    },
    "risk_analyst": {
        "max_length": 100,
        "target_length": 60,
        "key_points": 4
    },
    "designer": {
        "max_length": 80,
        "target_length": 50,
        "key_points": 4
    },
    "engineer": {
        "max_length": 100,
        "target_length": 60,
        "key_points": 4
    }
}

# Prompt optimization settings
PROMPT_OPTIMIZATION = {
    "max_tokens": 500,
    "temperature": 0.3,
    "top_p": 0.9,
    "frequency_penalty": 0.1,
    "presence_penalty": 0.1
}

# Response formatting rules
RESPONSE_FORMATTING = {
    "remove_redundancy": True,
    "enforce_word_limits": True,
    "standardize_format": True,
    "add_bullet_points": False,
    "truncate_long_responses": True
}

# Quality control settings
QUALITY_CONTROL = {
    "min_confidence_score": 0.6,
    "max_processing_time_ms": 30000,
    "require_key_insights": True,
    "validate_recommendations": True
}

# Concise prompt templates
CONCISE_PROMPT_TEMPLATES = {
    "market_researcher": """
    ROLE: Market Research Expert
    TASK: Analyze market opportunity in 2-3 sentences
    
    IDEA: {product_idea}
    CONTEXT: {context}
    
    RESPOND WITH:
    1. Market size (one number/range)
    2. Top 2 competitors
    3. Key market risk
    4. One actionable recommendation
    
    Keep each point to 10 words or less. Be direct.
    """,
    
    "customer_researcher": """
    ROLE: Customer Research Expert
    TASK: Identify customer needs in 2-3 sentences
    
    IDEA: {product_idea}
    CONTEXT: {context}
    
    RESPOND WITH:
    1. Primary pain point (5 words max)
    2. Target customer (5 words max)
    3. Key need (5 words max)
    4. Acquisition insight (10 words max)
    
    Be specific. No fluff.
    """,
    
    "product_manager": """
    ROLE: Product Manager
    TASK: Evaluate product strategy in 2-3 sentences
    
    IDEA: {product_idea}
    CONTEXT: {context}
    
    RESPOND WITH:
    1. Product-market fit (1-10)
    2. Top 3 features (5 words each)
    3. MVP timeline (weeks/months)
    4. Success metric (5 words max)
    
    Focus on execution.
    """,
    
    "risk_analyst": """
    ROLE: Risk Management Expert
    TASK: Assess risks in 2-3 sentences
    
    IDEA: {product_idea}
    CONTEXT: {context}
    
    RESPOND WITH:
    1. Highest risk (5 words max)
    2. Probability (Low/Medium/High)
    3. Mitigation (10 words max)
    4. Risk score (1-10)
    
    Be direct. Focus on actionable risks.
    """,
    
    "designer": """
    ROLE: UX/UI Design Expert
    TASK: Evaluate design needs in 2-3 sentences
    
    IDEA: {product_idea}
    CONTEXT: {context}
    
    RESPOND WITH:
    1. Design challenge (5 words max)
    2. Key UI element (5 words max)
    3. Design principle (5 words max)
    4. UX improvement (10 words max)
    
    Focus on user experience.
    """,
    
    "engineer": """
    ROLE: Senior Software Engineer
    TASK: Assess technical feasibility in 2-3 sentences
    
    IDEA: {product_idea}
    CONTEXT: {context}
    
    RESPOND WITH:
    1. Technical complexity (Low/Medium/High)
    2. Tech stack (5 words max)
    3. Key challenge (5 words max)
    4. Timeline (weeks/months)
    
    Focus on implementation. Be realistic.
    """
}

# Response validation rules
RESPONSE_VALIDATION = {
    "required_fields": ["analysis", "recommendations", "concerns", "confidence_score"],
    "field_length_limits": {
        "analysis": 200,
        "recommendations": 100,
        "concerns": 100,
        "reasoning": 150
    },
    "confidence_score_range": (0.0, 1.0)
}

# Performance optimization
PERFORMANCE_OPTIMIZATION = {
    "max_concurrent_agents": 6,
    "agent_timeout_seconds": 30,
    "debate_timeout_seconds": 45,
    "synthesis_timeout_seconds": 60,
    "enable_caching": True,
    "cache_ttl_seconds": 3600
}
