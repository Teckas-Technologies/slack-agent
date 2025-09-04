#!/bin/bash
# Use single worker to avoid ChromaDB synchronization issues
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1