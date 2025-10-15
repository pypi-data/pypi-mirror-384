#!/usr/bin/env python3
"""
MCP Proxy Adapter - Main Entry Point

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import sys
import ssl
import hypercorn.asyncio
import hypercorn.config
import asyncio
import argparse
from pathlib import Path

# Add the project root to the path only if running from source
# This allows the installed package to be used when installed via pip
if not str(Path(__file__).parent.parent) in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_proxy_adapter.api.app import create_app
from mcp_proxy_adapter.config import Config
from mcp_proxy_adapter.core.config_validator import ConfigValidator
from mcp_proxy_adapter.core.signal_handler import setup_signal_handling, is_shutdown_requested
from mcp_proxy_adapter.core.utils import (
    check_port_availability,
    handle_port_conflict,
    find_port_for_internal_server,
)


def main():
    """Main entry point for the MCP Proxy Adapter."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="MCP Proxy Adapter Server",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to configuration file",
    )
    args = parser.parse_args()

    # Load configuration
    if args.config:
        config = Config(config_path=args.config)
    else:
        config = Config()

    # Load configuration from file
    config.load_config()

    # Validate UUID configuration (mandatory)
    validator = ConfigValidator(config.get_all())
    if not validator.validate_all():
        print("❌ Configuration validation failed:")
        for error in validator.get_errors():
            print(f"   - {error}")
        sys.exit(1)
    print("✅ Configuration validation passed")

    # Setup signal handling for graceful shutdown
    def shutdown_callback():
        """Callback for graceful shutdown with proxy unregistration."""
        print("\n🛑 Graceful shutdown initiated...")
        try:
            from mcp_proxy_adapter.core.async_proxy_registration import (
                stop_async_registration,
                get_registration_status,
            )
            
            # Get final status
            final_status = get_registration_status()
            print(f"📊 Final registration status: {final_status}")
            
            # Stop async registration (this will unregister from proxy)
            stop_async_registration()
            print("✅ Proxy unregistration completed")
            
        except Exception as e:
            print(f"❌ Error during shutdown: {e}")
    
    setup_signal_handling(shutdown_callback)
    print("🔧 Signal handling configured for graceful shutdown")

    # Create application (pass config_path so reload uses same file)
    app = create_app(app_config=config.get_all(), config_path=args.config)

    # Get server configuration
    host = config.get("server.host", "0.0.0.0")
    port = config.get("server.port", 8000)

    # Check external port availability - this is critical, must exit if occupied
    print(f"🔍 Checking external server port availability: {host}:{port}")
    if not check_port_availability(host, port):
        print(f"❌ CRITICAL: External server port {port} is occupied")
        handle_port_conflict(host, port)
    print(f"✅ External server port {port} is available")

    # Get protocol and SSL configuration
    protocol = config.get("server.protocol", "http")
    verify_client = config.get("transport.verify_client", False)
    chk_hostname = config.get("transport.chk_hostname", False)
    
    # Check if mTLS is required
    is_mtls_mode = protocol == "mtls" or verify_client
    
    if is_mtls_mode:
        # mTLS mode: hypercorn on localhost, mTLS proxy on external port
        hypercorn_host = "127.0.0.1"  # localhost only
        hypercorn_port = port + 1000   # internal port
        mtls_proxy_port = port         # external port
        ssl_enabled = True
        
        # Check internal port availability (flexible - find alternative if occupied)
        print(f"🔍 Checking internal server port availability: {hypercorn_host}:{hypercorn_port}")
        if not check_port_availability(hypercorn_host, hypercorn_port):
            print(f"⚠️  Internal server preferred port {hypercorn_port} is occupied, searching for alternative...")
            hypercorn_port = find_port_for_internal_server(hypercorn_host, hypercorn_port)
            print(f"✅ Internal server will use port: {hypercorn_port}")
        else:
            print(f"✅ Internal server port {hypercorn_port} is available")
        
        print(f"🔐 mTLS Mode: hypercorn on {hypercorn_host}:{hypercorn_port}, mTLS proxy on {host}:{mtls_proxy_port}")
    else:
        # Regular mode: hypercorn on external port (no proxy needed)
        hypercorn_host = host
        hypercorn_port = port
        mtls_proxy_port = None
        ssl_enabled = protocol == "https"
        print(f"🌐 Regular Mode: hypercorn on {hypercorn_host}:{hypercorn_port}")
    
    # SSL configuration based on protocol
    ssl_cert_file = None
    ssl_key_file = None
    ssl_ca_cert = None
    
    if ssl_enabled:
        # Configure SSL certificates from configuration
        ssl_cert_file = config.get("transport.cert_file")
        ssl_key_file = config.get("transport.key_file")
        ssl_ca_cert = config.get("transport.ca_cert")
        
        # Convert relative paths to absolute paths
        project_root = Path(__file__).parent.parent
        if ssl_cert_file and not Path(ssl_cert_file).is_absolute():
            ssl_cert_file = str(project_root / ssl_cert_file)
        if ssl_key_file and not Path(ssl_key_file).is_absolute():
            ssl_key_file = str(project_root / ssl_key_file)
        if ssl_ca_cert and not Path(ssl_ca_cert).is_absolute():
            ssl_ca_cert = str(project_root / ssl_ca_cert)

    print("🔍 Debug config:")
    print(f"   protocol: {protocol}")
    print(f"   ssl_enabled: {ssl_enabled}")
    print("🔍 Source: configuration")

    print("🚀 Starting MCP Proxy Adapter")
    if mtls_proxy_port:
        print(f"🔐 mTLS Proxy: {host}:{mtls_proxy_port}")
        print(f"🌐 Internal Server: {hypercorn_host}:{hypercorn_port}")
    else:
        print(f"🌐 Server: {hypercorn_host}:{hypercorn_port}")
    print(f"🔒 Protocol: {protocol}")
    if ssl_enabled:
        print("🔐 SSL: Enabled")
        print(f"   Certificate: {ssl_cert_file}")
        print(f"   Key: {ssl_key_file}")
        if ssl_ca_cert:
            print(f"   CA: {ssl_ca_cert}")
        print(f"   Client verification: {verify_client}")
    print("=" * 50)

    # Configure hypercorn using framework
    config_hypercorn = hypercorn.config.Config()
    config_hypercorn.bind = [f"{hypercorn_host}:{hypercorn_port}"]

    if ssl_enabled and ssl_cert_file and ssl_key_file:
        # Use framework to convert SSL configuration
        from mcp_proxy_adapter.core.server_adapter import ServerConfigAdapter
        
        ssl_config = {
            "cert_file": ssl_cert_file,
            "key_file": ssl_key_file,
            "ca_cert": ssl_ca_cert,
            "verify_client": verify_client,
            "chk_hostname": chk_hostname
        }
        
        hypercorn_ssl = ServerConfigAdapter.convert_ssl_config_for_engine(ssl_config, "hypercorn")
        
        # Apply converted SSL configuration
        for key, value in hypercorn_ssl.items():
            setattr(config_hypercorn, key, value)
        
        print("🔐 SSL: Configured via framework")
        if verify_client:
            print("🔐 mTLS: Client certificate verification enabled")
        else:
            print("🔐 HTTPS: Regular HTTPS without client certificate verification")
        
        chk_hostname = ssl_config.get("chk_hostname", True)
        print(f"🔍 Hostname checking: {'enabled' if chk_hostname else 'disabled'}")

        # Prefer modern protocols
        try:
            config_hypercorn.alpn_protocols = ["h2", "http/1.1"]
        except Exception:
            pass

    # Log hypercorn configuration
    print("=" * 50)
    print("🔍 HYPERCORN CONFIGURATION:")
    print(
        "🔍 certfile="
        f"{getattr(config_hypercorn, 'certfile', None)}",
    )
    print(
        "🔍 keyfile="
        f"{getattr(config_hypercorn, 'keyfile', None)}",
    )
    print(
        "🔍 ca_certs="
        f"{getattr(config_hypercorn, 'ca_certs', None)}",
    )
    print(
        "🔍 verify_mode="
        f"{getattr(config_hypercorn, 'verify_mode', None)}",
    )
    print(
        "🔍 alpn_protocols="
        f"{getattr(config_hypercorn, 'alpn_protocols', None)}",
    )
    print("=" * 50)

    if ssl_enabled:
        print("🔐 Starting HTTPS server with hypercorn...")
    else:
        print("🌐 Starting HTTP server with hypercorn...")
    
    print("🛑 Use Ctrl+C or send SIGTERM for graceful shutdown")
    print("=" * 50)

    # Run the server
    try:
        if is_mtls_mode:
            # mTLS mode: start hypercorn and mTLS proxy
            print("🔐 Starting mTLS mode with proxy...")
            
            async def run_mtls_mode():
                # Start hypercorn server on localhost
                hypercorn_task = asyncio.create_task(
                    hypercorn.asyncio.serve(app, config_hypercorn)
                )
                
                # Start mTLS proxy on external port
                from mcp_proxy_adapter.core.mtls_proxy import start_mtls_proxy
                proxy = await start_mtls_proxy(config.get_all())
                
                if proxy:
                    print("✅ mTLS proxy started successfully")
                else:
                    print("⚠️  mTLS proxy not started, running hypercorn only")
                
                # Wait for hypercorn
                await hypercorn_task
                
            asyncio.run(run_mtls_mode())
        else:
            # Regular mode: start hypercorn only (no proxy needed)
            print("🌐 Starting regular mode...")
            asyncio.run(hypercorn.asyncio.serve(app, config_hypercorn))
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user (Ctrl+C)")
        if is_shutdown_requested():
            print("✅ Graceful shutdown completed")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
