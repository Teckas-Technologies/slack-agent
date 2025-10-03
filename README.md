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

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Detailed Setup Guide](#-detailed-setup-guide)
  - [Step 1: Create Slack App](#step-1-create-slack-app-and-get-credentials)
  - [Step 2: Get Google Drive Credentials](#step-2-get-google-drive-credentials)
  - [Step 3: Get Confluence Credentials](#step-3-get-confluence-credentials-optional)
  - [Step 4: Get AI API Keys](#step-4-get-ai-api-keys)
  - [Step 5: Configure Environment](#step-5-configure-environment-variables)
- [Running the Application](#-running-the-application)
  - [Local Development](#option-1-local-development)
  - [Docker](#option-2-docker)
  - [VM with HTTPS](#option-3-vm-with-https)
- [Usage Examples](#-usage-examples)
- [Troubleshooting](#-troubleshooting)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Slack workspace with admin access
- Google Cloud account (for Google Drive)
- Confluence account (optional)
- OpenAI or Anthropic API key

### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd slack-agent

# 2. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment template
cp .env.example .env

# 5. Edit .env with your credentials (see detailed setup below)
nano .env

# 6. Run the bot
./start.sh
```

## 📖 Detailed Setup Guide

### Step 1: Create Slack App and Get Credentials

#### 1.1 Create New Slack App

1. **Go to Slack API portal**: https://api.slack.com/apps
2. Click **"Create New App"**
3. Select **"From scratch"**
4. **App Name**: Enter `InfoBot` (or your preferred name)
5. **Pick a workspace**: Select your workspace
6. Click **"Create App"**

#### 1.2 Configure OAuth Scopes

1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll down to **"Scopes"** section
3. Under **"Bot Token Scopes"**, click **"Add an OAuth Scope"**
4. Add these scopes one by one:
   ```
   app_mentions:read     - Read messages that mention @InfoBot
   chat:write           - Send messages as InfoBot
   im:history           - View message history in DMs
   im:read              - View basic DM channel info
   channels:history     - Read messages in public channels (optional)
   users:read           - View people in workspace
   ```

#### 1.3 Enable Event Subscriptions

1. In the left sidebar, click **"Event Subscriptions"**
2. Toggle **"Enable Events"** to **ON**
3. **Request URL**:
   - For local testing with ngrok: `https://your-ngrok-url.ngrok.io/slack/events`
   - For production: `https://your-domain.com/slack/events`
   - For VM: `https://your-vm-ip:8443/slack/events`
4. Under **"Subscribe to bot events"**, click **"Add Bot User Event"**
5. Add these events:
   - `app_mention` - When someone mentions @InfoBot
   - `message.im` - Direct messages to InfoBot
6. Click **"Save Changes"**

**Note**: Slack will verify the URL. Make sure your application is running before saving!

#### 1.4 Install App to Workspace

1. In the left sidebar, click **"Install App"**
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. You'll see **"Bot User OAuth Token"** - this starts with `xoxb-`
5. Click **"Copy"** to copy the token

#### 1.5 Get Signing Secret

1. In the left sidebar, click **"Basic Information"**
2. Scroll to **"App Credentials"** section
3. Find **"Signing Secret"**
4. Click **"Show"** and copy the secret

#### 1.6 Add to .env File

```bash
SLACK_BOT_TOKEN=xoxb-1234567890-1234567890123-xxxxxxxxxxxxxxxxxxxxxxxx
SLACK_SIGNING_SECRET=abc123def456ghi789jkl012mno345pq
```

---

### Step 2: Get Google Drive Credentials

We'll use a Service Account for secure, server-to-server access.

#### 2.1 Create Google Cloud Project

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. Click the project dropdown at the top
3. Click **"New Project"**
4. **Project Name**: Enter `InfoBot` (or your preferred name)
5. Click **"Create"**
6. Wait for project creation, then select it

#### 2.2 Enable Google Drive API

1. In the search bar at top, search for **"Google Drive API"**
2. Click on **"Google Drive API"** in results
3. Click **"Enable"**
4. Wait for API to be enabled

#### 2.3 Create Service Account

1. In the left sidebar, click **"APIs & Services"** > **"Credentials"**
2. Click **"+ Create Credentials"** at the top
3. Select **"Service Account"**
4. **Service account details**:
   - **Service account name**: `infobot-drive-reader`
   - **Service account ID**: (auto-filled)
   - **Description**: "InfoBot Google Drive access"
5. Click **"Create and Continue"**
6. **Grant this service account access to project** (optional, skip this step)
   - Click **"Continue"**
7. **Grant users access to this service account** (optional, skip this step)
   - Click **"Done"**

#### 2.4 Generate JSON Key

1. You'll see your service accounts list
2. Click on the **service account email** you just created
3. Go to the **"Keys"** tab
4. Click **"Add Key"** > **"Create new key"**
5. Select **"JSON"** format
6. Click **"Create"**
7. A JSON file will download automatically
8. **IMPORTANT**: Keep this file secure! It contains your private key

#### 2.5 Share Google Drive Folders with Service Account

1. Open the downloaded JSON file
2. Find the `"client_email"` field (looks like: `infobot-drive-reader@project-id.iam.gserviceaccount.com`)
3. Copy this email address
4. **Go to Google Drive**: https://drive.google.com/
5. **For each folder** you want InfoBot to access:
   - Right-click the folder
   - Click **"Share"**
   - Paste the service account email
   - Set permission to **"Viewer"**
   - **Uncheck** "Notify people" (it's not a real person)
   - Click **"Share"**

#### 2.6 Add to .env File

**Option A: Paste JSON content directly (Recommended)**

1. Open the JSON file in a text editor
2. Copy the ENTIRE content
3. Add to `.env` as a single line:

```bash
GOOGLE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"your-project","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQE...\n-----END PRIVATE KEY-----\n","client_email":"infobot-drive-reader@your-project.iam.gserviceaccount.com","client_id":"...","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"..."}'
```

**Option B: Use file path (For local development)**

```bash
# Move the JSON file to your project
mkdir -p credentials
mv ~/Downloads/your-project-xxxxxx.json credentials/google-service-account.json

# Add path to .env
GOOGLE_SERVICE_ACCOUNT_KEY=./credentials/google-service-account.json
```

---

### Step 3: Get Confluence Credentials (Optional)

#### 3.1 Generate API Token

1. **Go to Atlassian Account Security**: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **"Create API token"**
3. **Label**: Enter `InfoBot`
4. Click **"Create"**
5. Click **"Copy"** to copy the token
6. **IMPORTANT**: Save this token somewhere safe - you can't view it again!

#### 3.2 Get Your Confluence Base URL

Your Confluence URL looks like:
- `https://your-company.atlassian.net/wiki/spaces/...`

The **base URL** is: `https://your-company.atlassian.net`

**DO NOT** include `/wiki` at the end!

#### 3.3 Find Space Keys

1. Go to any Confluence space
2. Look at the URL: `https://your-company.atlassian.net/wiki/spaces/DEV/pages/...`
3. The **space key** is the part after `/spaces/` (in this example: `DEV`)
4. Repeat for all spaces you want to index

#### 3.4 Add to .env File

```bash
CONFLUENCE_BASE_URL=https://your-company.atlassian.net
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=ATATT3xFfGF0T...your-token-here
CONFLUENCE_SPACES=DEV,PROD,DOCS,HR
```

**Note**: Separate multiple space keys with commas (no spaces)

---

### Step 4: Get AI API Keys

You need **at least ONE** of these (both is better):

#### Option A: Anthropic Claude (Recommended)

1. **Go to Anthropic Console**: https://console.anthropic.com/
2. **Sign up** or **log in** with your email
3. In the left sidebar, click **"API Keys"**
4. Click **"Create Key"**
5. **Name**: Enter `InfoBot`
6. Click **"Create Key"**
7. **Copy** the key (starts with `sk-ant-api03-...`)
8. Add to `.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Pricing**: Pay-as-you-go, ~$3 per million input tokens

#### Option B: OpenAI GPT

1. **Go to OpenAI Platform**: https://platform.openai.com/
2. **Sign up** or **log in**
3. Click your profile icon (top-right) > **"View API keys"**
4. Click **"+ Create new secret key"**
5. **Name**: Enter `InfoBot`
6. Click **"Create secret key"**
7. **Copy** the key (starts with `sk-...`)
8. **IMPORTANT**: Save this - you can't view it again!
9. Add to `.env`:

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Pricing**: Pay-as-you-go, ~$0.50 per million input tokens

---

### Step 5: Configure Environment Variables

#### 5.1 Copy Template

```bash
cp .env.example .env
```

#### 5.2 Edit .env File

```bash
nano .env  # or use your preferred text editor
```

#### 5.3 Complete .env Configuration

```bash
# ======================
# REQUIRED - Slack
# ======================
SLACK_BOT_TOKEN=xoxb-your-bot-token-from-step-1
SLACK_SIGNING_SECRET=your-signing-secret-from-step-1

# ======================
# REQUIRED - AI Service (At least one)
# ======================
ANTHROPIC_API_KEY=sk-ant-your-key-from-step-4
OPENAI_API_KEY=sk-your-openai-key-from-step-4

# ======================
# REQUIRED - Google Drive
# ======================
# Option A: Paste JSON content (recommended for deployment)
GOOGLE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'

# Option B: Or use file path (for local development)
# GOOGLE_SERVICE_ACCOUNT_KEY=./credentials/google-service-account.json

# ======================
# OPTIONAL - Confluence
# ======================
CONFLUENCE_BASE_URL=https://your-company.atlassian.net
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-api-token-from-step-3
CONFLUENCE_SPACES=DEV,PROD,DOCS

# ======================
# Application Settings
# ======================
CHROMA_DB_PATH=./chroma_db
PORT=8000
DEBUG=False

# ======================
# HTTPS Settings (for VM deployment)
# ======================
HOST=0.0.0.0
SSL_CERT=./ssl_certs/cert.pem
SSL_KEY=./ssl_certs/key.pem
```

#### 5.4 Verify Configuration

```bash
# Check file is not empty
cat .env

# Make sure all required variables are set
grep "SLACK_BOT_TOKEN" .env
grep "ANTHROPIC_API_KEY\|OPENAI_API_KEY" .env
grep "GOOGLE_SERVICE_ACCOUNT_KEY" .env
```

---

## 🏃 Running the Application

### Option 1: Local Development

#### For Local Testing (with ngrok)

1. **Start the application**:
   ```bash
   ./start.sh
   ```

2. **In another terminal, start ngrok**:
   ```bash
   # Install ngrok first: https://ngrok.com/download
   ngrok http 8000
   ```

3. **Copy the ngrok URL** (looks like: `https://xxxx-xx-xx-xxx-xxx.ngrok-free.app`)

4. **Update Slack Event Subscription URL**:
   - Go to https://api.slack.com/apps
   - Select your app
   - Click **"Event Subscriptions"**
   - Update **Request URL** to: `https://your-ngrok-url.ngrok-free.app/slack/events`
   - Click **"Save Changes"**

5. **Test in Slack**:
   ```
   @InfoBot Hi
   @InfoBot How many documents are there?
   ```

#### For Local Development (without Slack)

```bash
# Start the application
./start.sh

# Application will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
# - Health: http://localhost:8000/health

# Test health endpoint
curl http://localhost:8000/health
```

#### View Logs

```bash
# Real-time logs
tail -f nohup.out

# Search for errors
grep ERROR nohup.out
```

#### Stop the Application

```bash
# Find and kill the process
pkill -f "uvicorn main:app"

# Or use the PID
ps aux | grep uvicorn
kill <PID>
```

---

### Option 2: Docker

#### 2.1 Install Docker

**macOS/Windows**: Download Docker Desktop from https://www.docker.com/products/docker-desktop

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### 2.2 Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Services started:
# - InfoBot application (port 8000)
# - Redis (for caching)
# - Watchtower (auto-updates)
```

#### 2.3 View Logs

```bash
# All services
docker-compose logs -f

# Only InfoBot
docker-compose logs -f slack-agent

# Last 100 lines
docker-compose logs -f --tail=100
```

#### 2.4 Check Status

```bash
# Check running containers
docker-compose ps

# Check health
curl http://localhost:8000/health
```

#### 2.5 Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

#### 2.6 Restart Services

```bash
# Restart all
docker-compose restart

# Restart only InfoBot
docker-compose restart slack-agent
```

#### 2.7 Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose up -d --build
```

---

### Option 3: VM with HTTPS

#### 3.1 Prerequisites

- Linux VM (Ubuntu 20.04+ recommended)
- Public IP address
- Domain name (optional, for Let's Encrypt)
- Port 443 or 8443 open

#### 3.2 Install Python 3.11

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Verify installation
python3.11 --version
```

#### 3.3 Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd slack-agent

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your credentials
```

#### 3.4 Generate SSL Certificate

**Option A: Self-Signed (Development/Testing)**

```bash
# Generate certificate
./generate_ssl_cert.sh

# Certificates created at:
# - ssl_certs/cert.pem
# - ssl_certs/key.pem
```

**Option B: Let's Encrypt (Production with Domain)**

```bash
# Install certbot
sudo apt update
sudo apt install certbot -y

# Generate certificate (replace your-domain.com)
sudo certbot certonly --standalone -d your-domain.com

# Copy to project
mkdir -p ssl_certs
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl_certs/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl_certs/key.pem
sudo chown $USER:$USER ssl_certs/*.pem
chmod 600 ssl_certs/key.pem
```

**Option C: Use Existing Certificate**

```bash
# Copy your existing certificate and key
mkdir -p ssl_certs
cp /path/to/your/certificate.crt ssl_certs/cert.pem
cp /path/to/your/private.key ssl_certs/key.pem
chmod 600 ssl_certs/key.pem
```

#### 3.5 Configure Firewall

```bash
# Using UFW (Ubuntu)
sudo ufw allow 8443/tcp  # For custom HTTPS port
# OR
sudo ufw allow 443/tcp   # For standard HTTPS port
sudo ufw enable
sudo ufw status

# Check if port is open
sudo netstat -tlnp | grep 8443
```

**For Cloud Providers:**

- **AWS**: Add inbound rule to Security Group for TCP port 8443/443
- **Google Cloud**: Add firewall rule: `gcloud compute firewall-rules create allow-https --allow tcp:8443`
- **Azure**: Add inbound port rule to Network Security Group for port 8443/443

#### 3.6 Update .env for HTTPS

```bash
nano .env
```

Add/update:
```bash
PORT=8443  # Or 443 if you prefer
SSL_CERT=./ssl_certs/cert.pem
SSL_KEY=./ssl_certs/key.pem
HOST=0.0.0.0
```

#### 3.7 Start Application

```bash
# Start with HTTPS
./start_https.sh

# Application will be available at:
# https://your-vm-ip:8443
# or
# https://your-domain.com:8443
```

#### 3.8 Run as System Service (Recommended for Production)

```bash
# Create service file
sudo nano /etc/systemd/system/infobot.service
```

Paste this content (replace `your-username` with your actual username):

```ini
[Unit]
Description=InfoBot Slack Agent
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/slack-agent
Environment="PATH=/home/your-username/slack-agent/venv/bin"
ExecStart=/home/your-username/slack-agent/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8443 --ssl-keyfile ./ssl_certs/key.pem --ssl-certfile ./ssl_certs/cert.pem --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable infobot
sudo systemctl start infobot

# Check status
sudo systemctl status infobot

# View logs
sudo journalctl -u infobot -f

# Manage service
sudo systemctl stop infobot
sudo systemctl restart infobot
```

#### 3.9 Update Slack Event URL

1. Go to https://api.slack.com/apps
2. Select your app
3. Click **"Event Subscriptions"**
4. Update **Request URL** to: `https://your-vm-ip:8443/slack/events`
   - Or: `https://your-domain.com:8443/slack/events`
5. Click **"Save Changes"**

#### 3.10 Test Deployment

```bash
# Test health endpoint
curl -k https://localhost:8443/health

# From another machine
curl -k https://your-vm-ip:8443/health

# Test in Slack
@InfoBot Hello
```

---

## 💬 Usage Examples

### Greetings

```
User: @InfoBot Hi
Bot: 👋 Hello! I'm InfoBot, your AI assistant. I can help you find information
     from your documents or answer general questions. Just ask me anything!

User: @InfoBot Hello
Bot: 👋 Hello! I'm InfoBot, your AI assistant...
```

### Help and Information

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

### System Commands

```
User: @InfoBot /status
Bot: 📊 System Status:
     • Documents Indexed: 16
     • Total Chunks: 48
     • Last Sync: 2 minutes ago
     • AI Model: Claude (Anthropic)
     • Status: Healthy

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
       • Team Handbook.docx
       ...

     CONFLUENCE (6 documents):
       • Team Guidelines
       • API Documentation
       • Onboarding Guide
       ...
```

### Document Questions

```
User: @InfoBot What are the key features of our mobile app?
Bot: The mobile app includes user authentication, real-time notifications,
     offline mode, and biometric security. It also supports dark mode and
     multi-language interface.

     Here is the reference: [Mobile App Requirements.pdf](https://drive.google.com/file/d/xxx)

User: @InfoBot What is our company's vacation policy?
Bot: The company offers 20 days of paid vacation per year, plus 10 public
     holidays. Vacation days can be carried over for up to 6 months.

     Here is the reference: [HR Policies](https://company.atlassian.net/wiki/spaces/HR/pages/xxx)
```

### General Questions

```
User: @InfoBot What is the weather in Chennai?
Bot: I don't have access to real-time weather data, but you can check current
     weather for Chennai on weather.com, your weather app, or Google!

User: @InfoBot What is Python?
Bot: Python is a high-level, interpreted programming language known for its
     simplicity and readability. It's widely used for web development, data
     analysis, artificial intelligence, automation, and scientific computing.

User: @InfoBot How are you?
Bot: I'm doing great, thanks for asking! I'm ready to help you find information
     from your documents or answer any questions you have. What can I help you with?
```

### Manual Refresh

```
User: @InfoBot /refresh
Bot: 🔄 Starting document refresh... This may take a few minutes.
     [After completion]
     ✅ Document refresh completed!
     • Total documents: 18
     • New documents: 2
     • Updated documents: 1
     • Removed documents: 0
```

---

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

---

## 🛠️ Troubleshooting

### Bot Not Responding

**Issue**: Mentioning @InfoBot in Slack doesn't get a response

**Check:**
1. Application is running:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy",...}
   ```

2. Slack Event URL is correct and verified:
   - Go to https://api.slack.com/apps → Your App → Event Subscriptions
   - URL should show ✅ Verified

3. Check application logs:
   ```bash
   # If running locally
   tail -f nohup.out

   # If running as systemd service
   sudo journalctl -u infobot -f

   # If running with Docker
   docker-compose logs -f slack-agent
   ```

**Fix:**
```bash
# Restart application
pkill -f "uvicorn main:app"
./start.sh

# Or if using systemd
sudo systemctl restart infobot

# Or if using Docker
docker-compose restart slack-agent
```

---

### Slack Event URL Verification Failed

**Issue**: Slack shows "Your URL didn't respond with the value of the challenge parameter"

**Fix:**
1. Make sure application is running BEFORE saving the Event URL
2. Test health endpoint:
   ```bash
   curl https://your-domain.com/health
   ```
3. Check firewall allows incoming connections
4. For ngrok, make sure ngrok is running:
   ```bash
   ngrok http 8000
   ```

---

### No Documents Found

**Issue**: Bot says "No documents have been indexed yet"

**Check:**
1. Google Drive folders are shared with service account:
   - Open the JSON key file
   - Copy the `client_email` value
   - Go to Google Drive
   - Check if this email has "Viewer" access to your folders

2. Confluence credentials are correct:
   ```bash
   # Test Confluence connection
   curl -u "your-email@company.com:your-api-token" \
     "https://your-company.atlassian.net/wiki/rest/api/space"
   ```

3. Check logs for errors:
   ```bash
   grep -i "error\|failed" nohup.out
   ```

**Fix:**
```bash
# Manually trigger refresh
curl -X POST http://localhost:8000/refresh

# Or in Slack
@InfoBot /refresh

# Check sync logs
tail -f nohup.out | grep -i "document\|sync"
```

---

### Confluence 404 Error

**Issue**: `Error fetching pages from space XXX: 404`

**Fix:**
1. Ensure `CONFLUENCE_BASE_URL` does NOT include `/wiki` at the end:
   ```bash
   # Correct ✅
   CONFLUENCE_BASE_URL=https://your-company.atlassian.net

   # Wrong ❌
   CONFLUENCE_BASE_URL=https://your-company.atlassian.net/wiki
   ```

2. Verify space keys are correct:
   - Go to Confluence space
   - Check URL: `.../wiki/spaces/DEV/...` → Space key is `DEV`

3. Restart application after changing `.env`

---

### AI Not Responding

**Issue**: Bot returns "Information not found" or empty responses

**Check:**
1. API keys are correct in `.env`:
   ```bash
   grep "ANTHROPIC_API_KEY\|OPENAI_API_KEY" .env
   ```

2. API has available quota/credits:
   - Anthropic: https://console.anthropic.com/ → Settings → Billing
   - OpenAI: https://platform.openai.com/ → Settings → Billing

3. Check logs for API errors:
   ```bash
   grep -i "anthropic\|openai\|api" nohup.out
   ```

**Fix:**
```bash
# Test AI connection
python3 << EOF
from app.query_engine import QueryEngine
qe = QueryEngine()
result = qe.test_ai_connection()
print(result)
EOF
```

---

### SSL Certificate Warnings

**Issue**: Browser shows "Your connection is not private" or curl shows SSL errors

**For Self-Signed Certificates (Development):**
- This is expected behavior
- Use `-k` flag with curl:
  ```bash
  curl -k https://localhost:8443/health
  ```
- In browser, click "Advanced" → "Proceed to site"

**For Production:**
- Use Let's Encrypt for free, trusted certificates
- Renew certificates before expiry:
  ```bash
  sudo certbot renew
  ```

---

### Docker Issues

**Issue**: `Cannot connect to the Docker daemon`

**Fix:**
```bash
# Start Docker service
sudo systemctl start docker

# Check status
sudo systemctl status docker

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

**Issue**: Port 8000 already in use

**Fix:**
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Or change port in .env
PORT=8001
```

---

### Permission Denied Errors

**Issue**: `Permission denied` when accessing files or ports

**Fix:**
```bash
# Fix file permissions
chmod 600 .env
chmod 700 start.sh start_https.sh generate_ssl_cert.sh
chmod 600 ssl_certs/*.pem

# For port 443 (requires root)
# Option 1: Use port > 1024 (e.g., 8443)
PORT=8443

# Option 2: Allow Python to bind privileged ports
sudo setcap CAP_NET_BIND_SERVICE=+eip $(which python3.11)
```

---

### Memory Issues

**Issue**: Application crashing or slow due to memory

**Fix:**
```bash
# Check memory usage
free -h
docker stats  # For Docker

# Reduce chunk size in document_processor.py
# Edit line ~21
self.chunk_size = 500  # Reduced from 1000

# Limit search results in query_engine.py
# Edit line ~35
self.max_search_results = 3  # Reduced from 5

# Restart application
```

---

## 📊 Monitoring

### Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-10-03T10:30:00.123456",
  "documents_indexed": 16,
  "ai_models": ["Claude (Anthropic)"],
  "version": "1.0.0"
}
```

### View Logs

```bash
# Local development
tail -f nohup.out

# Systemd service
sudo journalctl -u infobot -f
sudo journalctl -u infobot -n 100  # Last 100 lines

# Docker
docker-compose logs -f
docker-compose logs -f --tail=100
```

### Document Statistics

**Via Slack:**
```
@InfoBot /status
@InfoBot How many documents are there?
```

**Via API:**
```bash
curl http://localhost:8000/status
```

### Performance Metrics

```bash
# CPU and Memory (Docker)
docker stats

# System resources
htop  # Install: sudo apt install htop

# Disk usage
df -h
du -sh chroma_db/
```

---

## 🔒 Security Best Practices

1. **Environment Variables**
   - Never commit `.env` file (already in `.gitignore`)
   - Use strong, unique API keys
   - Rotate keys every 90 days

2. **HTTPS**
   - Always use HTTPS in production
   - Use Let's Encrypt for free certificates
   - Renew certificates before expiry

3. **Google Drive**
   - Only share necessary folders with service account
   - Use "Viewer" permission only
   - Regularly audit shared folders

4. **Confluence**
   - Use read-only API tokens
   - Limit to specific spaces
   - Revoke unused tokens

5. **System**
   - Keep system and dependencies updated
   - Use firewall rules
   - Run as non-root user
   - Monitor logs for suspicious activity

6. **Docker**
   - Use official base images
   - Run containers as non-root
   - Limit container resources
   - Scan images for vulnerabilities

---

## 🚀 Performance Tips

1. **Optimize Chunk Size**: Reduce if processing is slow
   ```python
   # Edit app/document_processor.py line ~21
   self.chunk_size = 500  # Reduced from 1000
   ```

2. **Limit Search Results**: Faster responses
   ```python
   # Edit app/query_engine.py line ~35
   self.max_search_results = 3  # Reduced from 5
   ```

3. **Increase Workers**: For production with multiple CPU cores
   ```bash
   # Edit start.sh or systemd service
   uvicorn main:app --workers 4
   ```

4. **Schedule Syncs**: Adjust sync frequency
   ```python
   # Edit main.py line ~53
   trigger=IntervalTrigger(minutes=5)  # Changed from 2
   ```

5. **Use Redis**: For caching (already in docker-compose.yml)

6. **Monitor Resources**: Keep an eye on memory and CPU
   ```bash
   docker stats
   htop
   ```

---

## 📚 Project Structure

```
slack-agent/
├── app/                           # Application modules
│   ├── __init__.py
│   ├── confluence_handler.py      # Confluence API integration
│   ├── document_processor.py      # Document chunking and processing
│   ├── google_drive_handler.py    # Google Drive API integration
│   ├── query_engine.py            # RAG and AI response generation
│   └── vector_store.py            # ChromaDB vector database
├── ssl_certs/                     # SSL certificates (gitignored)
│   ├── cert.pem
│   └── key.pem
├── chroma_db/                     # Vector database storage (gitignored)
├── credentials/                   # Service account keys (gitignored)
├── main.py                        # FastAPI application entry point
├── config.py                      # Configuration management
├── fix_sqlite.py                  # SQLite compatibility fix
├── requirements.txt               # Python dependencies
├── start.sh                       # Local HTTP startup script
├── start_https.sh                 # HTTPS startup script
├── generate_ssl_cert.sh           # SSL certificate generator
├── startup.sh                     # Azure App Service startup
├── Dockerfile                     # Docker image definition
├── docker-compose.yml             # Multi-service Docker setup
├── .env.example                   # Environment template
├── .env                          # Environment variables (gitignored)
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

---

## 🔧 Advanced Configuration

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SLACK_BOT_TOKEN` | ✅ Yes | - | Slack bot OAuth token (xoxb-...) |
| `SLACK_SIGNING_SECRET` | ✅ Yes | - | Slack request signing secret |
| `ANTHROPIC_API_KEY` | One of | - | Anthropic Claude API key |
| `OPENAI_API_KEY` | One of | - | OpenAI GPT API key |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | For Drive | - | JSON content or file path |
| `CONFLUENCE_BASE_URL` | For Confluence | - | Without /wiki suffix |
| `CONFLUENCE_USERNAME` | For Confluence | - | Account email |
| `CONFLUENCE_API_TOKEN` | For Confluence | - | API token |
| `CONFLUENCE_SPACES` | For Confluence | - | Comma-separated space keys |
| `CHROMA_DB_PATH` | No | `./chroma_db` | Vector database directory |
| `PORT` | No | `8000` | HTTP port |
| `HOST` | No | `0.0.0.0` | Bind address |
| `SSL_CERT` | For HTTPS | - | SSL certificate path |
| `SSL_KEY` | For HTTPS | - | SSL private key path |
| `DEBUG` | No | `False` | Debug mode |

### Customization

**Modify AI Prompts**: Edit `app/query_engine.py` → `_create_prompt()` method

**Change Chunk Size**: Edit `app/document_processor.py` → `self.chunk_size`

**Adjust Sync Frequency**: Edit `main.py` → `IntervalTrigger(minutes=2)`

**Add New Document Sources**: Create new handler in `app/` directory

---

## 📝 License

This project is licensed under the MIT License.

---

## 🆘 Support

For issues or questions:

1. ✅ Check this README thoroughly
2. ✅ Review [Troubleshooting](#-troubleshooting) section
3. ✅ Check application logs for errors
4. ✅ Verify all environment variables are set
5. ✅ Test individual components (Slack, Google Drive, Confluence, AI)

---

**Built with ❤️ using FastAPI, ChromaDB, Claude AI, and OpenAI**

🎉 **Congratulations! Your InfoBot is now ready to help your team!**
