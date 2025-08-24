#!/usr/bin/env python3
"""
Test script for the AI Product Council API
Run this to test POST requests to your endpoints
"""

import requests
import json
import time

# API base URL
BASE_URL = "http://127.0.0.1:8000"

def test_health():
    """Test the health endpoint"""
    print("🏥 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health: {data['status']}")
            print(f"   Database: {'✅' if data['database_connected'] else '❌'}")
            print(f"   AI Service: {'✅' if data['ai_service_available'] else '❌'}")
        else:
            print(f"❌ Health check failed: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_sync_refine():
    """Test the synchronous refine endpoint"""
    print("\n🚀 Testing Sync Refine Endpoint...")
    
    # Test data
    test_idea = {
        "idea": "A mobile app that helps people find and book local fitness classes with real-time availability and instant booking",
        "priority_focus": "balanced"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/refine/sync",
            json=test_idea,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Refinement successful!")
            print(f"   Refined: {data['refined_requirement']}")
            print(f"   Priority Score: {data['priority_score']}/10")
            print(f"   Effort: {data['estimated_effort']}")
            print(f"   Key Changes: {len(data['key_changes_summary'])} points")
            print(f"   User Stories: {len(data['user_stories'])} stories")
            print(f"   Technical Tasks: {len(data['technical_tasks'])} tasks")
            print(f"   Agent Responses: {len(data['agent_debate'])} agents")
            
            # Show agent feedback
            print("\n🤖 Agent Feedback:")
            for agent in data['agent_debate']:
                print(f"   {agent['agent_name']}: {agent['feedback'][:80]}...")
                print(f"     Confidence: {agent['confidence_score']:.2f}")
            
            return True
        else:
            print(f"❌ Refinement failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Refinement error: {e}")
        return False

def test_async_refine():
    """Test the asynchronous refine endpoint"""
    print("\n⏳ Testing Async Refine Endpoint...")
    
    # Test data
    test_idea = {
        "idea": "A web platform for remote teams to collaborate on design projects with real-time feedback and version control",
        "priority_focus": "technical"
    }
    
    try:
        # Start refinement
        response = requests.post(
            f"{BASE_URL}/refine",
            json=test_idea,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Start Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            session_id = data['session_id']
            print(f"✅ Refinement started! Session ID: {session_id}")
            
            # Wait and check status
            print("⏳ Waiting for completion...")
            for i in range(10):  # Wait up to 10 seconds
                time.sleep(1)
                
                status_response = requests.get(f"{BASE_URL}/refine/{session_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data['status'] == 'completed':
                        print("✅ Async refinement completed!")
                        result = status_data['result']
                        print(f"   Refined: {result['refined_requirement']}")
                        print(f"   Processing Time: {status_data['processing_time_seconds']}s")
                        return True
                    elif status_data['status'] == 'failed':
                        print(f"❌ Async refinement failed: {status_data.get('error_message', 'Unknown error')}")
                        return False
                    else:
                        print(f"   Status: {status_data['status']}...")
            
            print("⏰ Timeout waiting for completion")
            return False
        else:
            print(f"❌ Failed to start refinement: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Async refinement error: {e}")
        return False

def main():
    """Main test function"""
    print("=" * 60)
    print("AI Product Council API Test")
    print("=" * 60)
    
    # Check if server is running
    print("🔍 Checking if server is running...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Server is running!")
            data = response.json()
            print(f"   API: {data['message']}")
            print(f"   Version: {data['version']}")
        else:
            print("❌ Server response unexpected")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Make sure to start the server with: python -m uvicorn app.main:app --reload")
        return
    
    # Run tests
    tests = [
        ("Health Check", test_health),
        ("Sync Refine", test_sync_refine),
        ("Async Refine", test_async_refine),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 SUCCESS: All API tests passed!")
        print("\nYour backend is working perfectly!")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        exit(1)
