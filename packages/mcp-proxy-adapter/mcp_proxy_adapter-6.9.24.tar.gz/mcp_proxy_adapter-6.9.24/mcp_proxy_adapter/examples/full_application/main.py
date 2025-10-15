#!/usr/bin/env python3
"""
Full Application Example
This is a complete application that demonstrates all features of MCP Proxy Adapter framework:
- Built-in commands
- Custom commands
- Dynamically loaded commands
- Built-in command hooks
- Application hooks
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""
import sys
import argparse
import logging
from pathlib import Path

# Add the framework to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from mcp_proxy_adapter.core.app_factory import create_and_run_server
from mcp_proxy_adapter.api.app import create_app
from mcp_proxy_adapter.config import Config
from mcp_proxy_adapter.commands.command_registry import CommandRegistry


class FullApplication:
    """Full application example with all framework features."""

    def __init__(self, config_path: str):
        self.config_path = config_path
        try:
            self.config = Config(config_path, validate_on_load=True)
            self.config.load_config()  # Explicitly load the configuration
            self.logger = logging.getLogger(__name__)
            self.logger.info("✅ Configuration loaded and validated successfully")
        except Exception as e:
            logging.basicConfig(level=logging.ERROR)
            self.logger = logging.getLogger(__name__)
            self.logger.error(f"❌ Configuration error: {e}")
            raise
        
        self.app = None
        self.command_registry = None
        # Setup logging
        logging.basicConfig(level=logging.INFO)

    def setup_hooks(self):
        """Setup application hooks."""
        try:
            # Import hooks
            from hooks.application_hooks import ApplicationHooks
            from hooks.builtin_command_hooks import BuiltinCommandHooks

            # Register application hooks
            self.logger.info("🔧 Setting up application hooks...")
            # Register built-in command hooks
            self.logger.info("🔧 Setting up built-in command hooks...")
            # Note: In a real implementation, these hooks would be registered
            # with the framework's hook system
            self.logger.info("✅ Hooks setup completed")
        except ImportError as e:
            self.logger.warning(f"⚠️ Could not import hooks: {e}")

    def setup_custom_commands(self):
        """Setup custom commands."""
        try:
            self.logger.info("🔧 Setting up custom commands...")
            # Import custom commands
            from commands.custom_echo_command import CustomEchoCommand
            from commands.dynamic_calculator_command import DynamicCalculatorCommand

            # Register custom commands
            # Note: In a real implementation, these would be registered
            # with the framework's command registry
            self.logger.info("✅ Custom commands setup completed")
        except ImportError as e:
            self.logger.warning(f"⚠️ Could not import custom commands: {e}")

    def setup_proxy_endpoints(self):
        """Setup proxy registration endpoints."""
        try:
            self.logger.info("🔧 Setting up proxy endpoints...")
            # Import proxy endpoints
            from proxy_endpoints import router as proxy_router

            # Add proxy router to the application
            self.app.include_router(proxy_router)
            self.logger.info("✅ Proxy endpoints setup completed")
        except ImportError as e:
            self.logger.warning(f"⚠️ Could not import proxy endpoints: {e}")

    def create_application(self):
        """Create the FastAPI application."""
        self.logger.info("🔧 Creating application...")
        # Setup hooks and commands before creating app
        self.setup_hooks()
        self.setup_custom_commands()
        # Create application with configuration
        self.app = create_app(app_config=self.config)
        # Setup proxy endpoints after app creation
        self.setup_proxy_endpoints()
        self.logger.info("✅ Application created successfully")

    def run(self, host: str = None, port: int = None, debug: bool = False):
        """Run the application using the factory method with port checking."""
        print(f"🚀 Starting Full Application Example")
        print(f"📋 Configuration: {self.config_path}")
        print(
            f"🔧 Features: Built-in commands, Custom commands, Dynamic commands, Hooks, Proxy endpoints"
        )
        print("=" * 60)
        
        # Use the factory method to create and run the server with port checking
        import asyncio
        asyncio.run(create_and_run_server(
            config_path=self.config_path,
            title="Full Application Example",
            description="Complete MCP Proxy Adapter with all features",
            version="1.0.0",
            host=host or "0.0.0.0",
            log_level="debug" if debug else "info"
        ))


def main():
    """Main entry point for the full application example."""
    parser = argparse.ArgumentParser(description="Full Application Example")
    parser.add_argument(
        "--config", "-c", required=True, help="Path to configuration file"
    )
    parser.add_argument("--host", help="Server host")
    parser.add_argument("--port", type=int, help="Server port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()
    # Create and run application
    app = FullApplication(args.config)
    app.run(host=args.host, port=args.port, debug=args.debug)


# Create global app instance for import
app = None


def get_app():
    """Get the FastAPI application instance."""
    global app
    if app is None:
        # Create a default configuration for import
        config = Config("configs/mtls_with_roles.json")  # Default config
        app_instance = FullApplication("configs/mtls_with_roles.json")
        app_instance.create_application()
        app = app_instance.app
    return app


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Proxy Adapter Full Application")
    parser.add_argument("--config", required=True, help="Path to configuration file")
    parser.add_argument("--port", type=int, help="Port to run server on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    
    args = parser.parse_args()
    
    # Create application
    app_instance = FullApplication(args.config)
    
    # Override port if specified
    if args.port:
        app_instance.config.config_data["server"]["port"] = args.port
        print(f"🔧 Overriding port to {args.port}")
    
    # Override host if specified
    if args.host:
        app_instance.config.config_data["server"]["host"] = args.host
        print(f"🔧 Overriding host to {args.host}")
    
    # Run server
    app_instance.run()

if __name__ == "__main__":
    main()
