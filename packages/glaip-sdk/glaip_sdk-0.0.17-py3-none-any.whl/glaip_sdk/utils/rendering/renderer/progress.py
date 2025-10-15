"""Progress and timing utilities for the renderer package.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from time import monotonic

from glaip_sdk.utils.rendering.formatting import get_spinner_char


def get_spinner() -> str:
    """Return the current animated spinner character for visual feedback."""
    return get_spinner_char()


def format_working_indicator(
    started_at: float | None,
    server_elapsed_time: float | None = None,
    streaming_started_at: float | None = None,
) -> str:
    """Format a working indicator with elapsed time.

    Args:
        started_at: Timestamp when work started, or None
        server_elapsed_time: Server-reported elapsed time if available
        streaming_started_at: When streaming started

    Returns:
        Formatted working indicator string with elapsed time
    """
    chip = "Working..."

    # Use server timing if available (more accurate)
    if server_elapsed_time is not None and streaming_started_at is not None:
        elapsed = server_elapsed_time
    elif started_at:
        try:
            elapsed = monotonic() - started_at
        except Exception:
            return chip
    else:
        return chip

    if elapsed >= 1:
        chip = f"Working... ({elapsed:.2f}s)"
    else:
        elapsed_ms = int(elapsed * 1000)
        chip = f"Working... ({elapsed_ms}ms)" if elapsed_ms > 0 else "Working... (<1ms)"
    return chip


def format_elapsed_time(elapsed_seconds: float) -> str:
    """Format elapsed time in a human-readable format.

    Args:
        elapsed_seconds: Time in seconds

    Returns:
        Formatted time string
    """
    if elapsed_seconds >= 60:
        minutes = int(elapsed_seconds // 60)
        seconds = elapsed_seconds % 60
        return f"{minutes}m {seconds:.1f}s"
    elif elapsed_seconds >= 1:
        return f"{elapsed_seconds:.2f}s"
    else:
        ms = int(elapsed_seconds * 1000)
        return f"{ms}ms" if ms > 0 else "<1ms"


def is_delegation_tool(tool_name: str) -> bool:
    """Check if a tool name indicates delegation functionality.

    Args:
        tool_name: The name of the tool to check

    Returns:
        True if this is a delegation tool
    """
    return (
        tool_name.startswith("delegate_to_")
        or tool_name.startswith("delegate_")
        or "sub_agent" in tool_name.lower()
    )


def format_tool_title(tool_name: str) -> str:
    """Format tool name for panel title display.

    Args:
        tool_name: The full tool name (may include file paths)

    Returns:
        Formatted title string suitable for panel display
    """
    # Check if this is a delegation tool
    if is_delegation_tool(tool_name):
        # Extract the sub-agent name from delegation tool names
        if tool_name.startswith("delegate_to_"):
            sub_agent_name = tool_name.replace("delegate_to_", "")
            return f"Sub-Agent: {sub_agent_name}"
        elif tool_name.startswith("delegate_"):
            sub_agent_name = tool_name.replace("delegate_", "")
            return f"Sub-Agent: {sub_agent_name}"

    # For regular tools, clean up the name
    # Remove file path prefixes if present
    if "/" in tool_name:
        tool_name = tool_name.split("/")[-1]
    if "." in tool_name:
        tool_name = tool_name.split(".")[0]

    # Convert snake_case to Title Case
    return tool_name.replace("_", " ").title()
