"""Formatting helpers for renderer.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from typing import Any

# Constants for argument formatting
DEFAULT_ARGS_MAX_LEN = 100
IMPORTANT_PARAMETER_KEYS = [
    "model",
    "temperature",
    "max_tokens",
    "top_p",
    "frequency_penalty",
    "presence_penalty",
    "query",
    "url",
]
SECRET_VALUE_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # OpenAI API keys (at least 20 chars)
    re.compile(r"ya29\.[a-zA-Z0-9_-]+"),  # Google OAuth tokens
    re.compile(r"ghp_[a-zA-Z0-9]{20,}"),  # GitHub tokens (at least 20 chars)
    re.compile(r"gho_[a-zA-Z0-9]{20,}"),  # GitHub tokens (at least 20 chars)
    re.compile(r"ghu_[a-zA-Z0-9]{20,}"),  # GitHub tokens (at least 20 chars)
    re.compile(r"ghs_[a-zA-Z0-9]{20,}"),  # GitHub tokens (at least 20 chars)
    re.compile(r"ghr_[a-zA-Z0-9]{20,}"),  # GitHub tokens (at least 20 chars)
    re.compile(r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"),  # JWT tokens
]
SENSITIVE_PATTERNS = re.compile(
    r"password\s*[:=]\s*[^\s,}]+|secret\s*[:=]\s*[^\s,}]+|token\s*[:=]\s*[^\s,}]+|key\s*[:=]\s*[^\s,}]+|api_key\s*[:=]\s*[^\s,}]+|^password$|^secret$|^token$|^key$|^api_key$",
    re.IGNORECASE,
)


def _truncate_string(s: str, max_len: int) -> str:
    """Truncate a string to a maximum length."""
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "…"


def mask_secrets_in_string(text: str) -> str:
    """Mask sensitive information in a string."""
    result = text
    for pattern in SECRET_VALUE_PATTERNS:
        result = re.sub(pattern, "••••••", result)
    return result


def redact_sensitive(text: str | dict | list) -> str | dict | list:
    """Redact sensitive information in a string, dict, or list."""
    if isinstance(text, dict):
        return _redact_dict_values(text)
    elif isinstance(text, list):
        return _redact_list_items(text)
    elif isinstance(text, str):
        return _redact_string_content(text)
    else:
        return text


def _redact_dict_values(text: dict) -> dict:
    """Recursively process dictionary values and redact sensitive keys."""
    result = {}
    for key, value in text.items():
        if _is_sensitive_key(key):
            result[key] = "••••••"
        elif _should_recurse_redaction(value):
            result[key] = redact_sensitive(value)
        else:
            result[key] = value
    return result


def _redact_list_items(text: list) -> list:
    """Recursively process list items."""
    return [redact_sensitive(item) for item in text]


def _redact_string_content(text: str) -> str:
    """Process string - first mask secrets, then redact sensitive patterns."""
    result = text
    # First mask secrets
    for pattern in SECRET_VALUE_PATTERNS:
        result = re.sub(pattern, "••••••", result)
    # Then redact sensitive patterns
    result = re.sub(
        SENSITIVE_PATTERNS,
        lambda m: m.group(0).split("=")[0] + "=••••••",
        result,
    )
    return result


def _is_sensitive_key(key: str) -> bool:
    """Check if a key contains sensitive information."""
    key_lower = key.lower()
    return any(
        sensitive in key_lower
        for sensitive in ["password", "secret", "token", "key", "api_key"]
    )


def _should_recurse_redaction(value: Any) -> bool:
    """Check if a value should be recursively processed."""
    return isinstance(value, dict | list) or isinstance(value, str)


def pretty_args(args: dict | None, max_len: int = DEFAULT_ARGS_MAX_LEN) -> str:
    """Format arguments in a pretty way."""
    if not args:
        return "{}"

    # Mask secrets first by recursively processing the structure
    try:
        masked_args = redact_sensitive(args)
    except Exception:
        # Fallback to original args if redact_sensitive fails
        masked_args = args

    # Convert to JSON string and truncate if needed
    try:
        import json

        args_str = json.dumps(masked_args, ensure_ascii=False, separators=(",", ":"))
        return _truncate_string(args_str, max_len)
    except (TypeError, ValueError, Exception):
        # Fallback to string representation if JSON serialization fails
        args_str = str(masked_args)
        return _truncate_string(args_str, max_len)


def pretty_out(output: any, max_len: int = DEFAULT_ARGS_MAX_LEN) -> str:
    """Format output in a pretty way."""
    if output is None:
        return "None"

    if isinstance(output, str):
        # Mask secrets in string output
        masked_output = mask_secrets_in_string(output)

        # Remove LaTeX commands (common math expressions)
        masked_output = re.sub(r"\\[a-zA-Z]+\{[^}]*\}", "", masked_output)
        masked_output = re.sub(r"\\[a-zA-Z]+", "", masked_output)

        # Strip leading/trailing whitespace but preserve internal spacing
        masked_output = masked_output.strip()
        # Replace newlines with spaces to preserve formatting
        masked_output = masked_output.replace("\n", " ")
        return _truncate_string(masked_output, max_len)

    # For other types, convert to string and truncate
    output_str = str(output)
    return _truncate_string(output_str, max_len)


def get_spinner_char() -> str:
    """Get the next character for a spinner animation.

    Returns:
        A single character from the spinner frames based on current time
    """
    frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    return frames[int(time.time() * 10) % len(frames)]


def get_step_icon(step_kind: str) -> str:
    """Get the appropriate icon for a step kind."""
    if step_kind == "tool":
        return "⚙️"  # Gear emoji for tool
    if step_kind == "delegate":
        return "🤝"  # Handshake for delegate
    if step_kind == "agent":
        return "🧠"  # Brain emoji for agent
    return ""


def is_step_finished(step: Any) -> bool:
    """Check if a step is finished.

    Args:
        step: The step object to check

    Returns:
        True if the step status is "finished", False otherwise
    """
    return getattr(step, "status", None) == "finished"


def format_main_title(
    header_text: str,
    has_running_steps: bool,
    get_spinner_char: Callable[[], str],
) -> str:
    """Generate the main panel title with dynamic status indicators.

    Args:
        header_text: The header text from the renderer
        has_running_steps: Whether there are running steps
        get_spinner_char: Function to get spinner character

    Returns:
        A formatted title string showing the agent name and status.
    """
    # base name
    name = (header_text or "").strip() or "Assistant"
    # strip leading rule emojis if present
    name = name.replace("—", " ").strip()
    # spinner if still working
    mark = "✓" if not has_running_steps else get_spinner_char()
    return f"{name}  {mark}"


def print_header_once(
    console: Any,
    text: str,
    last_header: str,
    rules_enabled: bool,
    style: str | None = None,
) -> str:
    """Print header text only when it changes to avoid duplicate output.

    Args:
        console: Rich console instance
        text: The header text to display
        last_header: The last header text that was printed
        rules_enabled: Whether header rules are enabled
        style: Optional Rich style for the header rule

    Returns:
        The updated last_header value
    """
    if not rules_enabled:
        return text
    if text and text != last_header:
        try:
            console.rule(text, style=style)
        except Exception:
            console.print(text)
        return text
    return last_header
