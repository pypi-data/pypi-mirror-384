"""
Signal handler for graceful shutdown with proxy unregistration.

This module provides signal handling for SIGTERM, SIGINT, and SIGHUP
to ensure proper proxy unregistration before server shutdown.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import signal
import asyncio
import threading
from typing import Optional, Callable, Any
from mcp_proxy_adapter.core.logging import get_global_logger


class SignalHandler:
    """
    Signal handler for graceful shutdown with proxy unregistration.
    """
    
    def __init__(self):
        """Initialize signal handler."""
        self._shutdown_callback: Optional[Callable] = None
        self._shutdown_event = threading.Event()
        self._original_handlers = {}
        self._setup_signal_handlers()
    
    def set_shutdown_callback(self, callback: Callable):
        """
        Set callback function to be called during shutdown.
        
        Args:
            callback: Function to call during shutdown
        """
        self._shutdown_callback = callback
        get_global_logger().info("Shutdown callback set for signal handler")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        # Handle SIGTERM (termination signal)
        self._original_handlers[signal.SIGTERM] = signal.signal(
            signal.SIGTERM, self._handle_shutdown_signal
        )
        
        # Handle SIGINT (Ctrl+C)
        self._original_handlers[signal.SIGINT] = signal.signal(
            signal.SIGINT, self._handle_shutdown_signal
        )
        
        # Handle SIGHUP (hangup signal)
        self._original_handlers[signal.SIGHUP] = signal.signal(
            signal.SIGHUP, self._handle_shutdown_signal
        )
        
        get_global_logger().info("Signal handlers installed for SIGTERM, SIGINT, SIGHUP")
    
    def _handle_shutdown_signal(self, signum: int, frame: Any):
        """
        Handle shutdown signals.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        signal_name = signal.Signals(signum).name
        get_global_logger().info(f"🛑 Received {signal_name} signal, initiating graceful shutdown...")
        
        # Set shutdown event
        self._shutdown_event.set()
        
        # Call shutdown callback if set
        if self._shutdown_callback:
            try:
                get_global_logger().info("🔄 Executing shutdown callback...")
                self._shutdown_callback()
                get_global_logger().info("✅ Shutdown callback completed successfully")
            except Exception as e:
                get_global_logger().error(f"❌ Shutdown callback failed: {e}")
        
        # Force exit immediately to avoid server hang
        get_global_logger().info("🔄 Force exiting to avoid server hang...")
        import os
        # Use os._exit for immediate termination
        get_global_logger().warning("⚠️ Using os._exit for immediate termination...")
        os._exit(0)
    
    def _force_exit(self):
        """Force exit if graceful shutdown takes too long."""
        if self._shutdown_event.is_set():
            get_global_logger().warning("⚠️ Forcing exit after timeout")
            import os
            os._exit(1)
    
    def wait_for_shutdown(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for shutdown signal.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if shutdown signal received, False if timeout
        """
        return self._shutdown_event.wait(timeout)
    
    def is_shutdown_requested(self) -> bool:
        """
        Check if shutdown has been requested.
        
        Returns:
            True if shutdown signal received
        """
        return self._shutdown_event.is_set()
    
    def restore_handlers(self):
        """Restore original signal handlers."""
        for sig, handler in self._original_handlers.items():
            if handler is not None:
                signal.signal(sig, handler)
        get_global_logger().info("Original signal handlers restored")


# Global signal handler instance
_signal_handler: Optional[SignalHandler] = None


def get_signal_handler() -> SignalHandler:
    """Get the global signal handler instance."""
    global _signal_handler
    if _signal_handler is None:
        _signal_handler = SignalHandler()
    return _signal_handler


def setup_signal_handling(shutdown_callback: Optional[Callable] = None):
    """
    Setup signal handling for graceful shutdown.
    
    Args:
        shutdown_callback: Optional callback to execute during shutdown
    """
    handler = get_signal_handler()
    if shutdown_callback:
        handler.set_shutdown_callback(shutdown_callback)
    get_global_logger().info("Signal handling setup completed")


def wait_for_shutdown_signal(timeout: Optional[float] = None) -> bool:
    """
    Wait for shutdown signal.
    
    Args:
        timeout: Maximum time to wait in seconds
        
    Returns:
        True if shutdown signal received, False if timeout
    """
    handler = get_signal_handler()
    return handler.wait_for_shutdown(timeout)


def is_shutdown_requested() -> bool:
    """
    Check if shutdown has been requested.
    
    Returns:
        True if shutdown signal received
    """
    handler = get_signal_handler()
    return handler.is_shutdown_requested()
