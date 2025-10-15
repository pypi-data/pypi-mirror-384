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
        ps_result = subprocess.run(
            ["ps", "-o", "user:20,pid,cmd", "-C", "deluged"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        if ps_result.returncode != 0:
            logger.warning("No deluged process found")
            return None
        
        lines = ps_result.stdout.strip().split('\n')[1:]  # Skip header "USER PID CMD"
        if not lines:
            logger.warning("No deluge processes found")
            return None
        
        # Look for a process line with "config" in it first, then fall back to first process
        selected_line = None
        for line in lines:
            if "config" in line.lower():
                selected_line = line
                break
        
        # Fall back to first process line if no config-specific line found
        if not selected_line:
            selected_line = lines[0]  # First actual process (header already skipped)
        
        # Parse the selected line
        line_parts = selected_line.split(None, 2)  # Split into user, pid, cmd
        if len(line_parts) < 3:
            logger.warning("Could not parse deluge process info")
            return None
            
        deluge_user = line_parts[0].strip()
        cmd_line = line_parts[2].strip()
        
        logger.debug(f"Found deluge running as user: {deluge_user}")
        logger.debug(f"Command line: {cmd_line}")
        
        # Parse config directory from command line
        config_dir = None
        cmd_parts = cmd_line.split()
        
        for i, part in enumerate(cmd_parts):
            # Look for -c or --config
            if part == "-c" and i + 1 < len(cmd_parts):
                config_dir = cmd_parts[i + 1]
                break
            elif part.startswith("--config="):
                config_dir = part.split("=", 1)[1]
                break
        
        # Default config location if not specified
        if not config_dir:
            config_dir = f"/home/{deluge_user}/.config/deluge"
        
        # Handle relative paths and strip trailing slashes
        config_dir = config_dir.rstrip('/')
        if not config_dir.startswith('/'):
            # Relative path, make it absolute
            config_dir = f"/home/{deluge_user}/{config_dir}"
        
        logger.debug(f"Config directory: {config_dir}")
        
        # Read auth file
        auth_file = Path(config_dir) / "auth"
        if not auth_file.exists():
            logger.warning(f"Auth file not found: {auth_file}")
            return None
        
        # Read auth file as the deluge user (or try as current user if same)
        try:
            if deluge_user == os.getenv('USER'):
                # Same user, read directly
                with open(auth_file, 'r') as f:
                    auth_content = f.read()
            else:
                # Different user, use sudo
                auth_result = subprocess.run(
                    ["sudo", "-u", deluge_user, "cat", str(auth_file)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                auth_content = auth_result.stdout
        except Exception as e:
            logger.warning(f"Could not read auth file: {e}")
            return None
        
        # Parse auth file (format: username:password:level)
        for line in auth_content.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(':')
                if len(parts) >= 2:
                    auth_user = parts[0]
                    auth_pass = parts[1]
                    
                    # Extract port from command line or use default
                    port = "58846"  # Default deluge port
                    for i, part in enumerate(cmd_parts):
                        if part == "--port" and i + 1 < len(cmd_parts):
                            port = cmd_parts[i + 1]
                            break
                        elif part.startswith("--port="):
                            port = part.split("=", 1)[1]
                            break
                    
                    host = "127.0.0.1"
                    
                    _deluge_connection = (deluge_user, host, port, auth_user, auth_pass)
                    logger.debug(f"Found auth: user={auth_user}, host={host}:{port}, config={config_dir}")
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

        # Return combined stdout and stderr since deluge-console exit codes are unreliable
        output_parts = []
        if stdout_text:
            output_parts.append(stdout_text)
        if stderr_text:
            output_parts.append(f"STDERR: {stderr_text}")
        
        if output_parts:
            combined_output = "\n".join(output_parts)
            logger.debug(f"Combined output length: {len(combined_output)}")
            return combined_output
        else:
            # No output at all
            logger.warning("No output from deluge-console command")
            return "No output from deluge-console"

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


@mcp.tool()
async def remove_torrent(torrent_id: str, dry_run: bool = True) -> str:
    """
    Remove a torrent from Deluge (data files are preserved).
    
    Args:
        torrent_id: The torrent ID or name to remove
        dry_run: If True (default), only shows what would be removed. If False, actually removes the torrent.
    
    Returns:
        Success message with removal details
    """
    logger.info(f"Removing torrent: {torrent_id} (dry_run={dry_run})")
    
    if dry_run:
        # Dry run: just check what will be removed (without any confirmation flags)
        check_command = f"rm {torrent_id}"
        
        logger.debug(f"Dry run - checking what will be removed: {check_command}")
        check_output = await run_deluge_command(check_command)
        
        return f"DRY RUN - Would remove the following torrents (data preserved):\n\n{check_output}\n\nTo actually remove, set dry_run=False"
    else:
        # Actual removal with --confirm flag
        confirm_command = f"rm {torrent_id} --confirm"
        
        logger.debug(f"Actually removing torrent: {confirm_command}")
        removal_output = await run_deluge_command(confirm_command)
        
        return f"Torrent removed successfully (data preserved)!\n\nRemoval result:\n{removal_output}"


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
    