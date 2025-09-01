# app.py
import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio
from contextlib import asynccontextmanager
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from app.document_processor import DocumentProcessor
from app.query_engine import QueryEngine
from app.google_drive_handler import GoogleDriveHandler
from app.confluence_handler import ConfluenceHandler
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for the agent
agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global agent
    # Startup
    logger.info("Starting Slack Document Agent...")
    agent = SlackDocumentAgent()
    logger.info("Slack Document Agent initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Slack Document Agent...")

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
        self.slack_client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
        self.signature_verifier = SignatureVerifier(os.environ["SLACK_SIGNING_SECRET"])

        # Initialize document handlers
        self.gdrive_handler = GoogleDriveHandler()
        self.confluence_handler = ConfluenceHandler()

        # Initialize document processor and query engine
        self.doc_processor = DocumentProcessor()
        self.query_engine = QueryEngine()

        # Track processing status
        self.processing_status = {}

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
        # Remove <@BOTID> mentions
        import re
        message = re.sub(r'<@\w+>', '', message).strip()
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
            
            # Refresh Google Drive documents
            gdrive_docs = await loop.run_in_executor(None, self.gdrive_handler.get_all_documents)

            # Refresh Confluence documents
            confluence_docs = await loop.run_in_executor(None, self.confluence_handler.get_all_documents)

            # Process all documents
            all_docs = gdrive_docs + confluence_docs
            processed = 0

            for doc in all_docs:
                try:
                    await loop.run_in_executor(None, self.doc_processor.process_document, doc)
                    processed += 1

                    # Send progress update every 10 documents
                    if processed % 10 == 0:
                        self.slack_client.chat_postMessage(
                            channel=channel_id,
                            thread_ts=thread_ts,
                            text=f"📈 Processed {processed}/{len(all_docs)} documents..."
                        )

                except Exception as e:
                    logger.error(f"Error processing document {doc.get('name', 'Unknown')}: {str(e)}")
                    continue

            # Send completion message
            self.slack_client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=f"✅ Refresh complete! Processed {processed} documents."
            )

        except Exception as e:
            logger.error(f"Error in background refresh: {str(e)}")
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
            background_tasks.add_task(agent.handle_message, event)

        # Handle direct message events
        elif event.get("type") == "message" and event.get("channel_type") == "im":
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
    
    # Configuration
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting FastAPI server on {host}:{port}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True
    )