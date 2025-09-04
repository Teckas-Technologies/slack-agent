# 🤖 Slack Document Agent (FastAPI)

A high-performance Slack bot built with FastAPI that can search and answer questions from your Google Drive documents and Confluence pages using advanced AI models.

## ✨ Features

- 🔍 **Intelligent Document Search**: Search across Google Drive and Confluence with semantic understanding
- 🤖 **AI-Powered Responses**: Get accurate answers using Claude (Anthropic) or GPT (OpenAI)  
- 📄 **Multi-Format Support**: PDFs, Word docs, Google Docs, spreadsheets, presentations, and more
- 💬 **Natural Language Interface**: Ask questions in plain English
- 🔄 **Real-time Updates**: Refresh document index with `/refresh` command
- 📊 **Source Attribution**: See which documents your answers came from
- ⚡ **High Performance**: Built with FastAPI for 2-3x faster performance than Flask
- 📚 **Auto Documentation**: Interactive API docs at `/docs` and `/redoc`
- 🔄 **Async Support**: Native async/await for better concurrency
- 🏢 **Enterprise Ready**: Production-grade with automatic validation and error handling

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd slack-agent
python setup.py
```

### 2. Configure Environment
Copy and edit the environment file:
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Deploy
```bash
./deploy.sh
```

### 4. Verify Installation
```bash
python verify_setup.py
```

## ⚙️ Configuration

### Required Environment Variables

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# AI Services (at least one required)
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
```

### Optional Configuration

```bash
# Google Drive (Service Account)
GOOGLE_SERVICE_ACCOUNT_KEY=/path/to/service-account-key.json

# Confluence
CONFLUENCE_BASE_URL=https://your-company.atlassian.net
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-confluence-api-token
```

### Setting Up Credentials

#### Slack App Setup
1. Create a new Slack app at https://api.slack.com/apps
2. Add the following OAuth scopes:
   - `app_mentions:read`
   - `chat:write`
   - `im:history`
   - `im:read`
3. Enable Event Subscriptions and set Request URL to: `https://your-domain.com/slack/events`
4. Subscribe to bot events: `app_mention`, `message.im`

#### Google Drive Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Drive API
4. Create a Service Account
5. Download the JSON key file
6. Share your Google Drive folders with the service account email

#### Confluence Setup
1. Go to your Confluence settings
2. Create an API token: Account Settings → Security → API tokens
3. Note your Confluence base URL (e.g., https://company.atlassian.net)

## 💬 Usage Examples

### Mention the bot in channels:
```
@DocumentBot What are the key features of our mobile app?
@DocumentBot Show me the quarterly sales data
@DocumentBot How do I configure the authentication system?
```

### Send direct messages:
```
What technologies are used in the e-commerce project?
Can you find information about our company policies?
Show me the latest product roadmap
```

### Bot Commands:
- `/refresh` - Update the document index
- `/status` - Show bot status and document statistics

## 📁 Supported File Types

### Google Drive
- **Google Workspace**: Docs, Sheets, Slides
- **Microsoft Office**: Word (.docx/.doc), Excel (.xlsx/.xls), PowerPoint (.pptx/.ppt)
- **Documents**: PDF, TXT, Markdown, HTML, JSON, XML
- **Data**: CSV files

### Confluence
- **Pages**: All page content with formatting
- **Tables**: Converted to readable text format
- **Lists**: Bullet points and numbered lists
- **Code blocks**: Preserved formatting
- **Attachments**: Metadata and file information

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│     Slack       │    │  FastAPI App     │    │   Document      │
│                 │────▶│                  │────▶│   Processors    │
│   - Events      │    │ - Event Handler  │    │                 │
│   - Messages    │    │ - Query Engine   │    │ - Google Drive  │
│   - Commands    │    │ - RAG Pipeline   │    │ - Confluence    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                       ┌────────▼────────┐
                       │   Vector DB     │
                       │                 │
                       │   - ChromaDB    │
                       │   - Embeddings  │
                       │   - Search      │
                       └─────────────────┘
                                │
                       ┌────────▼────────┐
                       │   AI Models     │
                       │                 │
                       │ - Claude (Anthropic) │
                       │ - GPT (OpenAI)  │
                       └─────────────────┘
```

## 🐳 Deployment Options

### 1. Azure App Service (Production Recommended)
```bash
# Automated Azure deployment
./deploy-azure.sh
```
**Features**: Auto-scaling, managed infrastructure, built-in monitoring  
**Guide**: See [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)

### 2. Docker Compose (Self-Hosted)
```bash
# Production deployment
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Local Development

**Option 1: Full Setup Script (Recommended)**
```bash
# Complete setup with environment validation
./start.sh
```

**Option 2: Quick Development Mode**
```bash
# Fast startup for development (requires .env)
./dev.sh
```

**Option 3: Manual Setup**
```bash
# Install dependencies
pip install -r requirements.txt

# Run in development mode
python app.py

# Or with uvicorn directly
uvicorn app:app --reload --port 8000
```

### 3. Production with Uvicorn (Manual)
```bash
# Run with uvicorn (included in requirements)
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 2

# Or with auto-reload for development
uvicorn app:app --reload --port 8000
```

### 4. Other Cloud Platforms
- **AWS**: Use Elastic Beanstalk or ECS with provided Docker config
- **Google Cloud**: Deploy to Cloud Run or App Engine
- **Heroku**: Use `startup.sh` as startup command

### 📚 API Documentation
Once running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc  
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## 🔒 Security Features

- **Environment-based configuration**: No hardcoded secrets
- **Service account authentication**: Secure Google Drive access
- **Request signature verification**: Validates Slack requests
- **Non-root containers**: Docker security best practices
- **Secret management**: Credentials stored outside codebase

## 🛠️ Development

### Project Structure
```
slack-agent/
├── app/                    # Application modules
│   ├── __init__.py
│   ├── confluence_handler.py
│   ├── document_processor.py
│   ├── google_drive_handler.py
│   └── query_engine.py
├── app.py                  # Main FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Multi-service setup
├── setup.py              # Setup script
├── verify_setup.py       # Verification script
├── deploy.sh             # Deployment script
├── start.sh              # Local development server
├── dev.sh                # Quick development mode
├── .env.example          # Environment template
└── README.md            # This file
```

### Adding New Document Sources
1. Create a new handler in `app/`
2. Implement `get_all_documents()` and `get_document_content()` methods
3. Add the handler to `document_processor.py`
4. Update configuration in `.env.example`

### Customizing AI Responses
Edit `query_engine.py` to:
- Modify the AI prompt template
- Adjust similarity thresholds
- Change response formatting
- Add new AI models

## 📊 Monitoring and Maintenance

### Health Checks
- **Application**: `GET /health`
- **Docker**: Built-in health checks
- **Services**: `docker-compose ps`

### Log Management
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f slack-agent

# Follow new logs
docker-compose logs -f --tail=100
```

### Database Maintenance
```bash
# View document statistics
curl http://localhost:8000/status

# Manual refresh trigger
curl -X POST http://localhost:8000/refresh

# View document summary
curl http://localhost:8000/docs-summary
```

## 🔧 Troubleshooting

### Common Issues

**"No relevant documents found"**
- Run `/refresh` command to update document index
- Check if Google Drive/Confluence credentials are correct
- Verify documents are shared with service account

**Slack events not received**
- Ensure your server is publicly accessible
- Check Event Subscriptions URL in Slack app settings
- Verify signing secret is correct

**AI responses are empty**
- Check if OpenAI or Anthropic API key is valid
- Look for rate limiting or quota issues
- Review application logs for errors

**Docker services won't start**
- Check if ports 8000 and 6379 are available  
- Verify Docker and docker-compose are installed
- Review docker-compose logs for specific errors

### Log Analysis
```bash
# Check FastAPI application logs
docker-compose logs slack-agent | grep ERROR

# Monitor real-time logs
docker-compose logs -f slack-agent

# Check system resources
docker stats
```

## 📚 API Reference

### Webhook Endpoints
- `POST /slack/events` - Slack event handler
- `GET /health` - Health check
- `POST /refresh` - Manual document refresh

### Slack Commands
- `/refresh` - Refresh document index
- `/status` - Show statistics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues, questions, or feature requests:
1. Check the troubleshooting section above
2. Review the logs for specific errors
3. Create an issue with detailed information
4. Contact your system administrator

## 🎯 Roadmap

- [ ] Support for more document types (PowerBI, Notion)
- [ ] Advanced search filters
- [ ] Multi-language support
- [ ] Analytics dashboard
- [ ] Slack slash commands
- [ ] Team-specific document access
- [ ] Integration with more AI models