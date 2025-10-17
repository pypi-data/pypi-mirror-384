"""Debug rendering utilities for verbose SSE event display.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import json
from datetime import datetime
from time import monotonic
from typing import Any

from rich.console import Console
from rich.markdown import Markdown

from glaip_sdk.rich_components import AIPPanel


def _calculate_relative_time(started_ts: float | None) -> tuple[float, str]:
    """Calculate relative time since start."""
    now_mono = monotonic()
    rel = 0.0
    if started_ts is not None:
        rel = max(0.0, now_mono - started_ts)

    ts_full = datetime.now().strftime("%H:%M:%S.%f")
    ts_ms = ts_full[:-3]  # trim to milliseconds

    return rel, ts_ms


def _get_event_metadata(event: dict[str, Any]) -> tuple[str, str | None]:
    """Extract event kind and status."""
    sse_kind = (event.get("metadata") or {}).get("kind") or "event"
    status_str = event.get("status") or (event.get("metadata") or {}).get("status")
    return sse_kind, status_str


def _build_debug_title(
    sse_kind: str, status_str: str | None, ts_ms: str, rel: float
) -> str:
    """Build the debug event title."""
    if status_str:
        return f"SSE: {sse_kind} — {status_str} @ {ts_ms} (+{rel:.2f}s)"
    else:
        return f"SSE: {sse_kind} @ {ts_ms} (+{rel:.2f}s)"


def _dejson_value(obj: Any) -> Any:
    """Deep-parse JSON strings in nested objects."""
    if isinstance(obj, dict):
        return {k: _dejson_value(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_dejson_value(x) for x in obj]
    if isinstance(obj, str):
        s = obj.strip()
        if (s.startswith("{") and s.endswith("}")) or (
            s.startswith("[") and s.endswith("]")
        ):
            try:
                return _dejson_value(json.loads(s))
            except Exception:
                return obj
        return obj
    return obj


def _format_event_json(event: dict[str, Any]) -> str:
    """Format event as JSON with deep parsing."""
    try:
        return json.dumps(_dejson_value(event), indent=2, ensure_ascii=False)
    except Exception:
        return str(event)


def _get_border_color(sse_kind: str) -> str:
    """Get border color for event type."""
    border_map = {
        "agent_step": "blue",
        "content": "green",
        "final_response": "green",
        "status": "yellow",
        "artifact": "grey42",
    }
    return border_map.get(sse_kind, "grey42")


def _create_debug_panel(title: str, event_json: str, border: str) -> AIPPanel:
    """Create the debug panel."""
    md = Markdown(f"```json\n{event_json}\n```", code_theme="monokai")
    return AIPPanel(md, title=title, border_style=border)


def render_debug_event(
    event: dict[str, Any], console: Console, started_ts: float | None = None
) -> None:
    """Render a debug panel for an SSE event.

    Args:
        event: The SSE event data
        console: Rich console to print to
        started_ts: Monotonic timestamp when streaming started
    """
    try:
        # Calculate timing information
        rel, ts_ms = _calculate_relative_time(started_ts)

        # Extract event metadata
        sse_kind, status_str = _get_event_metadata(event)

        # Build title
        title = _build_debug_title(sse_kind, status_str, ts_ms, rel)

        # Format event JSON
        event_json = _format_event_json(event)

        # Get border color
        border = _get_border_color(sse_kind)

        # Create and print panel
        panel = _create_debug_panel(title, event_json, border)
        console.print(panel)

    except Exception as e:
        # Debug helpers must not break streaming
        print(f"Debug error: {e}")  # Fallback debug output
