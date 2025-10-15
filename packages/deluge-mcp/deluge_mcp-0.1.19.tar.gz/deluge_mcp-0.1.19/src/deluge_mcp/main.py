#!/usr/bin/env python3
import asyncio
import logging
import sys
import os
import subprocess
from pathlib import Path

from fastmcp import FastMCP

# Configure logging with more detail for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger("deluge-mcp")

# Create the FastMCP server
mcp = FastMCP("deluge-mcp")

# Cache for deluge connection info
_deluge_connection = None


def get_deluge_user_and_auth():
    """
    Detect deluge user and get auth credentials.
    
    Returns:
        tuple: (username, host, port, auth_user, auth_pass) or None if not found
    """
    global _deluge_connection
    if _deluge_connection:
        return _deluge_connection
    
    try:
        # Find deluge daemon process and user
        result = subprocess.run(
            ["pgrep", "-a", "deluged"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        if result.returncode != 0:
            logger.warning("No deluged process found")
            return None
        
        # Extract user from process info
        ps_result = subprocess.run(
            ["ps", "-o", "user:20,pid,cmd", "-C", "deluged"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        if ps_result.returncode != 0:
            logger.warning("Could not get deluge process info")
            return None
        
        lines = ps_result.stdout.strip().split('\n')[1:]  # Skip header
        if not lines:
            logger.warning("No deluge processes found")
            return None
        
        # Get the first deluge user
        deluge_user = lines[0].split()[0].strip()
        logger.debug(f"Found deluge running as user: {deluge_user}")
        
        # Read auth file
        auth_file = Path(f"/home/{deluge_user}/.config/deluge/auth")
        if not auth_file.exists():
            logger.warning(f"Auth file not found: {auth_file}")
            return None
        
        # Read auth file as the deluge user
        auth_result = subprocess.run(
            ["sudo", "-u", deluge_user, "cat", str(auth_file)],
            capture_output=True,
            text=True,
            check=False,
        )
        
        if auth_result.returncode != 0:
            logger.warning(f"Could not read auth file: {auth_result.stderr}")
            return None
        
        # Parse auth file (format: username:password:level)
        for line in auth_result.stdout.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(':')
                if len(parts) >= 2:
                    auth_user = parts[0]
                    auth_pass = parts[1]
                    
                    # Default connection info
                    host = "127.0.0.1"
                    port = "58846"
                    
                    _deluge_connection = (deluge_user, host, port, auth_user, auth_pass)
                    logger.debug(f"Found auth: user={auth_user}, host={host}:{port}")
                    return _deluge_connection
        
        logger.warning("No valid auth entries found")
        return None
        
    except Exception as e:
        logger.error(f"Error getting deluge auth: {e}", exc_info=True)
        return None


async def run_deluge_command(command: str) -> str:
    """
    Run a deluge-console command asynchronously with proper authentication.

    Args:
        command: The deluge-console command to run

    Returns:
        Command output as string

    Raises:
        RuntimeError: If command fails
    """
    logger.debug(f"Running deluge command: {command}")
    
    # Get deluge connection info
    connection_info = get_deluge_user_and_auth()
    if not connection_info:
        raise RuntimeError("Could not find deluge daemon or auth credentials")
    
    deluge_user, host, port, auth_user, auth_pass = connection_info
    
    # Build the full command with connection
    full_command = f"connect {host}:{port} {auth_user} {auth_pass}; {command}"
    logger.debug(f"Full deluge command: connect {host}:{port} {auth_user} [REDACTED]; {command}")
    
    try:
        # Run as the deluge user
        process = await asyncio.create_subprocess_exec(
            "sudo", "-u", deluge_user, "deluge-console", full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()
        stdout_text = stdout.decode("utf-8").strip()
        stderr_text = stderr.decode("utf-8").strip()

        logger.debug(f"Command exit code: {process.returncode}")
        logger.debug(f"Command stdout: {stdout_text}")
        logger.debug(f"Command stderr: {stderr_text}")

        if process.returncode == 0:
            logger.debug(f"Command succeeded. Output length: {len(stdout_text)}")
            return stdout_text
        else:
            # Create comprehensive error message
            error_msg = f"deluge-console command failed (exit code {process.returncode})"
            if stderr_text:
                error_msg += f"\nSTDERR: {stderr_text}"
            if stdout_text:
                error_msg += f"\nSTDOUT: {stdout_text}"
            
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    except FileNotFoundError:
        error_msg = "deluge-console command not found. Is Deluge installed?"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Error running deluge-console: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg)


@mcp.tool()
async def get_running_torrents() -> str:
    """
    Get information about all running torrents in Deluge.
    
    Returns details like name, state, progress, speeds, etc.
    """
    logger.info("Getting running torrents")
    output = await run_deluge_command("info")
    return f"Running Torrents:\n\n{output}"


@mcp.tool()
async def add_torrent_magnet(magnet_url: str) -> str:
    """
    Add a new torrent to Deluge using a magnet URL.
    
    Args:
        magnet_url: The magnet URL of the torrent to add (must start with 'magnet:')
    
    Returns:
        Success message with torrent details
    """
    logger.info(f"Adding torrent from magnet URL")
    
    # Validate magnet URL
    if not magnet_url.startswith("magnet:"):
        raise ValueError("Invalid magnet URL. Must start with 'magnet:'")
    
    # Add the torrent
    output = await run_deluge_command(f"add {magnet_url}")
    return f"Torrent added successfully!\n\nOutput: {output}"


def main():
    """Main entry point when run as module."""
    import sys
    
    # Default to HTTP transport for service
    transport = "http"
    host = "0.0.0.0" 
    port = 58880
    
    # Parse basic arguments if provided
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--transport" and i + 1 < len(args):
            transport = args[i + 1]
            i += 2
        elif args[i] == "--host" and i + 1 < len(args):
            host = args[i + 1]
            i += 2
        elif args[i] == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
            i += 2
        else:
            i += 1
    
    logger.info(f"Starting deluge-mcp via module (transport={transport}, host={host}, port={port})")
    
    # Run with FastMCP v2 API
    if transport == "http":
        mcp.run(transport="http", port=port, host=host)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
    