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

1. **Open Google Cloud Console**: [https://console.cloud.google.com/](https://console.cloud.google.com/)

2. **Select your project** from the dropdown at the top of the page
   - Or create a new project if needed: [Create Project](https://console.cloud.google.com/projectcreate)

3. **Enable Vertex AI API**:
   - Direct link: [Enable Vertex AI API](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com)
   - Or manually:
     - Navigate to **APIs & Services > Library**
     - Search for **"Vertex AI API"**
     - Click on the result
     - Click **Enable** button

4. **Verify it's enabled**:
   - Go to [Enabled APIs](https://console.cloud.google.com/apis/dashboard)
   - You should see "Vertex AI API" in the list

## Step 2: Set Up Service Account Permissions

The VertexAI RAG Engine requires a special service account to access your Google Drive files.

### Find the VertexAI RAG Service Account

The service account name follows this format:
```
service-{PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com
```

**To find your PROJECT_NUMBER:**

1. Go to [Google Cloud Console Dashboard](https://console.cloud.google.com/home/dashboard)
2. Select your project from the dropdown
3. Look at the **Project info** card on the dashboard
4. You'll see:
   ```
   Project name: your-project-name
   Project ID: your-project-id
   Project number: 123456789012  ← This is what you need
   ```
5. Your VertexAI RAG service account will be:
   ```
   service-123456789012@gcp-sa-vertex-rag.iam.gserviceaccount.com
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

1. **Go to IAM & Admin**:
   - Direct link: [IAM Permissions](https://console.cloud.google.com/iam-admin/iam)
   - Or navigate: **IAM & Admin > IAM**

2. **Find your service account** in the list
   - Look for: `your-service-account@your-project.iam.gserviceaccount.com`
   - This is the service account you're using for Google Drive access

3. **Click the pencil icon** (Edit) next to your service account

4. **Add Role**:
   - Click **+ ADD ANOTHER ROLE**
   - Search for: **Vertex AI User**
   - Select: **Vertex AI > Vertex AI User**
   - Click **Save**

5. **Verify the role is added**:
   - Your service account should now have both:
     - Any existing roles (e.g., for Drive access)
     - **Vertex AI User** (new)

**Alternative method - Grant via Service Accounts page:**
1. Go to [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. Click on your service account email
3. Go to **Permissions** tab
4. Click **GRANT ACCESS**
5. Enter your service account email in "Add principals"
6. Select role: **Vertex AI User**
7. Click **Save**

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

## Step 6: Set Up Service Account Key

Your application authenticates using a service account JSON key file.

### Create or Use Existing Service Account Key

**If you already have a service account key** (from Google Drive setup):
- Use the same key - just ensure you added the "Vertex AI User" role in Step 3
- Skip to Step 7

**If you need to create a new service account:**

1. **Go to Service Accounts page**:
   - Direct link: [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)

2. **Create Service Account** (if needed):
   - Click **+ CREATE SERVICE ACCOUNT**
   - Service account name: `slack-agent-sa` (or your preferred name)
   - Click **CREATE AND CONTINUE**

3. **Grant Roles**:
   - Add role: **Vertex AI User**
   - Add role: **Drive Reader** (if accessing Drive)
   - Click **CONTINUE**
   - Click **DONE**

4. **Create JSON Key**:
   - Click on your service account email in the list
   - Go to **KEYS** tab
   - Click **ADD KEY > Create new key**
   - Select **JSON**
   - Click **CREATE**
   - The JSON key file will download automatically

5. **Configure the application**:

   **Option A: Use JSON content directly** (recommended for deployment)
   ```bash
   # In your .env file, paste the entire JSON content
   GOOGLE_SERVICE_ACCOUNT_KEY='{"type":"service_account","project_id":"your-project",...}'
   ```

   **Option B: Use file path** (for local development)
   ```bash
   # Save the downloaded JSON file to a secure location
   # In your .env file, reference the path
   GOOGLE_SERVICE_ACCOUNT_KEY=/path/to/service-account-key.json
   ```

**Security Note**: Keep the JSON key file secure and never commit it to version control!

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

**Check if API is enabled:**
1. Go to [Enabled APIs](https://console.cloud.google.com/apis/dashboard)
2. Search for "Vertex AI API"
3. If not found, go back to Step 1 to enable it

### Error: "Permission denied" when syncing documents

**Solution**: Verify that the VertexAI RAG service account has Viewer access to your Google Drive folder.

1. Check service account email:
   ```
   service-{PROJECT_NUMBER}@gcp-sa-vertex-rag.iam.gserviceaccount.com
   ```
2. Verify it's added to your Drive folder's sharing settings

### Error: "Could not authenticate"

**Solution**: Ensure your application's service account has the `Vertex AI User` role:

1. Go to [IAM Permissions](https://console.cloud.google.com/iam-admin/iam)
2. Find your service account in the list
3. Check the "Role" column - you should see **Vertex AI User**
4. If missing, click the pencil icon to edit and add the role (see Step 3)

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

### Google Cloud Console Links

- **Project Dashboard**: [https://console.cloud.google.com/home/dashboard](https://console.cloud.google.com/home/dashboard)
- **Enable Vertex AI API**: [https://console.cloud.google.com/apis/library/aiplatform.googleapis.com](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com)
- **IAM & Admin**: [https://console.cloud.google.com/iam-admin/iam](https://console.cloud.google.com/iam-admin/iam)
- **Service Accounts**: [https://console.cloud.google.com/iam-admin/serviceaccounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
- **Enabled APIs**: [https://console.cloud.google.com/apis/dashboard](https://console.cloud.google.com/apis/dashboard)

### Documentation

- [VertexAI RAG Overview](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview)
- [VertexAI RAG Quickstart](https://cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-quickstart)
- [Google Drive API Setup](https://developers.google.com/drive/api/guides/enable-sdk)
- [Service Account Keys](https://cloud.google.com/iam/docs/keys-create-delete)

## Next Steps

Once VertexAI RAG is configured:

1. **Test queries** in your Slack workspace
2. **Monitor performance** via the `/status` command
3. **Adjust chunking** if needed (see `drive_sync_service.py`)
4. **Scale up** - VertexAI can handle 10,000+ documents
