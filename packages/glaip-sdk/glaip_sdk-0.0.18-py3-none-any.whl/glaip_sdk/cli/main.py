"""Main CLI entry point for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import os
import subprocess
import sys
from typing import Any

import click
from rich.console import Console

from glaip_sdk import Client
from glaip_sdk._version import __version__ as _SDK_VERSION
from glaip_sdk.branding import AIPBranding
from glaip_sdk.cli.commands.agents import agents_group
from glaip_sdk.cli.commands.configure import (
    config_group,
    configure_command,
)
from glaip_sdk.cli.commands.mcps import mcps_group
from glaip_sdk.cli.commands.models import models_group
from glaip_sdk.cli.commands.tools import tools_group
from glaip_sdk.cli.config import load_config
from glaip_sdk.cli.update_notifier import maybe_notify_update
from glaip_sdk.cli.utils import spinner_context, update_spinner
from glaip_sdk.config.constants import (
    DEFAULT_AGENT_RUN_TIMEOUT,
)
from glaip_sdk.rich_components import AIPPanel, AIPTable

# Import SlashSession for potential mocking in tests
try:
    from glaip_sdk.cli.slash import SlashSession
except ImportError:  # pragma: no cover - optional slash dependencies
    # Slash dependencies might not be available in all environments
    SlashSession = None


@click.group(invoke_without_command=True)
@click.version_option(version=_SDK_VERSION, prog_name="aip")
@click.option("--api-url", envvar="AIP_API_URL", help="AIP API URL")
@click.option("--api-key", envvar="AIP_API_KEY", help="AIP API Key")
@click.option("--timeout", default=30.0, help="Request timeout in seconds")
@click.option(
    "--view",
    "view",
    type=click.Choice(["rich", "plain", "json", "md"]),
    default="rich",
    help="Output view format",
)
@click.option("--no-tty", is_flag=True, help="Disable TTY renderer")
@click.pass_context
def main(
    ctx: Any,
    api_url: str | None,
    api_key: str | None,
    timeout: float | None,
    view: str | None,
    no_tty: bool,
) -> None:
    """GL AIP SDK Command Line Interface.

    A comprehensive CLI for managing GL AIP resources including
    agents, tools, MCPs, and more.

    Examples:
        aip version                     # Show detailed version info
        aip configure                   # Configure credentials
        aip agents list                   # List all agents
        aip tools create my_tool.py      # Create a new tool
        aip agents run my-agent "Hello world"  # Run an agent
    """
    # Store configuration in context
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url
    ctx.obj["api_key"] = api_key
    ctx.obj["timeout"] = timeout
    ctx.obj["view"] = view

    ctx.obj["tty"] = not no_tty

    if not ctx.resilient_parsing and ctx.obj["tty"]:
        console = Console()
        maybe_notify_update(
            _SDK_VERSION,
            console=console,
        )

    if ctx.invoked_subcommand is None and not ctx.resilient_parsing:
        if _should_launch_slash(ctx) and SlashSession is not None:
            session = SlashSession(ctx)
            session.run()
            ctx.exit()
        else:
            click.echo(ctx.get_help())
            ctx.exit()


# Add command groups
main.add_command(agents_group)
main.add_command(config_group)
main.add_command(tools_group)
main.add_command(mcps_group)
main.add_command(models_group)

# Add top-level commands
main.add_command(configure_command)


# Tip: `--version` is provided by click.version_option above.


def _should_launch_slash(ctx: click.Context) -> bool:
    """Determine whether to open the command palette automatically."""
    ctx_obj = ctx.obj or {}
    if not bool(ctx_obj.get("tty", True)):
        return False

    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return False

    return True


def _load_and_merge_config(ctx: click.Context) -> dict:
    """Load configuration from multiple sources and merge them."""
    # Load config from file and merge with context
    file_config = load_config()
    context_config = ctx.obj or {}

    # Load environment variables (middle priority)
    env_config = {}
    if os.getenv("AIP_API_URL"):
        env_config["api_url"] = os.getenv("AIP_API_URL")
    if os.getenv("AIP_API_KEY"):
        env_config["api_key"] = os.getenv("AIP_API_KEY")

    # Filter out None values from context config to avoid overriding other configs
    filtered_context = {k: v for k, v in context_config.items() if v is not None}

    # Merge configs: file (low) -> env (mid) -> CLI args (high)
    return {**file_config, **env_config, **filtered_context}


def _validate_config_and_show_error(config: dict, console: Console) -> None:
    """Validate configuration and show error if incomplete."""
    if not config.get("api_url") or not config.get("api_key"):
        console.print(
            AIPPanel(
                "[bold red]❌ Configuration incomplete[/bold red]\n\n"
                f"🔍 Current config:\n"
                f"   • API URL: {config.get('api_url', 'Not set')}\n"
                f"   • API Key: {'***' + config.get('api_key', '')[-4:] if config.get('api_key') else 'Not set'}\n\n"
                f"💡 To fix this:\n"
                f"   • Run 'aip configure' to set up credentials\n"
                f"   • Or run 'aip config list' to see current config",
                title="❌ Configuration Error",
                border_style="red",
            )
        )
        console.print(
            f"\n[bold green]✅ AIP - Ready[/bold green] (SDK v{_SDK_VERSION}) - Configure to connect"
        )
        sys.exit(1)


def _create_and_test_client(config: dict, console: Console) -> Client:
    """Create client and test connection by fetching resources."""
    # Try to create client
    client = Client(
        api_url=config["api_url"],
        api_key=config["api_key"],
        timeout=config.get("timeout", 30.0),
    )

    # Test connection by listing resources
    try:
        with spinner_context(
            None,  # We'll pass ctx later
            "[bold blue]Checking GL AIP status…[/bold blue]",
            console_override=console,
            spinner_style="cyan",
        ) as status_indicator:
            update_spinner(status_indicator, "[bold blue]Fetching agents…[/bold blue]")
            agents = client.list_agents()

            update_spinner(status_indicator, "[bold blue]Fetching tools…[/bold blue]")
            tools = client.list_tools()

            update_spinner(status_indicator, "[bold blue]Fetching MCPs…[/bold blue]")
            mcps = client.list_mcps()

        # Create status table
        table = AIPTable(title="🔗 GL AIP Status")
        table.add_column("Resource", style="cyan", width=15)
        table.add_column("Count", style="green", width=10)
        table.add_column("Status", style="green", width=15)

        table.add_row("Agents", str(len(agents)), "✅ Available")
        table.add_row("Tools", str(len(tools)), "✅ Available")
        table.add_row("MCPs", str(len(mcps)), "✅ Available")

        console.print(
            AIPPanel(
                f"[bold green]✅ Connected to GL AIP[/bold green]\n"
                f"🔗 API URL: {client.api_url}\n"
                f"🤖 Agent Run Timeout: {DEFAULT_AGENT_RUN_TIMEOUT}s",
                title="🚀 Connection Status",
                border_style="green",
            )
        )

        console.print(table)

    except Exception as e:
        # Show AIP Ready status even if connection fails
        console.print(
            f"\n[bold green]✅ AIP - Ready[/bold green] (SDK v{_SDK_VERSION})"
        )

        console.print(
            AIPPanel(
                f"[bold yellow]⚠️  Connection established but API call failed[/bold yellow]\n"
                f"🔗 API URL: {client.api_url}\n"
                f"❌ Error: {e}\n\n"
                f"💡 This usually means:\n"
                f"   • Network connectivity issues\n"
                f"   • API permissions problems\n"
                f"   • Backend service issues",
                title="⚠️  Partial Connection",
                border_style="yellow",
            )
        )

    return client


def _handle_connection_error(config: dict, console: Console, error: Exception) -> None:
    """Handle connection errors and show troubleshooting information."""
    console.print(
        AIPPanel(
            f"[bold red]❌ Connection failed[/bold red]\n\n"
            f"🔍 Error: {error}\n\n"
            f"💡 Troubleshooting steps:\n"
            f"   • Verify your API URL and key are correct\n"
            f"   • Check network connectivity to {config.get('api_url', 'your API')}\n"
            f"   • Run 'aip configure' to update credentials\n"
            f"   • Run 'aip config list' to check configuration",
            title="❌ Connection Error",
            border_style="red",
        )
    )
    sys.exit(1)


@main.command()
@click.pass_context
def status(ctx: Any) -> None:
    """Show connection status and basic info."""
    config = {}
    try:
        console = Console()

        # Display AIP status banner
        branding = AIPBranding.create_from_sdk(
            sdk_version=_SDK_VERSION, package_name="glaip-sdk"
        )
        branding.display_welcome_panel(title="🚀 AIP Status")

        # Show AIP Ready status
        console.print(
            f"\n[bold green]✅ AIP - Ready[/bold green] (SDK v{_SDK_VERSION})"
        )

        # Load and merge configuration
        config = _load_and_merge_config(ctx)

        # Validate configuration
        _validate_config_and_show_error(config, console)

        # Create and test client connection
        client = _create_and_test_client(config, console)
        client.close()

    except Exception as e:
        # Handle any unexpected errors during the process
        console = Console()
        _handle_connection_error(config if "config" in locals() else {}, console, e)


@main.command()
def version() -> None:
    """Show version information."""
    branding = AIPBranding.create_from_sdk(
        sdk_version=_SDK_VERSION, package_name="glaip-sdk"
    )
    branding.display_version_panel()


@main.command()
@click.option(
    "--check-only", is_flag=True, help="Only check for updates without installing"
)
@click.option(
    "--force",
    is_flag=True,
    help="Force reinstall even if already up-to-date (adds --force-reinstall)",
)
def update(check_only: bool, force: bool) -> None:
    """Update AIP SDK to the latest version from PyPI."""
    try:
        console = Console()

        if check_only:
            console.print(
                AIPPanel(
                    "[bold blue]🔍 Checking for updates...[/bold blue]\n\n"
                    "💡 To install updates, run: aip update",
                    title="📋 Update Check",
                    border_style="blue",
                )
            )
            return

        console.print(
            AIPPanel(
                "[bold blue]🔄 Updating AIP SDK...[/bold blue]\n\n"
                "📦 This will update the package from PyPI\n"
                "💡 Use --check-only to just check for updates",
                title="🚀 Update Process",
                border_style="blue",
                padding=(0, 1),
            )
        )

        # Update using pip
        try:
            cmd = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--upgrade",
                "glaip-sdk",
            ]
            if force:
                cmd.insert(5, "--force-reinstall")
            subprocess.run(cmd, capture_output=True, text=True, check=True)

            console.print(
                AIPPanel(
                    "[bold green]✅ Update successful![/bold green]\n\n"
                    "🔄 AIP SDK has been updated to the latest version\n"
                    "💡 Restart your terminal or run 'aip --version' to verify",
                    title="🎉 Update Complete",
                    border_style="green",
                    padding=(0, 1),
                )
            )

            # Show new version
            version_result = subprocess.run(
                [sys.executable, "-m", "glaip_sdk.cli.main", "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            console.print(f"📋 New version: {version_result.stdout.strip()}")

        except subprocess.CalledProcessError as e:
            console.print(
                AIPPanel(
                    f"[bold red]❌ Update failed[/bold red]\n\n"
                    f"🔍 Error: {e.stderr}\n\n"
                    "💡 Troubleshooting:\n"
                    "   • Check your internet connection\n"
                    "   • Try running: pip install --upgrade glaip-sdk\n"
                    "   • Check if you have write permissions",
                    title="❌ Update Error",
                    border_style="red",
                    padding=(0, 1),
                )
            )
            sys.exit(1)

    except ImportError:
        console.print(
            AIPPanel(
                "[bold red]❌ Rich library not available[/bold red]\n\n"
                "💡 Install rich: pip install rich\n"
                "   Then try: aip update",
                title="❌ Missing Dependency",
                border_style="red",
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
