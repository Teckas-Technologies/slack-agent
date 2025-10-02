# InfoBot Deployment Guide

Complete guide for deploying and running the InfoBot Slack Agent.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Google Drive Setup](#google-drive-setup)
4. [Confluence Setup](#confluence-setup)
5. [Slack Bot Setup](#slack-bot-setup)
6. [Installation](#installation)
7. [Configuration](#configuration)
8. [Running the Application](#running-the-application)
9. [Testing](#testing)
10. [Monitoring & Troubleshooting](#monitoring--troubleshooting)

## Prerequisites

- Python 3.9 or higher
- Google Cloud Project with Drive API enabled
- Confluence account with API access
- Slack workspace with admin access
- OpenAI API key or Anthropic API key (for AI responses)

## Environment Setup

### 1. Clone and Setup Project

```bash
git clone <repository-url>
cd slack-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Google Drive Setup

### 1. Create Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Enable Google Drive API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

4. Create Service Account:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Enter name and description
   - Click "Create and Continue"
   - Skip role assignment (click "Continue")
   - Click "Done"

5. Create Service Account Key:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Select "JSON" format
   - Download the key file and save it securely
   - Note the service account email (e.g., `bot@project.iam.gserviceaccount.com`)

### 2. Share Google Drive Folders

1. Open Google Drive
2. Right-click the folder(s) you want to index
3. Click "Share"
4. Add the service account email (from step 5 above)
5. Give "Viewer" permission
6. Click "Send"

## Confluence Setup

### 1. Generate API Token

1. Go to [Atlassian Account Settings](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click "Create API token"
3. Give it a label (e.g., "InfoBot")
4. Copy the token and save it securely

### 2. Identify Confluence Spaces

1. Log in to your Confluence instance
2. Note down the space keys you want to index
   - Space key is visible in the URL: `https://your-company.atlassian.net/wiki/spaces/SPACEKEY`
3. Make a comma-separated list of space keys (e.g., `DEV,PROD,DOCS`)

## Slack Bot Setup

### 1. Create Slack App

1. Go to [Slack API](https://api.slack.com/apps)
2. Click "Create New App" > "From scratch"
3. Enter app name: "InfoBot"
4. Select your workspace
5. Click "Create App"

### 2. Configure Bot Permissions

Go to "OAuth & Permissions" and add these Bot Token Scopes:
- `app_mentions:read` - View messages that mention the app
- `chat:write` - Send messages
- `im:history` - View messages in DMs
- `im:read` - View basic info about DMs
- `im:write` - Start DMs
- `channels:history` - View messages in channels (optional)
- `groups:history` - View messages in private channels (optional)

### 3. Enable Events

1. Go to "Event Subscriptions"
2. Enable Events
3. Enter Request URL: `https://your-domain.com/slack/events`
   - For local testing, use ngrok: `https://xxxx.ngrok.io/slack/events`
4. Subscribe to bot events:
   - `app_mention` - Mentions
   - `message.im` - Direct messages

### 4. Install App to Workspace

1. Go to "Install App"
2. Click "Install to Workspace"
3. Authorize the app
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 5. Get Signing Secret

1. Go to "Basic Information"
2. Find "App Credentials" section
3. Copy the "Signing Secret"

## Installation

### 1. Create Environment File

Copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

### 2. Edit .env File

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token
SLACK_SIGNING_SECRET=your-actual-signing-secret

# AI Services (at least one required)
OPENAI_API_KEY=sk-your-openai-key
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Google Drive Configuration
# Option 1: Paste JSON content directly (recommended for deployment)
GOOGLE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"your-project-id","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n","client_email":"bot@project.iam.gserviceaccount.com",...}'

# Option 2: Or use file path
# GOOGLE_SERVICE_ACCOUNT_KEY=/absolute/path/to/service-account-key.json

# Confluence Configuration
CONFLUENCE_BASE_URL=https://your-company.atlassian.net
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-confluence-api-token
CONFLUENCE_SPACES=SPACE1,SPACE2,SPACE3

# Database Configuration
CHROMA_DB_PATH=./chroma_db

# Application Configuration
PORT=8000
DEBUG=False
```

## Configuration

### Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| SLACK_BOT_TOKEN | Yes | Bot user OAuth token from Slack |
| SLACK_SIGNING_SECRET | Yes | Signing secret from Slack |
| OPENAI_API_KEY | One of AI keys | OpenAI API key for embeddings and chat |
| ANTHROPIC_API_KEY | One of AI keys | Anthropic API key for Claude chat |
| GOOGLE_SERVICE_ACCOUNT_KEY | Yes* | Google service account JSON (as string) or file path |
| CONFLUENCE_BASE_URL | Yes* | Confluence instance URL |
| CONFLUENCE_USERNAME | Yes* | Confluence user email |
| CONFLUENCE_API_TOKEN | Yes* | Confluence API token |
| CONFLUENCE_SPACES | Optional | Comma-separated space keys to index |
| CHROMA_DB_PATH | Optional | Path for ChromaDB storage (default: ./chroma_db) |
| PORT | Optional | Server port (default: 8000) |
| DEBUG | Optional | Debug mode (default: False) |

*At least one document source (Google Drive or Confluence) must be configured.

## Running the Application

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run using start script
./start.sh

# OR run directly with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

### Production Deployment

#### Using Docker

```bash
# Build image
docker build -t infobot:latest .

# Run container
docker run -d \
  --name infobot \
  -p 8000:8000 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/chroma_db:/app/chroma_db \
  -v $(pwd)/service-account-key.json:/app/service-account-key.json \
  infobot:latest
```

#### Using Docker Compose

```bash
docker-compose up -d
```

#### Using systemd (Linux)

Create `/etc/systemd/system/infobot.service`:

```ini
[Unit]
Description=InfoBot Slack Agent
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/slack-agent
Environment="PATH=/path/to/slack-agent/venv/bin"
ExecStart=/path/to/slack-agent/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable infobot
sudo systemctl start infobot
```

## Testing

### 1. Check Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-...",
  "documents_indexed": 0,
  "ai_models": ["Claude (Anthropic)"],
  "version": "1.0.0"
}
```

### 2. Manual Document Refresh

```bash
curl -X POST http://localhost:8000/refresh
```

### 3. Test Search

```bash
curl http://localhost:8000/test-search
```

### 4. Test in Slack

1. Invite the bot to a channel: `/invite @InfoBot`
2. Mention the bot: `@InfoBot /status`
3. Ask a question: `@InfoBot What is our company policy?`
4. Send DM to the bot directly

### 5. Test Slash Commands (Optional)

Configure slash commands in Slack:
- `/refresh` - Manually trigger document refresh

## Monitoring & Troubleshooting

### Check Application Logs

```bash
# If running with systemd
sudo journalctl -u infobot -f

# If running with Docker
docker logs -f infobot

# If running directly
# Logs are printed to console
```

### Common Issues

#### 1. No documents being indexed

**Symptoms:** Query returns "No documents have been indexed yet"

**Solutions:**
- Check Google Drive permissions - service account email must have access
- Check Confluence credentials and space keys
- Check logs for authentication errors
- Manually trigger refresh: `@InfoBot /refresh`

#### 2. Slack events not being received

**Symptoms:** Bot doesn't respond to mentions

**Solutions:**
- Verify Request URL in Slack app settings
- Check if server is publicly accessible (use ngrok for local testing)
- Check Slack signing secret is correct
- Check bot has correct permissions

#### 3. AI responses failing

**Symptoms:** Fallback responses or errors

**Solutions:**
- Verify OpenAI or Anthropic API keys are valid
- Check API key has sufficient credits
- Check logs for API errors

#### 4. ChromaDB errors

**Symptoms:** Database schema errors

**Solutions:**
```bash
# Delete and recreate database
rm -rf chroma_db/
# Restart application - it will recreate the database
```

#### 5. Scheduled sync not running

**Symptoms:** Documents not updating automatically

**Solutions:**
- Check logs for scheduler initialization
- Verify APScheduler is installed: `pip install APScheduler==3.10.4`
- Check for sync errors in logs

### Monitoring Endpoints

- **Health Check:** `GET /health` - Application health status
- **Status:** `GET /status` - Detailed statistics
- **Document Summary:** `GET /docs-summary` - Indexed documents info
- **Test Search:** `GET /test-search` - Test search functionality

### Performance Tuning

#### Document Sync Frequency

Edit `main.py` line 51-57 to change sync interval:
```python
scheduler.add_job(
    agent.scheduled_document_sync,
    trigger=IntervalTrigger(minutes=2),  # Change this value
    ...
)
```

#### Search Results

Edit `app/query_engine.py` line 35-37:
```python
self.max_search_results = 5  # Number of results to retrieve
self.similarity_threshold = 0.8  # Similarity threshold
```

#### Chunk Size

Edit `app/document_processor.py` line 22-24:
```python
self.chunk_size = 1000  # Characters per chunk
self.chunk_overlap = 200  # Overlap between chunks
```

## Architecture Overview

```
┌─────────────────┐
│   Slack Users   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Slack API     │
│   (Events)      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│         FastAPI Application              │
│  ┌────────────────────────────────────┐ │
│  │    SlackDocumentAgent              │ │
│  │  - Event Handling                  │ │
│  │  - Query Processing                │ │
│  │  - Scheduled Sync (every 2 min)    │ │
│  └────────────────────────────────────┘ │
└───────┬──────────────────┬──────────────┘
        │                  │
        ▼                  ▼
┌─────────────┐    ┌─────────────┐
│ Google      │    │ Confluence  │
│ Drive API   │    │ API         │
└──────┬──────┘    └──────┬──────┘
       │                  │
       └────────┬─────────┘
                ▼
     ┌─────────────────────┐
     │ Document Processor  │
     │  - Text Extraction  │
     │  - Chunking         │
     │  - Embedding        │
     └──────────┬──────────┘
                ▼
        ┌───────────────┐
        │   ChromaDB    │
        │ (Vector Store)│
        └───────┬───────┘
                │
                ▼
        ┌───────────────┐
        │ Query Engine  │
        │  - RAG        │
        │  - AI (Claude/│
        │    GPT)       │
        └───────────────┘
```

## Features Implemented

✅ **Slack Bot Integration**
- App mentions handling
- Direct message support
- Thread responses with reference links
- Slash commands (/refresh, /status)

✅ **Document Sources**
- Google Drive (PDF, DOCX, Google Docs, CSV, Excel, etc.)
- Confluence (Pages, with HTML to text conversion)

✅ **Automatic Synchronization**
- Scheduled sync every 2 minutes
- Incremental updates (only processes modified documents)
- Tracks document modification times

✅ **Vector Search & RAG**
- ChromaDB for vector storage
- OpenAI embeddings (text-embedding-ada-002)
- Fallback to simple embeddings if no API key

✅ **AI Integration**
- Claude (Anthropic) - Primary
- GPT (OpenAI) - Fallback
- Accurate responses with context
- Reference link attribution

✅ **Production Ready**
- FastAPI with async support
- Health check endpoints
- Error handling and logging
- Docker support
- Single worker mode (ChromaDB compatibility)

## Support & Contributing

For issues or questions, please check the logs first and review this guide. The application provides detailed logging that can help diagnose most issues.

## License

[Add your license information here]