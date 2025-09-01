#!/usr/bin/env python3
"""
Setup script for Slack Document Agent
"""
import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def create_directories():
    """Create necessary directories"""
    directories = [
        'chroma_db',
        'logs', 
        'credentials'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def copy_env_file():
    """Copy .env.example to .env if it doesn't exist"""
    if not Path('.env').exists():
        if Path('.env.example').exists():
            subprocess.run(['cp', '.env.example', '.env'])
            print("✅ Created .env file from .env.example")
            print("⚠️  Please edit .env file with your actual credentials")
        else:
            print("❌ .env.example file not found")
    else:
        print("✅ .env file already exists")

def install_requirements():
    """Install Python requirements"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Python requirements installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install requirements")
        sys.exit(1)

def verify_installation():
    """Verify that key packages are installed"""
    required_packages = [
        'flask',
        'slack-sdk',
        'openai',
        'anthropic',
        'chromadb',
        'google-api-python-client'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is not installed")

def create_sample_credentials():
    """Create sample credential files"""
    
    # Google Service Account template
    google_sa_template = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id", 
        "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
        "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
    }
    
    sample_sa_path = Path('credentials/google-service-account-sample.json')
    if not sample_sa_path.exists():
        with open(sample_sa_path, 'w') as f:
            json.dump(google_sa_template, f, indent=2)
        print("✅ Created sample Google Service Account file")
    
def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*60)
    print("🎉 Setup Complete! Next steps:")
    print("="*60)
    print("1. Edit .env file with your actual credentials:")
    print("   - Slack Bot Token and Signing Secret")
    print("   - OpenAI or Anthropic API key")
    print("   - Google Drive credentials")
    print("   - Confluence credentials")
    print()
    print("2. For Google Drive access, either:")
    print("   - Place your service account JSON in credentials/")
    print("   - Set up OAuth2 credentials")
    print()
    print("3. Run the application:")
    print("   - Development: python app.py")
    print("   - Production: gunicorn app:app")
    print("   - Docker: docker-compose up")
    print()
    print("4. Configure your Slack app:")
    print("   - Set Event Request URL to: https://your-domain.com/slack/events")
    print("   - Subscribe to 'app_mention' and 'message.im' events")
    print("   - Add required OAuth scopes")
    print()
    print("5. Test the setup:")
    print("   - python verify_setup.py")
    print("="*60)

def main():
    """Main setup function"""
    print("🚀 Setting up Slack Document Agent...")
    print("="*50)
    
    check_python_version()
    create_directories()
    copy_env_file()
    install_requirements()
    verify_installation()
    create_sample_credentials()
    print_next_steps()

if __name__ == "__main__":
    main()