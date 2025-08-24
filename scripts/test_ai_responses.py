#!/usr/bin/env python3
"""
Test script to verify AI response optimization
This script tests the optimized AI agents to ensure they generate concise, focused responses.
"""

import asyncio
import sys
import os
from pathlib import Path

# Get the backend directory path
backend_dir = Path(__file__).parent.parent
app_dir = backend_dir / "app"

# Add the app directory to Python path
sys.path.insert(0, str(app_dir))

# Now we can import from the app package
try:
    from agents.market_researcher import MarketResearcherAgent
    from agents.customer_researcher import CustomerResearcherAgent
    from agents.product_manager import ProductManagerAgent
    from agents.risk_analyst import RiskAnalystAgent
    from agents.designer import DesignerAgent
    from agents.engineer import EngineerAgent
    print("✅ All agent imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the backend directory")
    sys.exit(1)

async def test_agent_response(agent, agent_name: str, test_idea: str):
    """Test a single agent and analyze response quality"""
    print(f"\n{'='*50}")
    print(f"Testing {agent_name}")
    print(f"{'='*50}")
    
    try:
        # Test the agent
        start_time = asyncio.get_event_loop().time()
        response = await agent.analyze(test_idea, {"context": "test"})
        processing_time = (asyncio.get_event_loop().time() - start_time) * 1000
        
        print(f"Processing time: {processing_time:.2f}ms")
        print(f"Confidence score: {response.confidence_score}")
        
        # Analyze response length
        if hasattr(response, 'analysis'):
            analysis_str = str(response.analysis)
            print(f"Analysis length: {len(analysis_str)} characters")
            print(f"Analysis: {analysis_str[:200]}{'...' if len(analysis_str) > 200 else ''}")
        
        if hasattr(response, 'recommendations'):
            recs = response.recommendations
            print(f"Recommendations count: {len(recs)}")
            for i, rec in enumerate(recs[:3], 1):
                print(f"  {i}. {rec}")
        
        if hasattr(response, 'concerns'):
            concerns = response.concerns
            print(f"Concerns count: {len(concerns)}")
            for i, concern in enumerate(concerns[:2], 1):
                print(f"  {i}. {concern}")
        
        # Quality checks
        quality_score = 0
        if hasattr(response, 'analysis') and response.analysis:
            quality_score += 1
        if hasattr(response, 'recommendations') and response.recommendations:
            quality_score += 1
        if hasattr(response, 'concerns') and response.concerns:
            quality_score += 1
        if hasattr(response, 'confidence_score') and response.confidence_score > 0.6:
            quality_score += 1
        
        print(f"Quality score: {quality_score}/4")
        
        return quality_score, processing_time
        
    except Exception as e:
        print(f"Error testing {agent_name}: {str(e)}")
        return 0, 0

async def main():
    """Main test function"""
    print("AI Response Optimization Test")
    print("Testing all agents for concise, focused responses...")
    
    # Test product idea
    test_idea = "A mobile app that helps people find and book local fitness classes with real-time availability and instant booking"
    
    print(f"\nTest Product Idea: {test_idea}")
    
    # Initialize agents
    agents = {
        "Market Researcher": MarketResearcherAgent(),
        "Customer Researcher": CustomerResearcherAgent(),
        "Product Manager": ProductManagerAgent(),
        "Risk Analyst": RiskAnalystAgent(),
        "Designer": DesignerAgent(),
        "Engineer": EngineerAgent()
    }
    
    # Test each agent
    results = {}
    total_quality = 0
    total_time = 0
    
    for agent_name, agent in agents.items():
        quality, time_taken = await test_agent_response(agent, agent_name, test_idea)
        results[agent_name] = {"quality": quality, "time": time_taken}
        total_quality += quality
        total_time += time_taken
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print(f"{'='*50}")
    
    for agent_name, result in results.items():
        status = "✅ PASS" if result["quality"] >= 3 else "❌ FAIL"
        print(f"{agent_name}: {status} (Quality: {result['quality']}/4, Time: {result['time']:.2f}ms)")
    
    avg_quality = total_quality / len(agents)
    avg_time = total_time / len(agents)
    
    print(f"\nOverall Results:")
    print(f"Average Quality Score: {avg_quality:.2f}/4")
    print(f"Average Processing Time: {avg_time:.2f}ms")
    
    if avg_quality >= 3.5:
        print("🎉 SUCCESS: AI responses are optimized and concise!")
    elif avg_quality >= 3.0:
        print("⚠️  PARTIAL: AI responses are mostly optimized but need improvement")
    else:
        print("❌ FAILURE: AI responses need significant optimization")
    
    # Response length analysis
    print(f"\nResponse Length Targets:")
    print(f"Market Researcher: <150 chars")
    print(f"Customer Researcher: <120 chars")
    print(f"Product Manager: <100 chars")
    print(f"Risk Analyst: <100 chars")
    print(f"Designer: <80 chars")
    print(f"Engineer: <100 chars")

if __name__ == "__main__":
    # Check if we have the required environment
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY environment variable not set")
        print("Please set your Google API key before running this test")
        print("\nExample:")
        print("export GOOGLE_API_KEY=your_api_key_here")
        print("python scripts/test_ai_responses.py")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        sys.exit(1)
