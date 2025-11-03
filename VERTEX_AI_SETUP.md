# VertexAI RAG Setup Guide

This guide will help you set up VertexAI RAG Engine for your Slack Document Agent, which provides superior performance for handling 2000+ Google Drive documents.

## Why VertexAI RAG?

The original ChromaDB implementation works well for small to medium document sets (< 1000 documents), but performance degrades with larger document counts. VertexAI RAG Engine offers:

- **Better scalability**: Handles 2000+ documents efficiently
- **Improved search quality**: Google's advanced embedding models
- **Managed infrastructure**: No need to manage vector databases
- **Direct Google Drive integration**: Native support for Drive files
- **Automatic indexing**: Handles document updates seamlessly

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Google Drive** with documents to index
3. **Service Account** with appropriate permissions

## Step 1: Enable VertexAI API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select or create your project
3. Navigate to **APIs & Services > Library**
4. Search for **"Vertex AI API"**
5. Click **Enable**

Alternatively, use gcloud CLI:
```bash
gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
```

## Step 2: Set Up Service Account Permissions

The VertexAI RAG Engine requires a special service account to access your Google Drive files.

### Find the VertexAI RAG Service Account

The service account name follows this format:
```
service-{PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com
```

To find your PROJECT_NUMBER:
```bash
gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)"
```

### Grant Drive Access

You have two options:

#### Option A: Share Specific Folders (Recommended)

1. Go to Google Drive
2. Right-click the folder containing documents you want to index
3. Click **Share**
4. Add the VertexAI RAG service account email:
   ```
   service-{PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com
   ```
5. Grant **Viewer** permission
6. Click **Send**

#### Option B: Domain-Wide Delegation (For Google Workspace)

If you're using Google Workspace and want to index documents across the organization:

1. Enable domain-wide delegation for your service account
2. Set the `GOOGLE_DRIVE_DELEGATED_USER` environment variable to an admin email
3. Grant the service account Drive API scopes

## Step 3: Configure Application Credentials

Your application needs credentials to interact with VertexAI. Use your existing Google Service Account (the one used for Drive API).

### Grant Required Roles to Your Service Account

```bash
# Grant Vertex AI User role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:YOUR_SERVICE_ACCOUNT_EMAIL" \
  --role="roles/aiplatform.user"
```

## Step 4: Update Environment Variables

Update your `.env` file with the following configuration:

```bash
# ===== VertexAI RAG Configuration =====
USE_VERTEX_AI_RAG=true
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=europe-west1

# ===== Import Mode - Choose ONE of the two options =====

# OPTION 1: Specific Folders (RECOMMENDED ⭐)
# Benefits: Auto-sync enabled! VertexAI monitors folders and indexes new files automatically
# No periodic sync needed after initial import
GOOGLE_DRIVE_FOLDER_IDS=1a2b3c4d5e6f7g8h9i0j,2b3c4d5e6f7g8h9i0j1k
# How to get folder IDs: See section below

# OPTION 2: Full Drive Access
# Use if you can't specify folders or need to index everything
# Requires periodic sync (runs every 2 minutes)
# VERTEX_RAG_FULL_DRIVE=true

# ===== Existing Google Drive Configuration =====
GOOGLE_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
GOOGLE_DRIVE_DELEGATED_USER=admin@yourcompany.com  # Optional

# ===== AI Services (Keep existing) =====
ANTHROPIC_API_KEY=sk-ant-...  # For fallback responses
```

### How to Get Google Drive Folder IDs

1. Open Google Drive in your browser
2. Navigate to the folder you want to index
3. Look at the URL in the address bar:
   ```
   https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j
   ```
4. The folder ID is the last part: `1a2b3c4d5e6f7g8h9i0j`
5. For multiple folders, separate IDs with commas (no spaces)

### Import Mode Comparison

| Feature | Folder Mode (Option 1) | Full Drive Mode (Option 2) |
|---------|------------------------|----------------------------|
| **Auto-sync new files** | ✅ Yes - Automatic | ❌ No - Manual sync needed |
| **Initial setup** | Specify folder IDs | Set flag to true |
| **Periodic sync** | ❌ Not needed | ✅ Every 2 minutes |
| **Best for** | Most use cases | Can't specify folders |
| **Performance** | ⚡ Best | Good |

**Recommendation**: Use **Folder Mode** (Option 1) - VertexAI will automatically detect and index any new files added to those folders!

### Configuration Options

- **GCP_LOCATION**: Choose based on your region
  - `us-central1` - US Central (Iowa)
  - `us-east4` - US East (Virginia)
  - `europe-west1` - Belgium (recommended for EU)
  - `asia-southeast1` - Singapore

- **VERTEX_RAG_CORPUS_NAME**: Name for your document collection (default: "google_drive_documents")

## Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

The `google-cloud-aiplatform>=1.38.0` package will be installed automatically.

## Step 6: Authenticate with Google Cloud

### For Local Development

```bash
# Authenticate with your Google account
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### For Production/Deployment

Ensure your service account JSON key is properly set in the `GOOGLE_SERVICE_ACCOUNT_KEY` environment variable. The application will use this for authentication.

## Step 7: Initial Sync

### Folder Mode (Recommended)

When you start the application with folder IDs configured:

1. **One-time import**: The app imports all specified folders on first run
2. **Auto-sync enabled**: VertexAI monitors these folders continuously
3. **New files detected automatically**: No manual sync needed!
4. **Updates handled**: Modified files are re-indexed automatically

**After the initial import, you don't need to do anything** - VertexAI handles everything!

```bash
# Start the application
python main.py

# Check logs to confirm folder import
tail -f logs/app.log | grep "folder"
```

Expected output:
```
INFO - Using FOLDER mode - importing 2 folders
INFO - Successfully imported folder 1a2b3c4d5e6f7g8h9i0j
INFO - VertexAI will auto-sync new files.
```

### Full Drive Mode

When using full drive access:

1. **Initial discovery**: App scans all accessible Drive files
2. **Batch import**: Files imported in batches of 100
3. **Periodic sync**: Runs every 2 minutes to discover new files
4. **Manual sync available**: Use `/refresh` command when needed

Trigger manual sync:

```bash
# In Slack
/refresh

# Or via API
curl -X POST http://your-server:8000/refresh
```

## How Auto-Sync Works (Folder Mode)

```
┌─────────────────────────────────────────────────────────┐
│  User adds new document to monitored Drive folder       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  VertexAI detects new file (within minutes)             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  VertexAI automatically:                                │
│  - Fetches file content from Drive                      │
│  - Chunks the document                                  │
│  - Generates embeddings                                 │
│  - Updates RAG corpus                                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  New file is immediately searchable in Slack!           │
└─────────────────────────────────────────────────────────┘

No manual intervention required! ⚡
```

## Monitoring and Verification

### Check Application Status

```bash
curl http://your-server:8000/status
```

Expected response (VertexAI mode):
```json
{
  "status": "running",
  "statistics": {
    "rag_mode": "vertex_ai",
    "ai_models": ["Gemini 2.0 Flash"]
  }
}
```

### View Logs

```bash
# Check for successful initialization
tail -f logs/app.log | grep "VertexAI"
```

You should see:
```
INFO - Initializing VertexAI RAG mode (Google Drive only)
INFO - VertexAI RAG initialized successfully
INFO - Using VertexAI RAG for document search
```

## Troubleshooting

### Error: "VertexAI RAG not configured"

**Solution**: Ensure `GCP_PROJECT_ID` is set in your `.env` file and the VertexAI API is enabled.

```bash
# Check if API is enabled
gcloud services list --enabled --filter="name:aiplatform.googleapis.com"
```

### Error: "Permission denied" when syncing documents

**Solution**: Verify that the VertexAI RAG service account has Viewer access to your Google Drive folder.

1. Check service account email:
   ```
   service-{PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com
   ```
2. Verify it's added to your Drive folder's sharing settings

### Error: "Could not authenticate"

**Solution**: Ensure your application's service account has the `roles/aiplatform.user` role:

```bash
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:YOUR_SERVICE_ACCOUNT_EMAIL"
```

### Slow Initial Sync

VertexAI RAG processes documents asynchronously. For 2000+ documents:
- First sync may take 10-30 minutes
- Subsequent syncs are incremental and faster
- Documents are indexed in batches of 100

## Cost Considerations

VertexAI RAG Engine pricing (as of 2025):
- **Embeddings**: ~$0.00001 per character
- **Retrieval**: ~$0.001 per query
- **Storage**: Included in RAG corpus

For 2000 documents (~500KB average):
- Initial indexing: ~$10-20 (one-time)
- Monthly queries (10,000): ~$10

Compare to ChromaDB:
- Compute costs for embeddings (OpenAI): ~$40/month
- Infrastructure costs: Variable

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Slack Document Agent                     │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴──────────┐
         │                      │
    ┌────▼─────┐         ┌──────▼──────┐
    │  Slack   │         │   Google    │
    │  Events  │         │   Drive     │
    └────┬─────┘         └──────┬──────┘
         │                      │
         │     ┌────────────────┘
         │     │
    ┌────▼─────▼────┐
    │  Query Engine │
    └────┬──────────┘
         │
    ┌────▼────────────────┐
    │ VertexAI RAG Engine │
    │  - RAG Corpus       │
    │  - Embeddings       │
    │  - Gemini Models    │
    └─────────────────────┘
```

## Migration from ChromaDB

If you're migrating from the ChromaDB implementation:

1. **Backup existing data** (optional - VertexAI will re-index):
   ```bash
   cp -r ./chroma_db ./chroma_db.backup
   ```

2. **Update environment**:
   ```bash
   USE_VERTEX_AI_RAG=true
   ```

3. **Restart application**:
   ```bash
   python main.py
   ```

4. **Verify migration**:
   - Check logs for "Using VertexAI RAG"
   - Test queries in Slack
   - Monitor sync status

## Support and Resources

- [VertexAI RAG Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview)
- [Google Drive API Setup](https://developers.google.com/drive/api/guides/enable-sdk)
- [Issue Tracker](https://github.com/your-repo/issues)

## Next Steps

Once VertexAI RAG is configured:

1. **Test queries** in your Slack workspace
2. **Monitor performance** via the `/status` command
3. **Adjust chunking** if needed (see `drive_sync_service.py`)
4. **Scale up** - VertexAI can handle 10,000+ documents
