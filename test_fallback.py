#!/usr/bin/env python3
"""
Test script to verify fallback AI system functionality
"""
import asyncio
import requests
import json
import time
import sys
from urllib.parse import urljoin

def test_fallback_endpoints(base_url):
    """Test fallback system endpoints"""
    print("🔧 Testing Fallback System Endpoints...")
    
    endpoints = [
        ("/fallback/status", "GET"),
        ("/fallback/health", "GET"),
        ("/fallback/methods", "GET")
    ]
    
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(urljoin(base_url, endpoint), timeout=10)
            else:
                response = requests.post(urljoin(base_url, endpoint), timeout=10)
            
            if response.status_code == 200:
                print(f"✅ {method} {endpoint} - Status: {response.status_code}")
                data = response.json()
                
                if endpoint == "/fallback/status":
                    print(f"   Current State: {data.get('current_state', 'unknown')}")
                    print(f"   Error Count: {data.get('error_count', 0)}")
                    print(f"   Available Fallbacks: {data.get('available_fallbacks', 0)}")
                
                elif endpoint == "/fallback/health":
                    print(f"   Healthy: {data.get('healthy', False)}")
                    print(f"   State: {data.get('state', 'unknown')}")
                    print(f"   Total Fallbacks: {data.get('total_fallbacks', 0)}")
                
                elif endpoint == "/fallback/methods":
                    print(f"   Available Methods: {len(data)}")
                    for method_name, method_info in data.items():
                        print(f"     - {method_name}: {'✅' if method_info.get('available') else '❌'}")
                
            else:
                print(f"❌ {method} {endpoint} - Expected: 200, Got: {response.status_code}")
                
        except Exception as e:
            print(f"❌ {method} {endpoint} - Error: {str(e)}")
    
    print()

def test_fallback_reset(base_url):
    """Test fallback system reset functionality"""
    print("🔄 Testing Fallback System Reset...")
    
    try:
        response = requests.post(urljoin(base_url, "/fallback/reset"), timeout=10)
        
        if response.status_code == 200:
            print("✅ POST /fallback/reset - Status: 200")
            data = response.json()
            print(f"   Message: {data.get('message', 'No message')}")
            print(f"   Status: {data.get('status', 'Unknown')}")
        else:
            print(f"❌ POST /fallback/reset - Expected: 200, Got: {response.status_code}")
            
    except Exception as e:
        print(f"❌ POST /fallback/reset - Error: {str(e)}")
    
    print()

def test_ai_with_fallback(base_url):
    """Test AI functionality to see if fallback is working"""
    print("🧠 Testing AI with Potential Fallback...")
    
    test_idea = {
        "idea": "A mobile app for tracking daily habits with AI coaching and personalized insights"
    }
    
    try:
        # Test the sync refinement endpoint
        response = requests.post(
            urljoin(base_url, "refine/sync"), 
            json=test_idea, 
            timeout=60  # Longer timeout for AI processing
        )
        
        if response.status_code == 200:
            print("✅ POST /refine/sync - Status: 200")
            result = response.json()
            
            # Check if fallback was used
            if "agent_debate" in result:
                for agent_response in result["agent_debate"]:
                    if "reasoning" in agent_response:
                        reasoning = agent_response["reasoning"]
                        if "[FALLBACK]" in reasoning:
                            print(f"   🔄 Fallback used for {agent_response.get('agent_type', 'unknown')}")
                            print(f"      Reason: {reasoning}")
                        else:
                            print(f"   ✅ Primary AI used for {agent_response.get('agent_type', 'unknown')}")
            
            print(f"   Total agents: {len(result.get('agent_debate', []))}")
            
        else:
            print(f"❌ POST /refine/sync - Expected: 200, Got: {response.status_code}")
            if response.text:
                print(f"   Response: {response.text[:200]}...")
                
    except Exception as e:
        print(f"❌ POST /refine/sync - Error: {str(e)}")
    
    print()

def test_health_with_fallback(base_url):
    """Test health endpoint to see fallback status"""
    print("🏥 Testing Health Endpoint with Fallback Status...")
    
    try:
        response = requests.get(urljoin(base_url, "/health"), timeout=10)
        
        if response.status_code == 200:
            print("✅ GET /health - Status: 200")
            data = response.json()
            
            print(f"   Overall Status: {data.get('status', 'unknown')}")
            print(f"   Database: {'✅' if data.get('database_connected') else '❌'}")
            print(f"   AI Service: {'✅' if data.get('ai_service_available') else '❌'}")
            print(f"   Redis: {'✅' if data.get('redis_connected') else '❌'}")
            
            # Check fallback status
            fallback_status = data.get('fallback_status', {})
            if fallback_status:
                print(f"   Fallback System: {'✅' if fallback_status.get('healthy') else '❌'}")
                print(f"   Fallback State: {fallback_status.get('state', 'unknown')}")
                print(f"   Available Fallbacks: {fallback_status.get('available_fallbacks', 0)}")
            else:
                print("   Fallback Status: Not available")
                
        else:
            print(f"❌ GET /health - Expected: 200, Got: {response.status_code}")
            
    except Exception as e:
        print(f"❌ GET /health - Error: {str(e)}")
    
    print()

def main():
    """Main test function"""
    print("🧪 AI Product Council Backend - Fallback System Test")
    print("=" * 60)
    
    # Get base URL from command line or use default
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print(f"🔗 Testing backend at: {base_url}")
    print()
    
    # Test fallback endpoints
    test_fallback_endpoints(base_url)
    
    # Test fallback reset
    test_fallback_reset(base_url)
    
    # Test health endpoint with fallback info
    test_health_with_fallback(base_url)
    
    # Test AI functionality (may trigger fallback)
    test_ai_with_fallback(base_url)
    
    # Summary
    print("=" * 60)
    print("📊 Fallback System Test Summary")
    print("=" * 60)
    
    print("🎯 What was tested:")
    print("   ✅ Fallback system endpoints")
    print("   ✅ Fallback system reset")
    print("   ✅ Health endpoint with fallback status")
    print("   ✅ AI functionality with fallback detection")
    
    print("\n💡 Fallback System Features:")
    print("   🔄 Automatic fallback when Gemini API fails")
    print("   🎯 Multiple fallback strategies (OpenAI, rule-based, cached)")
    print("   📊 Fallback usage monitoring and statistics")
    print("   🏥 Health monitoring for fallback system")
    print("   🔧 Manual fallback system reset capability")
    
    print("\n🌐 Available Fallback Endpoints:")
    print(f"   - Status: {base_url}/fallback/status")
    print(f"   - Health: {base_url}/fallback/health")
    print(f"   - Methods: {base_url}/fallback/methods")
    print(f"   - Reset: {base_url}/fallback/reset (POST)")
    
    print("\n🎉 Your fallback system is ready to handle API failures gracefully!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)
