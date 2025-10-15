"""
Module with utility functions for the microservice.
"""

import hashlib
import json
import os
import socket
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from mcp_proxy_adapter.core.logging import get_global_logger


def generate_id() -> str:
    """
    Generates a unique identifier.

    Returns:
        String with unique identifier.
    """
    return str(uuid.uuid4())


def get_timestamp() -> int:
    """
    Returns current timestamp in milliseconds.

    Returns:
        Integer - timestamp in milliseconds.
    """
    return int(time.time() * 1000)


def format_datetime(
    dt: Optional[datetime] = None, format_str: str = "%Y-%m-%dT%H:%M:%S.%fZ"
) -> str:
    """
    Formats date and time as string.

    Args:
        dt: Datetime object to format. If None, current time is used.
        format_str: Format string for output.

    Returns:
        Formatted date/time string.
    """
    dt = dt or datetime.now(timezone.utc)
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%dT%H:%M:%S.%fZ") -> datetime:
    """
    Parses date/time string into datetime object.

    Args:
        dt_str: Date/time string.
        format_str: Date/time string format.

    Returns:
        Datetime object.
    """
    return datetime.strptime(dt_str, format_str)


def safe_json_loads(s: str, default: Any = None) -> Any:
    """
    Safe JSON string loading.

    Args:
        s: JSON string to load.
        default: Default value on parsing error.

    Returns:
        Loaded object or default value on error.
    """
    try:
        return json.loads(s)
    except Exception as e:
        get_global_logger().error(f"Error parsing JSON: {e}")
        return default


def safe_json_dumps(obj: Any, default: str = "{}", indent: Optional[int] = None) -> str:
    """
    Safe object conversion to JSON string.

    Args:
        obj: Object to convert.
        default: Default string on serialization error.
        indent: Indentation for JSON formatting.

    Returns:
        JSON string or default string on error.
    """
    try:
        return json.dumps(obj, ensure_ascii=False, indent=indent)
    except Exception as e:
        get_global_logger().error(f"Error serializing to JSON: {e}")
        return default


def calculate_hash(data: Union[str, bytes], algorithm: str = "sha256") -> str:
    """
    Calculates hash for data.

    Args:
        data: Data to hash (string or bytes).
        algorithm: Hashing algorithm (md5, sha1, sha256, etc.).

    Returns:
        String with hash in hexadecimal format.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data)
    return hash_obj.hexdigest()


def ensure_directory(path: str) -> bool:
    """
    Checks directory existence and creates it if necessary.

    Args:
        path: Path to directory.

    Returns:
        True if directory exists or was successfully created, otherwise False.
    """
    try:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        get_global_logger().error(f"Error creating directory {path}: {e}")
        return False


def check_port_availability(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    Checks if a port is available for binding.
    
    Args:
        host: Host address to check
        port: Port number to check
        timeout: Connection timeout in seconds
        
    Returns:
        True if port is available, False if port is in use
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            return result != 0  # True if connection failed (port is free)
    except Exception as e:
        get_global_logger().warning(f"Error checking port {port} on {host}: {e}")
        return True  # Assume port is available if check fails


def find_available_port(host: str, start_port: int, max_attempts: int = 100) -> Optional[int]:
    """
    Finds an available port starting from the specified port.
    
    Args:
        host: Host address to check
        start_port: Starting port number
        max_attempts: Maximum number of ports to check
        
    Returns:
        Available port number or None if no port found
    """
    for port in range(start_port, start_port + max_attempts):
        if check_port_availability(host, port):
            return port
    return None


def get_port_usage_info(port: int) -> str:
    """
    Gets information about what process is using a port.
    
    Args:
        port: Port number to check
        
    Returns:
        String with port usage information
    """
    try:
        import subprocess
        result = subprocess.run(
            ["lsof", "-i", f":{port}"], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return f"Port {port} is used by:\n{result.stdout.strip()}"
        else:
            return f"Port {port} appears to be in use but process info unavailable"
    except Exception as e:
        return f"Port {port} is in use (unable to get process info: {e})"


def handle_port_conflict(host: str, port: int) -> None:
    """
    Handles port conflict with user-friendly error message and suggestions.
    This is for MAIN server port conflicts - application must exit.
    
    Args:
        host: Host address
        port: Port number that's in conflict
    """
    print(f"❌ ERROR: Port {port} is already in use on {host}")
    print(f"💡 Suggestions:")
    print(f"   1. Choose a different port: --port <different_port>")
    print(f"   2. Stop the conflicting service")
    print(f"   3. Check what's using the port:")
    print(f"      lsof -i :{port}")
    print(f"      netstat -tulpn | grep :{port}")
    
    # Try to get more detailed info about port usage
    usage_info = get_port_usage_info(port)
    print(f"🔍 Port usage details:")
    print(f"   {usage_info}")
    
    # Try to find an alternative port
    alt_port = find_available_port(host, port + 1, 10)
    if alt_port:
        print(f"💡 Alternative port suggestion: {alt_port}")
        print(f"   Try: --port {alt_port}")
    else:
        print(f"💡 Try ports in range {port + 1}-{port + 20}")
    
    print(f"🛑 Application cannot start due to port conflict")
    sys.exit(1)


def find_port_for_internal_server(host: str, preferred_port: int) -> int:
    """
    Finds an available port for internal server (mTLS, etc.).
    If preferred port is occupied, finds any available port.
    
    Args:
        host: Host address
        preferred_port: Preferred port number
        
    Returns:
        Available port number
    """
    # First try the preferred port
    if check_port_availability(host, preferred_port):
        print(f"✅ Internal server port {preferred_port} is available")
        return preferred_port
    
    # If preferred port is occupied, find any available port
    print(f"⚠️  Internal server preferred port {preferred_port} is occupied, searching for alternative...")
    
    alt_port = find_available_port(host, preferred_port + 1, 50)
    if alt_port:
        print(f"✅ Found alternative port for internal server: {alt_port}")
        return alt_port
    
    # If no port found in range, try from 9000
    alt_port = find_available_port(host, 9000, 100)
    if alt_port:
        print(f"✅ Found alternative port for internal server: {alt_port}")
        return alt_port
    
    # Last resort - try from 10000
    alt_port = find_available_port(host, 10000, 100)
    if alt_port:
        print(f"✅ Found alternative port for internal server: {alt_port}")
        return alt_port
    
    # If still no port found, raise error
    raise RuntimeError(f"Unable to find available port for internal server on {host}")
