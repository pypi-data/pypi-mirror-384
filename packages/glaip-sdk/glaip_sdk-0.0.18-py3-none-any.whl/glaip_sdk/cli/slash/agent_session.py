"""Agent-specific interaction loop for the command palette.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

from glaip_sdk.cli.commands.agents import get as agents_get_command
from glaip_sdk.cli.commands.agents import run as agents_run_command
from glaip_sdk.cli.slash.prompt import _HAS_PROMPT_TOOLKIT, FormattedText

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from .session import SlashSession


class AgentRunSession:
    """Per-agent execution context for the command palette."""

    def __init__(self, session: SlashSession, agent: Any) -> None:
        """Initialize the agent run session.

        Args:
            session: The slash session context
            agent: The agent to interact with
        """
        self.session = session
        self.agent = agent
        self.console = session.console
        self._agent_id = str(getattr(agent, "id", ""))
        self._agent_name = getattr(agent, "name", "") or self._agent_id
        self._prompt_placeholder: str = (
            "Chat with this agent here; use / for shortcuts."
        )
        self._contextual_completion_help: dict[str, str] = {
            "details": "Show this agent's full configuration.",
            "help": "Display this context-aware menu.",
            "exit": "Return to the command palette.",
            "q": "Return to the command palette.",
            "verbose": "Toggle verbose streaming output.",
        }

    def run(self) -> None:
        """Run the interactive agent session loop."""
        self.session.set_contextual_commands(
            self._contextual_completion_help, include_global=False
        )
        try:
            self._display_agent_info()
            self._run_agent_loop()
        finally:
            self.session.set_contextual_commands(None)

    def _display_agent_info(self) -> None:
        """Display agent information and summary."""
        self.session._render_header(self.agent, focus_agent=True)

    def _run_agent_loop(self) -> None:
        """Run the main agent interaction loop."""
        while True:
            raw = self._get_user_input()
            if raw is None:
                return

            raw = raw.strip()
            if not raw:
                continue

            if raw.startswith("/"):
                if not self._handle_slash_command(raw, self._agent_id):
                    return
                continue

            self._run_agent(self._agent_id, raw)

    def _get_user_input(self) -> str | None:
        """Get user input with proper error handling."""
        try:

            def _prompt_message() -> Any:
                verbose_enabled = self.session.verbose_enabled
                verbose_tag = "[verbose:on]" if verbose_enabled else "[verbose:off]"
                prompt_prefix = f"{self._agent_name} ({self._agent_id}) "

                # Use FormattedText if prompt_toolkit is available, otherwise use simple string
                if _HAS_PROMPT_TOOLKIT and FormattedText is not None:
                    segments = [
                        ("class:prompt", prompt_prefix),
                        (
                            "class:prompt-verbose-on"
                            if verbose_enabled
                            else "class:prompt-verbose-off",
                            verbose_tag,
                        ),
                        ("class:prompt", "\n› "),
                    ]
                    return FormattedText(segments)

                return f"{prompt_prefix}{verbose_tag}\n› "

            raw = self.session._prompt(
                _prompt_message,
                placeholder=self._prompt_placeholder,
            )
            if self._prompt_placeholder:
                # Show the guidance once, then fall back to a clean prompt.
                self._prompt_placeholder = ""
            return raw
        except EOFError:
            self.console.print("\nExiting agent context.")
            return None
        except KeyboardInterrupt:
            self.console.print("")
            return ""

    def _handle_slash_command(self, raw: str, agent_id: str) -> bool:
        """Handle slash commands in agent context. Returns False if should exit."""
        # Handle simple commands first
        if raw == "/":
            return self._handle_help_command()

        if raw in {"/exit", "/back", "/q"}:
            return self._handle_exit_command()

        if raw in {"/details", "/detail"}:
            return self._handle_details_command(agent_id)

        if raw in {"/help", "/?"}:
            return self._handle_help_command()

        # Handle other commands through the main session
        return self._handle_other_command(raw)

    def _handle_help_command(self) -> bool:
        """Handle help command."""
        self.session._cmd_help([], True)
        return True

    def _handle_exit_command(self) -> bool:
        """Handle exit command."""
        self.console.print("[dim]Returning to the main prompt.[/dim]")
        return False

    def _handle_details_command(self, agent_id: str) -> bool:
        """Handle details command."""
        self._show_details(agent_id)
        return True

    def _handle_other_command(self, raw: str) -> bool:
        """Handle other commands through the main session."""
        self.session.handle_command(raw, invoked_from_agent=True)
        return not self.session._should_exit

    def _show_details(self, agent_id: str) -> None:
        try:
            self.session.ctx.invoke(agents_get_command, agent_ref=agent_id)
            self.console.print(
                "[dim]Tip: Continue the conversation in this prompt, or use /help for shortcuts."
            )
        except click.ClickException as exc:
            self.console.print(f"[red]{exc}[/red]")

    def _run_agent(self, agent_id: str, message: str) -> None:
        if not message:
            return

        try:
            ctx = self.session.ctx
            ctx_obj = getattr(ctx, "obj", None)
            previous_session = None
            if isinstance(ctx_obj, dict):
                previous_session = ctx_obj.get("_slash_session")
                ctx_obj["_slash_session"] = self.session

            self.session.notify_agent_run_started()
            self.session.ctx.invoke(
                agents_run_command,
                agent_ref=agent_id,
                input_text=message,
                verbose=self.session.verbose_enabled,
            )
            self.session.last_run_input = message
        except click.ClickException as exc:
            self.console.print(f"[red]{exc}[/red]")
        finally:
            try:
                self.session.notify_agent_run_finished()
            finally:
                if isinstance(ctx_obj, dict):
                    if previous_session is None:
                        ctx_obj.pop("_slash_session", None)
                    else:
                        ctx_obj["_slash_session"] = previous_session
