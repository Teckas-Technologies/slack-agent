#!/usr/bin/env python3
"""
Quick script to check VertexAI RAG corpus regions
"""
import os
import json
import vertexai
from vertexai.preview import rag
from google.oauth2 import service_account

# Load credentials
service_account_key = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY', '')
if service_account_key and service_account_key.strip().startswith('{'):
    service_account_info = json.loads(service_account_key)
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
else:
    credentials = None

project_id = os.getenv("GCP_PROJECT_ID", "slack-agent-470909")
location = os.getenv("GCP_LOCATION", "europe-west1")

print(f"Project ID: {project_id}")
print(f"Configured Location: {location}")
print("=" * 60)

# Check multiple regions
regions_to_check = ["us-central1", "europe-west1", "asia-southeast1"]

for region in regions_to_check:
    print(f"\n🔍 Checking region: {region}")
    try:
        # Initialize VertexAI for this region
        vertexai.init(
            project=project_id,
            location=region,
            credentials=credentials
        )

        # List corpora
        corpora = list(rag.list_corpora())

        if corpora:
            print(f"✅ Found {len(corpora)} corpus/corpora:")
            for corpus in corpora:
                print(f"   - Name: {corpus.name}")
                print(f"     Display Name: {corpus.display_name}")
                if hasattr(corpus, 'create_time'):
                    print(f"     Created: {corpus.create_time}")

                # Try to count files
                try:
                    files = list(rag.list_files(corpus_name=corpus.name))
                    print(f"     Files: {len(files)}")
                except Exception as e:
                    print(f"     Files: Could not count ({str(e)[:50]}...)")
        else:
            print(f"   No corpora found in {region}")

    except Exception as e:
        print(f"❌ Error checking {region}: {str(e)[:100]}")

print("\n" + "=" * 60)
print("Recommendation:")
print(f"  Use the region where your corpus exists, or")
print(f"  Use 'us-central1' if creating new (most stable)")
