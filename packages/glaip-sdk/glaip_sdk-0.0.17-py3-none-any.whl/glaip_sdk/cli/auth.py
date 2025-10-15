"""Authentication export helpers for MCP CLI commands.

This module provides utilities for preparing authentication data for export,
including interactive secret capture and placeholder generation.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from collections.abc import Iterable, Mapping
from typing import Any

import click
from rich.console import Console


def prepare_authentication_export(
    auth: dict[str, Any] | None,
    *,
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> dict[str, Any] | None:
    """Prepare authentication data for export with secret handling.

    This function processes authentication objects from MCP resources and prepares
    them for export. It handles secret capture (interactive or placeholder mode),
    reconstructs proper authentication structures from helper metadata, and ensures
    helper metadata doesn't leak into the final export.

    Args:
        auth: Authentication dictionary from an MCP resource. May contain helper
            metadata like ``header_keys`` that should be consumed and removed.
        prompt_for_secrets: If True, interactively prompt for missing secrets.
            If False, use ``placeholder`` automatically.
        placeholder: Placeholder text to use for missing secrets when not prompting.
        console: Rich ``Console`` instance for user interaction and warnings.

    Returns:
        A prepared authentication dictionary ready for export, or ``None`` if
        ``auth`` is ``None``.

    Notes:
        - Helper metadata (for example, ``header_keys``) is consumed to rebuild
          structures but never appears in the final output.
        - When ``prompt_for_secrets`` is False and stdin is not a TTY, a warning is
          logged.
        - Empty user input during prompts defaults to the placeholder value.
    """
    if auth is None:
        return None

    auth_type = auth.get("type")

    # Handle no-auth case
    if auth_type == "no-auth":
        return {"type": "no-auth"}

    # Handle bearer-token authentication
    if auth_type == "bearer-token":
        return _prepare_bearer_token_auth(
            auth, prompt_for_secrets, placeholder, console
        )

    # Handle api-key authentication
    if auth_type == "api-key":
        return _prepare_api_key_auth(auth, prompt_for_secrets, placeholder, console)

    # Handle custom-header authentication
    if auth_type == "custom-header":
        return _prepare_custom_header_auth(
            auth, prompt_for_secrets, placeholder, console
        )

    # Unknown auth type - return as-is but strip helper metadata
    result = auth.copy()
    result.pop("header_keys", None)
    return result


def _get_token_value(
    prompt_for_secrets: bool, placeholder: str, console: Console
) -> str:
    """Get bearer token value either by prompting or using a placeholder.

    Args:
        prompt_for_secrets: If True, prompt for the token value.
        placeholder: Placeholder to use when not prompting or when input is empty.
        console: Rich ``Console`` used to display informational messages.

    Returns:
        The token string, either provided by the user or the placeholder.
    """
    if prompt_for_secrets:
        console.print(
            "[yellow]Bearer token is missing or redacted. "
            "Please provide the token.[/yellow]"
        )
        token_value = click.prompt(
            "Bearer token (leave blank for placeholder)",
            default="",
            show_default=False,
        )
        return token_value.strip() or placeholder

    if not click.get_text_stream("stdin").isatty():
        console.print(
            "[yellow]⚠️  Non-interactive mode: "
            "using placeholder for bearer token[/yellow]"
        )
    return placeholder


def _build_bearer_headers(auth: dict[str, Any], token_value: str) -> dict[str, str]:
    """Build headers for bearer token authentication.

    Args:
        auth: Original authentication dictionary which may include ``header_keys``.
        token_value: The token value to embed into the headers.

    Returns:
        A dictionary of HTTP headers including the Authorization header when
        applicable.
    """
    header_keys = auth.get("header_keys", ["Authorization"])
    headers = {}
    for key in header_keys:
        # Prepend "Bearer " if this is Authorization header
        if key.lower() == "authorization":
            headers[key] = f"Bearer {token_value}"
        else:
            headers[key] = token_value
    return headers


def _prepare_bearer_token_auth(
    auth: dict[str, Any],
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> dict[str, Any]:
    """Prepare bearer-token authentication for export.

    Args:
        auth: Original authentication dictionary.
        prompt_for_secrets: Whether to prompt for secrets.
        placeholder: Placeholder value for secrets.
        console: Rich ``Console`` for interaction.

    Returns:
        A prepared ``bearer-token`` authentication dictionary.
    """
    # Check if token exists and is not masked
    token = auth.get("token")
    has_valid_token = token and token not in (None, "", "***", "REDACTED")

    # If we have a valid token, use it
    if has_valid_token:
        return {"type": "bearer-token", "token": token}

    # Get token value (prompt or placeholder)
    token_value = _get_token_value(prompt_for_secrets, placeholder, console)

    # Check if original had headers structure
    if "headers" in auth or "header_keys" in auth:
        headers = _build_bearer_headers(auth, token_value)
        return {"type": "bearer-token", "headers": headers}

    # Use token field structure
    return {"type": "bearer-token", "token": token_value}


def _extract_api_key_name(auth: dict[str, Any]) -> str | None:
    """Extract the API key name from an authentication dictionary.

    Args:
        auth: Authentication dictionary that may contain ``key`` or ``header_keys``.

    Returns:
        The API key name if available, otherwise ``None``.
    """
    key_name = auth.get("key")
    if not key_name and "header_keys" in auth:
        header_keys = auth["header_keys"]
        if isinstance(header_keys, list) and header_keys:
            key_name = header_keys[0]
    return key_name


def _get_api_key_value(
    key_name: str | None,
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> str:
    """Get API key value either by prompting or using a placeholder.

    Args:
        key_name: The name of the API key; used in prompt messages.
        prompt_for_secrets: If True, prompt for the API key value.
        placeholder: Placeholder to use when not prompting or when input is empty.
        console: Rich ``Console`` used to display informational messages.

    Returns:
        The API key value, either provided by the user or the placeholder.
    """
    if prompt_for_secrets:
        console.print(
            f"[yellow]API key value for '{key_name}' is missing or redacted.[/yellow]"
        )
        key_value = click.prompt(
            f"API key value for '{key_name}' (leave blank for placeholder)",
            default="",
            show_default=False,
        )
        return key_value.strip() or placeholder

    if not click.get_text_stream("stdin").isatty():
        console.print(
            f"[yellow]⚠️  Non-interactive mode: "
            f"using placeholder for API key '{key_name}'[/yellow]"
        )
    return placeholder


def _build_api_key_headers(
    auth: dict[str, Any], key_name: str | None, key_value: str
) -> dict[str, str]:
    """Build headers for API key authentication.

    Args:
        auth: Original authentication dictionary which may include ``header_keys``.
        key_name: The header key name if present.
        key_value: The API key value to populate.

    Returns:
        A dictionary of HTTP headers for API key authentication.
    """
    header_keys = auth.get("header_keys", [key_name] if key_name else [])
    return {key: key_value for key in header_keys}


def _prepare_api_key_auth(
    auth: dict[str, Any],
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> dict[str, Any]:
    """Prepare api-key authentication for export.

    Args:
        auth: Original authentication dictionary.
        prompt_for_secrets: Whether to prompt for secrets.
        placeholder: Placeholder value for secrets.
        console: Rich ``Console`` for interaction.

    Returns:
        A prepared ``api-key`` authentication dictionary.
    """
    # Extract key name and value
    key_name = _extract_api_key_name(auth)
    key_value = auth.get("value")

    # Check if we have a valid value
    has_valid_value = key_value and key_value not in (None, "", "***", "REDACTED")

    # Capture or use placeholder for value
    if not has_valid_value:
        key_value = _get_api_key_value(
            key_name, prompt_for_secrets, placeholder, console
        )

    # Check if original had headers structure
    if "headers" in auth or "header_keys" in auth:
        headers = _build_api_key_headers(auth, key_name, key_value)
        return {"type": "api-key", "headers": headers}

    # Use key/value field structure
    return {"type": "api-key", "key": key_name, "value": key_value}


def _prepare_custom_header_auth(
    auth: dict[str, Any],
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> dict[str, Any]:
    """Prepare custom-header authentication for export.

    Args:
        auth: Original authentication dictionary.
        prompt_for_secrets: Whether to prompt for header values.
        placeholder: Placeholder value when not prompting or input is empty.
        console: Rich ``Console`` for interaction.

    Returns:
        A prepared ``custom-header`` authentication dictionary.
    """
    existing_headers: dict[str, Any] = auth.get("headers", {})
    header_names = _extract_header_names(existing_headers, auth.get("header_keys", []))

    if not header_names:
        return {"type": "custom-header", "headers": {}}

    headers = _build_custom_headers(
        existing_headers=existing_headers,
        header_names=header_names,
        prompt_for_secrets=prompt_for_secrets,
        placeholder=placeholder,
        console=console,
    )

    return {"type": "custom-header", "headers": headers}


def _extract_header_names(
    existing_headers: Mapping[str, Any] | None, header_keys: Iterable[str] | None
) -> list[str]:
    """Extract the list of header names to process.

    Args:
        existing_headers: Existing headers mapping from the auth object.
        header_keys: Optional helper metadata listing header names.

    Returns:
        A list of header names to process.
    """
    if existing_headers:
        return list(existing_headers.keys())
    if header_keys:
        return list(header_keys)
    return []


def _is_valid_secret(value: Any) -> bool:
    """Determine whether a secret value is present and not masked.

    Args:
        value: The value to test.

    Returns:
        True if the value is non-empty and not one of the masked placeholders.
    """
    return bool(value) and value not in (None, "", "***", "REDACTED")


def _prompt_or_placeholder(
    name: str,
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> str:
    """Prompt for a header value or return the placeholder when not prompting.

    Args:
        name: Header name used in prompt messages.
        prompt_for_secrets: If True, prompt for the value interactively.
        placeholder: Placeholder value used when not prompting or empty input.
        console: Rich ``Console`` instance for user-facing messages.

    Returns:
        The provided value or the placeholder.
    """
    if prompt_for_secrets:
        console.print(f"[yellow]Header '{name}' is missing or redacted.[/yellow]")
        value = click.prompt(
            f"Value for header '{name}' (leave blank for placeholder)",
            default="",
            show_default=False,
        )
        return value.strip() or placeholder

    if not click.get_text_stream("stdin").isatty():
        console.print(
            f"[yellow]⚠️  Non-interactive mode: using placeholder for header '{name}'[/yellow]"
        )
    return placeholder


def _build_custom_headers(
    *,
    existing_headers: Mapping[str, Any],
    header_names: Iterable[str],
    prompt_for_secrets: bool,
    placeholder: str,
    console: Console,
) -> dict[str, str]:
    """Build a headers mapping for custom-header authentication.

    Args:
        existing_headers: Existing headers mapping from the auth object.
        header_names: Header names to process.
        prompt_for_secrets: Whether to prompt for missing values.
        placeholder: Placeholder to use for missing or masked values.
        console: Rich ``Console`` used for prompt/warning messages.

    Returns:
        A dictionary mapping header names to resolved values.
    """
    headers: dict[str, str] = {}
    for name in header_names:
        existing_value = existing_headers.get(name)
        if _is_valid_secret(existing_value):
            headers[name] = str(existing_value)
            continue

        headers[name] = _prompt_or_placeholder(
            name=name,
            prompt_for_secrets=prompt_for_secrets,
            placeholder=placeholder,
            console=console,
        )

    return headers
