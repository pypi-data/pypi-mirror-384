"""prompt_toolkit integration helpers for the slash session.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

_HAS_PROMPT_TOOLKIT = False

try:  # pragma: no cover - optional dependency
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.formatted_text import FormattedText, to_formatted_text
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.patch_stdout import patch_stdout
    from prompt_toolkit.styles import Style

    try:
        from prompt_toolkit.application import run_in_terminal as ptk_run_in_terminal
    except Exception:  # pragma: no cover - compatibility fallback
        ptk_run_in_terminal = None

    _HAS_PROMPT_TOOLKIT = True
except Exception:  # pragma: no cover - optional dependency
    PromptSession = None  # type: ignore[assignment]
    Completer = None  # type: ignore[assignment]
    Completion = None  # type: ignore[assignment]
    FormattedText = None  # type: ignore[assignment]
    to_formatted_text = None  # type: ignore[assignment]
    KeyBindings = None  # type: ignore[assignment]
    Style = None  # type: ignore[assignment]
    patch_stdout = None  # type: ignore[assignment]
    ptk_run_in_terminal = None

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .session import SlashSession


if _HAS_PROMPT_TOOLKIT:

    class SlashCompleter(Completer):
        """Provide slash command completions inside the prompt."""

        def __init__(self, session: SlashSession) -> None:
            """Initialize the slash completer.

            Args:
                session: The slash session context
            """
            self._session = session

        def get_completions(
            self,
            document: Any,
            _complete_event: Any,  # type: ignore[no-any-return]
        ) -> Iterable[Completion]:  # pragma: no cover - UI
            """Get completions for slash commands.

            Args:
                document: The document being edited
                _complete_event: The completion event

            Yields:
                Completion objects for matching commands
            """
            if Completion is None:
                return

            text = document.text_before_cursor or ""
            if not text.startswith("/") or " " in text:
                return

            yield from _iter_command_completions(self._session, text)
            yield from _iter_contextual_completions(self._session, text)

else:  # pragma: no cover - fallback when prompt_toolkit is missing

    class SlashCompleter:  # type: ignore[too-many-ancestors]
        """Fallback slash completer when prompt_toolkit is not available."""

        def __init__(self, session: SlashSession) -> None:  # noqa: D401 - stub
            """Initialize the fallback slash completer.

            Args:
                session: The slash session context
            """
            self._session = session


def setup_prompt_toolkit(
    session: SlashSession,
    *,
    interactive: bool,
) -> tuple[Any | None, Any | None]:
    """Configure prompt_toolkit session and style for interactive mode."""
    if not (interactive and _HAS_PROMPT_TOOLKIT):
        return None, None

    if PromptSession is None or Style is None:
        return None, None

    bindings = _create_key_bindings(session)

    prompt_session = PromptSession(
        completer=SlashCompleter(session),
        complete_while_typing=True,
        key_bindings=bindings,
    )
    prompt_style = Style.from_dict(
        {
            "prompt": "bg:#0f172a #facc15 bold",
            "prompt-verbose-on": "bg:#0f172a #34d399 bold",
            "prompt-verbose-off": "bg:#0f172a #f87171 bold",
            "": "bg:#0f172a #e2e8f0",
            "placeholder": "bg:#0f172a #94a3b8 italic",
        }
    )

    return prompt_session, prompt_style


def _create_key_bindings(session: SlashSession) -> Any:
    """Create prompt_toolkit key bindings for the command palette."""
    if KeyBindings is None:
        return None

    bindings = KeyBindings()

    def _refresh_completions(buffer: Any) -> None:  # type: ignore[no-any-return]
        text = buffer.document.text_before_cursor or ""
        if text.startswith("/") and " " not in text:
            buffer.start_completion(select_first=False)
        elif buffer.complete_state is not None:
            buffer.cancel_completion()

    def _trigger_slash_completion(event: Any) -> None:  # pragma: no cover - UI
        buffer = event.app.current_buffer
        buffer.insert_text("/")
        _refresh_completions(buffer)

    def _handle_backspace(event: Any) -> None:  # pragma: no cover - UI
        buffer = event.app.current_buffer
        if buffer.document.cursor_position > 0:
            buffer.delete_before_cursor()
        _refresh_completions(buffer)

    def _toggle_verbose(event: Any) -> None:  # pragma: no cover - UI
        _execute_toggle_verbose(session, event.app)

    @bindings.add("/")  # type: ignore[misc]
    def _add_trigger_slash_completion(event: Any) -> None:
        _trigger_slash_completion(event)

    @bindings.add("backspace")  # type: ignore[misc]
    def _add_handle_backspace(event: Any) -> None:
        _handle_backspace(event)

    @bindings.add("c-h")  # type: ignore[misc]
    def _add_handle_ctrl_h(event: Any) -> None:
        _handle_backspace(event)  # Reuse backspace handler

    @bindings.add("c-t")  # type: ignore[misc]
    def _add_toggle_verbose(event: Any) -> None:
        _toggle_verbose(event)

    return bindings


def _execute_toggle_verbose(
    session: SlashSession, app: Any
) -> None:  # pragma: no cover - UI
    """Execute verbose toggle with proper terminal handling."""

    def _announce() -> None:
        session.toggle_verbose(announce=False)

    run_in_terminal = getattr(app, "run_in_terminal", None)
    if callable(run_in_terminal):
        run_in_terminal(_announce)
    elif ptk_run_in_terminal is not None:
        ptk_run_in_terminal(_announce)
    else:
        _announce()
    app.invalidate()


def _iter_command_completions(
    session: SlashSession, text: str
) -> Iterable[Completion]:  # pragma: no cover - thin wrapper
    prefix = text[1:]
    seen: set[str] = set()

    # Early return for contextual commands scenario
    if not _should_include_commands(session):
        return []

    commands = sorted(session._unique_commands.values(), key=lambda c: c.name)

    for cmd in commands:
        yield from _generate_command_completions(cmd, prefix, text, seen)


def _should_include_commands(session: SlashSession) -> bool:
    """Check if commands should be included in completions."""
    return not (
        session.get_contextual_commands()
        and not session.should_include_global_commands()
    )


def _generate_command_completions(
    cmd: Any, prefix: str, text: str, seen: set[str]
) -> Iterable[Completion]:
    """Generate completion items for a single command."""
    for alias in (cmd.name, *cmd.aliases):
        if alias in seen or alias.startswith("?"):
            continue

        if prefix and not alias.startswith(prefix):
            continue

        seen.add(alias)
        label = f"/{alias}"
        yield Completion(
            text=label,
            start_position=-len(text),
            display=label,
            display_meta=cmd.help,
        )


def _iter_contextual_completions(
    session: SlashSession, text: str
) -> Iterable[Completion]:  # pragma: no cover - thin wrapper
    prefix = text[1:]
    seen: set[str] = set()

    contextual_commands = sorted(
        session.get_contextual_commands().items(), key=lambda item: item[0]
    )

    for alias, help_text in contextual_commands:
        if alias in seen:
            continue
        if prefix and not alias.startswith(prefix):
            continue
        seen.add(alias)
        label = f"/{alias}"
        yield Completion(
            text=label,
            start_position=-len(text),
            display=label,
            display_meta=help_text,
        )


__all__ = [
    "SlashCompleter",
    "setup_prompt_toolkit",
    "FormattedText",
    "to_formatted_text",
    "patch_stdout",
    "PromptSession",
    "Style",
    "_HAS_PROMPT_TOOLKIT",
]
