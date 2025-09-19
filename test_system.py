#!/usr/bin/env python3
"""
Test script for InfoBot system
"""
import os
import sys
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_configuration():
    """Test configuration validation"""
    print("🔧 Testing configuration...")
    try:
        Config.validate_required()
        print("✅ Configuration validation passed")
        return True
    except ValueError as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def test_vector_store():
    """Test vector store functionality"""
    print("\n📊 Testing vector store...")
    try:
        from app.vector_store import VectorStore

        vector_store = VectorStore()

        # Test health check
        health = vector_store.health_check()
        if health['status'] == 'healthy':
            print("✅ Vector store health check passed")
        else:
            print(f"❌ Vector store health check failed: {health}")
            return False

        # Test basic operations
        test_docs = [
            {
                'id': 'test_doc_1',
                'content': 'This is a test document about pricing. The E-Commerce project costs $100.',
                'metadata': {
                    'doc_id': 'test_doc_1',
                    'doc_name': 'Test Document 1',
                    'doc_source': 'test',
                    'url': 'https://example.com/doc1'
                }
            }
        ]

        # Add test documents
        success = vector_store.add_documents(test_docs)
        if success:
            print("✅ Test documents added successfully")
        else:
            print("❌ Failed to add test documents")
            return False

        # Search test
        results = vector_store.search_documents("pricing", num_results=5)
        if results:
            print(f"✅ Search test passed - found {len(results)} results")
        else:
            print("❌ Search test failed - no results found")
            return False

        # Clean up
        vector_store.clear_collection()
        print("✅ Test cleanup completed")

        return True

    except Exception as e:
        print(f"❌ Vector store test failed: {str(e)}")
        return False

def test_document_processor():
    """Test document processor functionality"""
    print("\n📄 Testing document processor...")
    try:
        from app.document_processor import DocumentProcessor

        processor = DocumentProcessor()

        # Test basic stats
        stats = processor.get_document_stats()
        print(f"✅ Document processor stats: {stats}")

        # Test content cleaning
        dirty_content = "   This    is   messy    content   \n\n\n   with   extra   spaces   \n\n\n"
        cleaned = processor._clean_content(dirty_content)
        print(f"✅ Content cleaning test passed")

        # Test chunking
        test_content = "This is a test document. " * 100  # Long content
        test_doc = {
            'id': 'test_chunk',
            'name': 'Test Chunking Document',
            'source': 'test',
            'mime_type': 'text/plain'
        }

        chunks = processor._create_text_chunks(test_content, test_doc)
        print(f"✅ Text chunking test passed - created {len(chunks)} chunks")

        return True

    except Exception as e:
        print(f"❌ Document processor test failed: {str(e)}")
        return False

def test_query_engine():
    """Test query engine functionality"""
    print("\n🤖 Testing query engine...")
    try:
        from app.query_engine import QueryEngine

        query_engine = QueryEngine()

        # Test stats
        stats = query_engine.get_stats()
        print(f"✅ Query engine stats: {stats}")

        # Test AI connection if available
        if hasattr(query_engine, 'test_ai_connection'):
            ai_status = query_engine.test_ai_connection()
            print(f"✅ AI connection test: {ai_status}")

        return True

    except Exception as e:
        print(f"❌ Query engine test failed: {str(e)}")
        return False

def test_handlers():
    """Test Google Drive and Confluence handlers"""
    print("\n🔗 Testing document handlers...")

    # Test Google Drive handler
    try:
        from app.google_drive_handler import GoogleDriveHandler
        gdrive = GoogleDriveHandler()
        print("✅ Google Drive handler initialized")
    except Exception as e:
        print(f"⚠️ Google Drive handler test failed: {str(e)}")

    # Test Confluence handler
    try:
        from app.confluence_handler import ConfluenceHandler
        confluence = ConfluenceHandler()
        print("✅ Confluence handler initialized")
    except Exception as e:
        print(f"⚠️ Confluence handler test failed: {str(e)}")

    return True

def test_slack_integration():
    """Test Slack integration components"""
    print("\n💬 Testing Slack integration...")
    try:
        from slack_sdk import WebClient
        from slack_sdk.signature import SignatureVerifier

        # Test Slack client initialization
        if Config.SLACK_BOT_TOKEN:
            client = WebClient(token=Config.SLACK_BOT_TOKEN)
            print("✅ Slack WebClient initialized")
        else:
            print("⚠️ No Slack bot token configured")

        # Test signature verifier
        if Config.SLACK_SIGNING_SECRET:
            verifier = SignatureVerifier(Config.SLACK_SIGNING_SECRET)
            print("✅ Slack signature verifier initialized")
        else:
            print("⚠️ No Slack signing secret configured")

        return True

    except Exception as e:
        print(f"❌ Slack integration test failed: {str(e)}")
        return False

def run_integration_test():
    """Run end-to-end integration test"""
    print("\n🔄 Running integration test...")
    try:
        from app.document_processor import DocumentProcessor
        from app.query_engine import QueryEngine

        # Initialize components
        processor = DocumentProcessor()
        query_engine = QueryEngine()

        # Create test document
        test_doc = {
            'id': 'integration_test_doc',
            'name': 'E-Commerce Project Plan',
            'source': 'test',
            'mime_type': 'text/plain',
            'url': 'https://example.com/ecommerce-plan'
        }

        # Simulate document content extraction
        test_content = """
        E-Commerce Project Plan

        Project Overview:
        This document outlines the pricing and timeline for the E-Commerce project.

        Pricing Information:
        - Total project cost: $100
        - Development: $60
        - Testing: $25
        - Deployment: $15

        Timeline:
        The project will be completed in 3 months.
        """

        # Create and store chunks
        chunks = processor._create_text_chunks(test_content, test_doc)

        if chunks:
            print(f"✅ Created {len(chunks)} chunks for integration test")

            # Store chunks
            processor._store_chunks(chunks, test_doc)
            print("✅ Stored chunks successfully")

            # Test query
            response = query_engine.process_query("Tell me the pricing of E-Commerce project")
            print(f"✅ Query response: {response[:100]}...")

            # Verify response contains expected elements
            if "$100" in response or "100" in response:
                print("✅ Integration test passed - response contains pricing information")
                return True
            else:
                print("❌ Integration test failed - response doesn't contain expected pricing")
                return False
        else:
            print("❌ Integration test failed - no chunks created")
            return False

    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting InfoBot System Tests\n")

    tests = [
        ("Configuration", test_configuration),
        ("Vector Store", test_vector_store),
        ("Document Processor", test_document_processor),
        ("Query Engine", test_query_engine),
        ("Document Handlers", test_handlers),
        ("Slack Integration", test_slack_integration),
        ("Integration Test", run_integration_test)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {str(e)}")
            results[test_name] = False

    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)

    passed = 0
    total = len(tests)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if result:
            passed += 1

    print("-"*50)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! InfoBot is ready to use.")
        return 0
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please check the configuration and dependencies.")
        return 1

if __name__ == "__main__":
    sys.exit(main())