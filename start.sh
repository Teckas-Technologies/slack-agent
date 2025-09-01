#!/bin/bash

# start.sh - Local development server startup script
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ASCII Art Banner
echo -e "${BLUE}"
cat << "EOF"
 ____  _            _      ____                                        _   
/ ___|| | __ _  ___| | __ |  _ \  ___   ___ _   _ _ __ ___   ___ _ __ | |_ 
\___ \| |/ _` |/ __| |/ / | | | |/ _ \ / __| | | | '_ ` _ \ / _ \ '_ \| __|
 ___) | | (_| | (__|   <  | |_| | (_) | (__| |_| | | | | | |  __/ | | | |_ 
|____/|_|\__,_|\___|_|\_\ |____/ \___/ \___|\__,_|_| |_| |_|\___|_| |_|\__|
                                                                            
    ___                    _     ___          _   _   ___ ___ 
   / _ \  __ _  ___ _ __  | |_  | __|__ _ ___| |_/_\ | _ \_ _|
  | (_) |/ _` |/ -_) '  \ |  _| | _/ _` (_-<|  _/ _ \|  _/| | 
   \__,_|\__, |\___|_||_| |\__| |_|\__,_/__/ \__/_/ \_\_| |___|
         |___/                                                 
EOF
echo -e "${NC}"

print_info "Starting Slack Document Agent (FastAPI)..."
echo "=========================================="

# Check Python version
print_info "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" = "$REQUIRED_VERSION" ]; then 
    print_success "Python $PYTHON_VERSION (OK)"
else
    print_error "Python $PYTHON_VERSION is too old. Need Python $REQUIRED_VERSION or higher"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found"
    
    if [ -f .env.example ]; then
        read -p "Would you like to create .env from .env.example? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp .env.example .env
            print_success "Created .env file"
            print_warning "Please edit .env file with your actual credentials"
            read -p "Press Enter to continue after editing .env file..."
        else
            print_error "Cannot start without .env file"
            exit 1
        fi
    else
        print_error ".env.example file not found. Cannot create .env"
        exit 1
    fi
else
    print_success ".env file found"
fi

# Load environment variables
print_info "Loading environment variables..."
set -a
source .env
set +a

# Check required environment variables
print_info "Checking required configuration..."
MISSING_VARS=()

# Check Slack credentials
if [ -z "$SLACK_BOT_TOKEN" ]; then
    MISSING_VARS+=("SLACK_BOT_TOKEN")
fi

if [ -z "$SLACK_SIGNING_SECRET" ]; then
    MISSING_VARS+=("SLACK_SIGNING_SECRET")
fi

# Check AI service credentials (at least one required)
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    MISSING_VARS+=("OPENAI_API_KEY or ANTHROPIC_API_KEY")
fi

# Report missing variables
if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    print_error "Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    print_warning "Please edit .env file and add the missing variables"
    exit 1
else
    print_success "All required environment variables are set"
fi

# Check optional services
print_info "Checking optional services..."

if [ ! -z "$GOOGLE_SERVICE_ACCOUNT_KEY" ]; then
    if [ -f "$GOOGLE_SERVICE_ACCOUNT_KEY" ]; then
        print_success "Google Drive configured"
    else
        print_warning "Google service account file not found: $GOOGLE_SERVICE_ACCOUNT_KEY"
    fi
else
    print_warning "Google Drive not configured (optional)"
fi

if [ ! -z "$CONFLUENCE_BASE_URL" ] && [ ! -z "$CONFLUENCE_USERNAME" ] && [ ! -z "$CONFLUENCE_API_TOKEN" ]; then
    print_success "Confluence configured"
else
    print_warning "Confluence not configured (optional)"
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p chroma_db logs credentials
print_success "Directories ready"

# Check if virtual environment exists
if [ -d "venv" ]; then
    print_info "Activating virtual environment..."
    source venv/bin/activate
    print_success "Virtual environment activated"
else
    print_warning "No virtual environment found"
    read -p "Would you like to create a virtual environment? (recommended) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        print_success "Virtual environment created and activated"
    fi
fi

# Install/upgrade dependencies
print_info "Checking Python dependencies..."
pip install -q --upgrade pip

# Check if requirements are already installed
if pip show fastapi &>/dev/null && pip show uvicorn &>/dev/null; then
    print_success "Dependencies already installed"
    read -p "Would you like to upgrade dependencies? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Upgrading dependencies..."
        pip install -q --upgrade -r requirements.txt
        print_success "Dependencies upgraded"
    fi
else
    print_info "Installing dependencies..."
    pip install -q -r requirements.txt
    print_success "Dependencies installed"
fi

# Set port
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}
WORKERS=${WORKERS:-1}

# Development or production mode
if [ "$DEBUG" = "True" ] || [ "$DEBUG" = "true" ]; then
    print_info "Starting in DEVELOPMENT mode with auto-reload..."
    RELOAD="--reload"
    LOG_LEVEL="debug"
else
    print_info "Starting in PRODUCTION mode..."
    RELOAD=""
    LOG_LEVEL="info"
    WORKERS=2
fi

# Clear screen for clean start
clear

# Display startup information
echo -e "${GREEN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     🚀 Slack Document Agent (FastAPI) - Starting...     ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

print_info "Server Configuration:"
echo "  • Host: $HOST"
echo "  • Port: $PORT"
echo "  • Workers: $WORKERS"
echo "  • Debug: ${DEBUG:-False}"
echo "  • Log Level: $LOG_LEVEL"
echo ""

print_info "AI Services:"
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "  • OpenAI: ✅ Configured"
else
    echo "  • OpenAI: ❌ Not configured"
fi

if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    echo "  • Anthropic: ✅ Configured"
else
    echo "  • Anthropic: ❌ Not configured"
fi
echo ""

print_info "Document Sources:"
if [ ! -z "$GOOGLE_SERVICE_ACCOUNT_KEY" ] && [ -f "$GOOGLE_SERVICE_ACCOUNT_KEY" ]; then
    echo "  • Google Drive: ✅ Ready"
else
    echo "  • Google Drive: ⚠️  Not configured"
fi

if [ ! -z "$CONFLUENCE_BASE_URL" ]; then
    echo "  • Confluence: ✅ Ready"
else
    echo "  • Confluence: ⚠️  Not configured"
fi
echo ""

print_success "Starting FastAPI server..."
echo ""
echo "📚 API Documentation will be available at:"
echo "  • Interactive docs: http://localhost:${PORT}/docs"
echo "  • Alternative docs: http://localhost:${PORT}/redoc"
echo "  • OpenAPI spec: http://localhost:${PORT}/openapi.json"
echo ""
echo "🔧 API Endpoints:"
echo "  • Health check: http://localhost:${PORT}/health"
echo "  • Status: http://localhost:${PORT}/status"
echo "  • Slack events: http://localhost:${PORT}/slack/events"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    print_info "Shutting down server..."
    print_success "Server stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Start the FastAPI server with uvicorn
if [ "$WORKERS" -eq 1 ]; then
    # Single worker for development
    uvicorn app:app \
        --host $HOST \
        --port $PORT \
        --log-level $LOG_LEVEL \
        $RELOAD \
        --access-log
else
    # Multiple workers for production
    uvicorn app:app \
        --host $HOST \
        --port $PORT \
        --workers $WORKERS \
        --log-level $LOG_LEVEL \
        --access-log
fi