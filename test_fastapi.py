#!/usr/bin/env python3
"""
Test script for FastAPI Slack Document Agent
"""
import os
import sys
import asyncio
from typing import Dict, Any

# Mock environment variables for testing
os.environ.update({
    'SLACK_BOT_TOKEN': 'xoxb-test-token',
    'SLACK_SIGNING_SECRET': 'test-secret',
    'OPENAI_API_KEY': 'sk-test-key',
    'ANTHROPIC_API_KEY': 'sk-ant-test-key'
})

def test_fastapi_imports():
    """Test FastAPI related imports"""
    print("🔍 Testing FastAPI imports...")
    
    try:
        import fastapi
        from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
        from fastapi.responses import JSONResponse
        import uvicorn
        print("✅ FastAPI and related imports successful")
        return True
    except ImportError as e:
        print(f"❌ FastAPI import error: {e}")
        return False

def test_app_creation():
    """Test FastAPI app creation"""
    print("\n🔍 Testing FastAPI app creation...")
    
    try:
        sys.path.insert(0, '.')
        
        # Import the main app - note: import the module first, then get the app
        import app as app_module
        app = app_module.app
        print("✅ FastAPI app imported successfully")
        
        # Check if it's a FastAPI instance
        import fastapi
        if isinstance(app, fastapi.FastAPI):
            print("✅ App is a FastAPI instance")
        else:
            print(f"❌ App is not a FastAPI instance, it's: {type(app)}")
            return False
            
        # Check app metadata
        print(f"✅ App title: {app.title}")
        print(f"✅ App version: {app.version}")
        print(f"✅ Docs URL: {app.docs_url}")
        print(f"✅ Redoc URL: {app.redoc_url}")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI app creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_routes():
    """Test if FastAPI app has the expected routes"""
    print("\n🔍 Testing FastAPI routes...")
    
    try:
        sys.path.insert(0, '.')
        import app as app_module
        app = app_module.app
        
        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                routes.append(f"{list(route.methods)} {route.path}")
        
        print("✅ Available routes:")
        for route in routes:
            print(f"   {route}")
        
        # Check for expected routes
        expected_endpoints = [
            "/health",
            "/slack/events", 
            "/refresh",
            "/status",
            "/docs-summary"
        ]
        
        route_paths = [route.path for route in app.routes if hasattr(route, 'path')]
        
        missing_routes = []
        for endpoint in expected_endpoints:
            if endpoint not in route_paths:
                missing_routes.append(endpoint)
        
        if missing_routes:
            print(f"❌ Missing routes: {missing_routes}")
            return False
        else:
            print("✅ All expected routes are present")
            return True
            
    except Exception as e:
        print(f"❌ Route testing error: {e}")
        return False

async def test_health_endpoint():
    """Test the health endpoint"""
    print("\n🔍 Testing health endpoint...")
    
    try:
        sys.path.insert(0, '.')
        import app as app_module
        app = app_module.app
        from fastapi.testclient import TestClient
        
        # Create test client
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        print(f"✅ Health endpoint status: {response.status_code}")
        
        if response.status_code in [200, 503]:  # 503 is expected if agent not initialized
            data = response.json()
            print(f"✅ Health response: {data}")
            return True
        else:
            print(f"❌ Unexpected health status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health endpoint test error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_docs():
    """Test if API documentation is accessible"""
    print("\n🔍 Testing API documentation...")
    
    try:
        sys.path.insert(0, '.')
        import app as app_module
        app = app_module.app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Test docs endpoint
        docs_response = client.get("/docs")
        print(f"✅ Docs endpoint status: {docs_response.status_code}")
        
        # Test redoc endpoint
        redoc_response = client.get("/redoc")
        print(f"✅ ReDoc endpoint status: {redoc_response.status_code}")
        
        # Test OpenAPI spec
        openapi_response = client.get("/openapi.json")
        print(f"✅ OpenAPI spec status: {openapi_response.status_code}")
        
        if all(r.status_code == 200 for r in [docs_response, redoc_response, openapi_response]):
            print("✅ All documentation endpoints working")
            return True
        else:
            print("❌ Some documentation endpoints failed")
            return False
            
    except Exception as e:
        print(f"❌ API docs test error: {e}")
        return False

async def test_slack_events_endpoint():
    """Test Slack events endpoint"""
    print("\n🔍 Testing Slack events endpoint...")
    
    try:
        sys.path.insert(0, '.')
        import app as app_module
        app = app_module.app
        from fastapi.testclient import TestClient
        import json
        
        client = TestClient(app)
        
        # Test URL verification (Slack setup)
        verification_payload = {
            "type": "url_verification",
            "challenge": "test_challenge_123"
        }
        
        # Note: This will fail signature verification, but we can test the structure
        response = client.post(
            "/slack/events",
            json=verification_payload,
            headers={"Content-Type": "application/json"}
        )
        
        # We expect 403 due to signature verification, but the endpoint should exist
        if response.status_code in [403, 422]:  # 403 = invalid signature, 422 = validation error
            print("✅ Slack events endpoint exists and validates signatures")
            return True
        else:
            print(f"❌ Unexpected Slack events status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Slack events test error: {e}")
        return False

def test_uvicorn_server():
    """Test if uvicorn can be imported and configured"""
    print("\n🔍 Testing Uvicorn server setup...")
    
    try:
        import uvicorn
        print("✅ Uvicorn imported successfully")
        
        # Test if we can create a server config
        config = uvicorn.Config(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
        print("✅ Uvicorn config created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Uvicorn test error: {e}")
        return False

async def run_async_tests():
    """Run all async tests"""
    print("🔄 Running async tests...")
    
    tests = [
        ("Health Endpoint", test_health_endpoint()),
        ("API Documentation", test_api_docs()),
        ("Slack Events", test_slack_events_endpoint())
    ]
    
    results = []
    for test_name, test_coro in tests:
        print(f"\n--- {test_name} ---")
        result = await test_coro
        results.append(result)
        print(f"{'✅' if result else '❌'} {test_name} {'PASSED' if result else 'FAILED'}")
    
    return results

async def main():
    """Main test function"""
    print("🚀 FastAPI Slack Document Agent - Tests")
    print("=" * 50)
    
    # Sync tests
    sync_tests = [
        ("FastAPI Imports", test_fastapi_imports),
        ("App Creation", test_app_creation),
        ("App Routes", test_app_routes),
        ("Uvicorn Server", test_uvicorn_server)
    ]
    
    sync_results = []
    for test_name, test_func in sync_tests:
        print(f"\n--- {test_name} ---")
        result = test_func()
        sync_results.append(result)
        print(f"{'✅' if result else '❌'} {test_name} {'PASSED' if result else 'FAILED'}")
    
    # Async tests
    async_results = await run_async_tests()
    
    # Summary
    all_results = sync_results + async_results
    passed = sum(all_results)
    total = len(all_results)
    
    print(f"\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All FastAPI tests passed!")
        print("\n✨ FastAPI Benefits in your app:")
        print("  • 🚀 2-3x faster than Flask")
        print("  • 📚 Automatic API documentation at /docs")
        print("  • ⚡ Built-in async support")
        print("  • 🔍 Better error handling")
        print("  • 🎯 Type validation with Pydantic")
        print("  • 🔧 Production-ready with uvicorn")
        print(f"\nRun: python app.py or uvicorn app:app --port 8000")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    # Install required packages if missing
    try:
        import fastapi
        from fastapi.testclient import TestClient
        import uvicorn
    except ImportError as e:
        print(f"❌ Missing required packages: {e}")
        print("Run: pip install fastapi uvicorn[standard]")
        sys.exit(1)
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)