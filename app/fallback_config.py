"""
Fallback AI Configuration
Provides multiple fallback options when primary Gemini API fails
"""

from typing import Dict, List, Optional
from enum import Enum

class FallbackStrategy(Enum):
    """Available fallback strategies"""
    OPENAI = "openai"
    LOCAL_LLM = "local_llm"
    RULE_BASED = "rule_based"
    CACHED_RESPONSES = "cached_responses"
    HYBRID = "hybrid"

class FallbackConfig:
    """Configuration for fallback AI systems"""
    
    # Primary fallback order
    FALLBACK_ORDER = [
        FallbackStrategy.OPENAI,
        FallbackStrategy.RULE_BASED,
        FallbackStrategy.CACHED_RESPONSES,
        FallbackStrategy.HYBRID
    ]
    
    # OpenAI fallback settings
    OPENAI_CONFIG = {
        "model": "gpt-3.5-turbo",
        "max_tokens": 500,
        "temperature": 0.3,
        "fallback_timeout": 15,
        "max_retries": 2
    }
    
    # Local LLM settings (if using Ollama, etc.)
    LOCAL_LLM_CONFIG = {
        "model": "llama2:7b",
        "base_url": "http://localhost:11434",
        "timeout": 30,
        "max_retries": 1
    }
    
    # Rule-based fallback templates
    RULE_BASED_TEMPLATES = {
        "market_researcher": {
            "market_size": [
                "Small market: <$100M",
                "Medium market: $100M-$1B", 
                "Large market: $1B+"
            ],
            "competitors": [
                "Established players dominate",
                "Emerging competition",
                "Blue ocean opportunity"
            ],
            "risks": [
                "Market saturation",
                "Regulatory challenges",
                "Technology disruption"
            ]
        },
        "customer_researcher": {
            "pain_points": [
                "Time inefficiency",
                "Cost concerns",
                "Complexity issues",
                "Integration challenges"
            ],
            "target_customers": [
                "Small businesses",
                "Enterprise users",
                "Individual consumers",
                "Developers"
            ]
        },
        "product_manager": {
            "priorities": [
                "User experience first",
                "Scalable architecture",
                "Market validation",
                "Iterative development"
            ],
            "success_metrics": [
                "User adoption rate",
                "Customer satisfaction",
                "Revenue growth",
                "Market share"
            ]
        },
        "risk_analyst": {
            "risk_levels": [
                "Low: Well-established market",
                "Medium: Emerging technology",
                "High: Unproven concept"
            ],
            "mitigation": [
                "Start with MVP",
                "Validate assumptions",
                "Build partnerships",
                "Secure funding"
            ]
        },
        "designer": {
            "design_principles": [
                "User-centered design",
                "Accessibility first",
                "Mobile responsive",
                "Intuitive navigation"
            ],
            "key_features": [
                "Clean interface",
                "Fast performance",
                "Cross-platform",
                "Customizable"
            ]
        },
        "engineer": {
            "tech_stack": [
                "Modern web framework",
                "Cloud infrastructure",
                "API-first design",
                "Scalable database"
            ],
            "architecture": [
                "Microservices",
                "Event-driven",
                "Containerized",
                "CI/CD pipeline"
            ]
        }
    }
    
    # Cached response patterns
    CACHED_PATTERNS = {
        "mobile_app": {
            "market_size": "Large: $50B+ global mobile app market",
            "competitors": "App Store, Google Play, major tech companies",
            "risks": "High competition, platform dependency",
            "recommendations": "Focus on unique value, build community"
        },
        "saas_platform": {
            "market_size": "Growing: $200B+ SaaS market",
            "competitors": "Established players, new startups",
            "risks": "Customer acquisition costs, churn",
            "recommendations": "Strong onboarding, customer success"
        },
        "ai_tool": {
            "market_size": "Emerging: $15B+ AI tools market",
            "competitors": "OpenAI, Anthropic, specialized tools",
            "risks": "Rapid technology changes, API dependency",
            "recommendations": "Differentiate features, build moats"
        }
    }
    
    # Hybrid fallback settings
    HYBRID_CONFIG = {
        "combine_sources": True,
        "confidence_threshold": 0.6,
        "max_sources": 3,
        "weight_primary": 0.7,
        "weight_fallback": 0.3
    }

# Fallback response quality settings
FALLBACK_QUALITY = {
    "min_response_length": 50,
    "max_response_length": 200,
    "require_key_insights": True,
    "allow_generic_responses": False,
    "confidence_penalty": 0.2  # Reduce confidence for fallback responses
}

# Fallback triggers
FALLBACK_TRIGGERS = {
    "api_timeout": 30,  # seconds
    "api_error_threshold": 3,  # consecutive failures
    "rate_limit_detected": True,
    "quota_exceeded": True,
    "network_timeout": 10,  # seconds
    "invalid_response": True
}

# Fallback monitoring
FALLBACK_MONITORING = {
    "log_fallback_usage": True,
    "track_fallback_performance": True,
    "alert_on_fallback": False,
    "fallback_metrics": [
        "usage_count",
        "response_quality",
        "user_satisfaction",
        "recovery_time"
    ]
}
