import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Slack Configuration
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
    
    # AI Services
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    
    # Google Drive Configuration
    GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")
    GOOGLE_DRIVE_DELEGATED_USER = os.getenv("GOOGLE_DRIVE_DELEGATED_USER")  # For domain-wide delegation

    # Google Cloud VertexAI Configuration
    GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
    GCP_LOCATION = os.getenv("GCP_LOCATION", "europe-west1")  # Default to europe-west1
    VERTEX_RAG_CORPUS_NAME = os.getenv("VERTEX_RAG_CORPUS_NAME", "google_drive_documents")

    # RAG Configuration
    USE_VERTEX_AI_RAG = os.getenv("USE_VERTEX_AI_RAG", "true").lower() == "true"  # Default to VertexAI RAG

    # VertexAI RAG Import Mode
    # Option 1: Specific folders (RECOMMENDED - auto-detects new files in these folders)
    # Provide comma-separated list of Google Drive folder IDs
    GOOGLE_DRIVE_FOLDER_IDS = os.getenv("GOOGLE_DRIVE_FOLDER_IDS", "")  # e.g., "abc123,def456"

    # Option 2: Full Drive access (if GOOGLE_DRIVE_FOLDER_IDS is empty)
    # Set to "true" to import ALL accessible Drive files
    # Note: This mode requires periodic sync to discover new files
    VERTEX_RAG_FULL_DRIVE = os.getenv("VERTEX_RAG_FULL_DRIVE", "false").lower() == "true"

    # Confluence Configuration (legacy - can be removed if not needed)
    CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
    CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME")
    CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
    CONFLUENCE_SPACES = os.getenv("CONFLUENCE_SPACES")  # Comma-separated list of space keys
    
    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Database Configuration
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    
    @classmethod
    def validate_required(cls):
        """Validate that required environment variables are set"""
        required_vars = []
        
        # Check Slack credentials
        if not cls.SLACK_BOT_TOKEN:
            required_vars.append("SLACK_BOT_TOKEN")
        if not cls.SLACK_SIGNING_SECRET:
            required_vars.append("SLACK_SIGNING_SECRET")
            
        # Check AI service credentials (at least one required)
        if not cls.OPENAI_API_KEY and not cls.ANTHROPIC_API_KEY:
            required_vars.append("OPENAI_API_KEY or ANTHROPIC_API_KEY")
            
        if required_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(required_vars)}")
        
        return True