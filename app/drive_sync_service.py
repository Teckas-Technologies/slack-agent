# drive_sync_service.py
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .google_drive_handler import GoogleDriveHandler
from .vertex_ai_rag_handler import VertexAIRAGHandler
from config import Config

logger = logging.getLogger(__name__)


class DriveSyncService:
    """Service to sync Google Drive documents to VertexAI RAG"""

    def __init__(self):
        self.drive_handler = GoogleDriveHandler()
        self.vertex_rag_handler = None
        self.last_sync_time = None
        self.synced_files = set()  # Track synced file IDs
        self.use_folder_mode = False
        self.folder_ids = []

        # Initialize VertexAI RAG if configured
        if Config.GCP_PROJECT_ID and Config.USE_VERTEX_AI_RAG:
            try:
                self.vertex_rag_handler = VertexAIRAGHandler(
                    project_id=Config.GCP_PROJECT_ID,
                    location=Config.GCP_LOCATION
                )
                # Create or get corpus
                self.vertex_rag_handler.create_or_get_corpus(
                    display_name=Config.VERTEX_RAG_CORPUS_NAME
                )

                # Determine import mode
                if Config.GOOGLE_DRIVE_FOLDER_IDS:
                    self.use_folder_mode = True
                    self.folder_ids = [fid.strip() for fid in Config.GOOGLE_DRIVE_FOLDER_IDS.split(',')]
                    logger.info(f"VertexAI RAG configured in FOLDER mode with {len(self.folder_ids)} folders")
                    logger.info("VertexAI will auto-detect new files in these folders - no periodic sync needed!")
                elif Config.VERTEX_RAG_FULL_DRIVE:
                    self.use_folder_mode = False
                    logger.info("VertexAI RAG configured in FULL DRIVE mode")
                    logger.info("Periodic sync enabled to discover new files")
                else:
                    logger.warning("No folder IDs or full drive mode specified. Using file discovery mode.")
                    self.use_folder_mode = False

                logger.info("VertexAI RAG handler initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize VertexAI RAG handler: {str(e)}")
                self.vertex_rag_handler = None
        else:
            logger.warning("VertexAI RAG not configured. Set GCP_PROJECT_ID in environment variables.")

    def is_configured(self) -> bool:
        """Check if VertexAI RAG is properly configured"""
        return self.vertex_rag_handler is not None

    def sync_all_documents(self, force: bool = False) -> Dict[str, Any]:
        """
        Sync all Google Drive documents to VertexAI RAG

        Args:
            force: If True, resync all documents even if already synced

        Returns:
            Dict with sync statistics
        """
        if not self.is_configured():
            return {
                'status': 'error',
                'message': 'VertexAI RAG not configured',
                'documents_synced': 0
            }

        try:
            # FOLDER MODE: Import folders directly (VertexAI auto-syncs after)
            if self.use_folder_mode:
                logger.info(f"Using FOLDER mode - importing {len(self.folder_ids)} folders")

                # Check if folders already imported
                if self.synced_files and not force:
                    return {
                        'status': 'success',
                        'message': 'Folders already imported. VertexAI auto-syncs new files.',
                        'mode': 'folder',
                        'folders_count': len(self.folder_ids),
                        'sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None
                    }

                # Import all configured folders
                total_synced = 0
                for folder_id in self.folder_ids:
                    logger.info(f"Importing folder: {folder_id}")
                    success = self.vertex_rag_handler.import_drive_folder(
                        folder_id=folder_id,
                        chunk_size=1024,
                        chunk_overlap=200
                    )
                    if success:
                        self.synced_files.add(folder_id)  # Track folder as synced
                        total_synced += 1
                        logger.info(f"Successfully imported folder {folder_id}")
                    else:
                        logger.error(f"Failed to import folder {folder_id}")

                self.last_sync_time = datetime.now()

                return {
                    'status': 'success',
                    'message': f'Imported {total_synced} folders. VertexAI will auto-sync new files.',
                    'mode': 'folder',
                    'folders_synced': total_synced,
                    'total_folders': len(self.folder_ids),
                    'sync_time': self.last_sync_time.isoformat(),
                    'note': 'No periodic sync needed - VertexAI monitors folders automatically'
                }

            # FULL DRIVE MODE: Discover and import all files
            logger.info("Using FULL DRIVE mode - discovering all files")

            # Get all documents from Google Drive
            documents = self.drive_handler.get_all_documents()
            logger.info(f"Found {len(documents)} documents in Google Drive")

            if not documents:
                return {
                    'status': 'success',
                    'message': 'No documents found in Google Drive',
                    'mode': 'full_drive',
                    'documents_synced': 0,
                    'sync_time': datetime.now().isoformat()
                }

            # Determine which documents need to be synced
            if force:
                docs_to_sync = documents
                logger.info("Force sync enabled - syncing all documents")
            else:
                # Only sync new documents
                docs_to_sync = [doc for doc in documents if doc['id'] not in self.synced_files]
                logger.info(f"{len(docs_to_sync)} new documents to sync")

            if not docs_to_sync:
                return {
                    'status': 'success',
                    'message': 'All documents already synced',
                    'mode': 'full_drive',
                    'documents_synced': 0,
                    'total_documents': len(documents),
                    'sync_time': datetime.now().isoformat()
                }

            # Extract file IDs
            file_ids = [doc['id'] for doc in docs_to_sync]

            # Import files to VertexAI RAG in batches
            batch_size = 100  # Process 100 files at a time
            total_synced = 0

            for i in range(0, len(file_ids), batch_size):
                batch = file_ids[i:i + batch_size]
                logger.info(f"Syncing batch {i//batch_size + 1}: {len(batch)} files")

                success = self.vertex_rag_handler.import_drive_files(
                    drive_file_ids=batch,
                    chunk_size=1024,
                    chunk_overlap=200
                )

                if success:
                    # Mark files as synced
                    self.synced_files.update(batch)
                    total_synced += len(batch)
                    logger.info(f"Successfully synced batch {i//batch_size + 1}")
                else:
                    logger.error(f"Failed to sync batch {i//batch_size + 1}")

            self.last_sync_time = datetime.now()

            return {
                'status': 'success',
                'message': f'Successfully synced {total_synced} documents',
                'mode': 'full_drive',
                'documents_synced': total_synced,
                'total_documents': len(documents),
                'sync_time': self.last_sync_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Error syncing documents: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return {
                'status': 'error',
                'message': f'Error during sync: {str(e)}',
                'documents_synced': 0
            }

    def sync_folder(self, folder_id: str) -> Dict[str, Any]:
        """
        Sync a specific Google Drive folder to VertexAI RAG

        Args:
            folder_id: Google Drive folder ID

        Returns:
            Dict with sync statistics
        """
        if not self.is_configured():
            return {
                'status': 'error',
                'message': 'VertexAI RAG not configured'
            }

        try:
            logger.info(f"Syncing folder {folder_id} to VertexAI RAG")

            success = self.vertex_rag_handler.import_drive_folder(
                folder_id=folder_id,
                chunk_size=1024,
                chunk_overlap=200
            )

            if success:
                return {
                    'status': 'success',
                    'message': f'Successfully synced folder {folder_id}',
                    'sync_time': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'Failed to sync folder {folder_id}'
                }

        except Exception as e:
            logger.error(f"Error syncing folder: {str(e)}")
            return {
                'status': 'error',
                'message': f'Error syncing folder: {str(e)}'
            }

    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        if not self.is_configured():
            return {
                'configured': False,
                'message': 'VertexAI RAG not configured'
            }

        try:
            corpus_stats = self.vertex_rag_handler.get_corpus_stats()

            return {
                'configured': True,
                'last_sync_time': self.last_sync_time.isoformat() if self.last_sync_time else None,
                'synced_files_count': len(self.synced_files),
                'corpus_name': corpus_stats.get('display_name'),
                'corpus_file_count': corpus_stats.get('file_count', 0),
                'status': 'active'
            }

        except Exception as e:
            logger.error(f"Error getting sync status: {str(e)}")
            return {
                'configured': True,
                'status': 'error',
                'error': str(e)
            }

    def query(self, query_text: str, top_k: int = 5, similarity_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Query documents using VertexAI RAG

        Args:
            query_text: Search query
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score

        Returns:
            List of relevant document chunks
        """
        if not self.is_configured():
            logger.error("VertexAI RAG not configured")
            return []

        try:
            return self.vertex_rag_handler.query_corpus(
                query=query_text,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
        except Exception as e:
            logger.error(f"Error querying VertexAI RAG: {str(e)}")
            return []

    def generate_answer(self, query_text: str, model_name: str = "gemini-2.0-flash-001") -> Dict[str, Any]:
        """
        Generate answer using VertexAI RAG with Gemini

        Args:
            query_text: User's question
            model_name: Gemini model to use

        Returns:
            Dict with answer and sources
        """
        if not self.is_configured():
            return {
                'answer': 'VertexAI RAG not configured. Please set up GCP_PROJECT_ID.',
                'sources': [],
                'error': 'Not configured'
            }

        try:
            return self.vertex_rag_handler.generate_answer(
                query=query_text,
                model_name=model_name,
                top_k=5,
                similarity_threshold=0.5,
                temperature=0.2
            )
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                'answer': f'Error generating answer: {str(e)}',
                'sources': [],
                'error': str(e)
            }
