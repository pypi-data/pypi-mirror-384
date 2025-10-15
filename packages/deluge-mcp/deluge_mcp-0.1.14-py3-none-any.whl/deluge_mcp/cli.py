#!/usr/bin/env python3
import os
import platform
import subprocess
import sys
import logging
from pathlib import Path

import typer
from typing_extensions import Annotated

app = typer.Typer(
    name="deluge-mcp",
    help="Deluge MCP Server - Manage Deluge torrent client via MCP",
    add_completion=False,
)

# Get version from package
try:
    from importlib.metadata import version
    __version__ = version("deluge-mcp")
except Exception:
    __version__ = "unknown"


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        typer.echo(f"deluge-mcp version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """Deluge MCP Server - Manage Deluge torrent client via MCP."""
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("deluge-mcp")

# Configuration
SERVICE_PORT = 58880
SERVICE_VENV_PATH = Path("/opt/deluge-mcp/venv")
SERVICE_LOG_PATH = Path("/var/log/deluge-mcp")


def is_ubuntu() -> bool:
    """Check if the system is running Ubuntu or Debian-based."""
    try:
        if platform.system() != "Linux":
            return False

        # Check /etc/os-release for Ubuntu
        if Path("/etc/os-release").exists():
            with open("/etc/os-release") as f:
                content = f.read().lower()
                return "ubuntu" in content or "debian" in content

        return False
    except Exception:
        return False


def is_root() -> bool:
    """Check if running as root."""
    return os.geteuid() == 0


def check_deluge_console() -> bool:
    """Check if deluge-console is available."""
    try:
        result = subprocess.run(
            ["which", "deluge-console"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        return False


@app.command()
def install(
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help="Show detailed output during installation",
        ),
    ] = False,
):
    """
    Install Deluge MCP server as a systemd service.
    Creates a dedicated venv, installs dependencies, and sets up service.
    Will prompt for sudo password when needed.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        typer.echo("🔧 Verbose mode enabled\n")
    
    typer.echo("🔍 Checking system requirements...")

    # Check if Ubuntu
    if not is_ubuntu():
        typer.echo(
            "❌ Error: Only supported on Ubuntu/Debian systems.",  # fmt: skip
            err=True,
        )
        raise typer.Exit(code=1)

    # Check if deluge-console is installed
    if not check_deluge_console():
        typer.echo(
            "❌ Error: deluge-console not found. Install deluge first:",
            err=True,
        )
        typer.echo("   sudo apt-get install deluge-console", err=True)
        raise typer.Exit(code=1)

    typer.echo("✅ System check passed: Ubuntu/Debian detected")
    typer.echo("✅ deluge-console is available")

    # Get the current package location
    package_path = Path(__file__).parent.parent.parent
    if verbose:
        typer.echo(f"📂 Package location: {package_path}")
        typer.echo(f"📂 Service venv path: {SERVICE_VENV_PATH}")
        typer.echo(f"📂 Service log path: {SERVICE_LOG_PATH}")
        typer.echo(f"📂 Service port: {SERVICE_PORT}")

    # Step 1: Create dedicated venv
    typer.echo(f"\n🔨 Creating dedicated venv at {SERVICE_VENV_PATH}...")
    
    # Get the current Python executable
    current_python = sys.executable
    if verbose:
        typer.echo(f"   Using Python: {current_python}")
        python_version = sys.version.split()[0]
        typer.echo(f"   Python version: {python_version}")
    
    try:
        # Create parent directory with sudo
        subprocess.run(
            ["sudo", "mkdir", "-p", str(SERVICE_VENV_PATH.parent)],
            check=True,
            capture_output=not verbose,
        )
        
        # Create venv with sudo using the same Python version
        if verbose:
            typer.echo(f"   Command: sudo {current_python} -m venv {SERVICE_VENV_PATH}")  # fmt: skip
        subprocess.run(
            ["sudo", current_python, "-m", "venv", str(SERVICE_VENV_PATH)],
            check=True,
            capture_output=not verbose,
        )
        typer.echo("✅ Virtual environment created")
    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Failed to create venv: {e}", err=True)
        raise typer.Exit(code=1)

    # Step 2: Install the package in the venv
    typer.echo("\n📦 Installing deluge-mcp in the service venv...")
    pip_path = SERVICE_VENV_PATH / "bin" / "pip"
    python_venv_path = SERVICE_VENV_PATH / "bin" / "python"

    try:
        # Upgrade pip
        typer.echo("   Upgrading pip...")
        if verbose:
            typer.echo(f"   Command: sudo {pip_path} install --upgrade pip")
        result = subprocess.run(
            ["sudo", str(pip_path), "install", "--upgrade", "pip"],
            check=True,
            capture_output=not verbose,  # Show output in verbose mode
            text=True,
        )
        if verbose and result.stdout:
            typer.echo(result.stdout)

        # Install the package with the same version as currently running
        typer.echo(f"   Installing deluge-mcp=={__version__}...")
        if verbose:
            typer.echo(f"   Command: sudo {pip_path} install deluge-mcp=={__version__}")  # fmt: skip
        result = subprocess.run(
            ["sudo", str(pip_path), "install", f"deluge-mcp=={__version__}"],
            check=True,
            capture_output=not verbose,  # Show output in verbose mode
            text=True,
        )
        if verbose and result.stdout:
            typer.echo(result.stdout)
        typer.echo("✅ Package installed in service venv")
    except subprocess.CalledProcessError as e:
        typer.echo(
            f"\n❌ Failed to install package. Error code: {e.returncode}",
            err=True,
        )
        if verbose and hasattr(e, 'stderr') and e.stderr:
            typer.echo(f"\nError output:\n{e.stderr}", err=True)
        typer.echo(
            "\nTry installing manually:",
            err=True,
        )
        typer.echo(
            f"  sudo {pip_path} install deluge-mcp=={__version__}",
            err=True,
        )
        raise typer.Exit(code=1)

    # Step 3: Create systemd service file
    # Build the service content without inline comments
    environment_path = f"{SERVICE_VENV_PATH}/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"  # fmt: skip
    fastmcp_bin = f"{SERVICE_VENV_PATH}/bin/fastmcp"
    server_module = f"{SERVICE_VENV_PATH}/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/deluge_mcp/main.py:mcp"  # fmt: skip
    exec_start = f"{fastmcp_bin} run {server_module} --transport http --port {SERVICE_PORT} --host 0.0.0.0"  # fmt: skip
    
    service_content = f"""[Unit]
Description=Deluge MCP Server
Documentation=https://github.com/abi-jey/deluge-mcp
After=network-online.target deluged.service
Wants=network-online.target deluged.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/deluge-mcp
Environment="PATH={environment_path}"
Environment="PYTHONUNBUFFERED=1"
ExecStart={exec_start}
Restart=always
RestartSec=10
TimeoutStartSec=30
TimeoutStopSec=30
StandardOutput=journal
StandardError=journal

# Logging
SyslogIdentifier=deluge-mcp

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadOnlyPaths=/opt/deluge-mcp

[Install]
WantedBy=multi-user.target
"""

    service_path = Path("/etc/systemd/system/deluge-mcp.service")
    typer.echo(f"\n📝 Creating systemd service file: {service_path}")

    try:
        # Write to temp file first
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.service') as f:  # fmt: skip
            f.write(service_content)
            temp_path = f.name
        
        # Move with sudo
        subprocess.run(
            ["sudo", "mv", temp_path, str(service_path)],
            check=True,
        )
        typer.echo("✅ Service file created")
    except Exception as e:
        typer.echo(f"❌ Failed to create service file: {e}", err=True)
        raise typer.Exit(code=1)

    # Step 5: Reload systemd and enable service
    typer.echo("\n🔄 Reloading systemd daemon...")
    try:
        if verbose:
            typer.echo("   Command: sudo systemctl daemon-reload")
        subprocess.run(
            ["sudo", "systemctl", "daemon-reload"],
            check=True,
            capture_output=not verbose,
        )
        typer.echo("✅ Systemd reloaded")
    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Failed to reload systemd: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo("\n🚀 Enabling deluge-mcp service...")
    try:
        if verbose:
            typer.echo("   Command: sudo systemctl enable deluge-mcp")
        subprocess.run(
            ["sudo", "systemctl", "enable", "deluge-mcp"],
            check=True,
            capture_output=not verbose,
        )
        typer.echo("✅ Service enabled")
    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Failed to enable service: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo("\n▶️  Starting deluge-mcp service...")
    try:
        if verbose:
            typer.echo("   Command: sudo systemctl start deluge-mcp")
        subprocess.run(
            ["sudo", "systemctl", "start", "deluge-mcp"],
            check=True,
            capture_output=not verbose,
        )
        typer.echo("✅ Service started")
    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Failed to start service: {e}", err=True)
        typer.echo("   Check logs: sudo journalctl -u deluge-mcp -n 50")
        raise typer.Exit(code=1)

    typer.echo("\n✅ Installation complete!")
    typer.echo("\n📋 Configuration:")
    typer.echo(f"   Service venv: {SERVICE_VENV_PATH}")
    typer.echo(f"   Server URL: http://localhost:{SERVICE_PORT}/mcp")
    typer.echo(f"   Transport: HTTP (Server-Sent Events)")
    typer.echo("\n📋 Service Management:")
    typer.echo("   Start:   sudo systemctl start deluge-mcp")
    typer.echo("   Stop:    sudo systemctl stop deluge-mcp")
    typer.echo("   Status:  sudo systemctl status deluge-mcp")
    typer.echo("   Restart: sudo systemctl restart deluge-mcp")
    typer.echo("\n📋 View Logs:")
    typer.echo("   Follow:  sudo journalctl -u deluge-mcp -f")
    typer.echo("   Recent:  sudo journalctl -u deluge-mcp -n 50")
    typer.echo("   Status:  deluge-mcp status --logs")


@app.command()
def uninstall(
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help="Show detailed output during uninstallation",
        ),
    ] = False,
):
    """
    Uninstall the deluge-mcp systemd service.
    Will prompt for sudo password when needed.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        typer.echo("🔧 Verbose mode enabled\n")
    
    typer.echo("🗑️  Uninstalling deluge-mcp service...")

    try:
        # Stop service
        typer.echo("⏹️  Stopping service...")
        if verbose:
            typer.echo("   Command: sudo systemctl stop deluge-mcp")
        subprocess.run(
            ["sudo", "systemctl", "stop", "deluge-mcp"],
            check=False,
            capture_output=not verbose,
        )

        # Disable service
        typer.echo("🔌 Disabling service...")
        if verbose:
            typer.echo("   Command: sudo systemctl disable deluge-mcp")
        subprocess.run(
            ["sudo", "systemctl", "disable", "deluge-mcp"],
            check=False,
            capture_output=not verbose,
        )

        # Remove service file
        typer.echo("📝 Removing service file...")
        if verbose:
            typer.echo("   Command: sudo rm -f /etc/systemd/system/deluge-mcp.service")  # fmt: skip
        subprocess.run(
            ["sudo", "rm", "-f", "/etc/systemd/system/deluge-mcp.service"],
            check=True,
            capture_output=not verbose,
        )

        # Reload systemd daemon
        typer.echo("🔄 Reloading systemd daemon...")
        if verbose:
            typer.echo("   Command: sudo systemctl daemon-reload")
        subprocess.run(
            ["sudo", "systemctl", "daemon-reload"],
            check=True,
            capture_output=not verbose,
        )

        typer.echo("\n✅ Service uninstalled!")
        typer.echo(
            f"\nNote: Venv remains at {SERVICE_VENV_PATH}"  # fmt: skip
        )
        typer.echo("Remove manually if desired.")

    except Exception as e:
        typer.echo(f"❌ Uninstallation failed: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def status(
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help="Show detailed status information",
        ),
    ] = False,
    logs: Annotated[
        bool,
        typer.Option(
            "--logs",
            "-l",
            help="Show recent log entries",
        ),
    ] = False,
):
    """
    Check the status of the deluge-mcp daemon service.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        typer.echo("🔧 Verbose mode enabled\n")
    
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "is-active", "deluge-mcp.service"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.stdout.strip() == "active":
            typer.echo("✅ deluge-mcp service is running")
        else:
            typer.echo("❌ deluge-mcp service is not running")

        # Show detailed status
        if verbose:
            typer.echo("\n📊 Detailed status:")
        subprocess.run(["sudo", "systemctl", "status", "deluge-mcp.service"])
        
        # Show logs if requested
        if logs:
            typer.echo("\n📋 Recent logs:")
            subprocess.run(
                ["sudo", "journalctl", "-u", "deluge-mcp", "-n", "50", "--no-pager"]  # fmt: skip
            )

    except Exception as e:
        typer.echo(f"❌ Failed to check status: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def run(
    transport: Annotated[
        str,
        typer.Option(
            "--transport",
            "-t",
            help="Transport mode: stdio or sse",
        ),
    ] = "stdio",
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Port for SSE transport"),
    ] = 58880,
    host: Annotated[
        str,
        typer.Option(
            "--host",
            "-h",
            help="Host address to bind to (default: 0.0.0.0 for all interfaces)",  # fmt: skip
        ),
    ] = "0.0.0.0",
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-V",
            help="Enable verbose/debug logging",
        ),
    ] = False,
):
    """
    Run the deluge-mcp server directly (not as daemon).
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
        typer.echo("🔧 Verbose mode enabled")
        typer.echo(f"📊 Transport: {transport}")
        typer.echo(f"📊 Host: {host}")
        typer.echo(f"📊 Port: {port}\n")
    
    typer.echo(
        f"🚀 Starting deluge-mcp server (transport={transport}, host={host}, port={port})..."  # fmt: skip
    )

    # Use fastmcp run command with the mcp object from main.py
    import subprocess
    from pathlib import Path
    
    main_file = Path(__file__).parent / "main.py"
    fastmcp_args = [
        "fastmcp", "run", f"{main_file}:mcp",
        "--transport", transport,
    ]
    
    if transport == "http":
        fastmcp_args.extend(["--port", str(port), "--host", host])
    
    try:
        subprocess.run(fastmcp_args, check=True)
    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Error running server: {e}", err=True)
        raise typer.Exit(1)
    except KeyboardInterrupt:
        typer.echo("\n✋ Server stopped by user")
        raise typer.Exit(0)


def cli():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
