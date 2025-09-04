# query_engine.py
import os
import logging
from typing import List, Dict, Any, Optional
import anthropic
import openai
from datetime import datetime
from .document_processor import DocumentProcessor
from config import Config

logger = logging.getLogger(__name__)


class QueryEngine:
    """Handle user queries using RAG with AI models"""

    def __init__(self):
        # Initialize AI clients
        self.openai_client = None
        self.anthropic_client = None
        
        # Initialize OpenAI if API key is available
        if Config.OPENAI_API_KEY:
            self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
        # Initialize Anthropic if API key is available
        if Config.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        
        # Document processor for search
        self.doc_processor = DocumentProcessor()
        
        # Configuration - Make similarity threshold more lenient
        self.max_context_length = 4000
        self.max_search_results = 8
        self.similarity_threshold = 1.5  # More lenient threshold (ChromaDB uses distance, lower is better)

    def process_query(self, query: str) -> str:
        """Process user query and return response"""
        try:
            logger.info(f"Processing query: {query[:100]}...")

            # Search for relevant documents
            search_results = self.doc_processor.search_documents(
                query=query, 
                num_results=self.max_search_results
            )

            logger.info(f"Found {len(search_results)} search results")

            if not search_results:
                # Check if we have any documents at all
                stats = self.doc_processor.get_document_stats()
                if stats.get('total_documents', 0) == 0:
                    return "📚 No documents have been indexed yet. Please use the `/refresh` command to index your documents first."
                else:
                    return f"❌ I couldn't find any relevant documents to answer your question among {stats.get('total_documents', 0)} indexed documents. Try rephrasing your question or using the `/refresh` command."

            # Log search results for debugging
            for i, result in enumerate(search_results):
                distance = result.get('distance', 'unknown')
                doc_name = result.get('metadata', {}).get('doc_name', 'Unknown')
                logger.info(f"Result {i}: distance={distance}, doc='{doc_name}'")

            # Take only the most relevant result for a focused response
            relevant_results = search_results[:min(1, len(search_results))]
            
            # If we have results with very poor similarity, inform the user
            if relevant_results and relevant_results[0].get('distance', 0) > 1.2:
                logger.warning(f"Best match has distance {relevant_results[0].get('distance', 0)}, which is quite high")

            # Always generate focused response (AI or direct)
            response = self._generate_focused_response(query, relevant_results)

            # Add source attribution
            sources = self._format_sources(relevant_results)
            final_response = f"{response}\n\n📋 **Sources:**\n{sources}"

            return final_response

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return "❌ Sorry, I encountered an error processing your query. Please try again or contact support."

    def _generate_ai_response(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """Generate AI response based on search results"""
        try:
            logger.info(f"Generating AI response. Anthropic available: {self.anthropic_client is not None}, OpenAI available: {self.openai_client is not None}")
            
            # Prepare context from search results
            context = self._prepare_context(search_results)
            logger.info(f"Prepared context length: {len(context)} characters")
            
            # Create prompt
            prompt = self._create_prompt(query, context)

            # Try Anthropic first (Claude), then fallback to OpenAI
            if self.anthropic_client:
                logger.info("Using Anthropic (Claude) for response")
                return self._get_anthropic_response(prompt)
            elif self.openai_client:
                logger.info("Using OpenAI (GPT) for response")
                return self._get_openai_response(prompt)
            else:
                logger.warning("No AI clients available, using simple response")
                return self._generate_simple_response(query, search_results)

        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return self._generate_simple_response(query, search_results)

    def _prepare_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Prepare context from search results"""
        context_parts = []
        total_length = 0

        for i, result in enumerate(search_results):
            content = result['content']
            metadata = result['metadata']
            
            # Format context entry
            doc_name = metadata.get('doc_name', 'Unknown Document')
            source = metadata.get('doc_source', 'unknown')
            
            context_entry = f"Document: {doc_name} (Source: {source})\nContent: {content}\n"
            
            # Check if adding this entry exceeds max context length
            if total_length + len(context_entry) > self.max_context_length:
                break
                
            context_parts.append(context_entry)
            total_length += len(context_entry)

        return "\n---\n".join(context_parts)

    def _create_prompt(self, query: str, context: str) -> str:
        """Create prompt for AI model"""
        prompt = f"""Answer the user's question based on the provided document context. Be very concise and direct.

Context from relevant documents:
{context}

User Question: {query}

Instructions:
1. Give a short, direct answer (1-2 sentences maximum)
2. Extract only the most relevant information that directly answers the question
3. Don't include unnecessary details or explanations
4. If the context doesn't contain the answer, say "Information not found in documents"

Answer:"""

        return prompt

    def _get_anthropic_response(self, prompt: str) -> str:
        """Get response from Anthropic Claude"""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Error getting Anthropic response: {str(e)}")
            raise

    def _get_openai_response(self, prompt: str) -> str:
        """Get response from OpenAI GPT"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful document assistant. Answer questions based on the provided context accurately and concisely."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error getting OpenAI response: {str(e)}")
            raise

    def _generate_simple_response(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """Generate simple response without AI (fallback)"""
        # Basic keyword-based response when AI is not available
        response_parts = ["Based on the documents I found:\n"]
        
        for i, result in enumerate(search_results[:3], 1):
            content = result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
            doc_name = result['metadata'].get('doc_name', 'Unknown Document')
            
            response_parts.append(f"{i}. From '{doc_name}':\n{content}\n")

        response_parts.append("\n⚠️ This is a basic response. For more detailed answers, please configure your AI API keys (OpenAI or Anthropic).")
        
        return "\n".join(response_parts)

    def _generate_focused_response(self, query: str, search_results: List[Dict[str, Any]]) -> str:
        """Generate focused response with AI if available, otherwise direct extraction"""
        if not search_results:
            return "No relevant information found."
        
        # Try AI response first if available
        if self.anthropic_client or self.openai_client:
            try:
                return self._generate_ai_response(query, search_results)
            except Exception as e:
                logger.error(f"AI response failed, falling back to direct extraction: {e}")
        
        # Direct extraction and formatting
        result = search_results[0]
        content = result['content'].strip()
        
        # Clean up the content and format it better
        import re
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Try to extract structured content (lists, numbered items)
        lines = content.split('.')
        formatted_lines = []
        
        for line in lines[:5]:  # Take first 5 sentences/points
            line = line.strip()
            if line and len(line) > 10:
                # Format numbered items
                if re.match(r'^\d+\s*[a-zA-Z]', line):
                    formatted_lines.append(line)
                # Format lettered items
                elif re.match(r'^[a-z]\.\s*', line):
                    formatted_lines.append('  ' + line)
                else:
                    formatted_lines.append(line)
        
        if formatted_lines:
            return '\n'.join(formatted_lines)
        
        # Fallback to first 300 characters if no structure found
        return content[:300] + "..." if len(content) > 300 else content

    def _format_sources(self, search_results: List[Dict[str, Any]]) -> str:
        """Format source information - show only the most relevant source"""
        if not search_results:
            return "No sources found"
        
        # Only show the first/most relevant source
        result = search_results[0]
        metadata = result['metadata']
        doc_name = metadata.get('doc_name', 'Unknown Document')
        doc_source = metadata.get('doc_source', 'unknown')
        doc_url = metadata.get('url', '')
        
        # Format source entry
        source_icon = "📄" if doc_source == "google_drive" else "🏢" if doc_source == "confluence" else "📋"
        
        if doc_url:
            return f"{source_icon} [{doc_name}]({doc_url})"
        else:
            return f"{source_icon} {doc_name}"

    def get_stats(self) -> Dict[str, Any]:
        """Get query engine statistics"""
        try:
            doc_stats = self.doc_processor.get_document_stats()
            
            # Add AI model availability
            ai_models = []
            if self.anthropic_client:
                ai_models.append("Claude (Anthropic)")
            if self.openai_client:
                ai_models.append("GPT (OpenAI)")
            if not ai_models:
                ai_models.append("Basic fallback (no AI)")

            stats = {
                'total_documents': doc_stats.get('total_documents', 0),
                'total_chunks': doc_stats.get('total_chunks', 0),
                'last_updated': doc_stats.get('last_updated', 'Unknown'),
                'ai_models': ai_models,
                'max_search_results': self.max_search_results,
                'similarity_threshold': self.similarity_threshold
            }
            
            return stats

        except Exception as e:
            logger.error(f"Error getting query engine stats: {str(e)}")
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'last_updated': 'Unknown',
                'ai_models': ['Error retrieving info'],
                'max_search_results': self.max_search_results,
                'similarity_threshold': self.similarity_threshold
            }

    def update_configuration(self, config: Dict[str, Any]) -> bool:
        """Update query engine configuration"""
        try:
            if 'max_search_results' in config:
                self.max_search_results = config['max_search_results']
            
            if 'similarity_threshold' in config:
                self.similarity_threshold = config['similarity_threshold']
            
            if 'max_context_length' in config:
                self.max_context_length = config['max_context_length']
            
            logger.info("Query engine configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating query engine configuration: {str(e)}")
            return False

    def test_ai_connection(self) -> Dict[str, Any]:
        """Test AI service connections"""
        results = {}
        
        # Test Anthropic
        if self.anthropic_client:
            try:
                test_response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=50,
                    messages=[{"role": "user", "content": "Hello, respond with 'Claude is working'"}]
                )
                results['anthropic'] = {
                    'status': 'connected',
                    'model': 'claude-3-haiku-20240307'
                }
            except Exception as e:
                results['anthropic'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            results['anthropic'] = {
                'status': 'not_configured',
                'error': 'No API key provided'
            }
        
        # Test OpenAI
        if self.openai_client:
            try:
                test_response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello, respond with 'OpenAI is working'"}],
                    max_tokens=50
                )
                results['openai'] = {
                    'status': 'connected',
                    'model': 'gpt-3.5-turbo'
                }
            except Exception as e:
                results['openai'] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            results['openai'] = {
                'status': 'not_configured',
                'error': 'No API key provided'
            }
        
        return results

    def search_and_summarize(self, query: str, max_docs: int = 5) -> Dict[str, Any]:
        """Search documents and provide summary without full AI response"""
        try:
            search_results = self.doc_processor.search_documents(
                query=query, 
                num_results=max_docs
            )
            
            if not search_results:
                return {
                    'query': query,
                    'found_documents': 0,
                    'summary': "No relevant documents found.",
                    'documents': []
                }
            
            # Prepare document summaries
            document_summaries = []
            for result in search_results:
                metadata = result['metadata']
                content_preview = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                
                doc_summary = {
                    'name': metadata.get('doc_name', 'Unknown'),
                    'source': metadata.get('doc_source', 'unknown'),
                    'url': metadata.get('url', ''),
                    'relevance_score': 1.0 - result.get('distance', 1.0),  # Convert distance to relevance
                    'content_preview': content_preview
                }
                document_summaries.append(doc_summary)
            
            return {
                'query': query,
                'found_documents': len(search_results),
                'summary': f"Found {len(search_results)} relevant documents",
                'documents': document_summaries
            }
            
        except Exception as e:
            logger.error(f"Error in search and summarize: {str(e)}")
            return {
                'query': query,
                'found_documents': 0,
                'summary': f"Error during search: {str(e)}",
                'documents': []
            }