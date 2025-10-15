"""MCP management commands.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import json
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console

from glaip_sdk.cli.context import detect_export_format, get_ctx_value, output_flags
from glaip_sdk.cli.display import (
    display_api_error,
    display_confirmation_prompt,
    display_creation_success,
    display_deletion_success,
    display_update_success,
    handle_json_output,
    handle_rich_output,
)
from glaip_sdk.cli.io import (
    fetch_raw_resource_details,
    load_resource_from_file_with_validation,
)
from glaip_sdk.cli.mcp_validators import (
    validate_mcp_auth_structure,
    validate_mcp_config_structure,
)
from glaip_sdk.cli.parsers.json_input import parse_json_input
from glaip_sdk.cli.resolution import resolve_resource_reference
from glaip_sdk.cli.rich_helpers import print_markup
from glaip_sdk.cli.utils import (
    coerce_to_row,
    get_client,
    output_list,
    output_result,
    spinner_context,
)
from glaip_sdk.config.constants import (
    DEFAULT_MCP_TYPE,
)
from glaip_sdk.rich_components import AIPPanel
from glaip_sdk.utils import format_datetime
from glaip_sdk.utils.import_export import convert_export_to_import_format
from glaip_sdk.utils.serialization import (
    build_mcp_export_payload,
    write_resource_export,
)

console = Console()


@click.group(name="mcps", no_args_is_help=True)
def mcps_group() -> None:
    """MCP management operations.

    Provides commands for creating, listing, updating, deleting, and managing
    Model Context Protocol (MCP) configurations.
    """
    pass


def _resolve_mcp(
    ctx: Any, client: Any, ref: str, select: int | None = None
) -> Any | None:
    """Resolve MCP reference (ID or name) with ambiguity handling.

    Args:
        ctx: Click context object
        client: API client instance
        ref: MCP reference (ID or name)
        select: Index to select when multiple matches found

    Returns:
        MCP object if found, None otherwise

    Raises:
        ClickException: If MCP not found or selection invalid
    """
    return resolve_resource_reference(
        ctx,
        client,
        ref,
        "mcp",
        client.mcps.get_mcp_by_id,
        client.mcps.find_mcps,
        "MCP",
        select=select,
    )


def _strip_server_only_fields(import_data: dict[str, Any]) -> dict[str, Any]:
    """Remove fields that should not be forwarded during import-driven creation.

    Args:
        import_data: Raw import payload loaded from disk.

    Returns:
        A shallow copy of the data with server-managed fields removed.
    """
    cleaned = dict(import_data)
    for key in (
        "id",
        "type",
        "status",
        "connection_status",
        "created_at",
        "updated_at",
    ):
        cleaned.pop(key, None)
    return cleaned


def _load_import_ready_payload(import_file: str) -> dict[str, Any]:
    """Load and normalise an imported MCP definition for create operations.

    Args:
        import_file: Path to an MCP export file (JSON or YAML).

    Returns:
        Normalised import payload ready for CLI/REST usage.

    Raises:
        click.ClickException: If the file cannot be parsed or validated.
    """
    raw_data = load_resource_from_file_with_validation(Path(import_file), "MCP")
    import_data = convert_export_to_import_format(raw_data)
    import_data = _strip_server_only_fields(import_data)

    transport = import_data.get("transport")

    if "config" in import_data:
        import_data["config"] = validate_mcp_config_structure(
            import_data["config"],
            transport=transport,
            source="import file",
        )

    if "authentication" in import_data:
        import_data["authentication"] = validate_mcp_auth_structure(
            import_data["authentication"],
            source="import file",
        )

    return import_data


def _coerce_cli_string(value: str | None) -> str | None:
    """Normalise CLI string values so blanks are treated as missing.

    Args:
        value: User-provided string option.

    Returns:
        The stripped string, or ``None`` when the value is blank/whitespace-only.
    """
    if value is None:
        return None
    trimmed = value.strip()
    # Treat whitespace-only strings as None
    return trimmed if trimmed else None


def _merge_config_field(
    merged_base: dict[str, Any],
    cli_config: str | None,
    final_transport: str | None,
) -> None:
    """Merge config field with validation.

    Args:
        merged_base: Base payload to update in-place.
        cli_config: Raw CLI JSON string for config.
        final_transport: Transport type for validation.

    Raises:
        click.ClickException: If config JSON parsing or validation fails.
    """
    if cli_config is not None:
        parsed_config = parse_json_input(cli_config)
        merged_base["config"] = validate_mcp_config_structure(
            parsed_config,
            transport=final_transport,
            source="--config",
        )
    elif "config" not in merged_base or merged_base["config"] is None:
        merged_base["config"] = {}


def _merge_auth_field(
    merged_base: dict[str, Any],
    cli_auth: str | None,
) -> None:
    """Merge authentication field with validation.

    Args:
        merged_base: Base payload to update in-place.
        cli_auth: Raw CLI JSON string for authentication.

    Raises:
        click.ClickException: If auth JSON parsing or validation fails.
    """
    if cli_auth is not None:
        parsed_auth = parse_json_input(cli_auth)
        merged_base["authentication"] = validate_mcp_auth_structure(
            parsed_auth,
            source="--auth",
        )
    elif "authentication" not in merged_base:
        merged_base["authentication"] = None


def _merge_import_payload(
    import_data: dict[str, Any] | None,
    *,
    cli_name: str | None,
    cli_transport: str | None,
    cli_description: str | None,
    cli_config: str | None,
    cli_auth: str | None,
) -> tuple[dict[str, Any], list[str]]:
    """Merge import data with CLI overrides while tracking missing fields.

    Args:
        import_data: Normalised payload loaded from file (if provided).
        cli_name: Name supplied via CLI option.
        cli_transport: Transport supplied via CLI option.
        cli_description: Description supplied via CLI option.
        cli_config: Raw CLI JSON string for config.
        cli_auth: Raw CLI JSON string for authentication.

    Returns:
        A tuple of (merged_payload, missing_required_fields).

    Raises:
        click.ClickException: If config/auth JSON parsing or validation fails.
    """
    merged_base = import_data.copy() if import_data else {}

    # Merge simple string fields using truthy CLI overrides
    for field, cli_value in (
        ("name", _coerce_cli_string(cli_name)),
        ("transport", _coerce_cli_string(cli_transport)),
        ("description", _coerce_cli_string(cli_description)),
    ):
        if cli_value is not None:
            merged_base[field] = cli_value

    # Determine final transport before validating config
    final_transport = merged_base.get("transport")

    # Merge config and authentication with validation
    _merge_config_field(merged_base, cli_config, final_transport)
    _merge_auth_field(merged_base, cli_auth)

    # Validate required fields
    missing_fields = []
    for required in ("name", "transport"):
        value = merged_base.get(required)
        if not isinstance(value, str) or not value.strip():
            missing_fields.append(required)

    return merged_base, missing_fields


@mcps_group.command(name="list")
@output_flags()
@click.pass_context
def list_mcps(ctx: Any) -> None:
    """List all MCPs in a formatted table.

    Args:
        ctx: Click context containing output format preferences

    Raises:
        ClickException: If API request fails
    """
    try:
        client = get_client(ctx)
        with spinner_context(
            ctx,
            "[bold blue]Fetching MCPs…[/bold blue]",
            console_override=console,
        ):
            mcps = client.mcps.list_mcps()

        # Define table columns: (data_key, header, style, width)
        columns = [
            ("id", "ID", "dim", 36),
            ("name", "Name", "cyan", None),
            ("config", "Config", "blue", None),
        ]

        # Transform function for safe dictionary access
        def transform_mcp(mcp: Any) -> dict[str, Any]:
            row = coerce_to_row(mcp, ["id", "name", "config"])
            # Ensure id is always a string
            row["id"] = str(row["id"])
            # Truncate config field for display
            if row["config"] != "N/A":
                row["config"] = (
                    str(row["config"])[:50] + "..."
                    if len(str(row["config"])) > 50
                    else str(row["config"])
                )
            return row

        output_list(ctx, mcps, "🔌 Available MCPs", columns, transform_mcp)

    except Exception as e:
        raise click.ClickException(str(e))


@mcps_group.command()
@click.option("--name", help="MCP name")
@click.option("--transport", help="MCP transport protocol")
@click.option("--description", help="MCP description")
@click.option(
    "--config",
    help="JSON configuration string or @file reference (e.g., @config.json)",
)
@click.option(
    "--auth",
    "--authentication",
    "auth",
    help="JSON authentication object or @file reference (e.g., @auth.json)",
)
@click.option(
    "--import",
    "import_file",
    type=click.Path(exists=True, dir_okay=False),
    help="Import MCP configuration from JSON or YAML export",
)
@output_flags()
@click.pass_context
def create(
    ctx: Any,
    name: str | None,
    transport: str | None,
    description: str | None,
    config: str | None,
    auth: str | None,
    import_file: str | None,
) -> None:
    """Create a new MCP with specified configuration.

    You can create an MCP by providing all parameters via CLI options, or by
    importing from a file and optionally overriding specific fields.

    Args:
        ctx: Click context containing output format preferences
        name: MCP name (required unless provided via --import)
        transport: MCP transport protocol (required unless provided via --import)
        description: Optional MCP description
        config: JSON configuration string or @file reference
        auth: JSON authentication object or @file reference
        import_file: Optional path to import configuration from export file.
            CLI options override imported values.

    Raises:
        ClickException: If JSON parsing fails or API request fails

    Examples:
        Create from CLI options:
            aip mcps create --name my-mcp --transport http --config '{"url": "https://api.example.com"}'

        Import from file:
            aip mcps create --import mcp-export.json

        Import with overrides:
            aip mcps create --import mcp-export.json --name new-name --transport sse
    """
    try:
        client = get_client(ctx)

        import_payload = (
            _load_import_ready_payload(import_file) if import_file is not None else None
        )

        merged_payload, missing_fields = _merge_import_payload(
            import_payload,
            cli_name=name,
            cli_transport=transport,
            cli_description=description,
            cli_config=config,
            cli_auth=auth,
        )

        if missing_fields:
            raise click.ClickException(
                "Missing required fields after combining import and CLI values: "
                + ", ".join(missing_fields)
            )

        effective_name = merged_payload["name"]
        effective_transport = merged_payload["transport"]
        effective_description = merged_payload.get("description")
        effective_config = merged_payload.get("config") or {}
        effective_auth = merged_payload.get("authentication")

        with spinner_context(
            ctx,
            "[bold blue]Creating MCP…[/bold blue]",
            console_override=console,
        ):
            create_kwargs: dict[str, Any] = {
                "name": effective_name,
                "config": effective_config,
                "transport": effective_transport,
            }

            if effective_description is not None:
                create_kwargs["description"] = effective_description

            if effective_auth:
                create_kwargs["authentication"] = effective_auth

            mcp_metadata = merged_payload.get("mcp_metadata")
            if mcp_metadata is not None:
                create_kwargs["mcp_metadata"] = mcp_metadata

            mcp = client.mcps.create_mcp(**create_kwargs)

        # Handle JSON output
        handle_json_output(ctx, mcp.model_dump())

        # Handle Rich output
        rich_panel = display_creation_success(
            "MCP",
            mcp.name,
            mcp.id,
            Type=getattr(mcp, "type", DEFAULT_MCP_TYPE),
            Transport=getattr(mcp, "transport", effective_transport),
            Description=effective_description or "No description",
        )
        handle_rich_output(ctx, rich_panel)

    except Exception as e:
        handle_json_output(ctx, error=e)
        if get_ctx_value(ctx, "view") != "json":
            display_api_error(e, "MCP creation")
        raise click.ClickException(str(e))


def _handle_mcp_export(
    ctx: Any,
    client: Any,
    mcp: Any,
    export_path: Path,
    no_auth_prompt: bool,
    auth_placeholder: str,
) -> None:
    """Handle MCP export to file with format detection and auth handling.

    Args:
        ctx: Click context for spinner management
        client: API client for fetching MCP details
        mcp: MCP object to export
        export_path: Target file path (format detected from extension)
        no_auth_prompt: Skip interactive secret prompts if True
        auth_placeholder: Placeholder text for missing secrets

    Note:
        Supports JSON (.json) and YAML (.yaml/.yml) export formats.
        In interactive mode, prompts for secret values.
        In non-interactive mode, uses placeholder values.
    """
    # Auto-detect format from file extension
    detected_format = detect_export_format(export_path)

    # Always export comprehensive data - re-fetch with full details
    try:
        with spinner_context(
            ctx,
            "[bold blue]Fetching complete MCP details…[/bold blue]",
            console_override=console,
        ):
            mcp = client.mcps.get_mcp_by_id(mcp.id)
    except Exception as e:
        print_markup(
            f"[yellow]⚠️  Could not fetch full MCP details: {e}[/yellow]",
            console=console,
        )
        print_markup(
            "[yellow]⚠️  Proceeding with available data[/yellow]", console=console
        )

    # Determine if we should prompt for secrets
    prompt_for_secrets = not no_auth_prompt and sys.stdin.isatty()

    # Warn user if non-interactive mode forces placeholder usage
    if not no_auth_prompt and not sys.stdin.isatty():
        print_markup(
            "[yellow]⚠️  Non-interactive mode detected. "
            "Using placeholder values for secrets.[/yellow]",
            console=console,
        )

    # Build and write export payload
    if prompt_for_secrets:
        # Interactive mode: no spinner during prompts
        export_payload = build_mcp_export_payload(
            mcp,
            prompt_for_secrets=prompt_for_secrets,
            placeholder=auth_placeholder,
            console=console,
        )
        with spinner_context(
            ctx,
            "[bold blue]Writing export file…[/bold blue]",
            console_override=console,
        ):
            write_resource_export(export_path, export_payload, detected_format)
    else:
        # Non-interactive mode: spinner for entire export process
        with spinner_context(
            ctx,
            "[bold blue]Exporting MCP configuration…[/bold blue]",
            console_override=console,
        ):
            export_payload = build_mcp_export_payload(
                mcp,
                prompt_for_secrets=prompt_for_secrets,
                placeholder=auth_placeholder,
                console=console,
            )
            write_resource_export(export_path, export_payload, detected_format)

    print_markup(
        f"[green]✅ Complete MCP configuration exported to: "
        f"{export_path} (format: {detected_format})[/green]",
        console=console,
    )


def _display_mcp_details(ctx: Any, client: Any, mcp: Any) -> None:
    """Display MCP details using raw API data or fallback to Pydantic model.

    Args:
        ctx: Click context containing output format preferences
        client: API client for fetching raw MCP data
        mcp: MCP object to display details for

    Note:
        Attempts to fetch raw API data first to preserve all fields.
        Falls back to Pydantic model data if raw data unavailable.
        Formats datetime fields for better readability.
    """
    # Try to fetch raw API data first to preserve ALL fields
    with spinner_context(
        ctx,
        "[bold blue]Fetching detailed MCP data…[/bold blue]",
        console_override=console,
    ):
        raw_mcp_data = fetch_raw_resource_details(client, mcp, "mcps")

    if raw_mcp_data:
        # Use raw API data - this preserves ALL fields
        formatted_data = raw_mcp_data.copy()
        if "created_at" in formatted_data:
            formatted_data["created_at"] = format_datetime(formatted_data["created_at"])
        if "updated_at" in formatted_data:
            formatted_data["updated_at"] = format_datetime(formatted_data["updated_at"])

        output_result(
            ctx,
            formatted_data,
            title="MCP Details",
            panel_title=f"🔌 {raw_mcp_data.get('name', 'Unknown')}",
        )
    else:
        # Fall back to Pydantic model data
        console.print("[yellow]Falling back to Pydantic model data[/yellow]")
        result_data = {
            "id": str(getattr(mcp, "id", "N/A")),
            "name": getattr(mcp, "name", "N/A"),
            "type": getattr(mcp, "type", "N/A"),
            "config": getattr(mcp, "config", "N/A"),
            "status": getattr(mcp, "status", "N/A"),
            "connection_status": getattr(mcp, "connection_status", "N/A"),
        }
        output_result(ctx, result_data, title=f"🔌 {mcp.name}")


@mcps_group.command()
@click.argument("mcp_ref")
@click.option(
    "--export",
    type=click.Path(dir_okay=False, writable=True),
    help="Export complete MCP configuration to file "
    "(format auto-detected from .json/.yaml extension)",
)
@click.option(
    "--no-auth-prompt",
    is_flag=True,
    help="Skip interactive secret prompts and use placeholder values.",
)
@click.option(
    "--auth-placeholder",
    default="<INSERT VALUE>",
    show_default=True,
    help="Placeholder text used when secrets are unavailable.",
)
@output_flags()
@click.pass_context
def get(
    ctx: Any,
    mcp_ref: str,
    export: str | None,
    no_auth_prompt: bool,
    auth_placeholder: str,
) -> None:
    """Get MCP details and optionally export configuration to file.

    Args:
        ctx: Click context containing output format preferences
        mcp_ref: MCP reference (ID or name)
        export: Optional file path to export MCP configuration
        no_auth_prompt: Skip interactive secret prompts if True
        auth_placeholder: Placeholder text for missing secrets

    Raises:
        ClickException: If MCP not found or export fails

    Examples:
        aip mcps get my-mcp
        aip mcps get my-mcp --export mcp.json    # Export as JSON
        aip mcps get my-mcp --export mcp.yaml    # Export as YAML
    """
    try:
        client = get_client(ctx)

        # Resolve MCP using helper function
        mcp = _resolve_mcp(ctx, client, mcp_ref)

        # Handle export option
        if export:
            _handle_mcp_export(
                ctx, client, mcp, Path(export), no_auth_prompt, auth_placeholder
            )

        # Display MCP details
        _display_mcp_details(ctx, client, mcp)

    except Exception as e:
        raise click.ClickException(str(e))


@mcps_group.command("tools")
@click.argument("mcp_ref")
@output_flags()
@click.pass_context
def list_tools(ctx: Any, mcp_ref: str) -> None:
    """List tools available from a specific MCP.

    Args:
        ctx: Click context containing output format preferences
        mcp_ref: MCP reference (ID or name)

    Raises:
        ClickException: If MCP not found or tools fetch fails
    """
    try:
        client = get_client(ctx)

        # Resolve MCP using helper function
        mcp = _resolve_mcp(ctx, client, mcp_ref)

        # Get tools from MCP
        with spinner_context(
            ctx,
            "[bold blue]Fetching MCP tools…[/bold blue]",
            console_override=console,
        ):
            tools = client.mcps.get_mcp_tools(mcp.id)

        # Define table columns: (data_key, header, style, width)
        columns = [
            ("name", "Name", "cyan", None),
            ("description", "Description", "green", 50),
        ]

        # Transform function for safe dictionary access
        def transform_tool(tool: dict[str, Any]) -> dict[str, Any]:
            return {
                "name": tool.get("name", "N/A"),
                "description": tool.get("description", "N/A")[:47] + "..."
                if len(tool.get("description", "")) > 47
                else tool.get("description", "N/A"),
            }

        output_list(
            ctx, tools, f"🔧 Tools from MCP: {mcp.name}", columns, transform_tool
        )

    except Exception as e:
        raise click.ClickException(str(e))


@mcps_group.command("connect")
@click.option(
    "--from-file",
    "config_file",
    required=True,
    help="MCP config JSON file",
)
@output_flags()
@click.pass_context
def connect(ctx: Any, config_file: str) -> None:
    """Test MCP connection using a configuration file.

    Args:
        ctx: Click context containing output format preferences
        config_file: Path to MCP configuration JSON file

    Raises:
        ClickException: If config file invalid or connection test fails

    Note:
        Loads MCP configuration from JSON file and tests connectivity.
        Displays success or failure with connection details.
    """
    try:
        client = get_client(ctx)

        # Load MCP config from file
        with open(config_file) as f:
            config = json.load(f)

        view = get_ctx_value(ctx, "view", "rich")
        if view != "json":
            print_markup(
                f"[yellow]Connecting to MCP with config from {config_file}...[/yellow]",
                console=console,
            )

        # Test connection using config
        with spinner_context(
            ctx,
            "[bold blue]Connecting to MCP…[/bold blue]",
            console_override=console,
        ):
            result = client.mcps.test_mcp_connection_from_config(config)

        view = get_ctx_value(ctx, "view", "rich")
        if view == "json":
            handle_json_output(ctx, result)
        else:
            success_panel = AIPPanel(
                f"[green]✓[/green] MCP connection successful!\n\n"
                f"[bold]Result:[/bold] {result}",
                title="🔌 Connection",
                border_style="green",
            )
            console.print(success_panel)

    except Exception as e:
        raise click.ClickException(str(e))


@mcps_group.command()
@click.argument("mcp_ref")
@click.option("--name", help="New MCP name")
@click.option("--description", help="New description")
@click.option(
    "--config",
    help="JSON configuration string or @file reference (e.g., @config.json)",
)
@click.option(
    "--auth",
    "--authentication",
    "auth",
    help="JSON authentication object or @file reference (e.g., @auth.json)",
)
@output_flags()
@click.pass_context
def update(
    ctx: Any,
    mcp_ref: str,
    name: str | None,
    description: str | None,
    config: str | None,
    auth: str | None,
) -> None:
    """Update an existing MCP with new configuration values.

    Args:
        ctx: Click context containing output format preferences
        mcp_ref: MCP reference (ID or name)
        name: New MCP name (optional)
        description: New description (optional)
        config: New JSON configuration string or @file reference (optional)
        auth: New JSON authentication object or @file reference (optional)

    Raises:
        ClickException: If MCP not found, JSON invalid, or no fields specified

    Note:
        At least one field must be specified for update.
        Uses PUT for complete updates or PATCH for partial updates.
    """
    try:
        client = get_client(ctx)

        # Resolve MCP using helper function
        mcp = _resolve_mcp(ctx, client, mcp_ref)

        # Build update data
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if config is not None:
            parsed_config = parse_json_input(config)
            update_data["config"] = validate_mcp_config_structure(
                parsed_config,
                transport=getattr(mcp, "transport", None),
                source="--config",
            )
        if auth is not None:
            parsed_auth = parse_json_input(auth)
            update_data["authentication"] = validate_mcp_auth_structure(
                parsed_auth, source="--auth"
            )

        if not update_data:
            raise click.ClickException("No update fields specified")

        # Update MCP (automatically chooses PUT or PATCH based on provided fields)
        with spinner_context(
            ctx,
            "[bold blue]Updating MCP…[/bold blue]",
            console_override=console,
        ):
            updated_mcp = client.mcps.update_mcp(mcp.id, **update_data)

        handle_json_output(ctx, updated_mcp.model_dump())
        handle_rich_output(ctx, display_update_success("MCP", updated_mcp.name))

    except Exception as e:
        handle_json_output(ctx, error=e)
        if get_ctx_value(ctx, "view") != "json":
            display_api_error(e, "MCP update")
        raise click.ClickException(str(e))


@mcps_group.command()
@click.argument("mcp_ref")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation")
@output_flags()
@click.pass_context
def delete(ctx: Any, mcp_ref: str, yes: bool) -> None:
    """Delete an MCP after confirmation.

    Args:
        ctx: Click context containing output format preferences
        mcp_ref: MCP reference (ID or name)
        yes: Skip confirmation prompt if True

    Raises:
        ClickException: If MCP not found or deletion fails

    Note:
        Requires confirmation unless --yes flag is provided.
        Deletion is permanent and cannot be undone.
    """
    try:
        client = get_client(ctx)

        # Resolve MCP using helper function
        mcp = _resolve_mcp(ctx, client, mcp_ref)

        # Confirm deletion
        if not yes and not display_confirmation_prompt("MCP", mcp.name):
            return

        with spinner_context(
            ctx,
            "[bold blue]Deleting MCP…[/bold blue]",
            console_override=console,
        ):
            client.mcps.delete_mcp(mcp.id)

        handle_json_output(
            ctx,
            {
                "success": True,
                "message": f"MCP '{mcp.name}' deleted",
            },
        )
        handle_rich_output(ctx, display_deletion_success("MCP", mcp.name))

    except Exception as e:
        handle_json_output(ctx, error=e)
        if get_ctx_value(ctx, "view") != "json":
            display_api_error(e, "MCP deletion")
        raise click.ClickException(str(e))
