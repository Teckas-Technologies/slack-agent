#!/usr/bin/env python3
"""
Verification script for Slack Document Agent setup
"""
import os
import sys
from pathlib import Path
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_variables():
    """Check if required environment variables are set"""
    required_vars = {
        'SLACK_BOT_TOKEN': 'Slack Bot Token',
        'SLACK_SIGNING_SECRET': 'Slack Signing Secret'
    }
    
    optional_vars = {
        'OPENAI_API_KEY': 'OpenAI API Key',
        'ANTHROPIC_API_KEY': 'Anthropic API Key',
        'GOOGLE_SERVICE_ACCOUNT_KEY': 'Google Service Account Key',
        'CONFLUENCE_BASE_URL': 'Confluence Base URL',
        'CONFLUENCE_USERNAME': 'Confluence Username',
        'CONFLUENCE_API_TOKEN': 'Confluence API Token'
    }
    
    print("🔍 Checking environment variables...")
    
    # Check required variables
    missing_required = []
    for var, description in required_vars.items():
        if os.environ.get(var):
            print(f"✅ {description} is set")
        else:
            print(f"❌ {description} is missing")
            missing_required.append(var)
    
    # Check optional variables (at least one AI service is needed)
    ai_services = []
    for var in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
        if os.environ.get(var):
            ai_services.append(var)
            print(f"✅ {optional_vars[var]} is set")
    
    if not ai_services:
        print("⚠️  No AI service configured (OpenAI or Anthropic required)")
        missing_required.append('OPENAI_API_KEY or ANTHROPIC_API_KEY')
    
    # Check other optional variables
    for var, description in optional_vars.items():
        if var not in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
            if os.environ.get(var):
                print(f"✅ {description} is set")
            else:
                print(f"⚠️  {description} is not set")
    
    return len(missing_required) == 0

def test_slack_connection():
    """Test Slack API connection"""
    print("\n🔍 Testing Slack connection...")
    
    token = os.environ.get('SLACK_BOT_TOKEN')
    if not token:
        print("❌ Slack token not configured")
        return False
    
    try:
        from slack_sdk import WebClient
        client = WebClient(token=token)
        
        # Test the connection
        response = client.auth_test()
        if response['ok']:
            print(f"✅ Connected to Slack as {response['user']}")
            return True
        else:
            print(f"❌ Slack connection failed: {response['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Slack connection error: {str(e)}")
        return False

def test_ai_services():
    """Test AI service connections"""
    print("\n🔍 Testing AI services...")
    
    results = []
    
    # Test OpenAI
    if os.environ.get('OPENAI_API_KEY'):
        try:
            import openai
            client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
            
            # Simple test
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            print("✅ OpenAI connection successful")
            results.append(True)
        except Exception as e:
            print(f"❌ OpenAI connection failed: {str(e)}")
            results.append(False)
    
    # Test Anthropic
    if os.environ.get('ANTHROPIC_API_KEY'):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
            
            # Simple test
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "Hello"}]
            )
            print("✅ Anthropic connection successful")
            results.append(True)
        except Exception as e:
            print(f"❌ Anthropic connection failed: {str(e)}")
            results.append(False)
    
    return any(results) if results else False

def test_google_drive():
    """Test Google Drive connection"""
    print("\n🔍 Testing Google Drive connection...")
    
    service_account_key = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY')
    if not service_account_key:
        print("⚠️  Google Drive not configured")
        return False
    
    if not Path(service_account_key).exists():
        print(f"❌ Service account file not found: {service_account_key}")
        return False
    
    try:
        from app.google_drive_handler import GoogleDriveHandler
        handler = GoogleDriveHandler()
        
        # Try to list files (just a few)
        docs = handler.get_all_documents()
        print(f"✅ Google Drive connection successful - Found {len(docs)} documents")
        return True
        
    except Exception as e:
        print(f"❌ Google Drive connection failed: {str(e)}")
        return False

def test_confluence():
    """Test Confluence connection"""
    print("\n🔍 Testing Confluence connection...")
    
    base_url = os.environ.get('CONFLUENCE_BASE_URL')
    username = os.environ.get('CONFLUENCE_USERNAME')
    api_token = os.environ.get('CONFLUENCE_API_TOKEN')
    
    if not all([base_url, username, api_token]):
        print("⚠️  Confluence not configured")
        return False
    
    try:
        from app.confluence_handler import ConfluenceHandler
        handler = ConfluenceHandler()
        
        # Test connection
        validation = handler.validate_connection()
        if validation['status'] == 'connected':
            print("✅ Confluence connection successful")
            return True
        else:
            print(f"❌ Confluence connection failed: {validation['message']}")
            return False
            
    except Exception as e:
        print(f"❌ Confluence connection failed: {str(e)}")
        return False

def test_database():
    """Test ChromaDB connection"""
    print("\n🔍 Testing database connection...")
    
    try:
        from app.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        # Get stats to test connection
        stats = processor.get_document_stats()
        print(f"✅ Database connection successful - {stats['total_documents']} documents indexed")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def test_flask_app():
    """Test if the Flask app can start"""
    print("\n🔍 Testing Flask application...")
    
    try:
        from app import app
        
        # Test app creation
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Flask application starts successfully")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Flask application failed to start: {str(e)}")
        return False

def main():
    """Main verification function"""
    print("🔍 Verifying Slack Document Agent Setup")
    print("=" * 50)
    
    results = []
    
    # Run all tests
    results.append(check_env_variables())
    results.append(test_slack_connection())
    results.append(test_ai_services())
    results.append(test_google_drive())
    results.append(test_confluence())
    results.append(test_database())
    results.append(test_flask_app())
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Verification Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("🎉 All checks passed! Your setup is ready.")
        print("\nYou can now:")
        print("1. Run the application: python app.py")
        print("2. Or use Docker: docker-compose up")
        print("3. Configure your Slack app to use your endpoint")
        return 0
    else:
        print(f"⚠️  {passed}/{total} checks passed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Check your .env file for missing or incorrect values")
        print("2. Ensure credential files are in the right location")
        print("3. Verify your API keys are valid")
        return 1

if __name__ == "__main__":
    sys.exit(main())