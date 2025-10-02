#!/bin/bash
# Azure App Service startup script

echo "Starting InfoBot application..."

# Azure creates 'antenv' automatically, use it if exists
if [ -d "antenv" ]; then
    echo "Using Azure's antenv virtual environment..."
    source antenv/bin/activate
elif [ -d "venv" ]; then
    echo "Using venv virtual environment..."
    source venv/bin/activate
else
    echo "No virtual environment found, using system Python..."
fi

# Create ChromaDB directory if it doesn't exist
echo "Creating ChromaDB directory..."
mkdir -p /home/chroma_db

# Change to application directory
cd /home/site/wwwroot || cd /tmp/*/

# Start the application
echo "Starting uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1