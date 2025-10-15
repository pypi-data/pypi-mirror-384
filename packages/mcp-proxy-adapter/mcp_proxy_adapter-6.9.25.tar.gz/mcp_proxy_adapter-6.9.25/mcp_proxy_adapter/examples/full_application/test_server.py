#!/usr/bin/env python3
"""
Test mTLS Server for Full Application Example
Simple HTTPS server with mTLS for testing curl commands.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import sys
import json
import ssl
import socket
import threading
import time
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

class TestMTLSHandler(BaseHTTPRequestHandler):
    """Test handler for mTLS requests."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy",
                "service": "mcp_proxy_adapter",
                "version": "6.2.33",
                "protocol": "mTLS",
                "timestamp": time.time()
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/echo':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "message": "Echo from mTLS server",
                "timestamp": time.time(),
                "client_cert": self.get_client_cert_info()
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"error": "Not found", "path": self.path}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode())
        except json.JSONDecodeError:
            data = {"raw": post_data.decode()}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "received": data,
            "timestamp": time.time(),
            "client_cert": self.get_client_cert_info(),
            "method": "POST"
        }
        self.wfile.write(json.dumps(response).encode())
    
    def get_client_cert_info(self):
        """Get client certificate information."""
        try:
            cert = self.connection.getpeercert()
            if cert:
                return {
                    "subject": dict(x[0] for x in cert.get('subject', [])),
                    "issuer": dict(x[0] for x in cert.get('issuer', [])),
                    "serial": cert.get('serialNumber'),
                    "not_before": cert.get('notBefore'),
                    "not_after": cert.get('notAfter')
                }
        except Exception:
            pass
        return None
    
    def log_message(self, format, *args):
        """Override log message to include client cert info."""
        client_cert = self.get_client_cert_info()
        if client_cert:
            print(f"[{self.address_string()}] {format % args} [Client: {client_cert.get('subject', {}).get('CN', 'Unknown')}]")
        else:
            print(f"[{self.address_string()}] {format % args} [No client cert]")

class TestMTLSServer:
    """Test mTLS server for the full application example."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self.load_config()
        self.server = None
        self.thread = None
        
    def load_config(self):
        """Load configuration from file."""
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def create_ssl_context(self):
        """Create SSL context for mTLS."""
        ssl_config = self.config.get('ssl', {})
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(
            ssl_config.get('cert_file'),
            ssl_config.get('key_file')
        )
        
        # Load CA certificate for client verification
        if ssl_config.get('verify_client', False):
            context.load_verify_locations(ssl_config.get('ca_cert_file'))
            context.verify_mode = ssl.CERT_REQUIRED
        
        # Set ciphers and protocols
        if ssl_config.get('ciphers'):
            context.set_ciphers(ssl_config['ciphers'])
        
        return context
    
    def start_server(self):
        """Start the mTLS server."""
        server_config = self.config.get('server', {})
        host = server_config.get('host', '0.0.0.0')
        port = server_config.get('port', 8443)
        
        print(f"🚀 Starting mTLS Test Server")
        print(f"📁 Configuration: {self.config_path}")
        print(f"🌐 Server: {host}:{port}")
        print(f"🔐 mTLS: {'Enabled' if self.config.get('ssl', {}).get('verify_client', False) else 'Disabled'}")
        
        # Create server
        self.server = HTTPServer((host, port), TestMTLSHandler)
        
        # Configure SSL
        ssl_context = self.create_ssl_context()
        self.server.socket = ssl_context.wrap_socket(
            self.server.socket,
            server_side=True
        )
        
        print(f"✅ mTLS Test Server started on {host}:{port}")
        print(f"🔐 SSL Context configured")
        print(f"📜 Available endpoints:")
        print(f"  - GET  /health - Health check")
        print(f"  - GET  /echo   - Echo test")
        print(f"  - POST /echo   - Echo with data")
        print(f"\n🛑 Press Ctrl+C to stop the server")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print(f"\n🛑 Server stopped by user")
            self.server.shutdown()
    
    def start_background(self):
        """Start server in background thread."""
        self.thread = threading.Thread(target=self.start_server, daemon=True)
        self.thread.start()
        time.sleep(1)  # Give server time to start
        return self.thread.is_alive()
    
    def stop_server(self):
        """Stop the server."""
        if self.server:
            self.server.shutdown()
        if self.thread:
            self.thread.join(timeout=5)

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test mTLS Server")
    parser.add_argument("--config", required=True, help="Configuration file path")
    parser.add_argument("--background", action="store_true", help="Run in background")
    args = parser.parse_args()
    
    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return 1
    
    # Create and start server
    server = TestMTLSServer(str(config_path))
    
    if args.background:
        print("🔄 Starting server in background...")
        if server.start_background():
            print("✅ Server started in background")
            print("💡 Use Ctrl+C to stop")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping background server...")
                server.stop_server()
        else:
            print("❌ Failed to start server in background")
            return 1
    else:
        server.start_server()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
