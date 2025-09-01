# Slack App Configuration Guide

## 1. Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. Enter app name: "Document Agent"
5. Select your workspace

## 2. Configure Bot Token Scopes

Navigate to "OAuth & Permissions" and add these scopes:

### Bot Token Scopes:
```
app_mentions:read     - Read messages that directly mention @your_bot
channels:read         - View basic information about channels
chat:write           - Send messages as the bot
im:read              - View messages in direct messages
im:write             - Start direct messages with people
users:read           - View people in the workspace
```

## 3. Event Subscriptions

Navigate to "Event Subscriptions":

1. **Enable Events**: Toggle ON
2. **Request URL**: `https://your-domain.com/slack/events`
3. **Subscribe to bot events**:
   ```
   app_mention          - Mentions of your app
   message.im           - Messages in direct message channels
   ```

## 4. Install App

1. Go to "Install App"
2. Click "Install to Workspace"
3. Authorize the app
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

## 5. Get Signing Secret

1. Go to "Basic Information"
2. Find "Signing Secret" section
3. Copy the signing secret

## 6. App Manifest (Alternative Setup)

You can also create the app using this manifest:

```json
{
  "display_information": {
    "name": "Document Agent",
    "description": "AI-powered document search and Q&A bot",
    "background_color": "#2c3e50"
  },
  "features": {
    "bot_user": {
      "display_name": "Document Agent",
      "always_online": true
    }
  },
  "oauth_config": {
    "scopes": {
      "bot": [
        "app_mentions:read",
        "channels:read",
        "chat:write",
        "im:read",
        "im:write",
        "users:read"
      ]
    }
  },
  "settings": {
    "event_subscriptions": {
      "request_url": "https://your-domain.com/slack/events",
      "bot_events": [
        "app_mention",
        "message.im"
      ]
    },
    "org_deploy_enabled": false,
    "socket_mode_enabled": false,
    "token_rotation_enabled": false
  }
}
```

## 7. Environment Variables Setup

Add these to your `.env` file:

```bash
# Get these from your Slack app configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
```

## 8. Test Your Bot

1. **Health Check**: `curl https://your-domain.com/health`
2. **Mention Bot**: In Slack, type `@Document Agent hello`
3. **Direct Message**: Send a DM to the bot
4. **Check Logs**: `docker-compose logs -f slack-agent`

## 9. Google Drive Setup

### Option A: Service Account (Recommended for Production)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Drive API
4. Create Service Account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Create service account
   - Generate JSON key
5. Share your Google Drive with the service account email
6. Save JSON file as `./credentials/google-service-account.json`

```bash
# Environment variable
GOOGLE_SERVICE_ACCOUNT_KEY=./credentials/google-service-account.json
```

### Option B: OAuth2 (For Development)

1. Go to Google Cloud Console
2. Enable Google Drive API
3. Create OAuth2 credentials
4. Download JSON file
5. Run OAuth flow to get tokens
6. Save credentials as `./credentials/google-oauth2.json`

```bash
# Environment variable
GOOGLE_CREDENTIALS_PATH=./credentials/google-oauth2.json
```

## 10. Confluence Setup (Optional)

1. Go to your Confluence instance
2. Generate API token:
   - Profile > Settings > Personal Access Tokens
   - Create token with read permissions
3. Add to environment:

```bash
CONFLUENCE_BASE_URL=https://your-company.atlassian.net/wiki
CONFLUENCE_USERNAME=your-email@company.com
CONFLUENCE_API_TOKEN=your-api-token
```

## 11. AI Service Setup

### Anthropic (Claude)
1. Sign up at https://console.anthropic.com/
2. Generate API key
3. Add to environment:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### OpenAI
1. Sign up at https://platform.openai.com/
2. Generate API key
3. Add to environment:
```bash
OPENAI_API_KEY=sk-your-openai-key-here
```

## 12. Deployment Checklist

- [ ] Slack app created and configured
- [ ] Bot token and signing secret obtained
- [ ] Google Drive API enabled and credentials configured
- [ ] Confluence API configured (if using)
- [ ] AI service API keys configured
- [ ] Environment variables set
- [ ] Docker containers running
- [ ] Health check passing
- [ ] Bot responds to mentions
- [ ] Document indexing working
- [ ] Queries returning relevant results

## 13. Production Considerations

### Security
- Use HTTPS for all endpoints
- Validate all incoming requests
- Store secrets in secure key management
- Implement rate limiting
- Regular security updates

### Scalability
- Use Redis for caching
- Implement background job processing
- Monitor resource usage
- Set up logging and alerting
- Database backups

### Monitoring
```bash
# Health checks
curl -f http://localhost:5000/health

# Container status
docker-compose ps

# Resource usage
docker stats

# Application logs
docker-compose logs -f
```

## 14. Troubleshooting

### Common Issues

**Bot not responding to mentions:**
- Check Event Subscriptions URL
- Verify bot token scopes
- Check application logs

**Document indexing fails:**
- Verify Google Drive permissions
- Check API quotas
- Review error logs

**AI responses not working:**
- Verify API keys are correct
- Check API rate limits
- Review response logs

### Debug Commands
```bash
# Test Slack events
curl -X POST https://your-domain.com/slack/events \
  -H "Content-Type: application/json" \
  -d '{"type":"url_verification","challenge":"test"}'

# Manual document refresh
curl -X POST https://your-domain.com/refresh

# Check document stats
# Send "/status" command to bot in Slack
```

## 15. Usage Examples

Once configured, users can interact with the bot:

```
# Basic queries
@Document Agent What technologies are used in our e-commerce project?

# Document-specific questions  
@Document Agent Summarize the requirements from the PRD document

# Data questions
@Document Agent What are our Q4 sales figures?

# System commands
@Document Agent /refresh
@Document Agent /status
@Document Agent /help
```