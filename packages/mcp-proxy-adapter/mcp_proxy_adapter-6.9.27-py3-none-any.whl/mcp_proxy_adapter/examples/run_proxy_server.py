#!/usr/bin/env python3
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Lightweight local proxy server for MCP Proxy Adapter examples.

This server provides proxy registration endpoints at /proxy for adapter instances
to register/unregister/heartbeat and for simple discovery.
"""

import argparse
import asyncio
import signal
import sys
from typing import Dict, List, Optional
import json
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mcp_proxy_adapter.core.server_adapter import UnifiedServerRunner


# Simple in-memory storage for registered adapters
registered_adapters: Dict[str, Dict] = {}


class AdapterRegistration(BaseModel):
    name: str
    url: str
    capabilities: List[str]
    metadata: Optional[Dict] = {}


class ProxyRouter:
    """Simple proxy router for MCP examples."""

    def __init__(self):
        self.app = FastAPI(title="MCP Local Proxy", version="1.0.0")
        self._setup_routes()

    def _setup_routes(self):
        @self.app.post("/register")
        async def register_adapter(registration_data: dict):
            """Register an adapter with the proxy."""
            # Handle adapter format: server_id, server_url, server_name
            adapter_id = registration_data["server_id"]
            name = registration_data.get("server_name", adapter_id)
            url = registration_data["server_url"]
            capabilities = registration_data.get("capabilities", [])
            metadata = {
                "description": registration_data.get("description", ""),
                "version": registration_data.get("version", ""),
                "endpoints": registration_data.get("endpoints", {})
            }
            
            registered_adapters[adapter_id] = {
                "name": name,
                "url": url,
                "capabilities": capabilities,
                "metadata": metadata,
                "registered_at": datetime.now().isoformat(),
                "last_heartbeat": datetime.now().isoformat(),
                "status": "active",
            }
            print(f"✅ Registered adapter: {adapter_id} at {url}")
            return {"status": "registered", "adapter_id": adapter_id, "success": True}

        @self.app.post("/unregister")
        async def unregister_adapter(adapter_id: str):
            """Unregister an adapter from the proxy."""
            if adapter_id in registered_adapters:
                del registered_adapters[adapter_id]
                print(f"✅ Unregistered adapter: {adapter_id}")
                return {"status": "unregistered", "adapter_id": adapter_id}
            else:
                raise HTTPException(status_code=404, detail="Adapter not found")

        @self.app.get("/proxy/list")
        async def list_adapters():
            """List all registered adapters."""
            return {
                "adapters": list(registered_adapters.values()),
                "count": len(registered_adapters),
            }

        @self.app.get("/proxy/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "adapters_count": len(registered_adapters),
            }

        @self.app.post("/proxy/heartbeat")
        async def heartbeat(adapter_id: str):
            """Receive heartbeat from adapter."""
            if adapter_id in registered_adapters:
                registered_adapters[adapter_id][
                    "last_heartbeat"
                ] = datetime.now().isoformat()
                return {"status": "ok", "adapter_id": adapter_id}
            else:
                raise HTTPException(status_code=404, detail="Adapter not found")


def create_proxy_app() -> FastAPI:
    """Create FastAPI app with proxy endpoints."""
    router = ProxyRouter()
    return router.app


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run local proxy server for MCP examples"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=3004, help="Port to bind to (default: 3004)"
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Log level",
    )

    args = parser.parse_args()

    # Create FastAPI app
    app = create_proxy_app()

    # Setup graceful shutdown
    def signal_handler(signum, frame):
        print("\n🛑 Shutting down proxy server...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("🚀 Starting MCP Local Proxy Server...")
    print(f"📡 Server URL: http://{args.host}:{args.port}")
    print(f"🔗 Proxy endpoints available at: http://{args.host}:{args.port}/proxy")
    print("📋 Supported endpoints:")
    print("   POST /proxy/register    - Register adapter")
    print("   POST /proxy/unregister  - Unregister adapter")
    print("   GET  /proxy/list        - List registered adapters")
    print("   GET  /proxy/health      - Health check")
    print("   POST /proxy/heartbeat   - Heartbeat from adapter")
    print("⚡ Press Ctrl+C to stop\n")

    # Run server via unified runner (hypercorn under the hood)
    runner = UnifiedServerRunner()
    runner.run_server(
        app,
        {
            "host": args.host,
            "port": args.port,
            "log_level": args.log_level,
        },
    )


if __name__ == "__main__":
    main()
