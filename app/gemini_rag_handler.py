# gemini_rag_handler.py
"""
Gemini AI RAG Handler
Handles document retrieval and question answering using Google Gemini 2.0 Flash
"""
import logging
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from config import Config

logger = logging.getLogger(__name__)


class GeminiRAGHandler:
    """Handle RAG queries using Gemini 2.0 Flash"""

    def __init__(self):
        """Initialize Gemini AI with API key"""
        try:
            # Configure Gemini API
            genai.configure(api_key=Config.GEMINI_API_KEY)

            # Initialize Gemini 2.0 Flash model
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

            # Configuration for responses
            self.generation_config = {
                'temperature': 0.3,  # Lower for factual responses
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 2048,
            }

            # Safety settings (permissive for business use)
            self.safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]

            logger.info("✅ Gemini 2.0 Flash initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini AI: {str(e)}")
            raise

    def generate_answer_with_context(
        self,
        query: str,
        context_documents: List[Dict[str, Any]],
        max_context_docs: int = 10
    ) -> Dict[str, Any]:
        """
        Generate answer using Gemini with retrieved document context

        Args:
            query: User's question
            context_documents: List of retrieved documents with metadata
            max_context_docs: Maximum number of documents to include in context

        Returns:
            Dict with answer and sources
        """
        try:
            # Limit context documents
            relevant_docs = context_documents[:max_context_docs]

            if not relevant_docs:
                # No context - answer as general knowledge query
                return self._generate_general_answer(query)

            # Build context from documents
            context_text = self._build_context(relevant_docs)

            # Create prompt
            prompt = f"""You are InfoBot, an intelligent AI assistant that answers questions based on document context and general knowledge.

**Context Documents:**
{context_text}

**User Question:** {query}

**Instructions:**
1. Answer the question using the provided context documents when relevant
2. If the context has the answer, cite the specific documents by their source URLs
3. If the context doesn't have enough information, use your general knowledge
4. Be clear, concise, and helpful
5. Format source citations as a numbered list at the end

**Answer:**"""

            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )

            answer = response.text

            # Extract sources from context documents
            sources = self._extract_sources(relevant_docs)

            # Format final response with sources
            final_response = self._format_response_with_sources(answer, sources)

            return {
                'answer': final_response,
                'sources': sources,
                'model': 'gemini-2.0-flash-exp',
                'documents_used': len(relevant_docs)
            }

        except Exception as e:
            logger.error(f"Error generating answer with context: {str(e)}")
            return {
                'answer': f"I encountered an error processing your question: {str(e)}",
                'sources': [],
                'model': 'gemini-2.0-flash-exp',
                'error': str(e)
            }

    def _generate_general_answer(self, query: str) -> Dict[str, Any]:
        """Generate answer for general knowledge queries without document context"""
        try:
            prompt = f"""You are InfoBot, a helpful AI assistant. Answer the user's question directly and concisely.

**User Question:** {query}

**Instructions:**
1. Provide a clear, helpful answer in 2-4 sentences
2. Be friendly and conversational
3. If you don't have current information (like weather, news), politely mention that
4. Keep the response concise and helpful

**Answer:**"""

            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )

            return {
                'answer': response.text,
                'sources': [],
                'model': 'gemini-2.0-flash-exp',
                'documents_used': 0
            }

        except Exception as e:
            logger.error(f"Error generating general answer: {str(e)}")
            return {
                'answer': "I'm here to help! I can answer questions about your documents and general knowledge queries.",
                'sources': [],
                'model': 'gemini-2.0-flash-exp',
                'error': str(e)
            }

    def _build_context(self, documents: List[Dict[str, Any]]) -> str:
        """Build context text from retrieved documents"""
        context_parts = []

        for i, doc in enumerate(documents, 1):
            metadata = doc.get('metadata', {})
            content = doc.get('content', '')

            # Get source information
            source = metadata.get('source', 'Unknown')
            title = metadata.get('title', metadata.get('name', 'Untitled'))
            source_type = metadata.get('source_type', 'document')

            # Build context entry
            context_entry = f"""
---
Document {i}:
Title: {title}
Source: {source}
Type: {source_type}

Content:
{content[:2000]}  # Limit content to 2000 chars per doc
---
"""
            context_parts.append(context_entry)

        return "\n".join(context_parts)

    def _extract_sources(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Extract unique source URLs from documents"""
        sources = []
        seen_urls = set()

        for doc in documents:
            metadata = doc.get('metadata', {})

            # Try different source fields
            source_url = (
                metadata.get('url') or
                metadata.get('source') or
                metadata.get('link') or
                metadata.get('web_link')
            )

            if source_url and source_url not in seen_urls:
                seen_urls.add(source_url)
                sources.append(source_url)

        return sources[:5]  # Limit to 5 sources

    def _format_response_with_sources(self, answer: str, sources: List[str]) -> str:
        """Format response with source citations"""
        if not sources:
            return answer

        # Check if answer already has source citations
        if "reference" in answer.lower() or "source" in answer.lower():
            # Gemini already added citations, return as is
            return answer

        # Add sources at the end
        source_text = "\n\n"
        if len(sources) == 1:
            source_text += f"Here is the reference: {sources[0]}"
        else:
            source_text += "Here are the references:\n"
            for i, source_url in enumerate(sources, 1):
                source_text += f"{i}. {source_url}\n"

        return f"{answer}{source_text}"

    def answer_query(self, query: str) -> Dict[str, Any]:
        """
        Answer a general query without document context
        Useful for math, facts, general knowledge
        """
        return self._generate_general_answer(query)
