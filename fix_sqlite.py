"""
Fix SQLite version for ChromaDB on Azure App Service
This must be imported BEFORE chromadb
"""

import sys

# Replace sqlite3 with pysqlite3 to get newer SQLite version
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    print("✅ Using pysqlite3 for ChromaDB compatibility")
except ImportError:
    print("⚠️  pysqlite3 not available, using system sqlite3")
