#!/usr/bin/env python3
"""
Minimal server test without lifespan issues.
"""

import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from mcp_proxy_adapter.api.handlers import execute_command
import uvicorn

def main():
    """Test minimal server startup."""
    print("🚀 Testing Minimal Server Startup")
    print("=" * 50)
    
    # Create minimal FastAPI app
    app = FastAPI(
        title="Test Server",
        description="Minimal test server",
        version="1.0.0"
    )
    
    # Add health endpoint
    @app.get("/health")
    async def health():
        return {"status": "ok", "message": "Server is running"}
    
    # Add JSON-RPC endpoint
    @app.post("/api/jsonrpc")
    async def jsonrpc_endpoint(request: dict):
        try:
            # Simple health command
            if request.get("method") == "health":
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {"status": "ok", "message": "Health check passed"}
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32601, "message": "Method not found"}
                }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32603, "message": str(e)}
            }
    
    print("✅ FastAPI app created successfully")
    
    # Start server
    print("🚀 Starting server on http://0.0.0.0:8000")
    print("📡 Test with: curl -X POST http://localhost:8000/api/jsonrpc -H 'Content-Type: application/json' -d '{\"jsonrpc\": \"2.0\", \"method\": \"health\", \"id\": 1}'")
    print("🛑 Press Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
