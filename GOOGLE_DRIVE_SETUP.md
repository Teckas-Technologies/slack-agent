# Google Drive Setup Guide

This guide explains how to configure Google Drive access for the Slack Agent to automatically index all documents without manually sharing each file.

## Option 1: Domain-Wide Delegation (Recommended for Google Workspace)

Domain-wide delegation allows the service account to access all files in your Google Workspace organization without requiring individual file sharing.

### Prerequisites
- Google Workspace account (not available for personal Gmail accounts)
- Super Admin access to Google Workspace Admin Console

### Steps

#### 1. Create Service Account (if not already done)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Drive API
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"
4. Create Service Account
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the details and click "Create"
   - Skip optional steps and click "Done"
5. Create Key
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Select "JSON" and click "Create"
   - Save the JSON file securely

#### 2. Enable Domain-Wide Delegation
1. In Google Cloud Console, go to your service account
2. Click "Show Domain-Wide Delegation"
3. Check "Enable Google Workspace Domain-wide Delegation"
4. Enter a product name (e.g., "Slack Agent")
5. Click "Save"
6. **Copy the Client ID** (you'll need this in the next step)

#### 3. Configure in Google Workspace Admin Console
1. Go to [Google Workspace Admin Console](https://admin.google.com/)
2. Navigate to: Security > Access and data control > API controls
3. Click "Manage Domain Wide Delegation"
4. Click "Add new"
5. Enter the following:
   - **Client ID**: Paste the Client ID from step 2.6
   - **OAuth Scopes**: `https://www.googleapis.com/auth/drive.readonly`
6. Click "Authorize"

#### 4. Update Your Code

Modify `app/google_drive_handler.py` to use domain-wide delegation:

```python
credentials = ServiceAccountCredentials.from_service_account_info(
    service_account_info,
    scopes=['https://www.googleapis.com/auth/drive.readonly'],
    subject='admin@yourdomain.com'  # Add this line with an admin email
)
```

Or if using file path:

```python
credentials = ServiceAccountCredentials.from_service_account_file(
    service_account_key,
    scopes=['https://www.googleapis.com/auth/drive.readonly'],
    subject='admin@yourdomain.com'  # Add this line with an admin email
)
```

#### 5. Set Environment Variable
```bash
export GOOGLE_SERVICE_ACCOUNT_KEY='{"type": "service_account", ...}'
```

---

## Option 2: Share Specific Folders (Current Method)

If you don't have Google Workspace or prefer not to use domain-wide delegation, you can share specific folders with the service account.

### Steps

#### 1. Get Service Account Email
From your service account JSON key file, find the `client_email` field. It looks like:
```
your-service-account@your-project.iam.gserviceaccount.com
```

#### 2. Share Folders in Google Drive
1. Go to Google Drive
2. Right-click on the folder(s) you want to index
3. Click "Share"
4. Enter the service account email
5. Set permission to "Viewer"
6. Click "Send"

**Tip**: Instead of sharing individual files, create a main folder (e.g., "Company Documents") and share that entire folder. All files and subfolders will be accessible.

#### 3. Set Environment Variable
```bash
export GOOGLE_SERVICE_ACCOUNT_KEY='{"type": "service_account", ...}'
```

---

## Option 3: Exclude Specific Folders (Filter Approach)

If you want to fetch all accessible documents but exclude certain folders, you can add filtering logic.

### Steps

1. Set environment variable with folder IDs to exclude:
```bash
export GOOGLE_DRIVE_EXCLUDE_FOLDERS="folder_id_1,folder_id_2,folder_id_3"
```

2. The code already fetches all documents, but you can add filtering in `get_all_documents()` method.

---

## Verification

To verify your setup:

1. Run the `/refresh` command in Slack
2. Check the logs for:
   ```
   Found X documents in Google Drive
   ```
3. Use the `list documents` command to see what was indexed

---

## Troubleshooting

### "Access Denied" Errors
- Verify the service account email has access to the folders
- Check that domain-wide delegation is properly configured
- Ensure the correct OAuth scopes are authorized

### No Documents Found
- Verify at least one folder/file is shared with the service account
- Check that the service account JSON key is correct
- Enable debug logging to see detailed error messages

### Domain-Wide Delegation Not Working
- Verify you're using a Google Workspace account (not personal Gmail)
- Check that you used the correct Client ID in Admin Console
- Ensure the `subject` parameter uses a valid admin email
- Wait a few minutes for changes to propagate

---

## Best Practices

1. **Security**: Never commit service account keys to version control
2. **Permissions**: Use read-only scope (`drive.readonly`)
3. **Organization**: Create a dedicated folder structure for documents to be indexed
4. **Monitoring**: Regularly check logs to ensure indexing is working correctly
5. **Updates**: Run `/refresh` command periodically or set up automated refresh
