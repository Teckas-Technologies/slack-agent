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

    # Confluence Configuration
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