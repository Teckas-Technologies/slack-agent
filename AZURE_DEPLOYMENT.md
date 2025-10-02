# Azure App Service Deployment Guide

Complete guide for deploying InfoBot to Azure App Services.

## Prerequisites

- Azure account with active subscription
- Azure CLI installed (optional, for command-line deployment)
- Git repository (for deployment)

## Deployment Options

### Option 1: GitHub Actions (Recommended)

This is the most automated approach.

#### Step 1: Create Azure App Service

1. **Login to Azure Portal** (https://portal.azure.com)

2. **Create App Service:**
   - Click "Create a resource" → "Web App"
   - **Basics:**
     - Resource Group: Create new or use existing
     - Name: `infobot-slack` (must be globally unique)
     - Publish: **Code**
     - Runtime stack: **Python 3.11**
     - Operating System: **Linux**
     - Region: Choose closest to your users
     - Pricing Plan: **Basic B1** or higher (recommended)

   - Click "Review + Create" → "Create"

#### Step 2: Configure App Service

1. **Go to your App Service** → **Configuration** → **Application settings**

2. **Add Environment Variables:**
   Click "New application setting" for each:

   ```
   SLACK_BOT_TOKEN = xoxb-your-bot-token
   SLACK_SIGNING_SECRET = your-signing-secret
   ANTHROPIC_API_KEY = sk-ant-your-anthropic-key
   OPENAI_API_KEY = sk-your-openai-key
   GOOGLE_SERVICE_ACCOUNT_KEY = {"type":"service_account",...full JSON...}
   CONFLUENCE_BASE_URL = https://your-company.atlassian.net
   CONFLUENCE_USERNAME = your-email@company.com
   CONFLUENCE_API_TOKEN = your-api-token
   CONFLUENCE_SPACES = SPACE1,SPACE2
   CHROMA_DB_PATH = /home/chroma_db
   PORT = 8000
   DEBUG = False
   WEBSITES_PORT = 8000
   SCM_DO_BUILD_DURING_DEPLOYMENT = true
   ```

   **Important:** For `GOOGLE_SERVICE_ACCOUNT_KEY`, paste the entire JSON as a single line:
   ```
   {"type":"service_account","project_id":"...","private_key_id":"...","private_key":"-----BEGIN PRIVATE KEY-----\nMIIE...\n-----END PRIVATE KEY-----\n",...}
   ```

3. **Save Configuration**

#### Step 3: Configure Startup Command

1. Go to **Configuration** → **General settings**
2. Set **Startup Command:**
   ```bash
   bash startup.sh
   ```
3. Click **Save**

#### Step 4: Deploy from GitHub

1. **Go to Deployment Center:**
   - Select **GitHub** as source
   - Authorize Azure to access GitHub
   - Select your repository and branch
   - Click **Save**

2. **Azure will automatically:**
   - Create GitHub Actions workflow
   - Deploy your application
   - Set up continuous deployment

#### Step 5: Configure Persistent Storage (Important!)

ChromaDB needs persistent storage:

1. Go to **Configuration** → **Path mappings**
2. Click **New Azure Storage Mount**
   - Name: `chromadb`
   - Configuration options: **Basic**
   - Storage accounts: Create new or select existing
   - Storage type: **Azure Blob**
   - Mount path: `/home/chroma_db`
3. Click **OK** → **Save**

### Option 2: Azure CLI Deployment

```bash
# Login to Azure
az login

# Create resource group
az group create --name infobot-rg --location eastus

# Create App Service Plan
az appservice plan create \
  --name infobot-plan \
  --resource-group infobot-rg \
  --sku B1 \
  --is-linux

# Create Web App
az webapp create \
  --resource-group infobot-rg \
  --plan infobot-plan \
  --name infobot-slack \
  --runtime "PYTHON:3.11"

# Configure startup command
az webapp config set \
  --resource-group infobot-rg \
  --name infobot-slack \
  --startup-file "startup.sh"

# Set environment variables
az webapp config appsettings set \
  --resource-group infobot-rg \
  --name infobot-slack \
  --settings \
    SLACK_BOT_TOKEN="xoxb-your-token" \
    SLACK_SIGNING_SECRET="your-secret" \
    ANTHROPIC_API_KEY="sk-ant-your-key" \
    GOOGLE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}' \
    CONFLUENCE_BASE_URL="https://your-company.atlassian.net" \
    CONFLUENCE_USERNAME="your-email@company.com" \
    CONFLUENCE_API_TOKEN="your-token" \
    CONFLUENCE_SPACES="SPACE1,SPACE2" \
    CHROMA_DB_PATH="/home/chroma_db" \
    PORT="8000" \
    WEBSITES_PORT="8000" \
    SCM_DO_BUILD_DURING_DEPLOYMENT="true"

# Deploy from local Git
az webapp deployment source config-local-git \
  --resource-group infobot-rg \
  --name infobot-slack

# Get deployment URL
az webapp deployment source show \
  --resource-group infobot-rg \
  --name infobot-slack

# Add Azure remote and push
git remote add azure <deployment-url>
git push azure main
```

### Option 3: ZIP Deployment

```bash
# Create ZIP file (exclude unnecessary files)
zip -r infobot.zip . \
  -x "*.git*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*chroma_db*" \
  -x "*.env" \
  -x "*venv*" \
  -x "*.DS_Store"

# Deploy ZIP
az webapp deployment source config-zip \
  --resource-group infobot-rg \
  --name infobot-slack \
  --src infobot.zip
```

## Post-Deployment Configuration

### 1. Update Slack Event Subscription URL

1. Go to [Slack API](https://api.slack.com/apps)
2. Select your app
3. Go to **Event Subscriptions**
4. Update **Request URL** to:
   ```
   https://infobot-slack.azurewebsites.net/slack/events
   ```
5. Save changes

### 2. Verify Deployment

1. **Check Health Endpoint:**
   ```bash
   curl https://infobot-slack.azurewebsites.net/health
   ```

   Should return:
   ```json
   {
     "status": "healthy",
     "timestamp": "2024-...",
     "documents_indexed": 0,
     "ai_models": ["Claude (Anthropic)"],
     "version": "1.0.0"
   }
   ```

2. **Check Logs:**
   - Go to Azure Portal → Your App Service
   - **Monitoring** → **Log stream**
   - Look for:
     ```
     INFO: Application startup complete
     INFO: Document sync scheduler started
     INFO: Using service account credentials from environment variable
     ```

3. **Test in Slack:**
   ```
   @InfoBot /status
   ```

### 3. Initial Document Sync

Trigger manual refresh:
```bash
curl -X POST https://infobot-slack.azurewebsites.net/refresh
```

Or wait for automatic sync (runs every 2 minutes).

## Important Azure-Specific Considerations

### 1. File System Limitations

**Problem:** Azure App Service has an ephemeral file system. ChromaDB data will be lost on restart.

**Solution:** Use Azure Storage Mount (configured in Step 5 above)

### 2. Cold Start

**Problem:** App Service may sleep after 20 minutes of inactivity (Basic tier).

**Solutions:**
- Upgrade to **Standard** tier for "Always On" feature
- Or configure health check pings
- Or accept occasional cold starts

### 3. Memory Limits

**Recommendations:**
- **Basic B1:** 1.75 GB RAM - Good for small deployments
- **Standard S1:** 1.75 GB RAM - With "Always On"
- **Premium P1V2:** 3.5 GB RAM - For large document sets

### 4. Logging

Enable Application Insights:
```bash
az webapp log config \
  --resource-group infobot-rg \
  --name infobot-slack \
  --application-logging filesystem \
  --level information
```

### 5. Custom Domain & SSL

1. **Add Custom Domain:**
   - Go to **Custom domains**
   - Add your domain
   - Configure DNS

2. **SSL Certificate:**
   - Azure provides free SSL for `*.azurewebsites.net`
   - For custom domains, use **App Service Managed Certificate** (free)

## Scaling Recommendations

### For Small Teams (< 50 users)
- **Tier:** Basic B1
- **Instances:** 1
- **Cost:** ~$13/month

### For Medium Teams (50-200 users)
- **Tier:** Standard S1
- **Instances:** 1-2
- **Features:** Always On, Auto-scale
- **Cost:** ~$70/month

### For Large Teams (200+ users)
- **Tier:** Premium P1V2
- **Instances:** 2-3 with auto-scale
- **Features:** Always On, Staging slots, Auto-scale
- **Cost:** ~$150/month

## Monitoring

### Application Insights Setup

1. **Create Application Insights:**
   ```bash
   az monitor app-insights component create \
     --app infobot-insights \
     --location eastus \
     --resource-group infobot-rg
   ```

2. **Link to App Service:**
   - Go to App Service → **Application Insights**
   - Click **Turn on Application Insights**
   - Select your component

3. **Key Metrics to Monitor:**
   - Request count and response times
   - Failed requests (5xx errors)
   - Memory and CPU usage
   - Document sync frequency
   - Slack event processing time

### Custom Monitoring Endpoints

- `/health` - Application health
- `/status` - Detailed statistics
- `/docs-summary` - Document counts

## Troubleshooting

### App Won't Start

**Check:**
1. Application logs in Log Stream
2. Environment variables are set correctly
3. Startup command is `bash startup.sh`
4. Python version is 3.11

### Slack Events Not Working

**Check:**
1. Event subscription URL is correct
2. App Service is accessible publicly
3. SLACK_SIGNING_SECRET is correct
4. Check logs for verification errors

### Documents Not Syncing

**Check:**
1. Google credentials JSON is valid
2. Confluence credentials are correct
3. ChromaDB storage mount is configured
4. Check scheduler logs every 2 minutes

### High Memory Usage

**Solutions:**
1. Reduce `max_search_results` in query_engine.py
2. Reduce `chunk_size` in document_processor.py
3. Upgrade to higher tier
4. Limit number of documents indexed

## Security Best Practices

1. **Use Key Vault for Secrets:**
   ```bash
   # Create Key Vault
   az keyvault create \
     --name infobot-vault \
     --resource-group infobot-rg

   # Store secrets
   az keyvault secret set \
     --vault-name infobot-vault \
     --name slack-bot-token \
     --value "xoxb-your-token"

   # Reference in App Service
   @Microsoft.KeyVault(SecretUri=https://infobot-vault.vault.azure.net/secrets/slack-bot-token/)
   ```

2. **Enable Managed Identity:**
   - Use for accessing Azure resources
   - No need to store credentials

3. **Network Security:**
   - Configure IP restrictions if needed
   - Use Private Endpoints for production

4. **Enable HTTPS Only:**
   - Configuration → General settings → HTTPS Only: **On**

## Backup Strategy

### ChromaDB Backup

Create scheduled backup:
```bash
# Via Azure Storage
az storage blob upload-batch \
  --account-name infobotbackups \
  --destination chromadb-backup \
  --source /home/chroma_db
```

Or use the built-in backup endpoint:
```bash
curl -X POST https://infobot-slack.azurewebsites.net/backup
```

## Cost Optimization

1. **Use Deployment Slots** (Standard tier+)
   - Test in staging before production
   - Zero-downtime deployments

2. **Auto-scale Rules:**
   - Scale based on CPU/Memory
   - Scale down during off-hours

3. **Use Azure Monitor Alerts:**
   - Alert on high error rates
   - Alert on high latency

## Continuous Deployment

GitHub Actions workflow is automatically created. Customize it:

```yaml
# .github/workflows/azure-deploy.yml
name: Deploy to Azure

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: infobot-slack
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
```

## Support & Maintenance

### Regular Tasks

1. **Weekly:** Check Application Insights for errors
2. **Monthly:** Review document sync logs
3. **Quarterly:** Update dependencies
4. **Yearly:** Review and optimize costs

### Useful Commands

```bash
# View logs
az webapp log tail --resource-group infobot-rg --name infobot-slack

# Restart app
az webapp restart --resource-group infobot-rg --name infobot-slack

# SSH into container
az webapp ssh --resource-group infobot-rg --name infobot-slack

# Scale up
az appservice plan update \
  --name infobot-plan \
  --resource-group infobot-rg \
  --sku S1

# Enable auto-scale
az monitor autoscale create \
  --resource-group infobot-rg \
  --resource infobot-slack \
  --resource-type Microsoft.Web/serverfarms \
  --name autoscale-infobot \
  --min-count 1 \
  --max-count 3 \
  --count 1
```

## Summary Checklist

- [ ] Create Azure App Service (Python 3.11, Linux)
- [ ] Configure all environment variables
- [ ] Set startup command to `bash startup.sh`
- [ ] Configure Azure Storage mount for ChromaDB
- [ ] Deploy code (GitHub/CLI/ZIP)
- [ ] Update Slack Event Subscription URL
- [ ] Test health endpoint
- [ ] Test Slack integration
- [ ] Trigger initial document sync
- [ ] Set up Application Insights
- [ ] Configure backups
- [ ] Enable "Always On" (Standard tier+)
- [ ] Review security settings

**Your InfoBot is now running on Azure!** 🚀