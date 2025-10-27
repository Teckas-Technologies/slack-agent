# Document Access Setup Guide

This guide explains how to configure the Slack Agent to automatically access all documents from Google Drive and Confluence without manual configuration.

## Quick Summary

### Confluence - ✅ Already Supported!
Your Confluence integration **already supports** fetching all accessible spaces! Just leave the `CONFLUENCE_SPACES` environment variable empty.

### Google Drive - Two Options
1. **Domain-Wide Delegation** (Recommended for Google Workspace) - Access all files automatically
2. **Folder Sharing** (Current method) - Share specific folders with service account

---

## Confluence Configuration

### Fetch ALL Spaces (Recommended)

To fetch documents from **all accessible Confluence spaces**:

1. **Option A**: Leave `CONFLUENCE_SPACES` empty in your `.env` file:
   ```bash
   CONFLUENCE_SPACES=
   ```

2. **Option B**: Don't set `CONFLUENCE_SPACES` at all in your `.env` file

The system will automatically discover and index all spaces your API credentials can access.

### Fetch Specific Spaces Only

If you want to limit indexing to specific spaces:

```bash
CONFLUENCE_SPACES=DEV,PM,DOCS,TECH
```

### How to Find Your Space Keys

Run the included helper script:

```bash
python scripts/list_confluence_spaces.py
```

This will:
- List all accessible Confluence spaces
- Show space keys and names
- Display document counts for each space
- Suggest the configuration for your `.env` file

**Example output:**
```
KEY             NAME                                     TYPE
--------------------------------------------------------------------------------
DEV             Development Team                         global
PM              Product Management                       global
DOCS            Documentation                            global

Total documents across all spaces: 547
```

---

## Google Drive Configuration

### Option 1: Domain-Wide Delegation (Recommended)

**Best for**: Google Workspace organizations

**Benefits**:
- Access all files automatically
- No manual sharing required
- Automatically includes new files

**Setup**: See detailed instructions in [GOOGLE_DRIVE_SETUP.md](./GOOGLE_DRIVE_SETUP.md)

**Quick steps**:
1. Create service account in Google Cloud Console
2. Enable domain-wide delegation
3. Authorize in Google Workspace Admin Console
4. Update code with `subject` parameter
5. Done! All files are accessible

### Option 2: Folder Sharing (Current Method)

**Best for**: Personal Gmail accounts or limited scope

**How it works**:
1. Get your service account email from the JSON key file:
   ```json
   {
     "client_email": "your-service-account@project.iam.gserviceaccount.com"
   }
   ```

2. In Google Drive, share folder(s) with this email

3. **Pro Tip**: Create one main folder (e.g., "Company Docs") and share it. All subfolders and files inside will be accessible!

**Example structure**:
```
📁 Company Documents (shared with service account)
  ├── 📁 HR Documents
  ├── 📁 Engineering Docs
  ├── 📁 Product Specs
  └── 📁 Marketing Materials
```

Share only "Company Documents" folder, and everything inside becomes accessible!

---

## Current Status

### What's Already Working

1. **Confluence**:
   - ✅ Can fetch all accessible spaces
   - ✅ Pagination supported (handles large number of pages)
   - ✅ Includes page content, attachments info, and metadata

2. **Google Drive**:
   - ✅ Fetches all files service account has access to
   - ✅ Supports multiple file types (Docs, Sheets, PDF, Word, etc.)
   - ✅ Pagination supported

### What You Need to Do

#### For Confluence:
1. **To index all spaces**: Remove or empty the `CONFLUENCE_SPACES` variable in `.env`
2. **Verify**: Run `python scripts/list_confluence_spaces.py` to see what will be indexed

#### For Google Drive:
Choose one approach:

**Approach A - Domain-Wide Delegation** (if you have Google Workspace):
1. Follow the guide in [GOOGLE_DRIVE_SETUP.md](./GOOGLE_DRIVE_SETUP.md)
2. Update code to add `subject` parameter
3. Done!

**Approach B - Folder Sharing** (easier, but requires manual sharing):
1. Create a main folder in Google Drive
2. Move/organize all documents under this folder
3. Share this folder with your service account email
4. Done!

---

## Verification

### Test Confluence Access

```bash
# List all spaces you can access
python scripts/list_confluence_spaces.py

# Run refresh in Slack
/refresh
```

Check logs for:
```
INFO: No specific spaces configured - fetching ALL accessible Confluence spaces
INFO: Found X accessible Confluence spaces
INFO: Found Y documents in Confluence
```

### Test Google Drive Access

In Slack, run:
```
/refresh
```

Check logs for:
```
INFO: Found X documents in Google Drive
```

Then ask:
```
list documents
```

You should see documents from both Google Drive and Confluence.

---

## Environment Variables Reference

```bash
# Confluence - Leave empty to fetch all spaces
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net
CONFLUENCE_USERNAME=your-email@domain.com
CONFLUENCE_API_TOKEN=your-api-token
CONFLUENCE_SPACES=    # Leave empty for all spaces, or set specific ones: DEV,PM,DOCS

# Google Drive
GOOGLE_SERVICE_ACCOUNT_KEY={"type":"service_account",...}
```

---

## Troubleshooting

### Confluence

**Problem**: No documents found
- **Solution**: Check API credentials are correct
- **Solution**: Verify your user has access to the spaces
- **Solution**: Run `python scripts/list_confluence_spaces.py` to see accessible spaces

**Problem**: Only finding some spaces
- **Solution**: Check the `CONFLUENCE_SPACES` environment variable - it might be set to specific spaces

### Google Drive

**Problem**: No documents found
- **Solution**: Verify at least one folder is shared with service account email
- **Solution**: Check service account JSON key is correctly set
- **Solution**: Try sharing a folder directly and wait a few minutes

**Problem**: Getting permission errors
- **Solution**: For domain-wide delegation, verify configuration in Admin Console
- **Solution**: For folder sharing, ensure "Viewer" permission is granted

---

## Next Steps

1. **Configure your environment**:
   - Remove `CONFLUENCE_SPACES` from `.env` (or leave it empty)
   - Set up Google Drive access using one of the two methods

2. **Verify access**:
   ```bash
   python scripts/list_confluence_spaces.py
   ```

3. **Refresh documents**:
   - In Slack: `/refresh`
   - Check logs for success messages

4. **Test queries**:
   - In Slack: `list documents`
   - Try asking questions about your documents

---

## Support

If you encounter issues:

1. Check the logs for detailed error messages
2. Review the troubleshooting sections above
3. Verify all environment variables are correctly set
4. Ensure API credentials have the necessary permissions
