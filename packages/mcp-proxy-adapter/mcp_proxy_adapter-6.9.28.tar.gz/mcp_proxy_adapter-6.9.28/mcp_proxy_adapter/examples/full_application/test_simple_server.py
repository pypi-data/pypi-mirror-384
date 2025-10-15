#!/usr/bin/env python3
"""
Simple server test without complex lifespan.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_proxy_adapter.api.app import create_app
from mcp_proxy_adapter.config import Config
import uvicorn

def main():
    """Test simple server startup."""
    print("🚀 Testing Simple Server Startup")
    print("=" * 50)
    
    # Load configuration
    config_path = "configs/http_simple_correct.json"
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return 1
    
    try:
        # Load config
        config = Config()
        config.load_from_file(config_path)
        app_config = config.get_all()
        
        print(f"✅ Configuration loaded: {config_path}")
        print(f"🔍 Config keys: {list(app_config.keys())}")
        
        # Create app
        app = create_app(
            title="Test Server",
            description="Simple test server",
            version="1.0.0",
            app_config=app_config
        )
        
        print("✅ FastAPI app created successfully")
        
        # Start server
        print("🚀 Starting server on http://0.0.0.0:8000")
        print("📡 Test with: curl -X POST http://localhost:8000/api/jsonrpc -H 'Content-Type: application/json' -d '{\"jsonrpc\": \"2.0\", \"method\": \"health\", \"id\": 1}'")
        print("🛑 Press Ctrl+C to stop")
        
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
