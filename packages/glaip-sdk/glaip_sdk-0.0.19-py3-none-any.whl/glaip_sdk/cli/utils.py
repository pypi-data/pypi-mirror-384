"""CLI utilities for glaip-sdk.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
    Putu Ravindra Wiguna (putu.r.wiguna@gdplabs.id)
"""

from __future__ import annotations

import json
import logging
import os
import sys
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from typing import TYPE_CHECKING, Any

import click
from rich.console import Console, Group
from rich.markdown import Markdown
from rich.pretty import Pretty

from glaip_sdk.cli.rich_helpers import markup_text
from glaip_sdk.rich_components import AIPPanel

# Optional interactive deps (fuzzy palette)
try:
    from prompt_toolkit.completion import Completion
    from prompt_toolkit.shortcuts import prompt

    _HAS_PTK = True
except Exception:  # pragma: no cover - optional dependency
    _HAS_PTK = False

try:
    import questionary
except Exception:  # pragma: no cover - optional dependency
    questionary = None

if TYPE_CHECKING:  # pragma: no cover - import-only during type checking
    from glaip_sdk import Client
from glaip_sdk.cli import masking, pager
from glaip_sdk.cli.config import load_config
from glaip_sdk.cli.context import (
    _get_view,
    get_ctx_value,
)
from glaip_sdk.cli.context import (
    detect_export_format as _detect_export_format,
)
from glaip_sdk.rich_components import AIPTable
from glaip_sdk.utils import is_uuid
from glaip_sdk.utils.rendering.renderer import (
    CapturingConsole,
    RendererConfig,
    RichStreamRenderer,
)

console = Console()
pager.console = console
logger = logging.getLogger("glaip_sdk.cli.utils")


# ----------------------------- Context helpers ---------------------------- #


def detect_export_format(file_path: str | os.PathLike[str]) -> str:
    """Backward-compatible proxy to `glaip_sdk.cli.context.detect_export_format`."""
    return _detect_export_format(file_path)


def in_slash_mode(ctx: click.Context | None = None) -> bool:
    """Return True when running inside the slash command palette."""
    if ctx is None:
        try:
            ctx = click.get_current_context(silent=True)
        except RuntimeError:
            ctx = None

    if ctx is None:
        return False

    obj = getattr(ctx, "obj", None)
    if isinstance(obj, dict):
        return bool(obj.get("_slash_session"))

    return bool(getattr(obj, "_slash_session", False))


def command_hint(
    cli_command: str | None,
    slash_command: str | None = None,
    *,
    ctx: click.Context | None = None,
) -> str | None:
    """Return the appropriate command string for the current mode.

    Args:
        cli_command: Command string without the ``aip`` prefix (e.g., ``"status"``).
        slash_command: Slash command counterpart (e.g., ``"status"`` or ``"/status"``).
        ctx: Optional Click context override.

    Returns:
        The formatted command string for the active mode, or ``None`` when no
        equivalent command exists in that mode.
    """
    if in_slash_mode(ctx):
        if not slash_command:
            return None
        return slash_command if slash_command.startswith("/") else f"/{slash_command}"

    if not cli_command:
        return None
    return f"aip {cli_command}"


def spinner_context(
    ctx: Any | None,
    message: str,
    *,
    console_override: Console | None = None,
    spinner: str = "dots",
    spinner_style: str = "cyan",
) -> AbstractContextManager[Any]:
    """Return a context manager that renders a spinner when appropriate."""
    active_console = console_override or console
    if not _can_use_spinner(ctx, active_console):
        return nullcontext()

    return active_console.status(
        message,
        spinner=spinner,
        spinner_style=spinner_style,
    )


def _can_use_spinner(ctx: Any | None, active_console: Console) -> bool:
    """Check if spinner output is allowed in the current environment."""
    if ctx is not None:
        tty_enabled = bool(get_ctx_value(ctx, "tty", True))
        view = (_get_view(ctx) or "rich").lower()
        if not tty_enabled or view not in {"", "rich"}:
            return False

    if not active_console.is_terminal:
        return False

    return _stream_supports_tty(getattr(active_console, "file", None))


def _stream_supports_tty(stream: Any) -> bool:
    """Return True if the provided stream can safely render a spinner."""
    target = stream if hasattr(stream, "isatty") else sys.stdout
    try:
        return bool(target.isatty())
    except Exception:
        return False


def update_spinner(status_indicator: Any | None, message: str) -> None:
    """Update spinner text when a status indicator is active."""
    if status_indicator is None:
        return

    try:
        status_indicator.update(message)
    except Exception:  # pragma: no cover - defensive update
        pass


def stop_spinner(status_indicator: Any | None) -> None:
    """Stop an active spinner safely."""
    if status_indicator is None:
        return

    try:
        status_indicator.stop()
    except Exception:  # pragma: no cover - defensive stop
        pass


# Backwards compatibility aliases for legacy callers
_spinner_update = update_spinner
_spinner_stop = stop_spinner


# ----------------------------- Client config ----------------------------- #


def get_client(ctx: Any) -> Client:  # pragma: no cover
    """Get configured client from context, env, and config file (ctx > env > file)."""
    from glaip_sdk import Client

    file_config = load_config() or {}
    context_config_obj = getattr(ctx, "obj", None)
    context_config = context_config_obj or {}

    raw_timeout = os.getenv("AIP_TIMEOUT", "0") or "0"
    try:
        timeout_value = float(raw_timeout)
    except ValueError:
        timeout_value = None

    env_config = {
        "api_url": os.getenv("AIP_API_URL"),
        "api_key": os.getenv("AIP_API_KEY"),
        "timeout": timeout_value if timeout_value else None,
    }
    env_config = {k: v for k, v in env_config.items() if v not in (None, "", 0)}

    # Merge config sources: context > env > file
    config = {
        **file_config,
        **env_config,
        **{k: v for k, v in context_config.items() if v is not None},
    }

    if not config.get("api_url") or not config.get("api_key"):
        configure_hint = command_hint("configure", slash_command="login", ctx=ctx)
        actions = []
        if configure_hint:
            actions.append(f"Run `{configure_hint}`")
        actions.append("set AIP_* env vars")
        raise click.ClickException(f"Missing api_url/api_key. {' or '.join(actions)}.")

    return Client(
        api_url=config.get("api_url"),
        api_key=config.get("api_key"),
        timeout=float(config.get("timeout") or 30.0),
    )


# ----------------------------- Secret masking ---------------------------- #

# ----------------------------- Fuzzy palette ----------------------------- #


def _extract_display_fields(row: dict[str, Any]) -> tuple[str, str, str, str]:
    """Extract display fields from row data."""
    name = str(row.get("name", "")).strip()
    _id = str(row.get("id", "")).strip()
    type_ = str(row.get("type", "")).strip()
    fw = str(row.get("framework", "")).strip()
    return name, _id, type_, fw


def _build_primary_parts(name: str, type_: str, fw: str) -> list[str]:
    """Build primary display parts from name, type, and framework."""
    parts = []
    if name:
        parts.append(name)
    if type_:
        parts.append(type_)
    if fw:
        parts.append(fw)
    return parts


def _get_fallback_columns(columns: list[tuple]) -> list[tuple]:
    """Get first two visible columns for fallback display."""
    return columns[:2]


def _is_standard_field(k: str) -> bool:
    """Check if field is a standard field to skip."""
    return k in ("id", "name", "type", "framework")


def _extract_fallback_values(row: dict[str, Any], columns: list[tuple]) -> list[str]:
    """Extract fallback values from columns."""
    fallback_parts = []
    for k, _hdr, _style, _w in columns:
        if _is_standard_field(k):
            continue
        val = str(row.get(k, "")).strip()
        if val:
            fallback_parts.append(val)
        if len(fallback_parts) >= 2:
            break
    return fallback_parts


def _build_display_parts(
    name: str, _id: str, type_: str, fw: str, row: dict[str, Any], columns: list[tuple]
) -> list[str]:
    """Build complete display parts list."""
    parts = _build_primary_parts(name, type_, fw)

    if not parts:
        # Use fallback columns
        fallback_columns = _get_fallback_columns(columns)
        parts.extend(_extract_fallback_values(row, fallback_columns))

    if _id:
        parts.append(f"[{_id}]")

    return parts


def _row_display(row: dict[str, Any], columns: list[tuple]) -> str:
    """Build a compact text label for the palette.

    Prefers: name • type • framework • [id] (when available)
    Falls back to first 2 columns + [id].
    """
    name, _id, type_, fw = _extract_display_fields(row)
    parts = _build_display_parts(name, _id, type_, fw, row, columns)
    return " • ".join(parts) if parts else (_id or "(row)")


def _check_fuzzy_pick_requirements() -> bool:
    """Check if fuzzy picking requirements are met."""
    return _HAS_PTK and console.is_terminal and os.isatty(1)


def _build_unique_labels(
    rows: list[dict[str, Any]], columns: list[tuple]
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    """Build unique display labels and reverse mapping."""
    labels = []
    by_label: dict[str, dict[str, Any]] = {}

    for r in rows:
        label = _row_display(r, columns)
        # Ensure uniqueness: if duplicate, suffix with …#n
        if label in by_label:
            i = 2
            base = label
            while f"{base} #{i}" in by_label:
                i += 1
            label = f"{base} #{i}"
        labels.append(label)
        by_label[label] = r

    return labels, by_label


class _FuzzyCompleter:
    """Fuzzy completer for prompt_toolkit."""

    def __init__(self, words: list[str]) -> None:
        self.words = words

    def get_completions(
        self, document: Any, _complete_event: Any
    ) -> Any:  # pragma: no cover
        word = document.get_word_before_cursor()
        if not word:
            return

        word_lower = word.lower()
        for label in self.words:
            label_lower = label.lower()
            if self._fuzzy_match(word_lower, label_lower):
                yield Completion(label, start_position=-len(word))

    def _fuzzy_match(self, search: str, target: str) -> bool:  # pragma: no cover
        """True fuzzy matching: checks if all characters in search appear in order in target."""
        if not search:
            return True

        search_idx = 0
        for char in target:
            if search_idx < len(search) and search[search_idx] == char:
                search_idx += 1
                if search_idx == len(search):
                    return True
        return False


def _perform_fuzzy_search(
    answer: str, labels: list[str], by_label: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """Perform fuzzy search fallback and return best match."""
    # Exact label match
    if answer in by_label:
        return by_label[answer]

    # Fuzzy search fallback
    best_match = None
    best_score = -1

    for label in labels:
        score = _fuzzy_score(answer.lower(), label.lower())
        if score > best_score:
            best_score = score
            best_match = label

    return by_label[best_match] if best_match and best_score > 0 else None


def _fuzzy_pick(
    rows: list[dict[str, Any]], columns: list[tuple], title: str
) -> dict[str, Any] | None:  # pragma: no cover - requires interactive prompt toolkit
    """Open a minimal fuzzy palette using prompt_toolkit.

    Returns the selected row (dict) or None if cancelled/missing deps.
    """
    if not _check_fuzzy_pick_requirements():
        return None

    # Build display labels and mapping
    labels, by_label = _build_unique_labels(rows, columns)

    # Create fuzzy completer
    completer = _FuzzyCompleter(labels)

    try:
        answer = prompt(
            message=f"Find {title.rstrip('s')}: ",
            completer=completer,
            complete_in_thread=True,
            complete_while_typing=True,
        )
    except (KeyboardInterrupt, EOFError):  # pragma: no cover - user cancelled input
        return None
    except Exception:  # pragma: no cover - prompt_toolkit not available in headless env
        return None

    return _perform_fuzzy_search(answer, labels, by_label) if answer else None


def _is_fuzzy_match(search: str, target: str) -> bool:
    """Check if search string is a fuzzy match for target."""
    if not search:
        return True

    search_idx = 0
    for char in target:
        if search_idx < len(search) and search[search_idx] == char:
            search_idx += 1
            if search_idx == len(search):
                return True
    return False


def _calculate_exact_match_bonus(search: str, target: str) -> int:
    """Calculate bonus for exact substring matches."""
    return 100 if search.lower() in target.lower() else 0


def _calculate_consecutive_bonus(search: str, target: str) -> int:
    """Calculate bonus for consecutive character matches."""
    consecutive = 0
    max_consecutive = 0
    search_idx = 0

    for char in target:
        if search_idx < len(search) and search[search_idx] == char:
            consecutive += 1
            max_consecutive = max(max_consecutive, consecutive)
            search_idx += 1
        else:
            consecutive = 0

    return max_consecutive * 10


def _calculate_length_bonus(search: str, target: str) -> int:
    """Calculate bonus for shorter search terms."""
    return (len(target) - len(search)) * 2


def _fuzzy_score(search: str, target: str) -> int:
    """Calculate fuzzy match score.

    Higher score = better match.
    Returns -1 if no match possible.
    """
    if not search:
        return 0

    if not _is_fuzzy_match(search, target):
        return -1  # Not a fuzzy match

    # Calculate score based on different factors
    score = 0
    score += _calculate_exact_match_bonus(search, target)
    score += _calculate_consecutive_bonus(search, target)
    score += _calculate_length_bonus(search, target)

    return score


# ----------------------------- Pretty outputs ---------------------------- #


def _coerce_result_payload(result: Any) -> Any:
    try:
        to_dict = getattr(result, "to_dict", None)
        if callable(to_dict):
            return to_dict()
    except Exception:
        return result
    return result


def _ensure_displayable(payload: Any) -> Any:
    if isinstance(payload, dict | list | str | int | float | bool) or payload is None:
        return payload

    if hasattr(payload, "__dict__"):
        try:
            return dict(payload)
        except Exception:
            try:
                return dict(payload.__dict__)
            except Exception:
                pass

    try:
        return str(payload)
    except Exception:
        return repr(payload)


def _render_markdown_output(data: Any) -> None:
    try:
        console.print(Markdown(str(data)))
    except ImportError:
        click.echo(str(data))


def output_result(
    ctx: Any,
    result: Any,
    title: str = "Result",
    panel_title: str | None = None,
) -> None:
    """Output a result to the console with optional title.

    Args:
        ctx: Click context
        result: Result data to output
        title: Optional title for the output
        panel_title: Optional Rich panel title for structured output
    """
    fmt = _get_view(ctx)

    data = _coerce_result_payload(result)
    data = masking.mask_payload(data)
    data = _ensure_displayable(data)

    if fmt == "json":
        click.echo(json.dumps(data, indent=2, default=str))
        return

    if fmt == "plain":
        click.echo(str(data))
        return

    if fmt == "md":
        _render_markdown_output(data)
        return

    renderable = Pretty(data)
    if panel_title:
        console.print(AIPPanel(renderable, title=panel_title))
    else:
        console.print(markup_text(f"[cyan]{title}:[/cyan]"))
        console.print(renderable)


# ----------------------------- List rendering ---------------------------- #

# Threshold no longer used - fuzzy palette is always default for TTY
# _PICK_THRESHOLD = int(os.getenv("AIP_PICK_THRESHOLD", "5") or "5")


def _normalise_rows(
    items: list[Any], transform_func: Callable[[Any], dict[str, Any]] | None
) -> list[dict[str, Any]]:
    try:
        rows: list[dict[str, Any]] = []
        for item in items:
            if transform_func:
                rows.append(transform_func(item))
            elif hasattr(item, "to_dict"):
                rows.append(item.to_dict())
            elif hasattr(item, "__dict__"):
                rows.append(vars(item))
            elif isinstance(item, dict):
                rows.append(item)
            else:
                rows.append({"value": item})
        return rows
    except Exception:
        return []


def _render_plain_list(
    rows: list[dict[str, Any]], title: str, columns: list[tuple]
) -> None:
    if not rows:
        click.echo(f"No {title.lower()} found.")
        return
    for row in rows:
        row_str = " | ".join(str(row.get(key, "N/A")) for key, _, _, _ in columns)
        click.echo(row_str)


def _render_markdown_list(
    rows: list[dict[str, Any]], title: str, columns: list[tuple]
) -> None:
    if not rows:
        click.echo(f"No {title.lower()} found.")
        return
    headers = [header for _, header, _, _ in columns]
    click.echo(f"| {' | '.join(headers)} |")
    click.echo(f"| {' | '.join('---' for _ in headers)} |")
    for row in rows:
        row_str = " | ".join(str(row.get(key, "N/A")) for key, _, _, _ in columns)
        click.echo(f"| {row_str} |")


def _should_sort_rows(rows: list[dict[str, Any]]) -> bool:
    return (
        os.getenv("AIP_TABLE_NO_SORT", "0") not in ("1", "true", "on")
        and rows
        and isinstance(rows[0], dict)
        and "name" in rows[0]
    )


def _create_table(columns: list[tuple[str, str, str, int | None]], title: str) -> Any:
    table = AIPTable(title=title, expand=True)
    for _key, header, style, width in columns:
        table.add_column(header, style=style, width=width)
    return table


def _build_table_group(
    rows: list[dict[str, Any]], columns: list[tuple], title: str
) -> Group:
    table = _create_table(columns, title)
    for row in rows:
        table.add_row(*[str(row.get(key, "N/A")) for key, _, _, _ in columns])
    footer = markup_text(f"\n[dim]Total {len(rows)} items[/dim]")
    return Group(table, footer)


def _handle_json_output(items: list[Any], rows: list[dict[str, Any]]) -> None:
    """Handle JSON output format."""
    data = (
        rows
        if rows
        else [it.to_dict() if hasattr(it, "to_dict") else it for it in items]
    )
    click.echo(json.dumps(data, indent=2, default=str))


def _handle_plain_output(
    rows: list[dict[str, Any]], title: str, columns: list[tuple]
) -> None:
    """Handle plain text output format."""
    _render_plain_list(rows, title, columns)


def _handle_markdown_output(
    rows: list[dict[str, Any]], title: str, columns: list[tuple]
) -> None:
    """Handle markdown output format."""
    _render_markdown_list(rows, title, columns)


def _handle_empty_items(title: str) -> None:
    """Handle case when no items are found."""
    console.print(markup_text(f"[yellow]No {title.lower()} found.[/yellow]"))


def _should_use_fuzzy_picker() -> bool:
    """Return True when the interactive fuzzy picker can be shown."""
    return console.is_terminal and os.isatty(1)


def _try_fuzzy_pick(
    rows: list[dict[str, Any]], columns: list[tuple], title: str
) -> dict[str, Any] | None:
    """Best-effort fuzzy selection; returns None if the picker fails."""
    if not _should_use_fuzzy_picker():
        return None

    try:
        return _fuzzy_pick(rows, columns, title)
    except Exception:
        logger.debug("Fuzzy picker failed; falling back to table output", exc_info=True)
        return None


def _resource_tip_command(title: str) -> str | None:
    """Resolve the follow-up command hint for the given table title."""
    title_lower = title.lower()
    mapping = {
        "agent": ("agents get", "agents"),
        "tool": ("tools get", None),
        "mcp": ("mcps get", None),
        "model": ("models list", None),  # models only ship a list command
    }
    for keyword, (cli_command, slash_command) in mapping.items():
        if keyword in title_lower:
            return command_hint(cli_command, slash_command=slash_command)
    return command_hint("agents get", slash_command="agents")


def _print_selection_tip(title: str) -> None:
    """Print the contextual follow-up tip after a fuzzy selection."""
    tip_cmd = _resource_tip_command(title)
    if tip_cmd:
        console.print(
            markup_text(f"\n[dim]Tip: use `{tip_cmd} <ID>` for details[/dim]")
        )


def _handle_fuzzy_pick_selection(
    rows: list[dict[str, Any]], columns: list[tuple], title: str
) -> bool:
    """Handle fuzzy picker selection, returns True if selection was made."""
    picked = _try_fuzzy_pick(rows, columns, title)
    if picked is None:
        return False

    table = _create_table(columns, title)
    table.add_row(*[str(picked.get(key, "N/A")) for key, _, _, _ in columns])
    console.print(table)
    _print_selection_tip(title)
    return True


def _handle_table_output(
    rows: list[dict[str, Any]],
    columns: list[tuple],
    title: str,
    *,
    use_pager: bool | None = None,
) -> None:
    """Handle table output with paging."""
    content = _build_table_group(rows, columns, title)
    should_page = (
        pager._should_page_output(len(rows), console.is_terminal and os.isatty(1))
        if use_pager is None
        else use_pager
    )

    if should_page:
        ansi = pager._render_ansi(content)
        if not pager._page_with_system_pager(ansi):
            with console.pager(styles=True):
                console.print(content)
    else:
        console.print(content)


def output_list(
    ctx: Any,
    items: list[Any],
    title: str,
    columns: list[tuple[str, str, str, int | None]],
    transform_func: Callable | None = None,
    *,
    skip_picker: bool = False,
    use_pager: bool | None = None,
) -> None:
    """Display a list with optional fuzzy palette for quick selection."""
    fmt = _get_view(ctx)
    rows = _normalise_rows(items, transform_func)
    rows = masking.mask_rows(rows)

    if fmt == "json":
        _handle_json_output(items, rows)
        return

    if fmt == "plain":
        _handle_plain_output(rows, title, columns)
        return

    if fmt == "md":
        _handle_markdown_output(rows, title, columns)
        return

    if not items:
        _handle_empty_items(title)
        return

    if _should_sort_rows(rows):
        try:
            rows = sorted(rows, key=lambda r: str(r.get("name", "")).lower())
        except Exception:
            pass

    if not skip_picker and _handle_fuzzy_pick_selection(rows, columns, title):
        return

    _handle_table_output(rows, columns, title, use_pager=use_pager)


# ------------------------- Ambiguity handling --------------------------- #


def coerce_to_row(item: Any, keys: list[str]) -> dict[str, Any]:
    """Coerce an item (dict or object) to a row dict with specified keys.

    Args:
        item: The item to coerce (dict or object with attributes)
        keys: List of keys/attribute names to extract

    Returns:
        Dict with the extracted values, "N/A" for missing values
    """
    result = {}
    for key in keys:
        if isinstance(item, dict):
            value = item.get(key, "N/A")
        else:
            value = getattr(item, key, "N/A")
        result[key] = str(value) if value is not None else "N/A"
    return result


def build_renderer(
    _ctx: Any,
    *,
    save_path: str | os.PathLike[str] | None,
    theme: str = "dark",
    verbose: bool = False,
    _tty_enabled: bool = True,
    live: bool | None = None,
    snapshots: bool | None = None,
) -> tuple[RichStreamRenderer, Console | CapturingConsole]:
    """Build renderer and capturing console for CLI commands.

    Args:
        _ctx: Click context object for CLI operations.
        save_path: Path to save output to (enables capturing console).
        theme: Color theme ("dark" or "light").
        verbose: Whether to enable verbose mode.
        _tty_enabled: Whether TTY is available for interactive features.
        live: Whether to enable live rendering mode (overrides verbose default).
        snapshots: Whether to capture and store snapshots.

    Returns:
        Tuple of (renderer, capturing_console) for streaming output.
    """
    # Use capturing console if saving output
    working_console = console
    if save_path:
        working_console = CapturingConsole(console, capture=True)

    # Configure renderer based on verbose mode and explicit overrides
    if live is None:
        live_enabled = not verbose  # Disable live mode in verbose (unless overridden)
    else:
        live_enabled = bool(live)

    renderer_cfg = RendererConfig(
        theme=theme,
        style="debug" if verbose else "pretty",
        live=live_enabled,
        show_delegate_tool_panels=True,
        append_finished_snapshots=bool(snapshots)
        if snapshots is not None
        else RendererConfig.append_finished_snapshots,
    )

    # Create the renderer instance
    renderer = RichStreamRenderer(
        working_console.original_console
        if isinstance(working_console, CapturingConsole)
        else working_console,
        cfg=renderer_cfg,
        verbose=verbose,
    )

    # Link the renderer back to the slash session when running from the palette.
    try:
        ctx_obj = getattr(_ctx, "obj", None)
        if isinstance(ctx_obj, dict):
            session = ctx_obj.get("_slash_session")
            if session and hasattr(session, "register_active_renderer"):
                session.register_active_renderer(renderer)
    except Exception:
        # Never let session bookkeeping break renderer creation
        pass

    return renderer, working_console


def _build_resource_labels(resources: list[Any]) -> tuple[list[str], dict[str, Any]]:
    """Build unique display labels for resources."""
    labels = []
    by_label: dict[str, Any] = {}

    for resource in resources:
        name = getattr(resource, "name", "Unknown")
        _id = getattr(resource, "id", "Unknown")

        # Create display label
        label_parts = []
        if name and name != "Unknown":
            label_parts.append(name)
        label_parts.append(f"[{_id[:8]}...]")  # Show first 8 chars of ID
        label = " • ".join(label_parts)

        # Ensure uniqueness
        if label in by_label:
            i = 2
            base = label
            while f"{base} #{i}" in by_label:
                i += 1
            label = f"{base} #{i}"

        labels.append(label)
        by_label[label] = resource

    return labels, by_label


def _fuzzy_pick_for_resources(
    resources: list[Any], resource_type: str, _search_term: str
) -> Any | None:  # pragma: no cover - interactive selection helper
    """Fuzzy picker for resource objects, similar to _fuzzy_pick but without column dependencies.

    Args:
        resources: List of resource objects to choose from
        resource_type: Type of resource (e.g., "agent", "tool")
        search_term: The search term that led to multiple matches

    Returns:
        Selected resource object or None if cancelled/no selection
    """
    if not _check_fuzzy_pick_requirements():
        return None

    # Build labels and mapping
    labels, by_label = _build_resource_labels(resources)

    # Create fuzzy completer
    completer = _FuzzyCompleter(labels)

    try:
        answer = prompt(
            message=f"Find 🤖 {resource_type.title()}: ",
            completer=completer,
            complete_in_thread=True,
            complete_while_typing=True,
        )
    except (KeyboardInterrupt, EOFError):
        return None

    return _perform_fuzzy_search(answer, labels, by_label) if answer else None


def _resolve_by_id(ref: str, get_by_id: Callable) -> Any | None:
    """Resolve resource by UUID if ref is a valid UUID."""
    if is_uuid(ref):
        return get_by_id(ref)
    return None


def _resolve_by_name_multiple_with_select(matches: list[Any], select: int) -> Any:
    """Resolve multiple matches using select parameter."""
    idx = int(select) - 1
    if not (0 <= idx < len(matches)):
        raise click.ClickException(f"--select must be 1..{len(matches)}")
    return matches[idx]


def _resolve_by_name_multiple_fuzzy(
    ctx: Any, ref: str, matches: list[Any], label: str
) -> Any:
    """Resolve multiple matches using fuzzy picker interface."""
    picked = _fuzzy_pick_for_resources(matches, label.lower(), ref)
    if picked:
        return picked
    # Fallback to original ambiguity handler if fuzzy picker fails
    return handle_ambiguous_resource(ctx, label.lower(), ref, matches)


def _resolve_by_name_multiple_questionary(
    ctx: Any, ref: str, matches: list[Any], label: str
) -> Any:
    """Resolve multiple matches using questionary interface."""
    return handle_ambiguous_resource(ctx, label.lower(), ref, matches)


def resolve_resource(
    ctx: Any,
    ref: str,
    *,
    get_by_id: Callable,
    find_by_name: Callable,
    label: str,
    select: int | None = None,
    interface_preference: str = "fuzzy",
    status_indicator: Any | None = None,
) -> Any | None:
    """Resolve resource reference (ID or name) with ambiguity handling.

    Args:
        ctx: Click context
        ref: Resource reference (ID or name)
        get_by_id: Function to get resource by ID
        find_by_name: Function to find resources by name
        label: Resource type label for error messages
        select: Optional selection index for ambiguity resolution
        interface_preference: "fuzzy" for fuzzy picker, "questionary" for up/down list
        status_indicator: Optional Rich status indicator for wait animations

    Returns:
        Resolved resource object
    """
    spinner = status_indicator
    _spinner_update(spinner, f"[bold blue]Resolving {label}…[/bold blue]")

    # Try to resolve by ID first
    _spinner_update(spinner, f"[bold blue]Fetching {label} by ID…[/bold blue]")
    result = _resolve_by_id(ref, get_by_id)
    if result is not None:
        _spinner_update(spinner, f"[bold green]{label} found[/bold green]")
        return result

    # If get_by_id returned None, the resource doesn't exist
    if is_uuid(ref):
        _spinner_stop(spinner)
        raise click.ClickException(f"{label} '{ref}' not found")

    # Find resources by name
    _spinner_update(
        spinner, f"[bold blue]Searching {label}s matching '{ref}'…[/bold blue]"
    )
    matches = find_by_name(name=ref)
    if not matches:
        _spinner_stop(spinner)
        raise click.ClickException(f"{label} '{ref}' not found")

    if len(matches) == 1:
        _spinner_update(spinner, f"[bold green]{label} found[/bold green]")
        return matches[0]

    # Multiple matches found, handle ambiguity
    if select:
        _spinner_stop(spinner)
        return _resolve_by_name_multiple_with_select(matches, select)

    # Choose interface based on preference
    _spinner_stop(spinner)
    if interface_preference == "fuzzy":
        return _resolve_by_name_multiple_fuzzy(ctx, ref, matches, label)
    else:
        return _resolve_by_name_multiple_questionary(ctx, ref, matches, label)


def _handle_json_view_ambiguity(matches: list[Any]) -> Any:
    """Handle ambiguity in JSON view by returning first match."""
    return matches[0]


def _handle_questionary_ambiguity(
    resource_type: str, ref: str, matches: list[Any]
) -> Any:
    """Handle ambiguity using questionary interactive interface."""
    if not (questionary and os.getenv("TERM") and os.isatty(0) and os.isatty(1)):
        raise click.ClickException("Interactive selection not available")

    # Escape special characters for questionary
    safe_resource_type = resource_type.replace("{", "{{").replace("}", "}}")
    safe_ref = ref.replace("{", "{{").replace("}", "}}")

    picked_idx = questionary.select(
        f"Multiple {safe_resource_type}s match '{safe_ref}'. Pick one:",
        choices=[
            questionary.Choice(
                title=f"{getattr(m, 'name', '—').replace('{', '{{').replace('}', '}}')} — {getattr(m, 'id', '').replace('{', '{{').replace('}', '}}')}",
                value=i,
            )
            for i, m in enumerate(matches)
        ],
        use_indicator=True,
        qmark="🧭",
        instruction="↑/↓ to select • Enter to confirm",
    ).ask()
    if picked_idx is None:
        raise click.ClickException("Selection cancelled")
    return matches[picked_idx]


def _handle_fallback_numeric_ambiguity(
    resource_type: str, ref: str, matches: list[Any]
) -> Any:
    """Handle ambiguity using numeric prompt fallback."""
    # Escape special characters for display
    safe_resource_type = resource_type.replace("{", "{{").replace("}", "}}")
    safe_ref = ref.replace("{", "{{").replace("}", "}}")

    console.print(
        markup_text(
            f"[yellow]Multiple {safe_resource_type}s found matching '{safe_ref}':[/yellow]"
        )
    )
    table = AIPTable(
        title=f"Select {safe_resource_type.title()}",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("ID", style="dim", width=36)
    table.add_column("Name", style="cyan")
    for i, m in enumerate(matches, 1):
        table.add_row(str(i), str(getattr(m, "id", "")), str(getattr(m, "name", "")))
    console.print(table)
    choice_str = click.prompt(
        f"Select {safe_resource_type} (1-{len(matches)})",
    )
    try:
        choice = int(choice_str)
    except ValueError:
        raise click.ClickException("Invalid selection")
    if 1 <= choice <= len(matches):
        return matches[choice - 1]
    raise click.ClickException("Invalid selection")


def _should_fallback_to_numeric_prompt(exception: Exception) -> bool:
    """Determine if we should fallback to numeric prompt for this exception."""
    # Re-raise cancellation - user explicitly cancelled
    if "Selection cancelled" in str(exception):
        return False

    # Fall back to numeric prompt for other exceptions
    return True


def handle_ambiguous_resource(
    ctx: Any, resource_type: str, ref: str, matches: list[Any]
) -> Any:
    """Handle multiple resource matches gracefully."""
    if _get_view(ctx) == "json":
        return _handle_json_view_ambiguity(matches)

    try:
        return _handle_questionary_ambiguity(resource_type, ref, matches)
    except Exception as e:
        if _should_fallback_to_numeric_prompt(e):
            try:
                return _handle_fallback_numeric_ambiguity(resource_type, ref, matches)
            except Exception:
                # If fallback also fails, re-raise the original exception
                raise e
        else:
            # Re-raise cancellation exceptions
            raise
