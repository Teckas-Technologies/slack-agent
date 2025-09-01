# document_processor.py
import os
import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import openai
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process and index documents for search and retrieval"""

    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.chroma_client = self._initialize_chromadb()
        self.collection = self._get_or_create_collection()

        # Chunking parameters
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.max_chunk_size = 2000

    def _initialize_chromadb(self):
        """Initialize ChromaDB client"""
        try:
            # Use persistent storage
            db_path = os.environ.get('CHROMA_DB_PATH', './chroma_db')

            settings = Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=db_path
            )

            client = chromadb.Client(settings)
            return client

        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            # Fallback to in-memory database
            return chromadb.Client()

    def _get_or_create_collection(self):
        """Get or create document collection"""
        try:
            return self.chroma_client.get_or_create_collection(
                name="documents",
                metadata={"description": "Document collection for Slack agent"}
            )
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise

    def process_document(self, document: Dict[str, Any]) -> bool:
        """Process a single document and add to vector store"""
        try:
            doc_id = document['id']
            doc_name = document['name']

            logger.info(f"Processing document: {doc_name}")

            # Check if document is already processed and up-to-date
            if self._is_document_current(document):
                logger.info(f"Document {doc_name} is already up-to-date")
                return True

            # Extract content based on document source
            if document['source'] == 'google_drive':
                from .google_drive_handler import GoogleDriveHandler
                handler = GoogleDriveHandler()
                content_result = handler.get_document_content(document)
            elif document['source'] == 'confluence':
                from .confluence_handler import ConfluenceHandler
                handler = ConfluenceHandler()
                content_result = handler.get_document_content(document)
            else:
                logger.error(f"Unknown document source: {document['source']}")
                return False

            if content_result.get('error'):
                logger.error(f"Error extracting content from {doc_name}: {content_result['error']}")
                return False

            content = content_result.get('content', '')
            if not content.strip():
                logger.warning(f"No content extracted from {doc_name}")
                return False

            # Clean and preprocess content
            cleaned_content = self._clean_content(content)

            # Create chunks
            chunks = self._create_chunks(cleaned_content, document)

            if not chunks:
                logger.warning(f"No chunks created for {doc_name}")
                return False

            # Generate embeddings and store
            self._store_chunks(chunks, document)

            # Update document metadata
            self._update_document_metadata(document)

            logger.info(f"Successfully processed {doc_name} - {len(chunks)} chunks created")
            return True

        except Exception as e:
            logger.error(f"Error processing document {document.get('name', 'Unknown')}: {str(e)}")
            return False

    def _is_document_current(self, document: Dict[str, Any]) -> bool:
        """Check if document is already processed and current"""
        try:
            doc_id = document['id']

            # Query existing chunks for this document
            results = self.collection.get(
                where={"doc_id": doc_id},
                limit=1
            )

            if not results['ids']:
                return False

            # Check if modification time has changed
            stored_metadata = results['metadatas'][0]
            stored_modified = stored_metadata.get('modified_time')
            current_modified = document.get('modified_time')

            return stored_modified == current_modified

        except Exception as e:
            logger.error(f"Error checking document currency: {str(e)}")
            return False

    def _clean_content(self, content: str) -> str:
        """Clean and preprocess document content"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)

        # Remove special characters that might interfere with processing
        content = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\'\/\\]', '', content)

        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Remove empty lines
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        content = '\n'.join(lines)

        return content.strip()

    def _create_chunks(self, content: str, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks from document content"""
        chunks = []

        # Split content based on document type
        doc_type = document.get('mime_type', '')

        if 'spreadsheet' in doc_type or doc_type == 'text/csv':
            # For structured data, split by rows/sections
            chunks = self._create_structured_chunks(content, document)
        else:
            # For text documents, use semantic chunking
            chunks = self._create_text_chunks(content, document)

        return chunks

    def _create_text_chunks(self, content: str, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks for text-based documents"""
        chunks = []

        # Split by paragraphs first
        paragraphs = content.split('\n\n')

        current_chunk = ""
        chunk_index = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # Check if adding this paragraph exceeds chunk size
            potential_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph

            if len(potential_chunk) > self.chunk_size and current_chunk:
                # Store current chunk
                chunk_data = self._create_chunk_data(
                    current_chunk, document, chunk_index
                )
                chunks.append(chunk_data)
                chunk_index += 1

                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(
                    current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_text + "\n\n" + paragraph
            else:
                current_chunk = potential_chunk

            # Handle very long paragraphs
            if len(current_chunk) > self.max_chunk_size:
                # Split long paragraph
                long_chunks = self._split_long_content(current_chunk, document, chunk_index)
                chunks.extend(long_chunks)
                chunk_index += len(long_chunks)
                current_chunk = ""

        # Add final chunk
        if current_chunk.strip():
            chunk_data = self._create_chunk_data(
                current_chunk, document, chunk_index
            )
            chunks.append(chunk_data)

        return chunks

    def _create_structured_chunks(self, content: str, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create chunks for structured documents (CSV, spreadsheets)"""
        chunks = []
        lines = content.split('\n')

        if not lines:
            return chunks

        # For CSV/spreadsheet, create chunks with headers
        header = lines[0] if lines else ""
        current_chunk_lines = [header]
        chunk_index = 0

        for i, line in enumerate(lines[1:], 1):
            current_chunk_lines.append(line)

            # Create chunk every 50 rows or when size limit reached
            chunk_content = '\n'.join(current_chunk_lines)
            if len(current_chunk_lines) >= 50 or len(chunk_content) > self.chunk_size:
                chunk_data = self._create_chunk_data(
                    chunk_content, document, chunk_index
                )
                chunks.append(chunk_data)
                chunk_index += 1

                # Start new chunk with header
                current_chunk_lines = [header]

        # Add final chunk
        if len(current_chunk_lines) > 1:  # More than just header
            chunk_content = '\n'.join(current_chunk_lines)
            chunk_data = self._create_chunk_data(
                chunk_content, document, chunk_index
            )
            chunks.append(chunk_data)

        return chunks

    def _split_long_content(self, content: str, document: Dict[str, Any], start_index: int) -> List[Dict[str, Any]]:
        """Split very long content into smaller chunks"""
        chunks = []
        sentences = re.split(r'[.!?]+', content)

        current_chunk = ""
        chunk_index = start_index

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            potential_chunk = current_chunk + ". " + sentence if current_chunk else sentence

            if len(potential_chunk) > self.chunk_size and current_chunk:
                chunk_data = self._create_chunk_data(
                    current_chunk, document, chunk_index
                )
                chunks.append(chunk_data)
                chunk_index += 1
                current_chunk = sentence
            else:
                current_chunk = potential_chunk

        if current_chunk.strip():
            chunk_data = self._create_chunk_data(
                current_chunk, document, chunk_index
            )
            chunks.append(chunk_data)

        return chunks

    def _create_chunk_data(self, content: str, document: Dict[str, Any], chunk_index: int) -> Dict[str, Any]:
        """Create chunk data structure"""
        chunk_id = f"{document['id']}_{chunk_index}"

        return {
            'id': chunk_id,
            'content': content,
            'metadata': {
                'doc_id': document['id'],
                'doc_name': document['name'],
                'doc_source': document['source'],
                'doc_type': document.get('mime_type', ''),
                'chunk_index': chunk_index,
                'modified_time': document.get('modified_time', ''),
                'url': document.get('url', ''),
                'chunk_length': len(content)
            }
        }

    def _store_chunks(self, chunks: List[Dict[str, Any]], document: Dict[str, Any]):
        """Store chunks in vector database"""
        try:
            # Remove existing chunks for this document
            self._remove_document_chunks(document['id'])

            if not chunks:
                return

            # Generate embeddings for all chunks
            contents = [chunk['content'] for chunk in chunks]
            embeddings = self._generate_embeddings(contents)

            # Prepare data for ChromaDB
            ids = [chunk['id'] for chunk in chunks]
            metadatas = [chunk['metadata'] for chunk in chunks]
            documents = [chunk['content'] for chunk in chunks]

            # Store in ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )

            logger.info(f"Stored {len(chunks)} chunks for document {document['name']}")

        except Exception as e:
            logger.error(f"Error storing chunks: {str(e)}")
            raise

    def _remove_document_chunks(self, doc_id: str):
        """Remove existing chunks for a document"""
        try:
            # Get existing chunk IDs
            results = self.collection.get(
                where={"doc_id": doc_id}
            )

            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Removed {len(results['ids'])} existing chunks for document {doc_id}")

        except Exception as e:
            logger.error(f"Error removing document chunks: {str(e)}")

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        try:
            # Use OpenAI embeddings
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )

            embeddings = [item.embedding for item in response.data]
            return embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return zero embeddings as fallback
            return [[0.0] * 1536] * len(texts)

    def _update_document_metadata(self, document: Dict[str, Any]):
        """Update document processing metadata"""
        try:
            metadata_key = f"doc_metadata_{document['id']}"

            metadata = {
                'doc_id': document['id'],
                'doc_name': document['name'],
                'processed_at': datetime.now().isoformat(),
                'modified_time': document.get('modified_time', ''),
                'source': document['source']
            }

            # Store metadata (you might want to use a separate store for this)
            # For now, we'll create a special metadata document
            self.collection.add(
                ids=[metadata_key],
                documents=[json.dumps(metadata)],
                metadatas=[{"type": "document_metadata", "doc_id": document['id']}],
                embeddings=[[0.0] * 1536]  # Zero embedding for metadata
            )

        except Exception as e:
            logger.error(f"Error updating document metadata: {str(e)}")

    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about processed documents"""
        try:
            # Get all chunks (excluding metadata)
            results = self.collection.get(
                where={"type": {"$ne": "document_metadata"}}
            )

            total_chunks = len(results['ids'])

            # Count unique documents
            doc_ids = set()
            for metadata in results['metadatas']:
                doc_ids.add(metadata.get('doc_id', ''))

            total_documents = len(doc_ids)

            return {
                'total_documents': total_documents,
                'total_chunks': total_chunks,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting document stats: {str(e)}")
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'last_updated': 'Unknown'
            }

    def search_documents(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search for relevant document chunks"""
        try:
            # Generate query embedding
            query_embedding = self._generate_embeddings([query])[0]

            # Search in ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=num_results,
                where={"type": {"$ne": "document_metadata"}}
            )

            # Format results
            search_results = []
            for i in range(len(results['ids'][0])):
                result = {
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else 0
                }
                search_results.append(result)

            return search_results

        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []

    def cleanup_old_documents(self, days_old: int = 30):
        """Clean up old/stale document chunks"""
        try:
            # This would implement cleanup logic based on modification dates
            # For now, just log the intent
            logger.info(f"Cleanup old documents older than {days_old} days")
            # Implementation would go here

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")