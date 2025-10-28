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
- 🌐 **Domain-Wide Access**: Supports Google Workspace domain-wide delegation for automatic access to all files
- 🔐 **Automatic Discovery**: Fetches all accessible Confluence spaces automatically

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setup Guide](#-setup-guide)
   - [Step 1: Slack App](#step-1-create-slack-app)
   - [Step 2: Google Drive](#step-2-google-drive-setup)
   - [Step 3: Confluence](#step-3-confluence-setup)
   - [Step 4: AI API Keys](#step-4-ai-api-keys)
   - [Step 5: Environment Variables](#step-5-environment-variables)
3. [Deployment](#-deployment)
   - [Local Development](#local-development)
   - [Docker](#docker-deployment)
4. [Usage](#-usage)
5. [Troubleshooting](#-troubleshooting)

---

## Prerequisites

- Python 3.11+
- Slack workspace with admin access
- Google Workspace account (for Google Drive)
- Confluence account (optional)
- OpenAI or Anthropic API key

---

## 🚀 Setup Guide

### Step 1: Create Slack App

#### 1.1 Create New App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name: `InfoBot`
4. Select your workspace
5. Click **"Create App"**

#### 1.2 Configure Bot Scopes

1. Go to **"OAuth & Permissions"**
2. Under **"Bot Token Scopes"**, add:
   - `app_mentions:read`
   - `chat:write`
   - `im:history`
   - `im:read`
   - `channels:history` (optional)
   - `users:read`

#### 1.3 Enable Event Subscriptions

1. Go to **"Event Subscriptions"**
2. Toggle **"Enable Events"** to **ON**
3. **Request URL**: `https://your-server-url/slack/events`
   - For local testing with ngrok: `https://your-ngrok-url.ngrok.io/slack/events`
4. Under **"Subscribe to bot events"**, add:
   - `app_mention`
   - `message.im`
5. Click **"Save Changes"**

#### 1.4 Install App

1. Go to **"Install App"**
2. Click **"Install to Workspace"**
3. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

#### 1.5 Get Signing Secret

1. Go to **"Basic Information"**
2. Find **"Signing Secret"**
3. Copy the secret

---

### Step 2: Google Drive Setup

You have two options: **Domain-Wide Delegation** (recommended for organizations) or **Manual Sharing**.

#### Option A: Domain-Wide Delegation (Recommended for Google Workspace)

**Access ALL files in your organization automatically!**

##### 2A.1 Create Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable **Google Drive API**:
   - Go to "APIs & Services" → "Library"
   - Search "Google Drive API" → Enable
4. Create Service Account:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "Service Account"
   - Name: `infobot-drive-reader`
   - Click "Create and Continue" → "Done"
5. Generate JSON Key:
   - Click on the service account
   - Go to "Keys" tab
   - Click "Add Key" → "Create new key" → "JSON"
   - Save the file securely

##### 2A.2 Enable Domain-Wide Delegation

1. In Google Cloud Console, go to your service account
2. Click "Show Domain-Wide Delegation"
3. Check "Enable Google Workspace Domain-wide Delegation"
4. Enter product name: "InfoBot"
5. Click "Save"
6. **Copy the Client ID** (you'll need this)

##### 2A.3 Authorize in Google Workspace Admin Console

1. Go to [Google Workspace Admin Console](https://admin.google.com/)
2. Navigate to: **Security** → **Access and data control** → **API controls**
3. Click **"Manage Domain Wide Delegation"**
4. Click **"Add new"**
5. Enter:
   - **Client ID**: (from step 2A.2)
   - **OAuth Scopes**: `https://www.googleapis.com/auth/drive.readonly`
6. Click **"Authorize"**

✅ **You're done!** All files in your organization are now accessible.

---

#### Option B: Manual Sharing (Alternative)

##### 2B.1 Create Service Account

Follow steps 2A.1 (same as above)

##### 2B.2 Share Folders

1. Open the JSON key file
2. Find `client_email` (e.g., `your-service@project.iam.gserviceaccount.com`)
3. Go to Google Drive
4. Share folders with this email:
   - Right-click folder → "Share"
   - Add service account email
   - Set permission to "Viewer"
   - Uncheck "Notify people"

**Tip**: Create one main folder and share it. All subfolders will be accessible!

---

### Step 3: Confluence Setup

**InfoBot automatically discovers ALL accessible Confluence spaces!**

#### 3.1 Generate API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **"Create API token"**
3. Label: `InfoBot`
4. Click **"Create"** and copy the token

#### 3.2 Get Confluence URL

Your Confluence URL format:
- Example: `https://your-company.atlassian.net/wiki/spaces/...`
- Base URL: `https://your-company.atlassian.net`

**Important**: Do NOT include `/wiki` at the end!

#### 3.3 Grant Space Access

Make sure your Confluence user has "View" permission on the spaces you want to index:

1. Go to each Confluence space
2. Click **Space settings** (gear icon)
3. Click **Permissions**
4. Verify your user has "View" access

**Note**: InfoBot will automatically fetch all spaces you have access to. No need to list them individually!

---

### Step 4: AI API Keys

You need **at least one** (both is better for fallback):

#### Option A: Anthropic Claude (Recommended)

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to "API Keys"
4. Click "Create Key"
5. Name: `InfoBot`
6. Copy the key (starts with `sk-ant-`)

**Pricing**: ~$3 per million input tokens

#### Option B: OpenAI GPT

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Click profile icon → "View API keys"
4. Click "Create new secret key"
5. Name: `InfoBot`
6. Copy the key (starts with `sk-`)

**Pricing**: ~$0.50 per million input tokens

---

### Step 5: Environment Variables

#### 5.1 Create `.env` File

```bash
cp .env.example .env
nano .env
```

#### 5.2 Configure `.env`

```bash
# ======================
# REQUIRED - Slack
# ======================
SLACK_BOT_TOKEN=xoxb-your-bot-token-from-step-1.4
SLACK_SIGNING_SECRET=your-signing-secret-from-step-1.5

# ======================
# REQUIRED - AI Service (At least one)
# ======================
ANTHROPIC_API_KEY=sk-ant-your-key-from-step-4
OPENAI_API_KEY=sk-your-key-from-step-4

# ======================
# REQUIRED - Google Drive
# ======================
# Paste the entire JSON content from step 2.1.5 as a single line
GOOGLE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"your-project",...}'

# For Domain-Wide Delegation (Option A) - ADD THIS LINE:
GOOGLE_DRIVE_DELEGATED_USER=admin@yourcompany.com

# For Manual Sharing (Option B) - LEAVE THIS BLANK or REMOVE IT:
# GOOGLE_DRIVE_DELEGATED_USER=

# ======================
# OPTIONAL - Confluence
# ======================
CONFLUENCE_BASE_URL=https://your-company.atlassian.net
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-api-token-from-step-3.1

# Leave empty to fetch ALL accessible spaces (recommended):
CONFLUENCE_SPACES=

# Or specify specific spaces (comma-separated):
# CONFLUENCE_SPACES=DEV,PM,DOCS

# ======================
# Application Settings
# ======================
CHROMA_DB_PATH=./chroma_db
PORT=8000
DEBUG=False
HOST=0.0.0.0
```

---

## 🚀 Deployment

### Local Development

#### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd slack-agent

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env  # Add your credentials

# 5. Run the application
./start.sh
```

#### For Local Testing with ngrok

```bash
# Terminal 1: Start the application
./start.sh

# Terminal 2: Start ngrok
ngrok http 8000

# Copy the ngrok URL and update Slack Event URL:
# https://your-ngrok-url.ngrok.io/slack/events
```

#### View Logs

```bash
# Real-time logs
tail -f nohup.out

# Search for errors
grep ERROR nohup.out
```

#### Stop Application

```bash
pkill -f "uvicorn main:app"
```

---

### Docker Deployment

#### Build and Run

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

#### Update Application

```bash
git pull
docker-compose up -d --build
```

---

## 💬 Usage

### System Commands

```
@InfoBot /status          - Check system status
@InfoBot /refresh         - Manually refresh documents
@InfoBot list documents   - Show all indexed documents
@InfoBot how many documents - Show document statistics
```

### Document Questions

```
User: @InfoBot What are the company vacation policies?
Bot: The company offers 20 days of paid vacation per year...
     Here is the reference: [HR Policies](link)

User: @InfoBot Summarize the Q3 roadmap
Bot: The Q3 roadmap focuses on three key areas...
     Here is the reference: [Product Roadmap](link)
```

### General Questions

```
User: @InfoBot What is Python?
Bot: Python is a high-level programming language...

User: @InfoBot How are you?
Bot: I'm doing great! Ready to help with your documents.
```

---

## 📁 Supported File Types

### Google Drive
- Google Workspace: Docs, Sheets, Slides
- Microsoft Office: Word (.docx), Excel (.xlsx), PowerPoint (.pptx)
- Documents: PDF, TXT, Markdown
- Data: CSV files

### Confluence
- Pages with formatting
- Tables
- Lists (bullet and numbered)
- Code blocks

---

## 🛠️ Troubleshooting

### Bot Not Responding

**Check:**
1. Application is running: `curl http://localhost:8000/health`
2. Slack Event URL is verified (green checkmark)
3. Check logs: `tail -f nohup.out`

**Fix:**
```bash
pkill -f "uvicorn main:app"
./start.sh
```

---

### No Documents Found

**For Google Drive:**

**If using Domain-Wide Delegation:**
1. Verify `GOOGLE_DRIVE_DELEGATED_USER` is set in `.env`
2. Check domain-wide delegation is authorized in Admin Console
3. Verify the scope is: `https://www.googleapis.com/auth/drive.readonly`
4. Make sure the delegated user has access to files

**If using Manual Sharing:**
1. Verify folders are shared with service account email
2. Check service account has "Viewer" permission
3. Look in JSON key file for `client_email`

**For Confluence:**
1. Check your user has "View" permission on spaces
2. Verify API token is valid
3. Run the discovery script: `python scripts/list_confluence_spaces.py`

**Fix:**
```bash
# Trigger manual refresh
@InfoBot /refresh

# Check logs
tail -f nohup.out | grep -i "document\|error"
```

---

### Confluence Spaces Not Showing

**Problem**: Some spaces are not being indexed

**Solution**:
1. Verify your Confluence user has access to those spaces
2. Go to space → Settings → Permissions
3. Ensure your user has "View" permission
4. Restart application after granting access

**Verify access:**
```bash
python scripts/list_confluence_spaces.py
```

---

### AI Model Errors (404)

**Problem**: `Error code: 404 - model not found`

**Solution**: The model you're trying to use isn't available with your API key.

**For Anthropic:**
- The app uses `claude-3-haiku-20240307` (most compatible)
- If you get 404 errors, your API key might not have access
- Try using OpenAI instead

**For OpenAI:**
- The app uses `gpt-3.5-turbo`
- Check your API key has credits: https://platform.openai.com/settings/billing

---

### Domain-Wide Delegation Not Working

**Check:**
1. Client ID is correctly authorized in Admin Console
2. OAuth scope is: `https://www.googleapis.com/auth/drive.readonly`
3. Delegated user email is correct in `.env`
4. Service account has delegation enabled in Cloud Console

**Verify in logs:**
```bash
tail -f nohup.out | grep -i delegation
```

You should see:
```
INFO: Using domain-wide delegation with user: admin@yourcompany.com
```

---

## 🔒 Security Best Practices

1. **Never commit `.env` file** (already in `.gitignore`)
2. **Use read-only scopes** for Google Drive and Confluence
3. **Rotate API keys** every 90 days
4. **Monitor access logs** regularly
5. **Use HTTPS** in production
6. **Limit delegated user access** (don't use super admin unless necessary)

---

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "documents_indexed": 15,
  "ai_models": ["Claude (Anthropic)"],
  "version": "1.0.0"
}
```

### View Logs

```bash
# Real-time logs
tail -f nohup.out

# Last 100 lines
tail -100 nohup.out

# Search for errors
grep -i error nohup.out
```

---

## 📚 Project Structure

```
slack-agent/
├── app/
│   ├── confluence_handler.py      # Confluence API integration
│   ├── document_processor.py      # Document chunking
│   ├── google_drive_handler.py    # Google Drive API integration
│   ├── query_engine.py            # RAG and AI responses
│   └── vector_store.py            # ChromaDB vector database
├── scripts/
│   └── list_confluence_spaces.py  # Discover Confluence spaces
├── main.py                        # FastAPI application
├── config.py                      # Configuration management
├── requirements.txt               # Python dependencies
├── start.sh                       # Startup script
├── Dockerfile                     # Docker image
├── docker-compose.yml             # Docker services
├── .env.example                   # Environment template
└── README.md                      # This file
```

---

## 🔧 Advanced Configuration

### Adjust Sync Frequency

Edit `main.py` line ~53:

```python
trigger=IntervalTrigger(minutes=5)  # Changed from 2
```

### Change AI Model

Edit `app/query_engine.py` line ~290 and ~339:

```python
model="claude-3-opus-20240229"  # For more powerful responses
```

### Limit Search Results

Edit `app/query_engine.py` line ~35:

```python
self.max_search_results = 3  # Reduced from 5
```

---

## 🆘 Support

For issues:

1. ✅ Check this README thoroughly
2. ✅ Review [Troubleshooting](#-troubleshooting)
3. ✅ Check logs: `tail -f nohup.out`
4. ✅ Verify `.env` file has all required variables
5. ✅ Test individual components


**Built with ❤️ using FastAPI, ChromaDB, Claude AI, and OpenAI**

🎉 **Your InfoBot is ready to help your team!**
