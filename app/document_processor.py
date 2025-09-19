# document_processor.py
import os
import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
from config import Config
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process and index documents for search and retrieval"""

    def __init__(self):
        self.vector_store = VectorStore()

        # Chunking parameters
        self.chunk_size = 1000
        self.chunk_overlap = 200
        self.max_chunk_size = 2000

        # Document type specific settings
        self.structured_chunk_size = 50  # rows for CSV/spreadsheets
        self.min_chunk_length = 50  # minimum characters for a chunk


    def process_document(self, document: Dict[str, Any]) -> bool:
        """Process a single document and add to vector store"""
        try:
            doc_id = document['id']
            doc_name = document['name']

            logger.info(f"Processing document: {doc_name}")

            # Check if document is already current (optional optimization)
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

            logger.info(f"Content extraction result for {doc_name}: {type(content_result)}")
            if content_result.get('error'):
                logger.error(f"Error extracting content from {doc_name}: {content_result['error']}")
                return False

            content = content_result.get('content', '')
            logger.info(f"Content extracted from {doc_name}: {len(content)} characters")
            if not content.strip():
                logger.warning(f"No content extracted from {doc_name}")
                return False

            # Clean and preprocess content
            cleaned_content = self._clean_content(content)

            # Create chunks
            logger.info(f"Creating chunks for {doc_name} from {len(cleaned_content)} cleaned characters")
            chunks = self._create_chunks(cleaned_content, document)
            logger.info(f"Created {len(chunks)} chunks for {doc_name}")

            if not chunks:
                logger.warning(f"No chunks created for {doc_name}")
                return False

            # Generate embeddings and store
            logger.info(f"Storing {len(chunks)} chunks for {doc_name}")
            self._store_chunks(chunks, document)
            logger.info(f"Successfully stored chunks for {doc_name}")

            # Update document metadata
            self._update_document_metadata(document)

            logger.info(f"Successfully processed {doc_name} - {len(chunks)} chunks created")
            return True

        except Exception as e:
            logger.error(f"Error processing document {document.get('name', 'Unknown')}: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def _is_document_current(self, document: Dict[str, Any]) -> bool:
        """Check if document is already processed and current"""
        try:
            doc_id = document['id']

            # Search for existing chunks for this document
            search_results = self.vector_store.search_documents(
                query="",  # Empty query to get any document
                num_results=1,
                filter_criteria={"doc_id": doc_id}
            )

            if not search_results:
                return False

            # Check if modification time has changed
            stored_metadata = search_results[0]['metadata']
            stored_modified = stored_metadata.get('modified_time')
            current_modified = document.get('modified_time')

            return stored_modified == current_modified

        except Exception as e:
            logger.error(f"Error checking document currency: {str(e)}")
            return False

    def _clean_content(self, content: str) -> str:
        """Clean and preprocess document content"""
        if not content:
            return ""

        # Remove excessive whitespace but preserve paragraph structure
        content = re.sub(r'[ \t]+', ' ', content)  # Multiple spaces/tabs to single space
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Multiple newlines to double newline

        # Remove special characters that might interfere with processing but keep essential punctuation
        content = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\'\/\\@#$%&+=<>{}|~`*]', '', content)

        # Normalize line endings
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        # Remove leading/trailing whitespace from lines while preserving structure
        lines = [line.strip() for line in content.split('\n')]
        content = '\n'.join(lines)

        # Remove excessive empty lines but keep paragraph breaks
        content = re.sub(r'\n{3,}', '\n\n', content)

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
            # For text documents, use intelligent chunking
            chunks = self._create_text_chunks(content, document)

        return chunks

    def _create_text_chunks(self, content: str, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create intelligent chunks for text-based documents"""
        chunks = []

        # First try to split by semantic sections (headers, etc.)
        sections = self._split_by_sections(content)

        if not sections:
            # Fallback to paragraph-based chunking
            sections = content.split('\n\n')

        current_chunk = ""
        chunk_index = 0

        for section in sections:
            section = section.strip()
            if not section or len(section) < self.min_chunk_length:
                continue

            # Check if adding this section exceeds chunk size
            potential_chunk = current_chunk + "\n\n" + section if current_chunk else section

            if len(potential_chunk) > self.chunk_size and current_chunk:
                # Store current chunk if it meets minimum length
                if len(current_chunk.strip()) >= self.min_chunk_length:
                    chunk_data = self._create_chunk_data(
                        current_chunk, document, chunk_index
                    )
                    chunks.append(chunk_data)
                    chunk_index += 1

                # Start new chunk with intelligent overlap
                overlap_text = self._get_smart_overlap(current_chunk)
                current_chunk = overlap_text + "\n\n" + section if overlap_text else section
            else:
                current_chunk = potential_chunk

            # Handle very long sections
            if len(current_chunk) > self.max_chunk_size:
                long_chunks = self._split_long_content(current_chunk, document, chunk_index)
                chunks.extend(long_chunks)
                chunk_index += len(long_chunks)
                current_chunk = ""

        # Add final chunk if it meets minimum length
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_length:
            chunk_data = self._create_chunk_data(
                current_chunk, document, chunk_index
            )
            chunks.append(chunk_data)

        return chunks

    def _split_by_sections(self, content: str) -> List[str]:
        """Split content by semantic sections (headers, etc.)"""
        # Look for common section markers
        section_patterns = [
            r'\n\s*#{1,6}\s+.+\n',  # Markdown headers
            r'\n\s*[A-Z][A-Z\s]{3,}\n',  # ALL CAPS headers
            r'\n\s*\d+\.\s+[A-Z].+\n',  # Numbered sections
            r'\n\s*[A-Z][a-z]+:?\s*\n'  # Title case headers
        ]

        # Try to split by any of these patterns
        for pattern in section_patterns:
            sections = re.split(pattern, content)
            if len(sections) > 1:
                return [section.strip() for section in sections if section.strip()]

        return []

    def _get_smart_overlap(self, chunk: str) -> str:
        """Get intelligent overlap from the end of a chunk"""
        if len(chunk) <= self.chunk_overlap:
            return chunk

        # Try to find a good breaking point (sentence end)
        overlap_text = chunk[-self.chunk_overlap:]

        # Look for sentence boundaries in the overlap
        sentences = re.split(r'[.!?]+', overlap_text)
        if len(sentences) > 1:
            # Take the last complete sentence(s)
            return sentences[-2] + '.' if len(sentences) > 2 else overlap_text

        return overlap_text

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

            # Store chunks using vector store
            success = self.vector_store.add_documents(chunks)

            if success:
                logger.info(f"Stored {len(chunks)} chunks for document {document['name']}")
            else:
                logger.error(f"Failed to store chunks for document {document['name']}")
                raise Exception("Vector store operation failed")

        except Exception as e:
            logger.error(f"Error storing chunks: {str(e)}")
            raise

    def _remove_document_chunks(self, doc_id: str):
        """Remove existing chunks for a document"""
        try:
            # Remove chunks using vector store filter
            success = self.vector_store.remove_documents_by_filter({"doc_id": doc_id})

            if not success:
                logger.warning(f"Failed to remove existing chunks for document {doc_id}")

        except Exception as e:
            logger.error(f"Error removing document chunks: {str(e)}")


    def _update_document_metadata(self, document: Dict[str, Any]):
        """Update document processing metadata"""
        try:
            metadata_key = f"doc_metadata_{document['id']}"

            metadata_doc = {
                'id': metadata_key,
                'content': json.dumps({
                    'doc_id': document['id'],
                    'doc_name': document['name'],
                    'processed_at': datetime.now().isoformat(),
                    'modified_time': document.get('modified_time', ''),
                    'source': document['source']
                }),
                'metadata': {
                    "type": "document_metadata",
                    "doc_id": document['id'],
                    "doc_name": document['name'],
                    "doc_source": document['source']
                }
            }

            # Store metadata using vector store
            self.vector_store.add_documents([metadata_doc])

        except Exception as e:
            logger.error(f"Error updating document metadata: {str(e)}")

    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about processed documents"""
        try:
            # Get stats from vector store
            vector_stats = self.vector_store.get_collection_stats()

            return {
                'total_documents': vector_stats.get('unique_documents', 0),
                'total_chunks': vector_stats.get('total_chunks', 0),
                'total_entries': vector_stats.get('total_entries', 0),
                'sources': vector_stats.get('sources', []),
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting document stats: {str(e)}")
            return {
                'total_documents': 0,
                'total_chunks': 0,
                'total_entries': 0,
                'sources': [],
                'last_updated': 'Unknown'
            }

    def search_documents(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search for relevant document chunks"""
        try:
            # Use vector store for search, excluding metadata documents
            # Note: ChromaDB uses different filter syntax than MongoDB
            search_results = self.vector_store.search_documents(
                query=query,
                num_results=num_results
            )

            # Filter out metadata documents from results
            filtered_results = []
            for result in search_results:
                metadata = result.get('metadata', {})
                if metadata.get('type') != 'document_metadata':
                    filtered_results.append(result)

            return filtered_results

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