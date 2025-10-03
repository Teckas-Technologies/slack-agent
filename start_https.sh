#!/bin/bash
# Start InfoBot with HTTPS support for VM deployment

echo "Starting InfoBot with HTTPS..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Default values
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8443}"
SSL_CERT="${SSL_CERT:-./ssl_certs/cert.pem}"
SSL_KEY="${SSL_KEY:-./ssl_certs/key.pem}"

# Check if SSL certificates exist
if [ ! -f "$SSL_CERT" ] || [ ! -f "$SSL_KEY" ]; then
    echo "❌ SSL certificates not found!"
    echo "   Expected certificate: $SSL_CERT"
    echo "   Expected key: $SSL_KEY"
    echo ""
    echo "Generate certificates by running:"
    echo "   ./generate_ssl_cert.sh"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Create ChromaDB directory if it doesn't exist
mkdir -p ./chroma_db

# Start the application with SSL
echo "Starting HTTPS server..."
echo "   Host: $HOST"
echo "   Port: $PORT"
echo "   Certificate: $SSL_CERT"
echo "   Private Key: $SSL_KEY"
echo ""
echo "Access the application at: https://<your-vm-ip>:$PORT"
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app \
    --host "$HOST" \
    --port "$PORT" \
    --ssl-keyfile "$SSL_KEY" \
    --ssl-certfile "$SSL_CERT" \
    --workers 1
