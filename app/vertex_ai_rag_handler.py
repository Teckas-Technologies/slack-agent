# vertex_ai_rag_handler.py
import os
import logging
from typing import List, Dict, Any, Optional
import vertexai
from vertexai.preview import rag
from vertexai.preview.generative_models import GenerativeModel, Tool

logger = logging.getLogger(__name__)


class VertexAIRAGHandler:
    """Handle VertexAI RAG operations for Google Drive documents"""

    def __init__(self, project_id: str, location: str = "europe-west1"):
        """
        Initialize VertexAI RAG handler

        Args:
            project_id: Google Cloud Project ID
            location: GCP region (default: europe-west1)
        """
        self.project_id = project_id
        self.location = location
        self.corpus = None
        self.corpus_name = None

        try:
            # Initialize Vertex AI
            vertexai.init(project=project_id, location=location)
            logger.info(f"Initialized VertexAI RAG in project {project_id}, location {location}")
        except Exception as e:
            logger.error(f"Failed to initialize VertexAI: {str(e)}")
            raise

    def create_or_get_corpus(self, display_name: str = "google_drive_documents") -> rag.RagCorpus:
        """
        Create a new RAG corpus or get existing one

        Args:
            display_name: Display name for the corpus

        Returns:
            RagCorpus object
        """
        try:
            # Try to list existing corpora
            existing_corpora = rag.list_corpora()

            # Check if corpus with display_name already exists
            for corpus in existing_corpora:
                if corpus.display_name == display_name:
                    logger.info(f"Found existing corpus: {corpus.name}")
                    self.corpus = corpus
                    self.corpus_name = corpus.name
                    return corpus

            # Create new corpus if not found
            logger.info(f"Creating new RAG corpus: {display_name}")

            # Configure embedding model
            embedding_model_config = rag.RagEmbeddingModelConfig(
                vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                    publisher_model="publishers/google/models/text-embedding-005"
                )
            )

            # Create corpus with managed vector DB
            self.corpus = rag.create_corpus(
                display_name=display_name,
                description="RAG corpus for Google Drive documents used in Slack Q&A bot",
                backend_config=rag.RagVectorDbConfig(
                    rag_embedding_model_config=embedding_model_config
                ),
            )

            self.corpus_name = self.corpus.name
            logger.info(f"Created new corpus: {self.corpus_name}")
            return self.corpus

        except Exception as e:
            logger.error(f"Error creating/getting corpus: {str(e)}")
            raise

    def import_drive_files(
        self,
        drive_file_ids: List[str],
        chunk_size: int = 1024,
        chunk_overlap: int = 200,
        max_embedding_requests_per_min: int = 900
    ) -> bool:
        """
        Import Google Drive files into the RAG corpus

        Args:
            drive_file_ids: List of Google Drive file IDs
            chunk_size: Size of text chunks (default: 1024 characters)
            chunk_overlap: Overlap between chunks (default: 200 characters)
            max_embedding_requests_per_min: Rate limit for embeddings

        Returns:
            bool: True if successful
        """
        if not self.corpus_name:
            raise ValueError("Corpus not initialized. Call create_or_get_corpus() first.")

        try:
            # Convert file IDs to Drive URLs
            drive_urls = [
                f"https://drive.google.com/file/d/{file_id}"
                for file_id in drive_file_ids
            ]

            logger.info(f"Importing {len(drive_urls)} files into corpus {self.corpus_name}")

            # Import files with chunking configuration
            response = rag.import_files(
                corpus_name=self.corpus_name,
                paths=drive_urls,
                transformation_config=rag.TransformationConfig(
                    chunking_config=rag.ChunkingConfig(
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                    ),
                ),
                max_embedding_requests_per_min=max_embedding_requests_per_min,
            )

            logger.info(f"Successfully imported files. Response: {response}")
            return True

        except Exception as e:
            logger.error(f"Error importing files: {str(e)}")
            return False

    def import_drive_folder(
        self,
        folder_id: str,
        chunk_size: int = 1024,
        chunk_overlap: int = 200
    ) -> bool:
        """
        Import entire Google Drive folder into the RAG corpus

        Args:
            folder_id: Google Drive folder ID
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks

        Returns:
            bool: True if successful
        """
        if not self.corpus_name:
            raise ValueError("Corpus not initialized. Call create_or_get_corpus() first.")

        try:
            folder_url = f"https://drive.google.com/drive/folders/{folder_id}"

            logger.info(f"Importing folder {folder_url} into corpus {self.corpus_name}")

            response = rag.import_files(
                corpus_name=self.corpus_name,
                paths=[folder_url],
                transformation_config=rag.TransformationConfig(
                    chunking_config=rag.ChunkingConfig(
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap,
                    ),
                ),
            )

            logger.info(f"Successfully imported folder. Response: {response}")
            return True

        except Exception as e:
            logger.error(f"Error importing folder: {str(e)}")
            return False

    def query_corpus(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Query the RAG corpus directly for relevant documents

        Args:
            query: Search query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of relevant document chunks with metadata
        """
        if not self.corpus_name:
            raise ValueError("Corpus not initialized. Call create_or_get_corpus() first.")

        try:
            # Configure retrieval settings
            rag_retrieval_config = rag.RagRetrievalConfig(
                top_k=top_k,
                filter=rag.Filter(vector_distance_threshold=similarity_threshold),
            )

            # Query the corpus
            response = rag.retrieval_query(
                rag_resources=[
                    rag.RagResource(rag_corpus=self.corpus_name)
                ],
                text=query,
                rag_retrieval_config=rag_retrieval_config,
            )

            # Parse response into structured format
            results = []
            if hasattr(response, 'contexts') and response.contexts:
                for context in response.contexts.contexts:
                    result = {
                        'text': context.text,
                        'distance': context.distance,
                        'source': context.source_uri if hasattr(context, 'source_uri') else None,
                    }
                    results.append(result)

            logger.info(f"Query returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Error querying corpus: {str(e)}")
            return []

    def generate_answer(
        self,
        query: str,
        model_name: str = "gemini-2.0-flash-001",
        top_k: int = 5,
        similarity_threshold: float = 0.5,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generate an answer using RAG with Gemini model

        Args:
            query: User's question
            model_name: Gemini model to use
            top_k: Number of context chunks to retrieve
            similarity_threshold: Minimum similarity score
            temperature: Model temperature (0-1, lower is more deterministic)

        Returns:
            Dict with answer and sources
        """
        if not self.corpus_name:
            raise ValueError("Corpus not initialized. Call create_or_get_corpus() first.")

        try:
            # Configure retrieval
            rag_retrieval_config = rag.RagRetrievalConfig(
                top_k=top_k,
                filter=rag.Filter(vector_distance_threshold=similarity_threshold),
            )

            # Create RAG retrieval tool
            rag_retrieval_tool = Tool.from_retrieval(
                retrieval=rag.Retrieval(
                    source=rag.VertexRagStore(
                        rag_resources=[
                            rag.RagResource(rag_corpus=self.corpus_name)
                        ],
                        rag_retrieval_config=rag_retrieval_config,
                    ),
                )
            )

            # Initialize model with RAG tool
            rag_model = GenerativeModel(
                model_name=model_name,
                tools=[rag_retrieval_tool]
            )

            # Generate response
            response = rag_model.generate_content(
                query,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 2048,
                }
            )

            # Extract answer and metadata
            answer = response.text

            # Try to extract source information if available
            sources = []
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'grounding_metadata'):
                        # Extract grounding sources
                        grounding = candidate.grounding_metadata
                        if hasattr(grounding, 'grounding_chunks'):
                            for chunk in grounding.grounding_chunks:
                                if hasattr(chunk, 'web') and hasattr(chunk.web, 'uri'):
                                    sources.append(chunk.web.uri)

            result = {
                'answer': answer,
                'sources': sources,
                'model': model_name
            }

            logger.info(f"Generated answer with {len(sources)} sources")
            return result

        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                'answer': f"I encountered an error while processing your question: {str(e)}",
                'sources': [],
                'model': model_name,
                'error': str(e)
            }

    def get_corpus_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the corpus

        Returns:
            Dict with corpus statistics
        """
        if not self.corpus:
            return {"error": "Corpus not initialized"}

        try:
            stats = {
                "name": self.corpus.name,
                "display_name": self.corpus.display_name,
                "description": self.corpus.description if hasattr(self.corpus, 'description') else None,
                "create_time": self.corpus.create_time if hasattr(self.corpus, 'create_time') else None,
                "update_time": self.corpus.update_time if hasattr(self.corpus, 'update_time') else None,
            }

            # Try to get file count
            try:
                files = rag.list_files(corpus_name=self.corpus_name)
                stats["file_count"] = len(list(files))
            except Exception as e:
                logger.warning(f"Could not get file count: {str(e)}")
                stats["file_count"] = "unknown"

            return stats

        except Exception as e:
            logger.error(f"Error getting corpus stats: {str(e)}")
            return {"error": str(e)}

    def delete_corpus(self) -> bool:
        """
        Delete the RAG corpus

        Returns:
            bool: True if successful
        """
        if not self.corpus_name:
            logger.warning("No corpus to delete")
            return False

        try:
            rag.delete_corpus(name=self.corpus_name)
            logger.info(f"Deleted corpus: {self.corpus_name}")
            self.corpus = None
            self.corpus_name = None
            return True
        except Exception as e:
            logger.error(f"Error deleting corpus: {str(e)}")
            return False

    def update_corpus_files(self, drive_file_ids: List[str]) -> bool:
        """
        Update corpus by re-importing files (useful for updated documents)

        Args:
            drive_file_ids: List of Google Drive file IDs to reimport

        Returns:
            bool: True if successful
        """
        # Note: VertexAI RAG handles updates automatically when reimporting
        # Files with same IDs will be updated rather than duplicated
        return self.import_drive_files(drive_file_ids)
