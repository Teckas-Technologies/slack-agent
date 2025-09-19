# vector_store.py
import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import openai
from config import Config

logger = logging.getLogger(__name__)


class VectorStore:
    """Abstraction layer for vector database operations"""

    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.chroma_client = self._initialize_chromadb()
        self.collection = self._get_or_create_collection()

    def _initialize_chromadb(self):
        """Initialize ChromaDB client with proper settings"""
        try:
            db_path = Config.CHROMA_DB_PATH
            os.makedirs(db_path, exist_ok=True)

            # Initialize ChromaDB client without deprecated settings
            client = chromadb.PersistentClient(path=db_path)
            logger.info(f"ChromaDB initialized at {db_path}")
            return client

        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            # If there's a schema issue, try to recreate the database
            try:
                import shutil
                logger.warning(f"Attempting to recreate ChromaDB due to schema issue")
                if os.path.exists(db_path):
                    shutil.rmtree(db_path)
                os.makedirs(db_path, exist_ok=True)
                client = chromadb.PersistentClient(path=db_path)
                logger.info(f"ChromaDB recreated successfully at {db_path}")
                return client
            except Exception as e2:
                logger.error(f"Failed to recreate ChromaDB: {str(e2)}")
                # Fallback to in-memory database
                logger.warning("Falling back to in-memory ChromaDB")
                return chromadb.EphemeralClient()

    def _get_or_create_collection(self):
        """Get or create document collection"""
        try:
            collection_name = "documents"
            return self.chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "Document collection for InfoBot"}
            )
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise

    def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to the vector store"""
        try:
            if not documents:
                return True

            # Prepare data for ChromaDB
            ids = [doc['id'] for doc in documents]
            contents = [doc['content'] for doc in documents]
            metadatas = [doc['metadata'] for doc in documents]

            # Generate embeddings
            embeddings = self._generate_embeddings(contents)

            # Store in ChromaDB
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=contents
            )

            logger.info(f"Added {len(documents)} documents to vector store")
            return True

        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            return False

    def search_documents(self, query: str, num_results: int = 10,
                        filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for relevant documents"""
        try:
            # Generate query embedding
            query_embedding = self._generate_embeddings([query])[0]

            # Prepare search parameters
            search_params = {
                "query_embeddings": [query_embedding],
                "n_results": num_results
            }

            # Add filter if provided (ChromaDB has specific filter syntax)
            if filter_criteria:
                # Handle simple equality filters
                where_clause = {}
                for key, value in filter_criteria.items():
                    if isinstance(value, dict) and "$ne" in value:
                        # Convert MongoDB-style $ne to ChromaDB syntax
                        continue  # Skip complex filters for now
                    else:
                        where_clause[key] = value

                if where_clause:
                    search_params["where"] = where_clause

            # Search in ChromaDB
            results = self.collection.query(**search_params)

            # Format results
            search_results = []
            for i in range(len(results['ids'][0])):
                result = {
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else 0
                }
                search_results.append(result)

            return search_results

        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []

    def remove_documents(self, doc_ids: List[str]) -> bool:
        """Remove documents from the vector store"""
        try:
            if not doc_ids:
                return True

            # Get existing documents to remove
            existing_results = self.collection.get(ids=doc_ids)

            if existing_results['ids']:
                self.collection.delete(ids=existing_results['ids'])
                logger.info(f"Removed {len(existing_results['ids'])} documents")

            return True

        except Exception as e:
            logger.error(f"Error removing documents: {str(e)}")
            return False

    def remove_documents_by_filter(self, filter_criteria: Dict[str, Any]) -> bool:
        """Remove documents matching filter criteria"""
        try:
            # Get documents matching the filter
            results = self.collection.get(where=filter_criteria)

            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"Removed {len(results['ids'])} documents matching filter")

            return True

        except Exception as e:
            logger.error(f"Error removing documents by filter: {str(e)}")
            return False

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            # Get all documents
            results = self.collection.get()
            total_documents = len(results['ids'])

            # Count unique document sources
            doc_ids = set()
            actual_chunks = 0
            sources = set()

            for metadata in results['metadatas']:
                if metadata and metadata.get('type') != 'document_metadata':
                    doc_ids.add(metadata.get('doc_id', ''))
                    sources.add(metadata.get('doc_source', 'unknown'))
                    actual_chunks += 1

            return {
                'total_entries': total_documents,
                'total_chunks': actual_chunks,
                'unique_documents': len(doc_ids),
                'sources': list(sources),
                'collection_name': self.collection.name
            }

        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                'total_entries': 0,
                'total_chunks': 0,
                'unique_documents': 0,
                'sources': [],
                'collection_name': 'unknown'
            }

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        try:
            if not Config.OPENAI_API_KEY:
                logger.warning("No OpenAI API key configured, using simple text-based embeddings")
                return self._generate_simple_embeddings(texts)

            # Use OpenAI embeddings
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )

            embeddings = [item.embedding for item in response.data]
            return embeddings

        except Exception as e:
            logger.error(f"Error generating OpenAI embeddings: {str(e)}")
            # Fall back to simple embeddings instead of zero embeddings
            logger.info("Falling back to simple text-based embeddings")
            return self._generate_simple_embeddings(texts)

    def _generate_simple_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate simple embeddings based on text features when OpenAI is unavailable"""
        import hashlib
        import math

        embeddings = []
        for text in texts:
            # Create a deterministic embedding based on text content
            text_lower = text.lower()

            # Use a hash-based approach for consistency
            hash_obj = hashlib.md5(text_lower.encode())
            hash_bytes = hash_obj.digest()

            # Convert hash to normalized float values
            embedding = []
            for i in range(0, len(hash_bytes), 2):
                # Use pairs of bytes to create float values
                val = int.from_bytes(hash_bytes[i:i+2], 'big') / 65535.0
                embedding.append(val)

            # Pad or truncate to match OpenAI embedding size (1536)
            target_size = 1536
            while len(embedding) < target_size:
                embedding.extend(embedding[:target_size - len(embedding)])
            embedding = embedding[:target_size]

            # Add some text-based features
            word_count = len(text_lower.split())
            char_count = len(text_lower)

            # Normalize and add as features
            embedding[0] = word_count / 1000.0  # Normalize word count
            embedding[1] = char_count / 10000.0  # Normalize char count

            # Add common keyword indicators
            keywords = ['price', 'cost', 'plan', 'strategy', 'logistics', 'brand', 'market']
            for i, keyword in enumerate(keywords):
                if i + 2 < len(embedding):
                    embedding[i + 2] = 1.0 if keyword in text_lower else 0.0

            embeddings.append(embedding)

        return embeddings

    def clear_collection(self) -> bool:
        """Clear all documents from the collection"""
        try:
            # Delete the collection and recreate it
            collection_name = self.collection.name
            self.chroma_client.delete_collection(name=collection_name)
            self.collection = self._get_or_create_collection()

            logger.info("Collection cleared successfully")
            return True

        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Check the health of the vector store"""
        try:
            # Try to get collection info
            stats = self.get_collection_stats()

            return {
                'status': 'healthy',
                'backend': 'ChromaDB',
                'statistics': stats
            }

        except Exception as e:
            logger.error(f"Vector store health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'backend': 'ChromaDB',
                'error': str(e)
            }

    def backup_collection(self, backup_path: str) -> bool:
        """Backup the collection to a file"""
        try:
            import json

            # Get all documents
            results = self.collection.get(include=['embeddings', 'metadatas', 'documents'])

            backup_data = {
                'collection_name': self.collection.name,
                'documents': results['documents'],
                'metadatas': results['metadatas'],
                'ids': results['ids'],
                'embeddings': results['embeddings']
            }

            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)

            logger.info(f"Collection backed up to {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Error backing up collection: {str(e)}")
            return False

    def restore_collection(self, backup_path: str) -> bool:
        """Restore the collection from a backup file"""
        try:
            import json

            with open(backup_path, 'r') as f:
                backup_data = json.load(f)

            # Clear existing collection
            self.clear_collection()

            # Restore data
            if backup_data['ids']:
                self.collection.add(
                    ids=backup_data['ids'],
                    embeddings=backup_data['embeddings'],
                    metadatas=backup_data['metadatas'],
                    documents=backup_data['documents']
                )

            logger.info(f"Collection restored from {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Error restoring collection: {str(e)}")
            return False