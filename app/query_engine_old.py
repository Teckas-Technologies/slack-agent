# query_engine.py
import os
import logging
from typing import List, Dict, Any, Optional
import anthropic
import openai
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)


class QueryEngine:
    """Handle user queries using RAG with AI models"""

    def __init__(self):
        # Initialize AI clients
        self.openai_client = None
        self.anthropic_client = None

        # Initialize Anthropic (primary for fallback responses)
        if Config.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

        # Initialize OpenAI (secondary fallback)
        if Config.OPENAI_API_KEY:
            self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)

        # Initialize VertexAI RAG (required - no ChromaDB fallback)
        self.use_vertex_rag = Config.USE_VERTEX_AI_RAG
        self.vertex_sync_service = None

        if self.use_vertex_rag:
            try:
                from .drive_sync_service import DriveSyncService
                self.vertex_sync_service = DriveSyncService()
                if self.vertex_sync_service.is_configured():
                    logger.info("✅ VertexAI RAG initialized successfully for document search")
                else:
                    raise ValueError("VertexAI RAG not configured. Set GCP_PROJECT_ID in .env")
            except Exception as e:
                logger.error(f"❌ Failed to initialize VertexAI RAG: {str(e)}")
                raise RuntimeError("VertexAI RAG initialization failed. Check your GCP configuration.")
        else:
            raise ValueError("VertexAI RAG is required. Set USE_VERTEX_AI_RAG=true in .env")

        # Configuration - Adjust for better search performance
        self.max_context_length = 4000
        self.max_search_results = 5  # Reduce to get more focused results
        self.similarity_threshold = 0.5  # Threshold for VertexAI RAG
        self.simple_similarity_threshold = 500.0  # Higher threshold for simple embeddings

    def process_query(self, query: str) -> str:
        """Process user query and return response"""
        try:
            logger.info(f"Processing query: {query[:100]}...")

            # Check for special query types first
            special_response = self._handle_special_queries(query)
            if special_response:
                return special_response

            # Use VertexAI RAG (required)
            return self._process_query_with_vertex_rag(query)

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return "❌ Sorry, I encountered an error processing your query. Please try again or contact support."

    def _process_query_with_vertex_rag(self, query: str) -> str:
        """Process query using VertexAI RAG"""
        try:
            logger.info("Processing query with VertexAI RAG")

            # Use VertexAI RAG with Gemini to generate answer
            result = self.vertex_sync_service.generate_answer(
                query_text=query,
                model_name="gemini-2.0-flash-001"
            )

            if 'error' in result:
                logger.error(f"VertexAI RAG error: {result['error']}")
                # Fallback to general response
                return self._generate_general_response(query)

            answer = result.get('answer', '')
            sources = result.get('sources', [])

            # Check if answer indicates no information found
            if not answer or "cannot find" in answer.lower() or "no information" in answer.lower():
                logger.info("VertexAI RAG returned no information, using general AI response")
                return self._generate_general_response(query)

            # Format response with sources
            if sources and len(sources) > 0:
                logger.info(f"Formatting {len(sources)} source URLs")
                # Format source links (they are Google Drive URLs)
                source_text = "\n\n"
                if len(sources) == 1:
                    source_text += f"Here is the reference: {sources[0]}"
                else:
                    source_text += "Here are the references:\n"
                    for i, source_url in enumerate(sources[:3], 1):  # Limit to 3 sources
                        source_text += f"{i}. {source_url}\n"

                final_response = f"{answer}{source_text}"
            else:
                # If no sources from grounding metadata, try direct retrieval query
                logger.info("No sources in response, attempting direct retrieval")
                try:
                    retrieval_results = self.vertex_sync_service.vertex_rag_handler.query_corpus(
                        query=query,
                        top_k=3,
                        similarity_threshold=0.5
                    )

                    if retrieval_results:
                        source_text = "\n\n"
                        unique_urls = set()
                        for result in retrieval_results:
                            source_url = result.get('source')
                            if source_url and source_url not in unique_urls:
                                unique_urls.add(source_url)

                        if unique_urls:
                            if len(unique_urls) == 1:
                                source_text += f"Here is the reference: {list(unique_urls)[0]}"
                            else:
                                source_text += "Here are the references:\n"
                                for i, url in enumerate(list(unique_urls)[:3], 1):
                                    source_text += f"{i}. {url}\n"
                            final_response = f"{answer}{source_text}"
                        else:
                            final_response = answer
                    else:
                        final_response = answer
                except Exception as e:
                    logger.error(f"Error in fallback retrieval: {str(e)}")
                    final_response = answer

            return final_response

        except Exception as e:
            logger.error(f"Error in VertexAI RAG query processing: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Fallback to general response
            return self._generate_general_response(query)

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

    def _handle_special_queries(self, query: str) -> Optional[str]:
        """Handle special queries like greetings, system info, document lists"""
        query_lower = query.lower().strip()

        # Greetings
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
        if any(query_lower == greeting or query_lower.startswith(greeting + ' ') for greeting in greetings):
            return "👋 Hello! I'm InfoBot, your AI assistant powered by VertexAI RAG. I can help you find information from your Google Drive documents. Just ask me anything!"

        # Help queries
        help_keywords = ['how can you help', 'what can you do', 'how are you helpful', 'help me', 'what do you do']
        if any(keyword in query_lower for keyword in help_keywords):
            return f"""I'm InfoBot, your intelligent assistant! Here's what I can do:

📚 **Document Search**: I search through your Google Drive documents using VertexAI RAG
💬 **General Questions**: I can answer general questions on any topic
📊 **System Commands**:
   • `/status` - Check my current status
   • `/refresh` - Refresh document index from shared folders

Just ask me anything - whether it's about your documents or a general question!"""

        # Document count/list queries - VertexAI doesn't expose these stats easily
        count_keywords = ['how many document', 'document count', 'number of document', 'total document', 'list document', 'show document']
        if any(keyword in query_lower for keyword in count_keywords):
            try:
                stats = self.vertex_sync_service.get_sync_status()
                if 'folders_count' in stats or 'synced_files_count' in stats:
                    folder_count = stats.get('folders_count', stats.get('synced_files_count', 'unknown'))
                    last_sync = stats.get('last_sync_time', 'Never')
                    return f"""📊 **Document Status**:
• Synced Folders: {folder_count}
• Last Sync: {last_sync}
• Mode: VertexAI RAG with auto-sync enabled

All documents in shared Google Drive folders are indexed and searchable!"""
                else:
                    return "📊 Documents are indexed via VertexAI RAG. All files in shared Google Drive folders are searchable!"
            except Exception as e:
                logger.error(f"Error getting sync status: {str(e)}")
                return "📊 Documents are indexed via VertexAI RAG and auto-synced from Google Drive."

        return None

    def _list_all_documents(self) -> str:
        """List all indexed documents"""
        try:
            # Get all document metadata from vector store
            results = self.doc_processor.vector_store.collection.get()

            if not results or not results.get('metadatas'):
                return "📚 No documents have been indexed yet. Use `/refresh` to index your documents."

            # Extract unique documents
            docs_by_source = {}
            for metadata in results['metadatas']:
                doc_name = metadata.get('doc_name', 'Unknown')
                doc_source = metadata.get('doc_source', 'unknown')
                doc_url = metadata.get('url', '')

                if doc_source not in docs_by_source:
                    docs_by_source[doc_source] = []

                # Avoid duplicates
                if not any(d['name'] == doc_name for d in docs_by_source[doc_source]):
                    docs_by_source[doc_source].append({
                        'name': doc_name,
                        'url': doc_url
                    })

            # Format response
            response_parts = ["📚 **Indexed Documents**:\n"]

            for source, docs in docs_by_source.items():
                response_parts.append(f"\n**{source.upper()}** ({len(docs)} documents):")
                for doc in sorted(docs, key=lambda x: x['name'])[:20]:  # Limit to 20 per source
                    if doc['url']:
                        response_parts.append(f"  • [{doc['name']}]({doc['url']})")
                    else:
                        response_parts.append(f"  • {doc['name']}")

                if len(docs) > 20:
                    response_parts.append(f"  ... and {len(docs) - 20} more")

            return '\n'.join(response_parts)

        except Exception as e:
            logger.error(f"Error listing documents: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return "❌ Error retrieving document list. Please try again."

    def _generate_general_response(self, query: str) -> str:
        """Generate response for general queries without document context"""
        try:
            logger.info("Generating general AI response (no document context)")

            # Create prompt for general knowledge
            prompt = f"""You are InfoBot, a helpful AI assistant. Answer the user's question directly and concisely.

User Question: {query}

Instructions:
1. Provide a clear, helpful answer in 2-3 sentences
2. Be friendly and conversational
3. If you don't have access to current information (like weather, news), politely mention that
4. Keep the response concise and helpful

Answer:"""

            # Try Anthropic first, then OpenAI
            if self.anthropic_client:
                logger.info("Using Anthropic (Claude) for general response")
                response = self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=500,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
            elif self.openai_client:
                logger.info("Using OpenAI (GPT) for general response")
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are InfoBot, a helpful AI assistant. Answer questions concisely and helpfully."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            else:
                return "I'm InfoBot, but I need AI API keys configured to answer general questions. I can still search through your indexed documents if you have any!"

        except Exception as e:
            logger.error(f"Error generating general response: {str(e)}")
            return "I'm here to help! I can search through your documents and answer questions. What would you like to know?"

    def _create_prompt(self, query: str, context: str) -> str:
        """Create prompt for AI model"""
        prompt = f"""Answer the user's question based ONLY on the provided document context. Be very concise and direct.

Context from relevant documents:
{context}

User Question: {query}

Instructions:
1. If the context contains relevant information to answer the question, provide a short, direct answer (1-2 sentences maximum)
2. Extract only the most relevant information that directly answers the question
3. If the context does NOT contain relevant information to answer the question, respond EXACTLY with: "Information not found in documents"
4. Do not make assumptions or provide general knowledge - only answer based on the provided context
5. Do not mention document names in your answer

Answer:"""

        return prompt

    def _get_anthropic_response(self, prompt: str) -> str:
        """Get response from Anthropic Claude"""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
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
        """Format source information according to requirements"""
        if not search_results:
            return "No sources found"

        # Format according to the example: "Here is the reference [Document Link]"
        unique_sources = {}

        for result in search_results:
            metadata = result['metadata']
            doc_name = metadata.get('doc_name', 'Unknown Document')
            doc_url = metadata.get('url', '')

            if doc_name not in unique_sources:
                unique_sources[doc_name] = doc_url

        # Create reference links
        source_links = []
        for doc_name, doc_url in unique_sources.items():
            if doc_url:
                source_links.append(f"[{doc_name}]({doc_url})")
            else:
                source_links.append(doc_name)

        if source_links:
            if len(source_links) == 1:
                return f"Here is the reference: {source_links[0]}"
            else:
                return f"Here are the references: {', '.join(source_links)}"
        else:
            return "No sources found"

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