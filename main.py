# main.py
# Fix SQLite for Azure App Service BEFORE any other imports
import fix_sqlite  # noqa: F401

import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from config import Config
from app.document_processor import DocumentProcessor
from app.query_engine import QueryEngine
from app.google_drive_handler import GoogleDriveHandler
from app.confluence_handler import ConfluenceHandler
from datetime import datetime

# VertexAI RAG support
try:
    from app.drive_sync_service import DriveSyncService
    VERTEX_RAG_AVAILABLE = True
except ImportError:
    VERTEX_RAG_AVAILABLE = False
    logger.warning("VertexAI RAG not available - make sure google-cloud-aiplatform is installed")
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for the agent and scheduler
agent = None
scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global agent, scheduler
    # Startup
    logger.info("Starting Slack Document Agent...")

    # Validate configuration
    try:
        Config.validate_required()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise

    agent = SlackDocumentAgent()
    logger.info("Slack Document Agent initialized successfully")

    # Initialize and start scheduler for periodic document sync
    scheduler = AsyncIOScheduler()

    # Schedule document sync every 2 minutes
    scheduler.add_job(
        agent.scheduled_document_sync,
        trigger=IntervalTrigger(minutes=2),
        id='document_sync',
        name='Periodic document synchronization',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Document sync scheduler started (runs every 2 minutes)")

    yield

    # Shutdown
    logger.info("Shutting down Slack Document Agent...")
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


# Create FastAPI app with lifespan management
app = FastAPI(
    title="Slack Document Agent",
    description="AI-powered Slack bot for document search and Q&A",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


class SlackDocumentAgent:
    def __init__(self):
        # Initialize Slack client with SSL context for certificate issues
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        self.slack_client = WebClient(
            token=Config.SLACK_BOT_TOKEN,
            ssl=ssl_context
        )
        self.signature_verifier = SignatureVerifier(Config.SLACK_SIGNING_SECRET)

        # Initialize document handlers
        self.gdrive_handler = GoogleDriveHandler()
        self.confluence_handler = ConfluenceHandler() if not Config.USE_VERTEX_AI_RAG else None

        # Initialize VertexAI RAG or ChromaDB depending on configuration
        self.use_vertex_rag = Config.USE_VERTEX_AI_RAG and VERTEX_RAG_AVAILABLE
        self.vertex_sync_service = None

        if self.use_vertex_rag:
            logger.info("Initializing VertexAI RAG mode (Google Drive only)")
            try:
                self.vertex_sync_service = DriveSyncService()
                if not self.vertex_sync_service.is_configured():
                    logger.error("VertexAI RAG not properly configured, falling back to ChromaDB")
                    self.use_vertex_rag = False
                    self.doc_processor = DocumentProcessor()
                else:
                    logger.info("VertexAI RAG initialized successfully")
                    self.doc_processor = None  # Not needed with VertexAI RAG
            except Exception as e:
                logger.error(f"Failed to initialize VertexAI RAG: {str(e)}, falling back to ChromaDB")
                self.use_vertex_rag = False
                self.doc_processor = DocumentProcessor()
        else:
            logger.info("Using ChromaDB mode (Google Drive + Confluence)")
            self.doc_processor = DocumentProcessor()

        # Initialize query engine (handles both modes internally)
        self.query_engine = QueryEngine()

        # Track processing status and last sync
        self.processing_status = {}
        self.last_sync_time = None
        self.sync_in_progress = False

        # Track processed documents to avoid re-processing unchanged docs
        self.processed_documents = {}  # {doc_id: modified_time}

    def verify_request(self, request_body: bytes, headers: Dict[str, str]) -> bool:
        """Verify Slack request signature"""
        return self.signature_verifier.is_valid_request(request_body, headers)

    async def handle_message(self, event: Dict[str, Any]) -> None:
        """Handle incoming Slack messages"""
        try:
            user_id = event['user']
            channel_id = event['channel']
            message_text = event['text'].strip()
            thread_ts = event.get('ts')

            # Remove bot mention from message
            message_text = self._clean_message(message_text)

            # Check for special commands
            if message_text.lower().startswith('/refresh'):
                await self._handle_refresh_command(channel_id, thread_ts, user_id)
                return

            if message_text.lower().startswith('/status'):
                await self._handle_status_command(channel_id, thread_ts)
                return

            # Process regular query
            await self._handle_query(message_text, channel_id, thread_ts, user_id)

        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await self._send_error_message(event['channel'], event.get('ts'))

    def _clean_message(self, message: str) -> str:
        """Remove bot mention and clean message"""
        # Remove <@BOTID> mentions (including InfoBot mentions)
        import re
        message = re.sub(r'<@\w+>', '', message).strip()
        # Also remove common bot name variations
        message = re.sub(r'@?InfoBot\s*', '', message, flags=re.IGNORECASE).strip()
        return message

    async def _handle_query(self, query: str, channel_id: str, thread_ts: str, user_id: str) -> None:
        """Handle user query"""
        try:
            # Send thinking message
            thinking_msg = self.slack_client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text="🤔 Searching through your documents..."
            )

            # Process query asynchronously
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, self.query_engine.process_query, query)

            # Update with response
            self.slack_client.chat_update(
                channel=channel_id,
                ts=thinking_msg['ts'],
                text=response
            )

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            self.slack_client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text="❌ Sorry, I encountered an error processing your query. Please try again."
            )

    async def _handle_refresh_command(self, channel_id: str, thread_ts: str, user_id: str) -> None:
        """Handle document refresh command"""
        self.slack_client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text="🔄 Starting document refresh... This may take a few minutes."
        )

        # Start background refresh
        asyncio.create_task(self._refresh_documents_background(channel_id, thread_ts))

    async def _handle_status_command(self, channel_id: str, thread_ts: str) -> None:
        """Handle status command"""
        try:
            loop = asyncio.get_event_loop()
            stats = await loop.run_in_executor(None, self.query_engine.get_stats)

            status_text = f"""📊 **Document Agent Status**

**Documents Indexed:** {stats.get('total_documents', 0)}
**Total Chunks:** {stats.get('total_chunks', 0)}
**Last Updated:** {stats.get('last_updated', 'Never')}
**AI Models:** {', '.join(stats.get('ai_models', ['None']))}

**Available Sources:**
• Google Drive: ✅
• Confluence: ✅

**Supported File Types:**
• PDFs, Word Docs, Google Docs
• Spreadsheets (CSV, Excel, Google Sheets)
• Text files, Markdown, HTML
• PowerPoint presentations
            """

            self.slack_client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=status_text
            )
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            await self._send_error_message(channel_id, thread_ts)

    async def _refresh_documents_background(self, channel_id: str, thread_ts: str) -> None:
        """Background document refresh"""
        try:
            loop = asyncio.get_event_loop()

            # Use VertexAI RAG sync if enabled
            if self.use_vertex_rag and self.vertex_sync_service:
                logger.info("Running VertexAI RAG sync (Google Drive only)")

                # Sync all documents to VertexAI RAG
                result = await loop.run_in_executor(
                    None,
                    self.vertex_sync_service.sync_all_documents,
                    True  # force=True for manual refresh
                )

                if result['status'] == 'success':
                    message = f"✅ Refresh complete! Synced {result['documents_synced']} documents to VertexAI RAG."
                else:
                    message = f"❌ Sync failed: {result.get('message', 'Unknown error')}"

                if channel_id:
                    self.slack_client.chat_postMessage(
                        channel=channel_id,
                        thread_ts=thread_ts,
                        text=message
                    )
                return

            # Legacy ChromaDB mode
            # Refresh Google Drive documents
            gdrive_docs = await loop.run_in_executor(None, self.gdrive_handler.get_all_documents)

            # Refresh Confluence documents
            confluence_docs = await loop.run_in_executor(None, self.confluence_handler.get_all_documents)

            # Process all documents
            all_docs = gdrive_docs + confluence_docs
            processed = 0

            for doc in all_docs:
                try:
                    # Use the same document processor instance as the query engine
                    result = await loop.run_in_executor(None, self.doc_processor.process_document, doc)
                    if result:
                        processed += 1
                        logger.info(f"Successfully processed document: {doc.get('name', 'Unknown')}")
                    else:
                        logger.error(f"Failed to process document: {doc.get('name', 'Unknown')}")

                    # Send progress update every 10 documents
                    if channel_id and processed % 10 == 0:
                        self.slack_client.chat_postMessage(
                            channel=channel_id,
                            thread_ts=thread_ts,
                            text=f"📈 Processed {processed}/{len(all_docs)} documents..."
                        )

                except Exception as e:
                    logger.error(f"Error processing document {doc.get('name', 'Unknown')}: {str(e)}")
                    continue

            # Send completion message
            if channel_id:
                self.slack_client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text=f"✅ Refresh complete! Processed {processed} documents."
                )

        except Exception as e:
            logger.error(f"Error in background refresh: {str(e)}")
            if channel_id:
                self.slack_client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text="❌ Document refresh failed. Please check the logs."
                )

    async def _send_error_message(self, channel_id: str, thread_ts: str = None) -> None:
        """Send generic error message"""
        self.slack_client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text="❌ Something went wrong. Please try again or contact support."
        )

    async def scheduled_document_sync(self) -> None:
        """Scheduled task to sync documents every 2 minutes"""
        try:
            # Prevent concurrent syncs
            if self.sync_in_progress:
                logger.info("Sync already in progress, skipping scheduled sync")
                return

            self.sync_in_progress = True
            logger.info("Starting scheduled document synchronization...")

            loop = asyncio.get_event_loop()

            # Use VertexAI RAG sync if enabled
            if self.use_vertex_rag and self.vertex_sync_service:
                logger.info("Running scheduled VertexAI RAG sync (Google Drive only)")

                result = await loop.run_in_executor(
                    None,
                    self.vertex_sync_service.sync_all_documents,
                    False  # force=False for scheduled sync (only new docs)
                )

                if result['status'] == 'success':
                    logger.info(f"VertexAI RAG sync completed: {result['documents_synced']} documents synced")
                else:
                    logger.error(f"VertexAI RAG sync failed: {result.get('message')}")

                self.last_sync_time = datetime.now()
                return

            # Legacy ChromaDB mode
            # Fetch documents from all sources
            gdrive_docs = await loop.run_in_executor(None, self.gdrive_handler.get_all_documents)
            confluence_docs = await loop.run_in_executor(None, self.confluence_handler.get_all_documents)

            all_docs = gdrive_docs + confluence_docs
            logger.info(f"Found {len(all_docs)} total documents ({len(gdrive_docs)} from Drive, {len(confluence_docs)} from Confluence)")

            # Process only new or modified documents
            new_or_modified = 0
            skipped = 0

            for doc in all_docs:
                try:
                    doc_id = doc['id']
                    modified_time = doc.get('modified_time', '')

                    # Check if document has been modified since last processing
                    if doc_id in self.processed_documents:
                        if self.processed_documents[doc_id] == modified_time:
                            skipped += 1
                            continue

                    # Process the document
                    result = await loop.run_in_executor(None, self.doc_processor.process_document, doc)

                    if result:
                        # Update tracking
                        self.processed_documents[doc_id] = modified_time
                        new_or_modified += 1
                        logger.info(f"Processed document: {doc.get('name', 'Unknown')}")
                    else:
                        logger.warning(f"Failed to process document: {doc.get('name', 'Unknown')}")

                except Exception as e:
                    logger.error(f"Error processing document {doc.get('name', 'Unknown')}: {str(e)}")
                    continue

            self.last_sync_time = datetime.now()
            logger.info(f"Scheduled sync completed: {new_or_modified} processed, {skipped} skipped (unchanged)")

        except Exception as e:
            logger.error(f"Error in scheduled document sync: {str(e)}")
        finally:
            self.sync_in_progress = False


@app.post("/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    """Handle Slack events"""
    try:
        # Get request body
        body = await request.body()

        # Verify request signature
        if not agent.verify_request(body, dict(request.headers)):
            raise HTTPException(status_code=403, detail="Invalid signature")

        data = json.loads(body.decode('utf-8'))

        # Handle URL verification (required for Slack setup)
        if data.get("type") == "url_verification":
            return {"challenge": data["challenge"]}

        # Handle app mention events
        event = data.get("event", {})
        if event.get("type") == "app_mention" and event.get("user") != data.get("authed_users", [None])[0]:
            # Ignore bot's own messages
            if not event.get("bot_id"):
                background_tasks.add_task(agent.handle_message, event)

        # Handle direct message events
        elif event.get("type") == "message" and event.get("channel_type") == "im":
            # Ignore bot's own messages and messages with subtypes (like file uploads)
            if not event.get("bot_id") and not event.get("subtype"):
                background_tasks.add_task(agent.handle_message, event)

        return {"status": "ok"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in slack_events: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if agent is initialized
        if agent is None:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "Agent not initialized",
                    "timestamp": datetime.now().isoformat()
                }
            )

        # Get basic stats
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(None, agent.query_engine.get_stats)

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "documents_indexed": stats.get('total_documents', 0),
            "ai_models": stats.get('ai_models', []),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.post("/slack/slash")
async def slack_slash_commands(request: Request, background_tasks: BackgroundTasks):
    """Handle Slack slash commands"""
    try:
        # Get request body
        body = await request.body()

        # Verify request signature
        if not agent.verify_request(body, dict(request.headers)):
            raise HTTPException(status_code=403, detail="Invalid signature")

        # Parse form data
        from urllib.parse import parse_qs
        form_data = parse_qs(body.decode('utf-8'))

        command = form_data.get('command', [None])[0]
        user_id = form_data.get('user_id', [None])[0]
        channel_id = form_data.get('channel_id', [None])[0]
        text = form_data.get('text', [''])[0]

        if command == '/refresh':
            # Acknowledge immediately
            response_text = "🔄 Starting document refresh... This may take a few minutes."

            # Start background refresh
            background_tasks.add_task(agent._refresh_documents_background, channel_id, None)

            return {"text": response_text}
        else:
            return {"text": f"Unknown command: {command}"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in slash command: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/refresh")
async def manual_refresh(background_tasks: BackgroundTasks):
    """Manual document refresh endpoint"""
    try:
        if agent is None:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        # Start background refresh
        background_tasks.add_task(agent._refresh_documents_background, "", "")

        return {"status": "refresh started", "timestamp": datetime.now().isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Manual refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Get application status and statistics"""
    try:
        if agent is None:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(None, agent.query_engine.get_stats)

        return {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "services": {
                "slack": "connected",
                "google_drive": "configured" if agent.gdrive_handler else "not configured",
                "confluence": "configured" if agent.confluence_handler else "not configured",
                "ai_models": stats.get('ai_models', [])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/docs-summary")
async def get_docs_summary():
    """Get summary of indexed documents"""
    try:
        if agent is None:
            raise HTTPException(status_code=503, detail="Agent not initialized")

        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(None, agent.doc_processor.get_document_stats)

        return {
            "summary": stats,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Docs summary error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test-search")
async def test_search():
    """Test document search functionality"""
    try:
        if agent is None:
            raise HTTPException(status_code=503, detail="Agent not initialized")
        
        loop = asyncio.get_event_loop()
        
        # Get basic stats
        stats = await loop.run_in_executor(None, agent.doc_processor.get_document_stats)
        
        # Try a simple search
        search_results = await loop.run_in_executor(
            None, 
            agent.doc_processor.search_documents, 
            "test", 
            5
        )
        
        return {
            "stats": stats,
            "search_results": len(search_results),
            "results": [
                {
                    "content": result['content'][:100] + "..." if len(result['content']) > 100 else result['content'],
                    "metadata": result['metadata'],
                    "distance": result.get('distance', 'unknown')
                }
                for result in search_results[:3]
            ],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Test search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"Path {request.url.path} not found",
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting FastAPI server on {Config.HOST}:{Config.PORT}")

    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level="info",
        access_log=True
    )
