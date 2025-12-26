# query_engine.py
"""
Query Engine - Handles user queries using Gemini AI with ChromaDB RAG
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from config import Config
from .gemini_rag_handler import GeminiRAGHandler
from .document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class QueryEngine:
    """Handle user queries using Gemini AI with hybrid RAG approach"""

    def __init__(self):
        """Initialize query engine with Gemini and ChromaDB"""
        try:
            # Initialize Gemini AI
            self.gemini_handler = GeminiRAGHandler()
            logger.info("✅ Gemini AI handler initialized")

            # Initialize document processor for ChromaDB vector search
            self.doc_processor = DocumentProcessor()
            logger.info("✅ ChromaDB document processor initialized")

            # Configuration
            self.max_search_results = 15  # Top K documents to retrieve (increased for better recall)
            self.similarity_threshold = 0.3  # Minimum similarity score (lower = more permissive)
            self.max_context_docs = 8  # Max documents to send to Gemini

        except Exception as e:
            logger.error(f"Failed to initialize query engine: {str(e)}")
            raise

    def process_query(self, query: str) -> str:
        """
        Process user query and return response

        Args:
            query: User's question

        Returns:
            str: Response text with sources
        """
        try:
            logger.info(f"Processing query: {query[:100]}...")

            # Check for special query types first
            special_response = self._handle_special_queries(query)
            if special_response:
                return special_response

            # Search for relevant documents in ChromaDB
            search_results = self.doc_processor.search_documents(
                query=query,
                num_results=self.max_search_results
            )

            # Filter by similarity threshold to remove poor matches
            filtered_results = [
                result for result in search_results
                if result.get('similarity', 0) >= self.similarity_threshold
            ]

            logger.info(f"Found {len(search_results)} documents, {len(filtered_results)} passed similarity threshold ({self.similarity_threshold})")

            # Log top matches for debugging
            if filtered_results:
                for i, result in enumerate(filtered_results[:3], 1):
                    doc_name = result.get('metadata', {}).get('doc_name', 'Unknown')
                    similarity = result.get('similarity', 0)
                    preview = result.get('content', '')[:100]
                    logger.info(f"  Match {i}: {doc_name} (similarity: {similarity:.3f}) - {preview}...")

            # Generate answer using Gemini with filtered context
            result = self.gemini_handler.generate_answer_with_context(
                query=query,
                context_documents=filtered_results,
                max_context_docs=self.max_context_docs
            )

            if 'error' in result:
                logger.error(f"Gemini error: {result['error']}")
                return "❌ Sorry, I encountered an error processing your query. Please try again."

            answer = result.get('answer', '')
            logger.info(f"Generated answer with {result.get('documents_used', 0)} documents")

            return answer

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return "❌ Sorry, I encountered an error processing your query. Please try again or contact support."

    def _handle_special_queries(self, query: str) -> Optional[str]:
        """Handle special queries like greetings, system info, document lists"""
        query_lower = query.lower().strip()

        # Greetings
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
        if any(query_lower == greeting or query_lower.startswith(greeting + ' ') for greeting in greetings):
            return "👋 Hello! I'm InfoBot, your AI assistant powered by Gemini 2.5 Flash. I can help you find information from your Google Drive documents and Confluence pages, plus answer general questions. Just ask me anything!"

        # Help queries
        help_keywords = ['how can you help', 'what can you do', 'how are you helpful', 'help me', 'what do you do']
        if any(keyword in query_lower for keyword in help_keywords):
            return f"""I'm InfoBot, your intelligent assistant! Here's what I can do:

📚 **Document Search**: I search through your Google Drive documents and Confluence pages
💡 **General Knowledge**: I can answer questions on any topic (math, facts, history, etc.)
📊 **System Commands**:
   • `/status` - Check my current status
   • `/refresh` - Refresh document index

Just ask me anything - whether it's about your documents or a general question!"""

        # Document count/list queries
        count_keywords = ['how many document', 'document count', 'number of document', 'total document', 'list document', 'show document']
        if any(keyword in query_lower for keyword in count_keywords):
            try:
                stats = self.doc_processor.get_document_stats()
                doc_count = stats.get('total_documents', 0)
                chunk_count = stats.get('total_chunks', 0)
                last_updated = stats.get('last_updated', 'Never')

                return f"""📊 **Document Status**:
• Indexed Documents: {doc_count}
• Total Chunks: {chunk_count}
• Last Updated: {last_updated}
• AI Model: Gemini 2.5 Flash

All your Google Drive and Confluence documents are indexed and searchable!"""
            except Exception as e:
                logger.error(f"Error getting document stats: {str(e)}")
                return "📊 Documents are indexed and searchable via ChromaDB with Gemini AI."

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get query engine statistics"""
        try:
            # Get ChromaDB stats
            doc_stats = self.doc_processor.get_document_stats()

            stats = {
                'mode': 'Gemini AI + ChromaDB',
                'total_documents': doc_stats.get('total_documents', 0),
                'total_chunks': doc_stats.get('total_chunks', 0),
                'last_updated': doc_stats.get('last_updated', 'Never'),
                'ai_models': ['Gemini 2.5 Flash'],
                'configured': True,
                'sources': ['Google Drive', 'Confluence']
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting query engine stats: {str(e)}")
            return {
                'mode': 'Gemini AI + ChromaDB',
                'ai_models': ['Gemini 2.5 Flash'],
                'configured': False,
                'total_documents': 0,
                'total_chunks': 0
            }
