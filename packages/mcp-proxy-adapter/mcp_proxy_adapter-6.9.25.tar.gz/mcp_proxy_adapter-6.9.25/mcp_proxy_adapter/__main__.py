"""Main entry point for MCP Proxy Adapter CLI.

This module provides a command-line interface for running
MCP Proxy Adapter applications.
"""

import sys
from pathlib import Path

# Add the current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from mcp_proxy_adapter.api.app import create_app


def main():
    """Main CLI entry point."""
    # Import and run the actual main function from main.py
    from mcp_proxy_adapter.main import main as run_server

    run_server()


if __name__ == "__main__":
    main()
