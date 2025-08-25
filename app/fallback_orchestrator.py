"""
Fallback AI Orchestrator
Manages automatic fallback when primary Gemini API fails
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import structlog

from .fallback_config import FallbackConfig, FallbackStrategy, FALLBACK_TRIGGERS
from .fallback_ai import (
    OpenAIFallback, RuleBasedFallback, CachedResponsesFallback, HybridFallback
)
from .models import AgentResponseModel, AgentType

logger = structlog.get_logger()

class FallbackState(Enum):
    """Current fallback state"""
    PRIMARY = "primary"
    FALLBACK = "fallback"
    DEGRADED = "degraded"
    EMERGENCY = "emergency"

class FallbackOrchestrator:
    """Orchestrates fallback AI systems when primary API fails"""
    
    def __init__(self):
        self.state = FallbackState.PRIMARY
        self.fallback_methods = {}
        self.error_count = 0
        self.last_error_time = 0
        self.fallback_usage_stats = {}
        self._initialize_fallback_methods()
    
    def _initialize_fallback_methods(self):
        """Initialize all available fallback methods"""
        try:
            # Initialize OpenAI fallback
            openai_fallback = OpenAIFallback()
            if openai_fallback.is_available():
                self.fallback_methods[FallbackStrategy.OPENAI] = openai_fallback
                logger.info("OpenAI fallback initialized")
            
            # Initialize rule-based fallback (always available)
            self.fallback_methods[FallbackStrategy.RULE_BASED] = RuleBasedFallback()
            logger.info("Rule-based fallback initialized")
            
            # Initialize cached responses fallback (always available)
            self.fallback_methods[FallbackStrategy.CACHED_RESPONSES] = CachedResponsesFallback()
            logger.info("Cached responses fallback initialized")
            
            # Initialize hybrid fallback
            available_methods = [m for m in self.fallback_methods.values() if m.is_available()]
            if len(available_methods) > 1:
                self.fallback_methods[FallbackStrategy.HYBRID] = HybridFallback(available_methods)
                logger.info("Hybrid fallback initialized")
            
            logger.info(f"Initialized {len(self.fallback_methods)} fallback methods")
            
        except Exception as e:
            logger.error("Failed to initialize fallback methods", error=str(e))
    
    def should_use_fallback(self, error: Exception = None) -> bool:
        """Determine if fallback should be used"""
        current_time = time.time()
        
        # Check error threshold
        if self.error_count >= FALLBACK_TRIGGERS["api_error_threshold"]:
            return True
        
        # Check if we're already in fallback mode
        if self.state != FallbackState.PRIMARY:
            return True
        
        # Check if error is a fallback trigger
        if error:
            error_str = str(error).lower()
            
            # Rate limiting
            if "rate limit" in error_str or "quota" in error_str:
                self.state = FallbackState.FALLBACK
                return True
            
            # API errors
            if "timeout" in error_str or "connection" in error_str:
                if current_time - self.last_error_time < 60:  # Within 1 minute
                    self.error_count += 1
                else:
                    self.error_count = 1
                self.last_error_time = current_time
                
                if self.error_count >= FALLBACK_TRIGGERS["api_error_threshold"]:
                    self.state = FallbackState.FALLBACK
                    return True
        
        return False
    
    def get_fallback_method(self, agent_type: str) -> Optional[Any]:
        """Get the best available fallback method"""
        if not self.fallback_methods:
            return None
        
        # Try fallback methods in order of preference
        for strategy in FallbackConfig.FALLBACK_ORDER:
            if strategy in self.fallback_methods:
                method = self.fallback_methods[strategy]
                if method.is_available():
                    return method
        
        # If no preferred methods available, return any available method
        for method in self.fallback_methods.values():
            if method.is_available():
                return method
        
        return None
    
    async def execute_with_fallback(self, primary_func, agent_type: str, 
                                  product_idea: str, context: Dict[str, Any] = None,
                                  *args, **kwargs) -> Tuple[AgentResponseModel, bool]:
        """
        Execute primary function with automatic fallback
        
        Returns:
            Tuple of (response, used_fallback)
        """
        try:
            # Try primary method first
            if self.state == FallbackState.PRIMARY:
                try:
                    response = await primary_func(*args, **kwargs)
                    # Reset error count on success
                    self.error_count = 0
                    return response, False
                except Exception as e:
                    logger.warning("Primary method failed, considering fallback", 
                                 error=str(e), agent_type=agent_type)
                    
                    if self.should_use_fallback(e):
                        return await self._execute_fallback(agent_type, product_idea, context), True
                    else:
                        raise  # Re-raise if fallback not needed yet
            
            # Already in fallback mode
            return await self._execute_fallback(agent_type, product_idea, context), True
            
        except Exception as e:
            logger.error("All methods failed", error=str(e), agent_type=agent_type)
            # Try emergency fallback
            return await self._execute_emergency_fallback(agent_type, product_idea, context), True
    
    async def _execute_fallback(self, agent_type: str, product_idea: str, 
                              context: Dict[str, Any] = None) -> AgentResponseModel:
        """Execute fallback method"""
        fallback_method = self.get_fallback_method(agent_type)
        
        if not fallback_method:
            raise RuntimeError("No fallback methods available")
        
        try:
            logger.info("Executing fallback method", 
                       method=fallback_method.__class__.__name__, 
                       agent_type=agent_type)
            
            response = await fallback_method.generate_response(agent_type, product_idea, context)
            
            # Track fallback usage
            self._track_fallback_usage(fallback_method.__class__.__name__, True)
            
            # Add fallback indicator to response
            response.reasoning = f"[FALLBACK] {response.reasoning}"
            
            return response
            
        except Exception as e:
            logger.error("Fallback method failed", 
                        method=fallback_method.__class__.__name__, 
                        error=str(e))
            
            # Track fallback failure
            self._track_fallback_usage(fallback_method.__class__.__name__, False)
            
            # Try emergency fallback
            return await self._execute_emergency_fallback(agent_type, product_idea, context)
    
    async def _execute_emergency_fallback(self, agent_type: str, product_idea: str, 
                                        context: Dict[str, Any] = None) -> AgentResponseModel:
        """Execute emergency fallback when all else fails"""
        self.state = FallbackState.EMERGENCY
        
        logger.warning("Executing emergency fallback", agent_type=agent_type)
        
        # Create minimal emergency response
        emergency_response = AgentResponseModel(
            agent_type=AgentType(agent_type),
            analysis=f"Emergency analysis for {agent_type}: {product_idea[:100]}...",
            recommendations=["Contact support", "Try again later", "Check system status"],
            concerns=["System degraded", "Limited functionality"],
            confidence_score=0.1,
            reasoning="Emergency fallback response - system experiencing issues",
            supporting_data="emergency_mode"
        )
        
        return emergency_response
    
    def _track_fallback_usage(self, method_name: str, success: bool):
        """Track fallback method usage statistics"""
        if method_name not in self.fallback_usage_stats:
            self.fallback_usage_stats[method_name] = {
                "total_attempts": 0,
                "successful_attempts": 0,
                "last_used": None
            }
        
        stats = self.fallback_usage_stats[method_name]
        stats["total_attempts"] += 1
        if success:
            stats["successful_attempts"] += 1
        stats["last_used"] = time.time()
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """Get fallback usage statistics"""
        stats = {
            "current_state": self.state.value,
            "error_count": self.error_count,
            "last_error_time": self.last_error_time,
            "available_fallbacks": len([m for m in self.fallback_methods.values() if m.is_available()]),
            "method_stats": self.fallback_usage_stats
        }
        
        # Calculate success rates
        for method_name, method_stats in self.fallback_usage_stats.items():
            if method_stats["total_attempts"] > 0:
                method_stats["success_rate"] = method_stats["successful_attempts"] / method_stats["total_attempts"]
            else:
                method_stats["success_rate"] = 0.0
        
        return stats
    
    def reset_to_primary(self):
        """Reset orchestrator to primary mode"""
        self.state = FallbackState.PRIMARY
        self.error_count = 0
        self.last_error_time = 0
        logger.info("Fallback orchestrator reset to primary mode")
    
    def is_healthy(self) -> bool:
        """Check if the fallback system is healthy"""
        if self.state == FallbackState.EMERGENCY:
            return False
        
        # Check if we have at least one fallback method available
        available_fallbacks = [m for m in self.fallback_methods.values() if m.is_available()]
        return len(available_fallbacks) > 0
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        return {
            "healthy": self.is_healthy(),
            "state": self.state.value,
            "available_fallbacks": len([m for m in self.fallback_methods.values() if m.is_available()]),
            "total_fallbacks": len(self.fallback_methods),
            "error_count": self.error_count,
            "last_error_time": self.last_error_time,
            "fallback_methods": {
                name: {
                    "available": method.is_available(),
                    "confidence": method.get_confidence_score()
                }
                for name, method in self.fallback_methods.items()
            }
        }

# Global fallback orchestrator instance
fallback_orchestrator = FallbackOrchestrator()
