# 🤖 InfoBot - Intelligent Slack Document Assistant

An AI-powered Slack bot that searches and answers questions from your Google Drive documents and Confluence pages using advanced AI models (Claude/GPT).

## ✨ Features

- 🔍 **Intelligent Document Search**: Semantic search across Google Drive and Confluence
- 🤖 **AI-Powered Responses**: Accurate answers using Claude (Anthropic) or GPT (OpenAI)
- 💬 **General Q&A**: Handles both document-specific AND general questions
- 📄 **Multi-Format Support**: PDFs, Word docs, Google Docs, spreadsheets, presentations, Confluence pages
- 🔄 **Auto-Sync**: Scheduled document refresh every 2 minutes
- 📊 **Source Attribution**: See which documents answers came from
- ⚡ **High Performance**: Built with FastAPI for superior performance
- 🎯 **Smart Query Routing**: Automatically uses documents when relevant, general AI when not

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Slack workspace with admin access
- Google Cloud account (for Google Drive)
- Confluence account (optional)
- OpenAI or Anthropic API key

### 1. Clone Repository

```bash
git clone <repository-url>
cd slack-agent
```

### 2. Install Dependencies

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required variables:
```bash
# Slack (Required)
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret

# AI Service (At least one required)
ANTHROPIC_API_KEY=sk-ant-your-key
OPENAI_API_KEY=sk-your-openai-key

# Google Drive (Required for Google Docs)
GOOGLE_SERVICE_ACCOUNT_KEY={"type":"service_account",...full JSON...}

# Confluence (Optional)
CONFLUENCE_BASE_URL=https://your-company.atlassian.net
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-api-token
CONFLUENCE_SPACES=SPACE1,SPACE2

# Database
CHROMA_DB_PATH=./chroma_db
PORT=8000
```

### 4. Run the Bot

```bash
# Local HTTP
./start.sh

# Or with HTTPS (for VM deployment)
./start_https.sh
```

## 📋 Setup Guides

### Slack App Configuration

#### Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Enter app name: **"InfoBot"**
4. Select your workspace

#### Step 2: Configure Bot Token Scopes

Go to **"OAuth & Permissions"** and add these **Bot Token Scopes**:

```
app_mentions:read     - Read messages that mention @InfoBot
chat:write           - Send messages as InfoBot
im:history           - View messages in DMs
im:read              - View basic DM info
channels:history     - Read messages in channels (if needed)
users:read           - View people in workspace
```

#### Step 3: Enable Event Subscriptions

1. Go to **"Event Subscriptions"**
2. Toggle **"Enable Events"** to **ON**
3. **Request URL**: `https://your-domain.com/slack/events` or `https://your-vm-ip:8443/slack/events`
4. Subscribe to **bot events**:
   - `app_mention` - When someone mentions @InfoBot
   - `message.im` - Direct messages to InfoBot

#### Step 4: Install App to Workspace

1. Go to **"Install App"**
2. Click **"Install to Workspace"**
3. Authorize the app
4. Copy the **"Bot User OAuth Token"** (starts with `xoxb-`)

#### Step 5: Get Signing Secret

1. Go to **"Basic Information"**
2. Find **"Signing Secret"** section
3. Click **"Show"** and copy the secret

Add both to your `.env`:
```bash
SLACK_BOT_TOKEN=xoxb-xxxxx
SLACK_SIGNING_SECRET=xxxxx
```

### Google Drive Setup

#### Option 1: Service Account (Recommended)

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com/
   - Create a new project or select existing

2. **Enable Google Drive API**
   - Navigate to **"APIs & Services"** → **"Enable APIs and Services"**
   - Search for **"Google Drive API"**
   - Click **"Enable"**

3. **Create Service Account**
   - Go to **"IAM & Admin"** → **"Service Accounts"**
   - Click **"Create Service Account"**
   - Name: `infobot-drive-reader`
   - Role: None needed (will use sharing)
   - Click **"Done"**

4. **Generate JSON Key**
   - Click on the service account
   - Go to **"Keys"** tab
   - Click **"Add Key"** → **"Create new key"**
   - Choose **"JSON"**
   - Download the file

5. **Share Drive Folders**
   - Open Google Drive
   - Right-click folders you want to index
   - Click **"Share"**
   - Add the service account email (from JSON: `client_email`)
   - Set permission to **"Viewer"**

6. **Add to Environment**

   **Method A: Paste JSON directly (Recommended for deployment)**
   ```bash
   GOOGLE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"...","private_key":"..."}'
   ```

   **Method B: File path (For local development)**
   ```bash
   GOOGLE_SERVICE_ACCOUNT_KEY=/path/to/service-account-key.json
   ```

### Confluence Setup (Optional)

1. **Generate API Token**
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Click **"Create API token"**
   - Name it **"InfoBot"**
   - Copy the token

2. **Get Confluence URL**
   - Your Confluence base URL (e.g., `https://company.atlassian.net`)
   - Note: DO NOT include `/wiki` at the end

3. **Find Space Keys**
   - Go to your Confluence space
   - URL will show space key: `.../wiki/spaces/DEV/...` (DEV is the key)
   - List all spaces you want to index

4. **Add to Environment**
   ```bash
   CONFLUENCE_BASE_URL=https://your-company.atlassian.net
   CONFLUENCE_USERNAME=your-email@company.com
   CONFLUENCE_API_TOKEN=your-api-token
   CONFLUENCE_SPACES=DEV,PROD,DOCS  # Comma-separated space keys
   ```

### AI Service Setup

#### Anthropic (Claude) - Recommended

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to **"API Keys"**
4. Create new key
5. Copy and add to `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
   ```

#### OpenAI (GPT)

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Go to **"API Keys"**
4. Create new secret key
5. Copy and add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-xxxxx
   ```

**Note**: You need at least ONE AI service (Anthropic OR OpenAI).

## 🐳 Deployment Options

### Option 1: Local Development

```bash
# Start the bot
./start.sh

# Bot will run on http://localhost:8000
```

For local testing with Slack, use a tunnel service like ngrok:
```bash
ngrok http 8000
# Use the ngrok URL in Slack Event Subscriptions
```

### Option 2: VM Deployment with HTTPS

#### A. Generate SSL Certificate

**Self-Signed (Development/Testing)**
```bash
./generate_ssl_cert.sh
```

**Let's Encrypt (Production)**
```bash
# Install certbot
sudo apt update
sudo apt install certbot

# Generate certificate (requires domain name)
sudo certbot certonly --standalone -d your-domain.com

# Copy certificates
mkdir -p ssl_certs
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl_certs/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl_certs/key.pem
sudo chown $USER:$USER ssl_certs/*.pem
chmod 600 ssl_certs/key.pem
```

#### B. Configure Firewall

```bash
# Allow HTTPS port
sudo ufw allow 8443/tcp  # Or 443 for standard HTTPS
sudo ufw enable

# For cloud providers (AWS/GCP/Azure):
# Add inbound rule in Security Group/Firewall for port 8443 or 443
```

#### C. Start with HTTPS

```bash
# Update .env
PORT=8443  # Or 443
SSL_CERT=./ssl_certs/cert.pem
SSL_KEY=./ssl_certs/key.pem

# Start server
./start_https.sh

# Access at: https://your-vm-ip:8443
```

#### D. Run as Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/infobot.service
```

Add:
```ini
[Unit]
Description=InfoBot Slack Agent
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/slack-agent
Environment="PATH=/home/your-username/slack-agent/venv/bin"
ExecStart=/home/your-username/slack-agent/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8443 --ssl-keyfile ./ssl_certs/key.pem --ssl-certfile ./ssl_certs/cert.pem
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable infobot
sudo systemctl start infobot

# Check status
sudo systemctl status infobot

# View logs
sudo journalctl -u infobot -f
```

### Option 3: Docker Deployment

```bash
# Build image
docker build -t infobot .

# Run container
docker run -d \
  --name infobot \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/chroma_db:/app/chroma_db \
  infobot

# View logs
docker logs -f infobot

# Stop
docker stop infobot
```

### Option 4: Azure App Service

Complete guide available in `AZURE_DEPLOYMENT.md` (if you need it).

Quick steps:
1. Create Python 3.11 Linux App Service
2. Set all environment variables in Configuration
3. Set startup command: `bash startup.sh`
4. Configure Azure Storage mount for ChromaDB
5. Deploy code via GitHub Actions

## 💬 Usage Examples

### Greetings

```
User: @InfoBot Hi
Bot: 👋 Hello! I'm InfoBot, your AI assistant. I can help you find information
     from your documents or answer general questions. Just ask me anything!
```

### System Commands

```
User: @InfoBot /status
Bot: 📊 System Status:
     • Documents Indexed: 16
     • Last Sync: 2 minutes ago
     • AI Model: Claude (Anthropic)

User: @InfoBot How many documents are there?
Bot: 📊 Document Statistics:
     • Total Documents: 16
     • Total Chunks: 48
     • Last Updated: 2025-10-03T09:11:35

User: @InfoBot List all documents
Bot: 📚 Indexed Documents:

     GOOGLE_DRIVE (10 documents):
       • Project Plan.pdf
       • Q1 Report.docx
       ...

     CONFLUENCE (6 documents):
       • Team Guidelines
       • API Documentation
       ...
```

### Document Questions

```
User: @InfoBot What are the key features of our mobile app?
Bot: The mobile app includes user authentication, real-time notifications,
     offline mode, and biometric security.

     Here is the reference: [Mobile App Requirements.pdf](https://drive.google.com/...)
```

### General Questions

```
User: @InfoBot What is the weather in Chennai?
Bot: I don't have access to real-time weather data, but you can check current
     weather for Chennai on weather.com or your weather app!

User: @InfoBot What is Python?
Bot: Python is a high-level, interpreted programming language known for its
     simplicity and readability. It's widely used for web development, data
     analysis, AI, and automation.
```

### Help

```
User: @InfoBot How can you help?
Bot: I'm InfoBot, your intelligent assistant! Here's what I can do:

     📚 Document Search: I have access to 16 documents from Google Drive and Confluence
     💬 General Questions: I can answer general questions on any topic
     📊 System Commands:
        • /status - Check my current status
        • /refresh - Refresh document index
        • Ask "how many documents" or "list documents" for document info

     Just ask me anything - whether it's about your documents or a general question!
```

### Manual Refresh

```
User: @InfoBot /refresh
Bot: 🔄 Starting document refresh... This may take a few minutes.
     [After completion]
     ✅ Document refresh completed! Indexed 18 documents (2 new, 1 updated).
```

## 📁 Supported File Types

### Google Drive
- **Google Workspace**: Docs, Sheets, Slides
- **Microsoft Office**: Word (.docx), Excel (.xlsx), PowerPoint (.pptx)
- **Documents**: PDF, TXT
- **Data**: CSV files

### Confluence
- **Pages**: All page content with formatting
- **Tables**: Converted to readable text
- **Lists**: Bullet points and numbered lists
- **Code blocks**: Preserved formatting

## 🏗️ Project Structure

```
slack-agent/
├── app/                           # Application modules
│   ├── __init__.py
│   ├── confluence_handler.py      # Confluence API integration
│   ├── document_processor.py      # Document chunking and processing
│   ├── google_drive_handler.py    # Google Drive API integration
│   ├── query_engine.py            # RAG and AI response generation
│   └── vector_store.py            # ChromaDB vector database
├── ssl_certs/                     # SSL certificates (for HTTPS)
├── chroma_db/                     # Vector database storage
├── main.py                        # FastAPI application entry point
├── config.py                      # Configuration management
├── fix_sqlite.py                  # SQLite compatibility fix
├── requirements.txt               # Python dependencies
├── start.sh                       # Local development startup
├── start_https.sh                 # HTTPS startup script
├── generate_ssl_cert.sh           # SSL certificate generator
├── startup.sh                     # Azure App Service startup
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
└── IMPLEMENTATION_SUMMARY.md      # Technical implementation details
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SLACK_BOT_TOKEN` | Yes | Slack bot token | `xoxb-xxxxx` |
| `SLACK_SIGNING_SECRET` | Yes | Slack signing secret | `xxxxx` |
| `ANTHROPIC_API_KEY` | One of AI | Anthropic Claude API key | `sk-ant-xxxxx` |
| `OPENAI_API_KEY` | One of AI | OpenAI GPT API key | `sk-xxxxx` |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | For Drive | Service account JSON or path | `{"type":"service_account"...}` |
| `CONFLUENCE_BASE_URL` | For Confluence | Confluence instance URL | `https://company.atlassian.net` |
| `CONFLUENCE_USERNAME` | For Confluence | Confluence account email | `user@company.com` |
| `CONFLUENCE_API_TOKEN` | For Confluence | Confluence API token | `xxxxx` |
| `CONFLUENCE_SPACES` | For Confluence | Comma-separated space keys | `DEV,PROD,DOCS` |
| `CHROMA_DB_PATH` | No | Vector database path | `./chroma_db` (default) |
| `PORT` | No | Server port | `8000` (default) |
| `HOST` | No | Server host | `0.0.0.0` (default) |
| `SSL_CERT` | For HTTPS | SSL certificate path | `./ssl_certs/cert.pem` |
| `SSL_KEY` | For HTTPS | SSL private key path | `./ssl_certs/key.pem` |

## 🔍 How It Works

### Architecture

```
┌─────────────────┐
│     Slack       │
│   User Query    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI App   │
│  - Event Handler│
│  - Query Router │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│     Query Engine                │
│  1. Check for special queries   │
│  2. Search vector database      │
│  3. Route to AI service         │
└────────┬────────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌──────┐  ┌──────────────┐
│ RAG  │  │  General AI  │
│ Mode │  │    Mode      │
└──┬───┘  └──────┬───────┘
   │             │
   ▼             ▼
┌─────────────────────┐
│   AI Models         │
│  - Claude (Anthropic)│
│  - GPT (OpenAI)     │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │   Response   │
    │ + References │
    └──────────────┘
```

### Query Processing Flow

1. **User mentions @InfoBot** in Slack
2. **Slack sends event** to `/slack/events` endpoint
3. **Bot processes query**:
   - **Special queries** (greetings, help, stats) → Direct response
   - **Document queries** → Search ChromaDB → AI generates answer with references
   - **General queries** → AI answers from general knowledge
4. **Bot responds** in Slack thread with answer and sources (if applicable)

### Document Sync (Every 2 Minutes)

1. **Fetch documents** from Google Drive and Confluence
2. **Check for changes** (new, updated, deleted)
3. **Process documents**:
   - Extract text content
   - Split into chunks (1000 chars with 200 overlap)
   - Generate embeddings using OpenAI
4. **Update ChromaDB** vector database
5. **Log sync results**

## 🛠️ Troubleshooting

### Bot Not Responding

**Check:**
1. Application is running: `curl http://localhost:8000/health`
2. Slack Event URL is correct and verified
3. Application logs: `tail -f nohup.out` or `sudo journalctl -u infobot -f`

**Fix:**
```bash
# Restart application
pkill -f "uvicorn main:app"
./start.sh
```

### No Documents Found

**Check:**
1. Google Drive folders are shared with service account email
2. Confluence credentials are correct
3. Spaces exist and are accessible

**Fix:**
```bash
# Manually trigger refresh
curl -X POST http://localhost:8000/refresh

# Or in Slack
@InfoBot /refresh
```

### AI Not Working

**Check:**
1. API keys are correct in `.env`
2. API has available quota/credits
3. Check logs for API errors

**Fix:**
```bash
# Test AI connection
python -c "
from app.query_engine import QueryEngine
qe = QueryEngine()
print(qe.test_ai_connection())
"
```

### Confluence 404 Error

**Issue:** Getting 404 when fetching Confluence pages

**Fix:**
- Ensure `CONFLUENCE_BASE_URL` does NOT include `/wiki` at the end
- Use: `https://company.atlassian.net` ✅
- Not: `https://company.atlassian.net/wiki` ❌
- Bot auto-detects correct API endpoint

### SSL Certificate Issues

**Self-signed certificate warnings:**
- Normal for development
- For production, use Let's Encrypt

**Test with:**
```bash
curl -k https://localhost:8443/health
```

## 📊 Monitoring

### Health Checks

```bash
# Application health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-10-03T...",
  "documents_indexed": 16,
  "ai_models": ["Claude (Anthropic)"],
  "version": "1.0.0"
}
```

### View Logs

```bash
# If running with start.sh
tail -f nohup.out

# If running as systemd service
sudo journalctl -u infobot -f

# If running with Docker
docker logs -f infobot
```

### Document Statistics

Send to bot in Slack:
```
@InfoBot /status
```

Or via API:
```bash
curl http://localhost:8000/status
```

## 🔒 Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Use HTTPS in production** - SSL certificates required
3. **Rotate API keys regularly** - Every 90 days recommended
4. **Limit Google Drive sharing** - Only share necessary folders
5. **Use Confluence read-only tokens** - Minimum required permissions
6. **Keep dependencies updated** - `pip install --upgrade -r requirements.txt`
7. **Monitor logs for suspicious activity**
8. **Use firewall rules** - Restrict access to necessary ports only

## 🚀 Performance Tips

1. **Reduce chunk size** if processing is slow - Edit `document_processor.py`
2. **Limit search results** - Adjust `max_search_results` in `query_engine.py`
3. **Use Redis for caching** - For high-traffic deployments
4. **Increase workers** for production - `--workers 4` in startup command
5. **Monitor memory usage** - ChromaDB can be memory-intensive
6. **Schedule syncs during off-hours** - Adjust cron schedule in `main.py`

## 📚 Additional Resources

- **Slack API Docs**: https://api.slack.com/docs
- **Google Drive API**: https://developers.google.com/drive
- **Confluence API**: https://developer.atlassian.com/cloud/confluence/rest
- **Anthropic Claude**: https://docs.anthropic.com/
- **OpenAI API**: https://platform.openai.com/docs
- **ChromaDB**: https://docs.trychroma.com/

## 🆘 Support

For issues or questions:

1. Check this README thoroughly
2. Review `IMPLEMENTATION_SUMMARY.md` for technical details
3. Check application logs for specific errors
4. Ensure all prerequisites are met
5. Verify all environment variables are set correctly

## 📝 License

This project is licensed under the MIT License.

---

**Built with ❤️ using FastAPI, ChromaDB, and AI**
