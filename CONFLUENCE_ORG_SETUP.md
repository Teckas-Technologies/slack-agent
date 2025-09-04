# Confluence Organization-Wide Setup

## Overview
The Slack Document Agent is now configured for **organization-wide Confluence access** instead of user-specific access. This provides better control and security for team environments.

## Configuration

### 1. Service Account Approach (Recommended)
Instead of using individual user credentials, create a dedicated service account:

1. **Create a dedicated Confluence user** (e.g., `document-bot@company.com`)
2. **Grant appropriate permissions** to organization spaces
3. **Generate API token** for this service account
4. **Configure specific spaces** the bot should access

### 2. Environment Variables

```bash
# Organization-wide Confluence configuration
CONFLUENCE_BASE_URL=https://your-company.atlassian.net
CONFLUENCE_USERNAME=document-bot@company.com
CONFLUENCE_API_TOKEN=your-api-token-here
CONFLUENCE_SPACES=PROJ,DOCS,KB,TEAM,HR,LEGAL  # Your organization space keys
```

### 3. Finding Your Space Keys

Space keys are the short identifiers for Confluence spaces:

- Go to your Confluence space
- Look at the URL: `https://company.atlassian.net/wiki/spaces/PROJ/overview`
- The space key is `PROJ`

Common space key examples:
- `PROJ` - Project Documentation
- `DOCS` - General Documentation
- `KB` - Knowledge Base
- `TEAM` - Team Space
- `HR` - Human Resources
- `LEGAL` - Legal Documents
- `PROD` - Product Documentation

### 4. Space Permissions

Ensure the service account has **VIEW** permissions for all specified spaces:

1. Go to each Confluence space
2. Click **Space Settings** → **Permissions**
3. Add the service account user with **View** permission
4. Remove individual user dependencies

## Benefits

✅ **Controlled Access** - Only access specified organization spaces
✅ **Team Independence** - Not tied to individual user accounts  
✅ **Better Security** - Dedicated service account with minimal permissions
✅ **Easier Management** - Centralized space configuration
✅ **Audit Trail** - Clear bot activity tracking

## Migration from User-Specific

If you're migrating from user-specific setup:

1. **Create service account** in Confluence
2. **Update environment variables** with new credentials
3. **Specify organization spaces** in `CONFLUENCE_SPACES`
4. **Grant permissions** to service account
5. **Test access** with `/refresh` command

## Troubleshooting

**No documents found:**
- Check space keys are correct
- Verify service account has permissions
- Ensure API token is valid

**Access denied:**
- Grant VIEW permissions to service account
- Check API token permissions
- Verify Confluence URL format

**Some spaces missing:**
- Add space keys to `CONFLUENCE_SPACES`
- Check space exists and is accessible
- Verify space key spelling (case-sensitive)