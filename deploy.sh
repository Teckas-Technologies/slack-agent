#!/bin/bash

# Deploy script for Slack Document Agent
set -e

echo "🚀 Deploying Slack Document Agent"
echo "=================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print colored output
print_status() {
    echo -e "\033[1;32m✅ $1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m⚠️  $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m❌ $1\033[0m"
}

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_status "Docker is available"

if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
print_status "Docker Compose is available"

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi
print_status ".env file found"

# Check if required environment variables are set
echo "🔍 Checking environment configuration..."
source .env

required_vars=("SLACK_BOT_TOKEN" "SLACK_SIGNING_SECRET")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        print_error "$var is not set in .env file"
        exit 1
    fi
done

# Check if at least one AI service is configured
if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ]; then
    print_error "At least one AI service (OpenAI or Anthropic) must be configured"
    exit 1
fi

print_status "Environment configuration looks good"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p chroma_db logs credentials
print_status "Directories created"

# Build and start services
echo "🏗️  Building Docker images..."
docker-compose build --no-cache

print_status "Docker images built successfully"

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🏥 Checking service health..."
if docker-compose ps | grep -q "Up"; then
    print_status "Services are running"
else
    print_error "Some services failed to start"
    echo "Checking logs:"
    docker-compose logs --tail=50
    exit 1
fi

# Test the health endpoint
echo "🔍 Testing application health..."
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    print_status "Application is healthy"
else
    print_warning "Health check failed, but service might still be starting"
fi

# Show running services
echo "📊 Service Status:"
docker-compose ps

# Print next steps
echo ""
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "Your Slack Document Agent is now running at:"
echo "🌐 http://localhost:8000"
echo "📚 Interactive API docs: http://localhost:8000/docs"
echo "📖 Alternative docs: http://localhost:8000/redoc"
echo ""
echo "Next steps:"
echo "1. Configure your Slack app Event Request URL to: https://your-domain.com/slack/events"
echo "2. Make sure your domain is accessible from the internet (use ngrok for testing)"
echo "3. Test the bot by mentioning it in a Slack channel"
echo ""
echo "Useful commands:"
echo "📋 View logs: docker-compose logs -f"
echo "🔄 Restart services: docker-compose restart"
echo "⏹️  Stop services: docker-compose down"
echo "🔧 Run verification: python verify_setup.py"
echo ""

# Optional: Set up ngrok for local testing
if command_exists ngrok; then
    read -p "🌐 Do you want to start ngrok for local testing? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚀 Starting ngrok..."
        echo "Your webhook URL will be: https://[random].ngrok.io/slack/events"
        ngrok http 8000
    fi
fi