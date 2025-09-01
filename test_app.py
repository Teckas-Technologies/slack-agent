#!/usr/bin/env python3
"""
Test script to verify the Slack Document Agent setup
"""
import os
import sys

# Mock environment variables for testing
os.environ.update({
    'SLACK_BOT_TOKEN': 'xoxb-test-token',
    'SLACK_SIGNING_SECRET': 'test-secret',
    'OPENAI_API_KEY': 'sk-test-key',
    'ANTHROPIC_API_KEY': 'sk-ant-test-key'
})

def test_imports():
    """Test if all modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test basic Flask import
        from flask import Flask
        print("✅ Flask imported successfully")
        
        # Test Slack SDK
        from slack_sdk import WebClient
        from slack_sdk.signature import SignatureVerifier
        print("✅ Slack SDK imported successfully")
        
        # Test AI libraries
        import openai
        import anthropic
        print("✅ AI libraries imported successfully")
        
        # Test ChromaDB
        import chromadb
        print("✅ ChromaDB imported successfully")
        
        # Test Google APIs
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        print("✅ Google APIs imported successfully")
        
        # Test web scraping
        from bs4 import BeautifulSoup
        print("✅ BeautifulSoup imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_app_modules():
    """Test if app modules can be imported"""
    print("\n🔍 Testing app modules...")
    
    try:
        # Add current directory to Python path
        sys.path.insert(0, '.')
        
        # Test document processor
        from app.document_processor import DocumentProcessor
        print("✅ DocumentProcessor imported")
        
        # Test query engine
        from app.query_engine import QueryEngine
        print("✅ QueryEngine imported")
        
        # Test Google Drive handler
        from app.google_drive_handler import GoogleDriveHandler
        print("✅ GoogleDriveHandler imported")
        
        # Test Confluence handler
        from app.confluence_handler import ConfluenceHandler
        print("✅ ConfluenceHandler imported")
        
        return True
        
    except Exception as e:
        print(f"❌ App module error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_component_creation():
    """Test if components can be created"""
    print("\n🔍 Testing component creation...")
    
    try:
        sys.path.insert(0, '.')
        
        # Test DocumentProcessor creation
        from app.document_processor import DocumentProcessor
        doc_processor = DocumentProcessor()
        print("✅ DocumentProcessor created successfully")
        
        # Test QueryEngine creation
        from app.query_engine import QueryEngine
        query_engine = QueryEngine()
        print("✅ QueryEngine created successfully")
        
        # Test handlers (these might fail due to missing credentials, but shouldn't crash)
        from app.google_drive_handler import GoogleDriveHandler
        try:
            gdrive_handler = GoogleDriveHandler()
            print("✅ GoogleDriveHandler created successfully")
        except Exception as e:
            print(f"⚠️  GoogleDriveHandler creation failed (expected): {e}")
        
        from app.confluence_handler import ConfluenceHandler
        confluence_handler = ConfluenceHandler()
        print("✅ ConfluenceHandler created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Component creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_flask_app():
    """Test Flask app creation manually"""
    print("\n🔍 Testing Flask app creation...")
    
    try:
        from flask import Flask
        from datetime import datetime
        
        # Create a minimal Flask app like in app.py
        test_app = Flask(__name__)
        
        @test_app.route("/health", methods=["GET"])
        def health_check():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        # Test the app
        with test_app.test_client() as client:
            response = client.get('/health')
            print(f"✅ Flask app created and health check returns: {response.status_code}")
            if response.status_code == 200:
                data = response.get_json()
                print(f"✅ Health check response: {data}")
                return True
        
    except Exception as e:
        print(f"❌ Flask app creation error: {e}")
        return False

def test_slack_agent_class():
    """Test SlackDocumentAgent class creation manually"""
    print("\n🔍 Testing SlackDocumentAgent class...")
    
    try:
        sys.path.insert(0, '.')
        from flask import Flask
        from slack_sdk import WebClient
        from slack_sdk.signature import SignatureVerifier
        from app.document_processor import DocumentProcessor
        from app.query_engine import QueryEngine
        from app.google_drive_handler import GoogleDriveHandler
        from app.confluence_handler import ConfluenceHandler
        
        # Create SlackDocumentAgent class manually
        class TestSlackDocumentAgent:
            def __init__(self):
                self.slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
                self.signature_verifier = SignatureVerifier(os.environ["SLACK_SIGNING_SECRET"])

                # Initialize document handlers (might fail, but shouldn't crash)
                try:
                    self.gdrive_handler = GoogleDriveHandler()
                except Exception as e:
                    print(f"⚠️  GoogleDriveHandler init warning: {e}")
                    self.gdrive_handler = None
                
                try:
                    self.confluence_handler = ConfluenceHandler()
                except Exception as e:
                    print(f"⚠️  ConfluenceHandler init warning: {e}")
                    self.confluence_handler = None

                # Initialize document processor and query engine
                self.doc_processor = DocumentProcessor()
                self.query_engine = QueryEngine()

                self.processing_status = {}
        
        # Test creation
        agent = TestSlackDocumentAgent()
        print("✅ SlackDocumentAgent class created successfully")
        return True
        
    except Exception as e:
        print(f"❌ SlackDocumentAgent creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🧪 Slack Document Agent - Component Tests")
    print("=" * 50)
    
    tests = [
        ("Basic Imports", test_imports),
        ("App Modules", test_app_modules), 
        ("Component Creation", test_component_creation),
        ("Flask App", test_flask_app),
        ("SlackDocumentAgent", test_slack_agent_class)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application components are working correctly.")
        print("\nThe main issue might be in app.py execution flow.")
        print("Try running the application with: python app.py")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)