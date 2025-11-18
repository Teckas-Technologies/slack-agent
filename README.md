# InfoBot - Slack Document Q&A Agent

**Powered by Google Gemini 2.0 Flash** 🚀

An intelligent Slack bot that answers questions about your Google Drive documents and Confluence pages using advanced RAG (Retrieval-Augmented Generation) with Google's Gemini AI.

## Features

✨ **Intelligent Document Search**
- Search through Google Drive documents (PDF, Word, Sheets, etc.)
- Search through Confluence pages and spaces
- Hybrid RAG approach using ChromaDB + Gemini 2.0 Flash

🤖 **General Knowledge Assistant**
- Answers general questions (math, facts, history, etc.)
- Powered by Gemini 2.0 Flash with huge 1M token context window
- No need for multiple AI services - one model for everything

💬 **Flexible Communication**
- Respond to @mentions in channels
- Direct message (DM) support - chat with InfoBot privately
- Thread-aware responses

📊 **Auto-Sync**
- Automatically syncs documents every 2 minutes
- Manual refresh via `/refresh` command
- Tracks document modifications to avoid reprocessing

🔗 **Source Attribution**
- Always includes source URLs in responses
- Direct links to Google Drive files and Confluence pages
- Clear, clickable references

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Google Drive   │────▶│   Document       │────▶│   ChromaDB      │
│  + Confluence   │     │   Processor      │     │  Vector Store   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Slack User     │────▶│  Query Engine    │────▶│  Gemini 2.0     │
│   Question      │     │                  │     │     Flash       │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │  Answer with     │
                        │  Source URLs     │
                        └──────────────────┘
```

## Setup Guide

### 1. Prerequisites

- Python 3.9 or higher
- Google Cloud Project (for service account)
- Slack Workspace (admin access to create apps)
- Gemini API Key

### 2. Get Gemini API Key

1. Visit **Google AI Studio**: https://aistudio.google.com/app/apikey
2. Click **"Get API Key"** or **"Create API Key"**
3. Select an existing Google Cloud project or create a new one
4. Copy the generated API key
5. Save it - you'll need it for the `.env` file

**Cost**: Gemini 2.0 Flash is very affordable:
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens
- Free tier: 1,500 requests per day

### 3. Google Drive Setup

#### Create Service Account

1. Go to **Google Cloud Console**: https://console.cloud.google.com/
2. Select your project (or create a new one)
3. Navigate to **IAM & Admin** → **Service Accounts**
4. Click **"Create Service Account"**
   - Name: `slack-agent-service-account`
   - Description: Service account for InfoBot Slack agent
5. Click **"Create and Continue"**
6. Skip granting roles (not needed)
7. Click **"Done"**

#### Generate Service Account Key

1. Click on the newly created service account
2. Go to the **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Select **JSON** format
5. Click **"Create"** - the JSON file will download
6. Save this file securely

#### Option A: Domain-Wide Delegation (Recommended for Organizations)

If you're using Google Workspace, you can grant the service account access to all users' drives:

1. In the service account details, note the **"Unique ID"** (long number)
2. Go to **Google Admin Console**: https://admin.google.com
3. Navigate to **Security** → **Access and data control** → **API Controls**
4. Click **"Manage Domain Wide Delegation"**
5. Click **"Add new"**
6. Enter the service account's **Client ID** (from JSON key file)
7. Add OAuth Scopes:
   ```
   https://www.googleapis.com/auth/drive.readonly
   https://www.googleapis.com/auth/drive.metadata.readonly
   ```
8. Click **"Authorize"**

In your `.env` file, set:
```bash
GOOGLE_DRIVE_DELEGATED_USER=your-admin-email@company.com
```

#### Option B: Manual Folder Sharing (For Personal Use)

1. Open Google Drive
2. Right-click the folders you want InfoBot to access
3. Click **"Share"**
4. Add the service account email (from the JSON key, looks like: `slack-agent-service-account@your-project.iam.gserviceaccount.com`)
5. Set permission to **"Viewer"**
6. Click **"Send"**

In your `.env` file, leave this empty:
```bash
GOOGLE_DRIVE_DELEGATED_USER=
```

### 4. Confluence Setup (Optional)

If you want to search Confluence pages:

1. Go to **Confluence Settings** → **Personal Settings** → **Password**
2. Click **"Create and manage API tokens"**
3. Click **"Create API token"**
4. Give it a name (e.g., "InfoBot")
5. Copy the generated token

### 5. Slack App Setup

#### Create Slack App

1. Go to **Slack API**: https://api.slack.com/apps
2. Click **"Create New App"**
3. Select **"From scratch"**
4. App Name: `InfoBot`
5. Select your workspace
6. Click **"Create App"**

#### Configure OAuth Scopes

1. Go to **OAuth & Permissions** (left sidebar)
2. Scroll to **"Bot Token Scopes"**
3. Add these scopes:
   - `app_mentions:read` - See messages that @mention your bot
   - `chat:write` - Send messages
   - `im:history` - View direct messages
   - `im:read` - View basic DM info
   - `im:write` - Send direct messages
   - `channels:history` - View messages in public channels (if needed)
   - `groups:history` - View messages in private channels (if needed)

#### Enable Events

1. Go to **Event Subscriptions** (left sidebar)
2. Toggle **"Enable Events"** to **ON**
3. Set **"Request URL"** to:
   ```
   https://your-domain.com/slack/events
   ```
   (Use ngrok for local testing: `https://abc123.ngrok.io/slack/events`)

4. Under **"Subscribe to bot events"**, add:
   - `app_mention` - Listen for @mentions
   - `message.im` - Listen for direct messages

5. Click **"Save Changes"**

#### Enable App Home

1. Go to **App Home** (left sidebar)
2. Under **"Show Tabs"**, find **"Messages Tab"**
3. Toggle **"Allow users to send Slash commands and messages from the messages tab"** to **ON**

#### Install App to Workspace

1. Go to **OAuth & Permissions**
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)

#### Get Signing Secret

1. Go to **Basic Information** (left sidebar)
2. Scroll to **"App Credentials"**
3. Copy the **"Signing Secret"**

### 6. Application Setup

#### Clone and Install

```bash
# Clone the repository
git clone <your-repo-url>
cd slack-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Configure Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your credentials:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-actual-token-here
SLACK_SIGNING_SECRET=your-actual-signing-secret-here
SLACK_VERIFY_SIGNATURE=true

# Gemini AI
GEMINI_API_KEY=your-gemini-api-key-here

# Google Drive
GOOGLE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'  # Paste entire JSON
GOOGLE_DRIVE_DELEGATED_USER=admin@yourcompany.com  # Or leave empty for manual sharing

# Confluence (Optional)
CONFLUENCE_BASE_URL=https://yourcompany.atlassian.net
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-confluence-api-token
CONFLUENCE_SPACES=  # Leave empty for all spaces

# Application Settings
CHROMA_DB_PATH=./chroma_db
PORT=8000
DEBUG=False
HOST=0.0.0.0
```

#### Run the Application

```bash
# Start the server
python main.py
```

You should see:
```
INFO:main:Starting Slack Document Agent...
INFO:main:Configuration validated successfully
INFO:app.gemini_rag_handler:✅ Gemini 2.0 Flash initialized successfully
INFO:app.query_engine:✅ ChromaDB document processor initialized
INFO:main:✅ Gemini AI + ChromaDB initialized successfully
INFO:main:Document sync scheduler started (runs every 2 minutes)
```

### 7. Testing

#### Test Direct Messages

1. In Slack, click **"Apps"** in the left sidebar
2. Find **"InfoBot"**
3. Send a message: `Hello!`
4. InfoBot should respond!

#### Test in Channels

1. Invite InfoBot to a channel: `/invite @InfoBot`
2. Mention it: `@InfoBot what is 2+2?`
3. InfoBot should respond!

#### Test Document Search

1. Make sure documents are synced (wait 2 minutes or use `/refresh`)
2. Ask: `@InfoBot tell me about [topic in your documents]`
3. InfoBot should respond with an answer and source URLs!

## Usage

### Commands

- **`/refresh`** - Manually refresh document index
- **`/status`** - Check bot status and document count

### Example Queries

**General Knowledge:**
```
What is 2+2?
When is Independence Day?
How many days in a year?
Tell me about World War 2
```

**Document Search:**
```
Tell me about the Q4 sales report
What are the requirements for project X?
Find information about user authentication
Show me the vacation policy
```

**System Info:**
```
How many documents do you have?
What can you do?
Help me
```

## Troubleshooting

### Bot Not Responding to DMs

**Issue**: "Sending messages to this app has been turned off"

**Solution**:
1. Go to Slack App settings → **App Home**
2. Enable **"Messages Tab"**
3. Toggle **"Allow users to send Slash commands and messages from the messages tab"** to ON

### No Documents Found

**Issue**: Bot says "I don't have enough information"

**Solution**:
1. Check if documents are synced: Send `/status`
2. Manually refresh: Send `/refresh`
3. Check logs for errors in document fetching
4. Verify Google Drive/Confluence credentials

### Gemini API Errors

**Issue**: "Error generating answer"

**Solution**:
1. Verify Gemini API key is correct
2. Check API quota: https://aistudio.google.com/app/apikey
3. Ensure billing is enabled (free tier has limits)

### Google Drive 403 Errors

**Issue**: "Permission denied" when accessing Drive

**Solution**:
- **Domain-wide delegation**: Verify delegation is set up correctly in Admin Console
- **Manual sharing**: Make sure folders are shared with the service account email

## Architecture Details

### Components

1. **Google Drive Handler** (`google_drive_handler.py`)
   - Fetches documents from Google Drive
   - Supports: PDF, Word, Sheets, Docs, etc.

2. **Confluence Handler** (`confluence_handler.py`)
   - Fetches pages from Confluence
   - Supports all space types

3. **Document Processor** (`document_processor.py`)
   - Processes documents into chunks
   - Stores embeddings in ChromaDB
   - Uses OpenAI embeddings for similarity search

4. **Gemini RAG Handler** (`gemini_rag_handler.py`)
   - Handles queries with Gemini 2.0 Flash
   - Generates answers with context
   - Formats responses with source URLs

5. **Query Engine** (`query_engine.py`)
   - Orchestrates retrieval + generation
   - Handles special queries (greetings, system info)
   - Returns formatted responses

### RAG Flow

1. **User asks a question** in Slack
2. **Query Engine** searches ChromaDB for relevant documents
3. **Top 8-10 documents** are retrieved based on similarity
4. **Gemini 2.0 Flash** receives:
   - User's question
   - Retrieved document context
5. **Gemini generates** an answer based on context
6. **Response is formatted** with source URLs
7. **User receives** answer with clickable references

### Why Gemini 2.0 Flash?

- **1M token context window** - can handle many documents at once
- **Fast and affordable** - $0.075 per 1M input tokens
- **Excellent comprehension** - understands complex queries
- **Single model** - handles both documents and general queries
- **Built-in safety** - configurable content filtering

## Development

### Project Structure

```
slack-agent/
├── app/
│   ├── confluence_handler.py     # Confluence API integration
│   ├── document_processor.py     # Document chunking + ChromaDB
│   ├── gemini_rag_handler.py     # Gemini AI integration
│   ├── google_drive_handler.py   # Google Drive API integration
│   ├── query_engine.py           # Query orchestration
│   └── vector_store.py           # ChromaDB wrapper
├── main.py                       # FastAPI server + Slack events
├── config.py                     # Configuration management
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment template
└── README.md                     # This file
```

### Running in Development

```bash
# With auto-reload
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --port 8000
```

### Testing with ngrok

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8000

# Update Slack Event URL with ngrok URL:
# https://abc123.ngrok.io/slack/events
```

## Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

```bash
# Build and run
docker build -t infobot .
docker run -p 8000:8000 --env-file .env infobot
```

### Production Checklist

- [ ] Set `SLACK_VERIFY_SIGNATURE=true` in `.env`
- [ ] Use HTTPS (required for Slack events)
- [ ] Set up proper logging and monitoring
- [ ] Configure firewall to allow only Slack IPs
- [ ] Enable Gemini API billing and set quotas
- [ ] Regularly backup ChromaDB data
- [ ] Set up health checks at `/health`

## Cost Estimation

### Gemini AI
- **Free Tier**: 1,500 requests/day
- **Paid**: ~$0.08 per 1M tokens (input)
- **Typical query**: 10,000 tokens = $0.0008 (less than a cent!)

### For 100 queries/day with 2000 documents:
- **Monthly cost**: ~$2-5 (extremely affordable)

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
- GitHub Issues: [your-repo-url]/issues
- Email: support@yourcompany.com

## Credits

Built with:
- **Google Gemini 2.0 Flash** - AI model
- **ChromaDB** - Vector database
- **Slack SDK** - Slack integration
- **FastAPI** - Web framework
- **Google Drive API** - Document access
- **Confluence API** - Knowledge base access

---

**Enjoy using InfoBot!** 🎉

If you find this useful, please ⭐ star the repository!
