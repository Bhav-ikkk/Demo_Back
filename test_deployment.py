#!/usr/bin/env python3
"""
Test script to verify backend deployment
"""
import requests
import json
import time
import sys
from urllib.parse import urljoin

def test_endpoint(base_url, endpoint, method="GET", data=None, expected_status=200):
    """Test a specific endpoint"""
    url = urljoin(base_url, endpoint)
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
            
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - Status: {response.status_code}")
            return True
        else:
            print(f"❌ {method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}")
            if response.text:
                print(f"   Response: {response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ {method} {endpoint} - Connection failed (server not running?)")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {method} {endpoint} - Request timed out")
        return False
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {str(e)}")
        return False

def test_ai_functionality(base_url):
    """Test AI functionality with a sample product idea"""
    test_idea = {
        "idea": "A mobile app for tracking daily habits with AI coaching and personalized insights"
    }
    
    print("\n🧠 Testing AI Functionality...")
    
    # Test sync refinement
    success = test_endpoint(
        base_url, 
        "refine/sync", 
        method="POST", 
        data=test_idea, 
        expected_status=200
    )
    
    if success:
        try:
            response = requests.post(urljoin(base_url, "refine/sync"), json=test_idea, timeout=30)
            result = response.json()
            
            if "refined_requirements" in result:
                print("✅ AI refinement working correctly")
                print(f"   Response length: {len(str(result))} characters")
                return True
            else:
                print("❌ AI refinement response format unexpected")
                print(f"   Response keys: {list(result.keys())}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing AI response: {str(e)}")
            return False
    
    return False

def main():
    """Main test function"""
    print("🧪 AI Product Council Backend Deployment Test")
    print("=" * 50)
    
    # Get base URL from command line or use default
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://localhost:8000"
    
    print(f"🔗 Testing backend at: {base_url}")
    print()
    
    # Test basic endpoints
    print("📡 Testing Basic Endpoints...")
    basic_tests = [
        ("", 200),  # Root endpoint
        ("health", 200),  # Health check
        ("docs", 200),  # API documentation
    ]
    
    basic_success = True
    for endpoint, expected_status in basic_tests:
        if not test_endpoint(base_url, endpoint, expected_status=expected_status):
            basic_success = False
    
    if not basic_success:
        print("\n❌ Basic endpoint tests failed. Backend may not be running properly.")
        return False
    
    # Test AI functionality
    ai_success = test_ai_functionality(base_url)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    if basic_success and ai_success:
        print("🎉 All tests passed! Your backend is working correctly.")
        print("\n🔗 Your backend is ready for frontend integration!")
        print(f"   API Base URL: {base_url}")
        print(f"   Documentation: {base_url}/docs")
        print(f"   Health Check: {base_url}/health")
        
        # Frontend integration tips
        print("\n💡 Frontend Integration Tips:")
        print("   1. Update your frontend API configuration to use this backend URL")
        print("   2. Ensure CORS is configured for your frontend domain")
        print("   3. Test API calls from your frontend application")
        
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting Tips:")
        print("   1. Ensure the backend server is running")
        print("   2. Check that all required environment variables are set")
        print("   3. Verify database and Redis connections")
        print("   4. Check server logs for error messages")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)
