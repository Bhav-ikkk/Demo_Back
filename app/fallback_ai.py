"""
Fallback AI Implementations
Provides alternative AI responses when primary Gemini API fails
"""

import asyncio
import json
import random
import time
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod
import structlog
from openai import AsyncOpenAI
import httpx

from .fallback_config import FallbackConfig, FallbackStrategy, FALLBACK_QUALITY
from .models import AgentResponseModel, AgentType

logger = structlog.get_logger()

class FallbackAI(ABC):
    """Base class for fallback AI implementations"""
    
    @abstractmethod
    async def generate_response(self, agent_type: str, product_idea: str, context: Dict[str, Any] = None) -> AgentResponseModel:
        """Generate AI response using fallback method"""
        pass
    
    @abstractmethod
    def get_confidence_score(self) -> float:
        """Get confidence score for this fallback method"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this fallback method is available"""
        pass

class OpenAIFallback(FallbackAI):
    """OpenAI API fallback implementation"""
    
    def __init__(self):
        self.client = None
        self.config = FallbackConfig.OPENAI_CONFIG
        self._setup_client()
    
    def _setup_client(self):
        """Setup OpenAI client if API key is available"""
        try:
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.client = AsyncOpenAI(api_key=api_key)
                logger.info("OpenAI fallback client initialized")
            else:
                logger.warning("OpenAI API key not found, fallback unavailable")
        except Exception as e:
            logger.error("Failed to initialize OpenAI client", error=str(e))
    
    def is_available(self) -> bool:
        return self.client is not None
    
    def get_confidence_score(self) -> float:
        return 0.8  # High confidence for OpenAI
    
    async def generate_response(self, agent_type: str, product_idea: str, context: Dict[str, Any] = None) -> AgentResponseModel:
        """Generate response using OpenAI API"""
        if not self.is_available():
            raise RuntimeError("OpenAI fallback not available")
        
        try:
            # Create agent-specific prompt
            prompt = self._create_prompt(agent_type, product_idea, context)
            
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.config["model"],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.config["max_tokens"],
                    temperature=self.config["temperature"]
                ),
                timeout=self.config["fallback_timeout"]
            )
            
            content = response.choices[0].message.content
            parsed_response = self._parse_openai_response(content, agent_type)
            
            return AgentResponseModel(
                agent_type=AgentType(agent_type),
                analysis=parsed_response["analysis"],
                recommendations=parsed_response["recommendations"],
                concerns=parsed_response["concerns"],
                confidence_score=parsed_response["confidence_score"] * FALLBACK_QUALITY["confidence_penalty"],
                reasoning=parsed_response["reasoning"],
                supporting_data=parsed_response.get("supporting_data")
            )
            
        except Exception as e:
            logger.error("OpenAI fallback failed", error=str(e))
            raise
    
    def _create_prompt(self, agent_type: str, product_idea: str, context: Dict[str, Any] = None) -> str:
        """Create agent-specific prompt for OpenAI"""
        base_prompt = f"""
        You are a {agent_type.replace('_', ' ').title()} expert. Analyze this product idea and provide concise insights.
        
        Product Idea: {product_idea}
        Context: {context or 'No additional context'}
        
        Provide a JSON response with these fields:
        - analysis: Brief analysis in 2-3 sentences
        - recommendations: List of 2-3 actionable recommendations
        - concerns: List of 1-2 key concerns
        - confidence_score: Number between 0.0 and 1.0
        - reasoning: One sentence explaining your analysis
        - supporting_data: Brief supporting data point if available
        
        Keep responses concise and actionable. Return only valid JSON.
        """
        return base_prompt
    
    def _parse_openai_response(self, response: str, agent_type: str) -> Dict[str, Any]:
        """Parse OpenAI response into structured format"""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback parsing if JSON extraction fails
        return self._fallback_parsing(response, agent_type)
    
    def _fallback_parsing(self, response: str, agent_type: str) -> Dict[str, Any]:
        """Fallback parsing when JSON extraction fails"""
        return {
            "analysis": response[:200] if response else "Analysis unavailable",
            "recommendations": ["Review and refine approach", "Validate with users"],
            "concerns": ["Requires further analysis"],
            "confidence_score": 0.6,
            "reasoning": "Generated using fallback parsing",
            "supporting_data": None
        }

class RuleBasedFallback(FallbackAI):
    """Rule-based fallback using predefined templates"""
    
    def __init__(self):
        self.templates = FallbackConfig.RULE_BASED_TEMPLATES
        self.cached_patterns = FallbackConfig.CACHED_PATTERNS
    
    def is_available(self) -> bool:
        return True  # Always available
    
    def get_confidence_score(self) -> float:
        return 0.5  # Lower confidence for rule-based
    
    async def generate_response(self, agent_type: str, product_idea: str, context: Dict[str, Any] = None) -> AgentResponseModel:
        """Generate response using rule-based templates"""
        try:
            # Analyze product idea to determine category
            category = self._categorize_product(product_idea)
            
            # Get relevant templates
            agent_templates = self.templates.get(agent_type, {})
            cached_patterns = self.cached_patterns.get(category, {})
            
            # Generate response using templates
            response = self._generate_from_templates(
                agent_type, product_idea, agent_templates, cached_patterns
            )
            
            return AgentResponseModel(
                agent_type=AgentType(agent_type),
                analysis=response["analysis"],
                recommendations=response["recommendations"],
                concerns=response["concerns"],
                confidence_score=response["confidence_score"] * FALLBACK_QUALITY["confidence_penalty"],
                reasoning=response["reasoning"],
                supporting_data=response.get("supporting_data")
            )
            
        except Exception as e:
            logger.error("Rule-based fallback failed", error=str(e))
            raise
    
    def _categorize_product(self, product_idea: str) -> str:
        """Categorize product idea for template selection"""
        idea_lower = product_idea.lower()
        
        if any(word in idea_lower for word in ["app", "mobile", "ios", "android"]):
            return "mobile_app"
        elif any(word in idea_lower for word in ["saas", "platform", "software", "tool"]):
            return "saas_platform"
        elif any(word in idea_lower for word in ["ai", "artificial intelligence", "machine learning"]):
            return "ai_tool"
        else:
            return "general"
    
    def _generate_from_templates(self, agent_type: str, product_idea: str, 
                               agent_templates: Dict, cached_patterns: Dict) -> Dict[str, Any]:
        """Generate response by combining templates and patterns"""
        
        # Select random items from templates
        analysis_parts = []
        recommendations = []
        concerns = []
        
        if agent_type == "market_researcher":
            if "market_size" in agent_templates:
                analysis_parts.append(random.choice(agent_templates["market_size"]))
            if "competitors" in agent_templates:
                analysis_parts.append(random.choice(agent_templates["competitors"]))
            if "risks" in agent_templates:
                concerns.append(random.choice(agent_templates["risks"]))
            
            # Add cached patterns if available
            if cached_patterns:
                if "market_size" in cached_patterns:
                    analysis_parts.append(cached_patterns["market_size"])
                if "recommendations" in cached_patterns:
                    recommendations.append(cached_patterns["recommendations"])
        
        elif agent_type == "customer_researcher":
            if "pain_points" in agent_templates:
                analysis_parts.append(f"Pain point: {random.choice(agent_templates['pain_points'])}")
            if "target_customers" in agent_templates:
                analysis_parts.append(f"Target: {random.choice(agent_templates['target_customers'])}")
        
        elif agent_type == "product_manager":
            if "priorities" in agent_templates:
                recommendations.extend(random.sample(agent_templates["priorities"], 2))
            if "success_metrics" in agent_templates:
                analysis_parts.append(f"Success: {random.choice(agent_templates['success_metrics'])}")
        
        elif agent_type == "risk_analyst":
            if "risk_levels" in agent_templates:
                analysis_parts.append(random.choice(agent_templates["risk_levels"]))
            if "mitigation" in agent_templates:
                recommendations.extend(random.sample(agent_templates["mitigation"], 2))
        
        elif agent_type == "designer":
            if "design_principles" in agent_templates:
                recommendations.extend(random.sample(agent_templates["design_principles"], 2))
            if "key_features" in agent_templates:
                analysis_parts.append(f"Features: {', '.join(random.sample(agent_templates['key_features'], 2))}")
        
        elif agent_type == "engineer":
            if "tech_stack" in agent_templates:
                recommendations.extend(random.sample(agent_templates["tech_stack"], 2))
            if "architecture" in agent_templates:
                analysis_parts.append(f"Architecture: {random.choice(agent_templates['architecture'])}")
        
        # Ensure we have minimum content
        if not analysis_parts:
            analysis_parts.append(f"Analysis for {agent_type.replace('_', ' ')}")
        if not recommendations:
            recommendations.append("Focus on core value proposition")
        if not concerns:
            concerns.append("Requires market validation")
        
        return {
            "analysis": ". ".join(analysis_parts),
            "recommendations": recommendations,
            "concerns": concerns,
            "confidence_score": 0.5,
            "reasoning": f"Generated using rule-based templates for {agent_type}",
            "supporting_data": None
        }

class CachedResponsesFallback(FallbackAI):
    """Fallback using cached/pattern-matched responses"""
    
    def __init__(self):
        self.patterns = FallbackConfig.CACHED_PATTERNS
        self.response_cache = {}
    
    def is_available(self) -> bool:
        return True  # Always available
    
    def get_confidence_score(self) -> float:
        return 0.4  # Lower confidence for cached responses
    
    async def generate_response(self, agent_type: str, product_idea: str, context: Dict[str, Any] = None) -> AgentResponseModel:
        """Generate response using cached patterns"""
        try:
            # Find best matching pattern
            pattern = self._find_best_pattern(product_idea)
            
            # Generate response based on pattern and agent type
            response = self._generate_from_pattern(agent_type, pattern, product_idea)
            
            return AgentResponseModel(
                agent_type=AgentType(agent_type),
                analysis=response["analysis"],
                recommendations=response["recommendations"],
                concerns=response["concerns"],
                confidence_score=response["confidence_score"] * FALLBACK_QUALITY["confidence_penalty"],
                reasoning=response["reasoning"],
                supporting_data=response.get("supporting_data")
            )
            
        except Exception as e:
            logger.error("Cached responses fallback failed", error=str(e))
            raise
    
    def _find_best_pattern(self, product_idea: str) -> str:
        """Find the best matching pattern for the product idea"""
        idea_lower = product_idea.lower()
        
        # Score each pattern
        pattern_scores = {}
        for pattern, data in self.patterns.items():
            score = 0
            if pattern == "mobile_app" and any(word in idea_lower for word in ["app", "mobile", "ios", "android"]):
                score += 3
            elif pattern == "saas_platform" and any(word in idea_lower for word in ["saas", "platform", "software", "tool"]):
                score += 3
            elif pattern == "ai_tool" and any(word in idea_lower for word in ["ai", "artificial intelligence", "machine learning"]):
                score += 3
            
            pattern_scores[pattern] = score
        
        # Return best pattern or default
        best_pattern = max(pattern_scores, key=pattern_scores.get)
        return best_pattern if pattern_scores[best_pattern] > 0 else "general"
    
    def _generate_from_pattern(self, agent_type: str, pattern: str, product_idea: str) -> Dict[str, Any]:
        """Generate response from cached pattern"""
        pattern_data = self.patterns.get(pattern, {})
        
        # Create agent-specific response
        if agent_type == "market_researcher":
            analysis = f"Market: {pattern_data.get('market_size', 'Varies by segment')}. "
            analysis += f"Competition: {pattern_data.get('competitors', 'Market dependent')}."
            recommendations = [pattern_data.get('recommendations', 'Focus on differentiation')]
            concerns = [pattern_data.get('risks', 'Market validation required')]
        
        elif agent_type == "customer_researcher":
            analysis = f"Customer needs vary by segment. {pattern_data.get('recommendations', 'Focus on core value')}."
            recommendations = ["Conduct user research", "Validate pain points"]
            concerns = ["Customer segment identification"]
        
        elif agent_type == "product_manager":
            analysis = f"Product strategy should align with {pattern} market dynamics."
            recommendations = ["Build MVP", "Iterate based on feedback", "Focus on core features"]
            concerns = ["Product-market fit"]
        
        elif agent_type == "risk_analyst":
            analysis = f"Risk profile typical for {pattern} category."
            recommendations = ["Start small", "Validate assumptions", "Build partnerships"]
            concerns = [pattern_data.get('risks', 'Market uncertainty')]
        
        elif agent_type == "designer":
            analysis = f"Design should prioritize user experience for {pattern} users."
            recommendations = ["User-centered design", "Accessibility first", "Mobile responsive"]
            concerns = ["User adoption"]
        
        elif agent_type == "engineer":
            analysis = f"Technical architecture should support {pattern} requirements."
            recommendations = ["Scalable architecture", "API-first design", "Cloud infrastructure"]
            concerns = ["Technical complexity"]
        
        else:
            analysis = f"General analysis for {agent_type} perspective."
            recommendations = ["Validate approach", "Build incrementally"]
            concerns = ["Requires further analysis"]
        
        return {
            "analysis": analysis,
            "recommendations": recommendations,
            "concerns": concerns,
            "confidence_score": 0.4,
            "reasoning": f"Generated from cached pattern: {pattern}",
            "supporting_data": pattern
        }

class HybridFallback(FallbackAI):
    """Hybrid fallback combining multiple sources"""
    
    def __init__(self, fallback_methods: List[FallbackAI]):
        self.fallback_methods = fallback_methods
        self.config = FallbackConfig.HYBRID_CONFIG
    
    def is_available(self) -> bool:
        return any(method.is_available() for method in self.fallback_methods)
    
    def get_confidence_score(self) -> float:
        if not self.fallback_methods:
            return 0.0
        return sum(method.get_confidence_score() for method in self.fallback_methods) / len(self.fallback_methods)
    
    async def generate_response(self, agent_type: str, product_idea: str, context: Dict[str, Any] = None) -> AgentResponseModel:
        """Generate response by combining multiple fallback methods"""
        try:
            available_methods = [m for m in self.fallback_methods if m.is_available()]
            if not available_methods:
                raise RuntimeError("No fallback methods available")
            
            # Get responses from available methods
            responses = []
            for method in available_methods[:self.config["max_sources"]]:
                try:
                    response = await method.generate_response(agent_type, product_idea, context)
                    responses.append(response)
                except Exception as e:
                    logger.warning(f"Fallback method {method.__class__.__name__} failed", error=str(e))
                    continue
            
            if not responses:
                raise RuntimeError("All fallback methods failed")
            
            # Combine responses
            combined_response = self._combine_responses(responses, agent_type)
            
            return combined_response
            
        except Exception as e:
            logger.error("Hybrid fallback failed", error=str(e))
            raise
    
    def _combine_responses(self, responses: List[AgentResponseModel], agent_type: str) -> AgentResponseModel:
        """Combine multiple fallback responses into one"""
        if len(responses) == 1:
            return responses[0]
        
        # Combine analysis
        analysis_parts = [r.analysis for r in responses if r.analysis]
        combined_analysis = ". ".join(analysis_parts[:2])  # Take first 2 analyses
        
        # Combine recommendations
        all_recommendations = []
        for r in responses:
            if r.recommendations:
                all_recommendations.extend(r.recommendations)
        combined_recommendations = list(set(all_recommendations))[:3]  # Remove duplicates, limit to 3
        
        # Combine concerns
        all_concerns = []
        for r in responses:
            if r.concerns:
                all_concerns.extend(r.concerns)
        combined_concerns = list(set(all_concerns))[:2]  # Remove duplicates, limit to 2
        
        # Calculate weighted confidence
        total_confidence = sum(r.confidence_score for r in responses)
        avg_confidence = total_confidence / len(responses)
        
        # Combine reasoning
        reasoning = f"Combined from {len(responses)} fallback sources"
        
        return AgentResponseModel(
            agent_type=responses[0].agent_type,
            analysis=combined_analysis,
            recommendations=combined_recommendations,
            concerns=combined_concerns,
            confidence_score=avg_confidence * FALLBACK_QUALITY["confidence_penalty"],
            reasoning=reasoning,
            supporting_data=None
        )
