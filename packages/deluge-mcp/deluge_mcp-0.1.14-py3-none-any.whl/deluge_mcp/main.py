#!/usr/bin/env python3
import asyncio
import logging
import sys

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


async def run_deluge_command(command: str) -> str:
    """
    Run a deluge-console command asynchronously.

    Args:
        command: The deluge-console command to run

    Returns:
        Command output as string

    Raises:
        RuntimeError: If command fails
    """
    logger.debug(f"Running deluge command: {command}")
    try:
        process = await asyncio.create_subprocess_exec(
            "deluge-console",
            command,
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


if __name__ == "__main__":
    mcp.run()
    