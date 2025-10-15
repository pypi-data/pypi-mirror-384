#!/usr/bin/env python3
"""
mTLS Server implementation using built-in http.server.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import threading
import ssl
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)


class mTLSHandler(BaseHTTPRequestHandler):
    """Handler for mTLS connections."""

    def __init__(self, *args, main_app=None, **kwargs):
        self.main_app = main_app
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Override to use our get_global_logger()."""
        get_global_logger().info(f"mTLS Server: {format % args}")

    def do_GET(self):
        """Handle GET requests."""
        try:
            # Get client certificate
            client_cert = None
            if hasattr(self.connection, "getpeercert"):
                client_cert = self.connection.getpeercert()

            # Process request through main app if available
            if self.main_app:
                # Forward to main FastAPI app
                response_data = self._forward_to_main_app(
                    "GET", self.path, client_cert
                )
            else:
                # Simple response
                response_data = {
                    "status": "ok",
                    "message": "mTLS connection successful",
                    "client_cert": client_cert,
                    "path": self.path,
                }

            # Send response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            get_global_logger().error(f"Error in mTLS GET handler: {e}")
            self.send_error(500, str(e))

    def do_POST(self):
        """Handle POST requests."""
        try:
            # Get content length
            content_length = int(self.headers.get("Content-Length", 0))

            # Read request body
            post_data = None
            if content_length > 0:
                post_data = self.rfile.read(content_length)

            # Get client certificate
            client_cert = None
            if hasattr(self.connection, "getpeercert"):
                client_cert = self.connection.getpeercert()

            # Process request through main app if available
            if self.main_app:
                # Forward to main FastAPI app
                response_data = self._forward_to_main_app(
                    "POST", self.path, client_cert, post_data
                )
            else:
                # Simple response
                response_data = {
                    "status": "ok",
                    "message": "mTLS POST successful",
                    "client_cert": client_cert,
                    "path": self.path,
                    "data_received": len(post_data) if post_data else 0,
                }

            # Send response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            get_global_logger().error(f"Error in mTLS POST handler: {e}")
            self.send_error(500, str(e))

    def _forward_to_main_app(
        self,
        method: str,
        path: str,
        client_cert: Optional[Dict],
        post_data: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Forward request to main FastAPI application."""
        try:
            # This is a simplified forwarding - in real implementation
            # you would use httpx or similar to make internal HTTP calls
            # to the main FastAPI app running on different port

            return {
                "status": "ok",
                "message": f"mTLS {method} forwarded to main app",
                "client_cert": client_cert,
                "path": path,
                "forwarded": True,
            }
        except Exception as e:
            get_global_logger().error(f"Error forwarding to main app: {e}")
            return {
                "status": "error",
                "message": f"Forwarding failed: {e}",
                "client_cert": client_cert,
                "path": path,
            }


class mTLSServer:
    """mTLS Server using built-in http.server."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8443,
        cert_file: str = None,
        key_file: str = None,
        ca_cert_file: str = None,
        main_app=None,
    ):
        """
        Initialize mTLS server.

        Args:
            host: Server host
            port: Server port
            cert_file: Server certificate file
            key_file: Server private key file
            ca_cert_file: CA certificate file for client verification
            main_app: Main FastAPI application for forwarding requests
        """
        self.host = host
        self.port = port
        self.cert_file = cert_file
        self.key_file = key_file
        self.ca_cert_file = ca_cert_file
        self.main_app = main_app

        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.running = False

        get_global_logger().info(f"mTLS Server initialized: {host}:{port}")

    def _create_handler(self):
        """Create handler with main app reference."""

        def handler(*args, **kwargs):
            return mTLSHandler(*args, main_app=self.main_app, **kwargs)

        return handler

    def start(self) -> bool:
        """Start mTLS server in separate thread."""
        try:
            # Check if certificate files exist
            if not os.path.exists(self.cert_file):
                get_global_logger().error(f"Certificate file not found: {self.cert_file}")
                return False

            if not os.path.exists(self.key_file):
                get_global_logger().error(f"Key file not found: {self.key_file}")
                return False

            if not os.path.exists(self.ca_cert_file):
                get_global_logger().error(
                    f"CA certificate file not found: {self.ca_cert_file}"
                )
                return False

            # Create server
            handler_class = self._create_handler()
            self.server = HTTPServer((self.host, self.port), handler_class)

            # Configure SSL context
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(self.cert_file, self.key_file)
            context.load_verify_locations(self.ca_cert_file)
            context.verify_mode = ssl.CERT_REQUIRED

            # Wrap socket with SSL
            self.server.socket = context.wrap_socket(
                self.server.socket, server_side=True
            )

            # Start server in separate thread
            self.server_thread = threading.Thread(
                target=self._run_server, daemon=True
            )
            self.server_thread.start()

            self.running = True
            get_global_logger().info(
                f"✅ mTLS Server started on https://{self.host}:{self.port}"
            )
            return True

        except Exception as e:
            get_global_logger().error(f"Failed to start mTLS server: {e}")
            return False

    def _run_server(self):
        """Run the server (blocking)."""
        try:
            get_global_logger().info(
                f"mTLS Server listening on https://{self.host}:{self.port}"
            )
            self.server.serve_forever()
        except Exception as e:
            get_global_logger().error(f"mTLS Server error: {e}")
        finally:
            self.running = False

    def stop(self):
        """Stop mTLS server."""
        if self.server and self.running:
            try:
                self.server.shutdown()
                self.server.server_close()
                self.running = False
                get_global_logger().info("✅ mTLS Server stopped")
            except Exception as e:
                get_global_logger().error(f"Error stopping mTLS server: {e}")

    def is_running(self) -> bool:
        """Check if server is running."""
        return (
            self.running
            and self.server_thread
            and self.server_thread.is_alive()
        )


def start_mtls_server_thread(
    config: Dict[str, Any], main_app=None
) -> Optional[mTLSServer]:
    """
    Start mTLS server in separate thread.

    Args:
        config: Configuration dictionary
        main_app: Main FastAPI application

    Returns:
        mTLSServer instance or None if failed
    """
    try:
        # Extract SSL configuration
        ssl_config = config.get("ssl", {})

        # Check if mTLS is enabled
        verify_client = ssl_config.get("verify_client", False)
        if not verify_client:
            get_global_logger().info(
                "mTLS not enabled (verify_client=False), skipping mTLS server"
            )
            return None

        # Get server configuration
        server_config = config.get("server", {})
        host = server_config.get("host", "127.0.0.1")
        preferred_port = ssl_config.get("mtls_port", 8443)  # Different port for mTLS
        
        # For internal servers (mTLS), find available port if preferred is occupied
        from mcp_proxy_adapter.core.utils import find_port_for_internal_server
        port = find_port_for_internal_server(host, preferred_port)

        # Get certificate paths - all required for mTLS
        cert_file = ssl_config.get("cert_file")
        key_file = ssl_config.get("key_file")
        ca_cert_file = ssl_config.get("ca_cert")
        
        if not cert_file or not key_file:
            raise ValueError(
                "mTLS server requires SSL certificate configuration. "
                "Please configure 'ssl.cert_file' and 'ssl.key_file' in your configuration file."
            )

        # Create and start mTLS server
        mtls_server = mTLSServer(
            host=host,
            port=port,
            cert_file=cert_file,
            key_file=key_file,
            ca_cert_file=ca_cert_file,
            main_app=main_app,
        )

        if mtls_server.start():
            return mtls_server
        else:
            get_global_logger().error("Failed to start mTLS server")
            return None

    except Exception as e:
        get_global_logger().error(f"Error starting mTLS server thread: {e}")
        return None
