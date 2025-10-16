"""SlashSession orchestrates the interactive command palette.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import os
import shlex
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from glaip_sdk.branding import AIPBranding
from glaip_sdk.cli.commands.configure import configure_command, load_config
from glaip_sdk.cli.utils import _fuzzy_pick_for_resources, command_hint, get_client
from glaip_sdk.rich_components import AIPPanel

from .agent_session import AgentRunSession
from .prompt import (
    FormattedText,
    PromptSession,
    Style,
    patch_stdout,
    setup_prompt_toolkit,
    to_formatted_text,
)

SlashHandler = Callable[["SlashSession", list[str], bool], bool]


@dataclass(frozen=True)
class SlashCommand:
    """Metadata for a slash command entry."""

    name: str
    help: str
    handler: SlashHandler
    aliases: tuple[str, ...] = ()


class SlashSession:
    """Interactive command palette controller."""

    def __init__(self, ctx: click.Context, *, console: Console | None = None) -> None:
        """Initialize the slash session.

        Args:
            ctx: The Click context
            console: Optional console instance, creates default if None
        """
        self.ctx = ctx
        self.console = console or Console()
        self._commands: dict[str, SlashCommand] = {}
        self._unique_commands: dict[str, SlashCommand] = {}
        self._contextual_commands: dict[str, str] = {}
        self._contextual_include_global: bool = True
        self._client: Any | None = None
        self.recent_agents: list[dict[str, str]] = []
        self.last_run_input: str | None = None
        self._should_exit = False
        self._interactive = bool(sys.stdin.isatty() and sys.stdout.isatty())
        self._config_cache: dict[str, Any] | None = None
        self._welcome_rendered = False
        self._verbose_enabled = False
        self._active_renderer: Any | None = None

        self._home_placeholder = "Start with / to browse commands"

        # Command string constants to avoid duplication
        self.STATUS_COMMAND = "/status"
        self.AGENTS_COMMAND = "/agents"

        self._ptk_session: PromptSession | None = None
        self._ptk_style: Style | None = None
        self._setup_prompt_toolkit()
        self._register_defaults()
        self._branding = AIPBranding.create_from_sdk()
        self._suppress_login_layout = False
        self._default_actions_shown = False

    # ------------------------------------------------------------------
    # Session orchestration
    # ------------------------------------------------------------------

    def _setup_prompt_toolkit(self) -> None:
        session, style = setup_prompt_toolkit(self, interactive=self._interactive)
        self._ptk_session = session
        self._ptk_style = style

    def run(self, initial_commands: Iterable[str] | None = None) -> None:
        """Start the command palette session loop."""
        if not self._interactive:
            self._run_non_interactive(initial_commands)
            return

        if not self._ensure_configuration():
            return

        self._render_header(initial=not self._welcome_rendered)
        if not self._default_actions_shown:
            self._show_default_quick_actions()
        self._render_home_hint()
        self._run_interactive_loop()

    def _run_interactive_loop(self) -> None:
        """Run the main interactive command loop."""
        while not self._should_exit:
            try:
                raw = self._prompt("› ", placeholder=self._home_placeholder)
            except EOFError:
                self.console.print("\n👋 Closing the command palette.")
                break
            except KeyboardInterrupt:
                self.console.print("")
                continue

            if not self._process_command(raw):
                break

    def _process_command(self, raw: str) -> bool:
        """Process a single command input. Returns False if should exit."""
        raw = raw.strip()
        if not raw:
            return True

        if raw == "/":
            self._cmd_help([], invoked_from_agent=False)
            return True

        if not raw.startswith("/"):
            self.console.print(
                "[yellow]Hint:[/] start commands with `/`. Try `/agents` to select an agent."
            )
            return True

        return self.handle_command(raw)

    def _run_non_interactive(
        self, initial_commands: Iterable[str] | None = None
    ) -> None:
        """Run slash commands in non-interactive mode."""
        commands = list(initial_commands or [])
        if not commands:
            commands = [line.strip() for line in sys.stdin if line.strip()]

        for raw in commands:
            if not raw.startswith("/"):
                continue
            if not self.handle_command(raw):
                break

    def _ensure_configuration(self) -> bool:
        """Ensure the CLI has both API URL and credentials before continuing."""
        while not self._configuration_ready():
            self.console.print(
                "[yellow]Configuration required.[/] Launching `/login` wizard..."
            )
            self._suppress_login_layout = True
            try:
                self._cmd_login([], False)
            except KeyboardInterrupt:
                self.console.print(
                    "[red]Configuration aborted. Closing the command palette.[/red]"
                )
                return False
            finally:
                self._suppress_login_layout = False

        return True

    def _configuration_ready(self) -> bool:
        """Check whether API URL and credentials are available."""
        config = self._load_config()
        api_url = self._get_api_url(config)
        if not api_url:
            return False

        api_key: str | None = None
        if isinstance(self.ctx.obj, dict):
            api_key = self.ctx.obj.get("api_key")

        api_key = api_key or config.get("api_key") or os.getenv("AIP_API_KEY")
        return bool(api_key)

    def handle_command(self, raw: str, *, invoked_from_agent: bool = False) -> bool:
        """Parse and execute a single slash command string."""
        verb, args = self._parse(raw)
        if not verb:
            self.console.print("[red]Unrecognised command[/red]")
            return True

        command = self._commands.get(verb)
        if command is None:
            suggestion = self._suggest(verb)
            if suggestion:
                self.console.print(
                    f"[yellow]Unknown command '{verb}'. Did you mean '/{suggestion}'?[/yellow]"
                )
            else:
                self.console.print(
                    "[yellow]Unknown command '{verb}'. Type `/help` for a list of options.[/yellow]"
                )
            return True

        should_continue = command.handler(self, args, invoked_from_agent)
        if not should_continue:
            self._should_exit = True
            return False
        return True

    # ------------------------------------------------------------------
    # Command handlers
    # ------------------------------------------------------------------
    def _cmd_help(self, _args: list[str], invoked_from_agent: bool) -> bool:
        try:
            if invoked_from_agent:
                self._render_agent_help()
            else:
                self._render_global_help()
        except Exception as exc:  # pragma: no cover - UI/display errors
            self.console.print(f"[red]Error displaying help: {exc}[/red]")
            return False

        return True

    def _render_agent_help(self) -> None:
        table = Table(title="Agent Context")
        table.add_column("Input", style="cyan", no_wrap=True)
        table.add_column("What happens", style="green")
        table.add_row("<message>", "Run the active agent once with that prompt.")
        table.add_row("/details", "Show the full agent export and metadata.")
        table.add_row(self.STATUS_COMMAND, "Display connection status without leaving.")
        table.add_row("/verbose", "Toggle verbose streaming output (Ctrl+T works too).")
        table.add_row("/exit (/back)", "Return to the slash home screen.")
        table.add_row("/help (/?)", "Display this context-aware menu.")
        self.console.print(table)
        if self.last_run_input:
            self.console.print(f"[dim]Last run input:[/] {self.last_run_input}")
        self.console.print(
            "[dim]Global commands (e.g. `/login`, `/status`) remain available inside the agent prompt.[/dim]"
        )

    def _render_global_help(self) -> None:
        table = Table(title="Slash Commands")
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description", style="green")

        for cmd in sorted(self._unique_commands.values(), key=lambda c: c.name):
            aliases = ", ".join(f"/{alias}" for alias in cmd.aliases if alias)
            verb = f"/{cmd.name}"
            if aliases:
                verb = f"{verb} ({aliases})"
            table.add_row(verb, cmd.help)

        self.console.print(table)
        self.console.print(
            "[dim]Tip: `{self.AGENTS_COMMAND}` lets you jump into an agent run prompt quickly.[/dim]"
        )

    def _cmd_login(self, _args: list[str], _invoked_from_agent: bool) -> bool:
        self.console.print("[cyan]Launching configuration wizard...[/cyan]")
        try:
            self.ctx.invoke(configure_command)
            self._config_cache = None
            if self._suppress_login_layout:
                self._welcome_rendered = False
                self._default_actions_shown = False
            else:
                self._render_header(initial=True)
                self._show_default_quick_actions()
        except click.ClickException as exc:
            self.console.print(f"[red]{exc}[/red]")
        return True

    def _cmd_status(self, _args: list[str], _invoked_from_agent: bool) -> bool:
        try:
            from glaip_sdk.cli.main import status as status_command

            self.ctx.invoke(status_command)
            hints: list[tuple[str, str]] = [
                (self.AGENTS_COMMAND, "Browse agents and run them")
            ]
            if self.recent_agents:
                top = self.recent_agents[0]
                label = top.get("name") or top.get("id")
                hints.append((f"/agents {top.get('id')}", f"Reopen {label}"))
            self._show_quick_actions(hints, title="Next actions")
        except click.ClickException as exc:
            self.console.print(f"[red]{exc}[/red]")
        return True

    def _cmd_agents(self, args: list[str], _invoked_from_agent: bool) -> bool:
        client = self._get_client_or_fail()
        if not client:
            return True

        agents = self._get_agents_or_fail(client)
        if not agents:
            return True

        picked_agent = self._resolve_or_pick_agent(client, agents, args)

        if not picked_agent:
            return True

        return self._run_agent_session(picked_agent)

    def _get_client_or_fail(self) -> Any:
        """Get client or handle failure and return None."""
        try:
            return self._get_client()
        except click.ClickException as exc:
            self.console.print(f"[red]{exc}[/red]")
            return None

    def _get_agents_or_fail(self, client: Any) -> list:
        """Get agents list or handle failure and return empty list."""
        try:
            agents = client.list_agents()
            if not agents:
                self._handle_no_agents()
            return agents
        except Exception as exc:  # pragma: no cover - API failures
            self.console.print(f"[red]Failed to load agents: {exc}[/red]")
            return []

    def _handle_no_agents(self) -> None:
        """Handle case when no agents are available."""
        hint = command_hint("agents create", slash_command=None, ctx=self.ctx)
        if hint:
            self.console.print(
                f"[yellow]No agents available. Use `{hint}` to add one.[/yellow]"
            )
        else:
            self.console.print("[yellow]No agents available.[/yellow]")

    def _resolve_or_pick_agent(self, client: Any, agents: list, args: list[str]) -> Any:
        """Resolve agent from args or pick interactively."""
        if args:
            picked_agent = self._resolve_agent_from_ref(client, agents, args[0])
            if picked_agent is None:
                self.console.print(
                    f"[yellow]Could not resolve agent '{args[0]}'. Try `/agents` to browse interactively.[/yellow]"
                )
                return None
        else:
            picked_agent = _fuzzy_pick_for_resources(agents, "agent", "")

        return picked_agent

    def _run_agent_session(self, picked_agent: Any) -> bool:
        """Run agent session and show follow-up actions."""
        self._remember_agent(picked_agent)
        AgentRunSession(self, picked_agent).run()

        # Refresh the main palette header and surface follow-up actions
        self._render_header()

        self._show_agent_followup_actions(picked_agent)
        return True

    def _show_agent_followup_actions(self, picked_agent: Any) -> None:
        """Show follow-up action hints after agent session."""
        agent_id = str(getattr(picked_agent, "id", ""))
        agent_label = getattr(picked_agent, "name", "") or agent_id or "this agent"

        hints: list[tuple[str, str]] = []
        if agent_id:
            hints.append((f"/agents {agent_id}", f"Reopen {agent_label}"))
        hints.extend(
            [
                (self.AGENTS_COMMAND, "Browse agents"),
                (self.STATUS_COMMAND, "Check connection"),
            ]
        )

        self._show_quick_actions(hints, title="Next actions")

    def _cmd_exit(self, _args: list[str], invoked_from_agent: bool) -> bool:
        if invoked_from_agent:
            # Returning False would stop the full session; we only want to exit
            # the agent context. Raising a custom flag keeps the outer loop
            # running.
            return True

        self.console.print("[cyan]Closing the command palette.[/cyan]")
        return False

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _register_defaults(self) -> None:
        self._register(
            SlashCommand(
                name="help",
                help="Show available command palette commands.",
                handler=SlashSession._cmd_help,
                aliases=("?",),
            )
        )
        self._register(
            SlashCommand(
                name="login",
                help="Run `/login` (alias `/configure`) to set credentials.",
                handler=SlashSession._cmd_login,
                aliases=("configure",),
            )
        )
        self._register(
            SlashCommand(
                name="status",
                help="Display connection status summary.",
                handler=SlashSession._cmd_status,
            )
        )
        self._register(
            SlashCommand(
                name="agents",
                help="Pick an agent and enter a focused run prompt.",
                handler=SlashSession._cmd_agents,
            )
        )
        self._register(
            SlashCommand(
                name="exit",
                help="Exit the command palette.",
                handler=SlashSession._cmd_exit,
                aliases=("q",),
            )
        )
        self._register(
            SlashCommand(
                name="verbose",
                help="Toggle verbose streaming output.",
                handler=SlashSession._cmd_verbose,
            )
        )

    def _register(self, command: SlashCommand) -> None:
        self._unique_commands[command.name] = command
        for key in (command.name, *command.aliases):
            self._commands[key] = command

    # ------------------------------------------------------------------
    # Verbose mode helpers
    # ------------------------------------------------------------------
    @property
    def verbose_enabled(self) -> bool:
        """Return whether verbose agent runs are enabled."""
        return self._verbose_enabled

    def set_verbose(self, enabled: bool, *, announce: bool = True) -> None:
        """Enable or disable verbose mode with optional announcement."""
        if self._verbose_enabled == enabled:
            if announce:
                self._print_verbose_status(context="already")
            return

        self._verbose_enabled = enabled
        self._sync_active_renderer()
        if announce:
            self._print_verbose_status(context="changed")

    def toggle_verbose(self, *, announce: bool = True) -> None:
        """Flip verbose mode state."""
        self.set_verbose(not self._verbose_enabled, announce=announce)

    def _cmd_verbose(self, args: list[str], _invoked_from_agent: bool) -> bool:
        """Slash handler for `/verbose` command."""
        if args:
            self.console.print(
                "Usage: `/verbose` toggles verbose streaming output. Press Ctrl+T as a shortcut."
            )
        else:
            self.toggle_verbose()

        return True

    def _print_verbose_status(self, *, context: str) -> None:
        state_word = "on" if self._verbose_enabled else "off"
        if context == "already":
            self.console.print(
                f"Verbose mode already {state_word}. Use Ctrl+T or `/verbose` to toggle."
            )
            return

        change_word = "enabled" if self._verbose_enabled else "disabled"
        self.console.print(
            f"Verbose mode {change_word}. Use Ctrl+T or `/verbose` to toggle."
        )

    # ------------------------------------------------------------------
    # Agent run coordination helpers
    # ------------------------------------------------------------------
    def register_active_renderer(self, renderer: Any) -> None:
        """Register the renderer currently streaming an agent run."""
        self._active_renderer = renderer
        self._sync_active_renderer()

    def clear_active_renderer(self, renderer: Any | None = None) -> None:
        """Clear the active renderer if it matches the provided instance."""
        if renderer is not None and renderer is not self._active_renderer:
            return
        self._active_renderer = None

    def notify_agent_run_started(self) -> None:
        """Mark that an agent run is in progress."""
        self.clear_active_renderer()

    def notify_agent_run_finished(self) -> None:
        """Mark that the active agent run has completed."""
        self.clear_active_renderer()

    def _sync_active_renderer(self) -> None:
        """Ensure the active renderer reflects the current verbose state."""
        renderer = self._active_renderer
        if renderer is None:
            return

        applied = False
        apply_verbose = getattr(renderer, "apply_verbosity", None)
        if callable(apply_verbose):
            try:
                apply_verbose(self._verbose_enabled)
                applied = True
            except Exception:
                pass

        if not applied and hasattr(renderer, "verbose"):
            try:
                renderer.verbose = self._verbose_enabled
            except Exception:
                pass

    def _parse(self, raw: str) -> tuple[str, list[str]]:
        try:
            tokens = shlex.split(raw)
        except ValueError:
            return "", []

        if not tokens:
            return "", []

        head = tokens[0]
        if head.startswith("/"):
            head = head[1:]

        return head, tokens[1:]

    def _suggest(self, verb: str) -> str | None:
        from difflib import get_close_matches

        keys = [cmd.name for cmd in self._unique_commands.values()]
        match = get_close_matches(verb, keys, n=1)
        return match[0] if match else None

    def _convert_message(self, value: Any) -> Any:
        """Convert a message value to the appropriate format for display."""
        if FormattedText is not None and to_formatted_text is not None:
            return to_formatted_text(value)
        if FormattedText is not None:
            return FormattedText([("class:prompt", str(value))])
        return str(value)

    def _get_prompt_kwargs(self, placeholder: str | None) -> dict[str, Any]:
        """Get prompt kwargs with optional placeholder styling."""
        prompt_kwargs: dict[str, Any] = {"style": self._ptk_style}
        if placeholder:
            placeholder_text = (
                FormattedText([("class:placeholder", placeholder)])
                if FormattedText is not None
                else placeholder
            )
            prompt_kwargs["placeholder"] = placeholder_text
        return prompt_kwargs

    def _prompt_with_prompt_toolkit(
        self, message: str | Callable[[], Any], placeholder: str | None
    ) -> str:
        """Handle prompting with prompt_toolkit."""
        with patch_stdout():  # pragma: no cover - UI specific
            if callable(message):

                def prompt_text() -> Any:
                    return self._convert_message(message())
            else:
                prompt_text = self._convert_message(message)

            prompt_kwargs = self._get_prompt_kwargs(placeholder)

            try:
                return self._ptk_session.prompt(prompt_text, **prompt_kwargs)
            except (
                TypeError
            ):  # pragma: no cover - compatibility with older prompt_toolkit
                prompt_kwargs.pop("placeholder", None)
                return self._ptk_session.prompt(prompt_text, **prompt_kwargs)

    def _extract_message_text(self, raw_value: Any) -> str:
        """Extract text content from various message formats."""
        if isinstance(raw_value, str):
            return raw_value

        try:
            if FormattedText is not None and isinstance(raw_value, FormattedText):
                return "".join(text for _style, text in raw_value)
            elif isinstance(raw_value, list):
                return "".join(segment[1] for segment in raw_value)
            else:
                return str(raw_value)
        except Exception:
            return str(raw_value)

    def _prompt_with_basic_input(
        self, message: str | Callable[[], Any], placeholder: str | None
    ) -> str:
        """Handle prompting with basic input."""
        if placeholder:
            self.console.print(f"[dim]{placeholder}[/dim]")

        raw_value = message() if callable(message) else message
        actual_message = self._extract_message_text(raw_value)

        return input(actual_message)

    def _prompt(
        self, message: str | Callable[[], Any], *, placeholder: str | None = None
    ) -> str:
        """Main prompt function with reduced complexity."""
        if self._ptk_session and self._ptk_style and patch_stdout:
            return self._prompt_with_prompt_toolkit(message, placeholder)

        return self._prompt_with_basic_input(message, placeholder)

    def _get_client(self) -> Any:  # type: ignore[no-any-return]
        if self._client is None:
            self._client = get_client(self.ctx)
        return self._client

    def set_contextual_commands(
        self, commands: dict[str, str] | None, *, include_global: bool = True
    ) -> None:
        """Set context-specific commands that should appear in completions."""
        self._contextual_commands = dict(commands or {})
        self._contextual_include_global = include_global if commands else True

    def get_contextual_commands(self) -> dict[str, str]:  # type: ignore[no-any-return]
        """Return a copy of the currently active contextual commands."""
        return dict(self._contextual_commands)

    def should_include_global_commands(self) -> bool:
        """Return whether global slash commands should appear in completions."""
        return self._contextual_include_global

    def _remember_agent(self, agent: Any) -> None:  # type: ignore[no-any-return]
        agent_data = {
            "id": str(getattr(agent, "id", "")),
            "name": getattr(agent, "name", "") or "",
            "type": getattr(agent, "type", "") or "",
        }

        self.recent_agents = [
            a for a in self.recent_agents if a.get("id") != agent_data["id"]
        ]
        self.recent_agents.insert(0, agent_data)
        self.recent_agents = self.recent_agents[:5]

    def _render_header(
        self,
        active_agent: Any | None = None,
        *,
        focus_agent: bool = False,
        initial: bool = False,
    ) -> None:
        if focus_agent and active_agent is not None:
            self._render_focused_agent_header(active_agent)
            return

        full_header = initial or not self._welcome_rendered
        self._render_main_header(active_agent, full=full_header)
        if full_header:
            self._welcome_rendered = True

    def _render_focused_agent_header(self, active_agent: Any) -> None:
        """Render header when focusing on a specific agent."""
        agent_id = str(getattr(active_agent, "id", ""))
        agent_name = getattr(active_agent, "name", "") or agent_id
        agent_type = getattr(active_agent, "type", "") or "-"
        description = getattr(active_agent, "description", "") or ""

        verbose_label = "verbose on" if self._verbose_enabled else "verbose off"

        header_grid = Table.grid(expand=True)
        header_grid.add_column(ratio=3)
        header_grid.add_column(ratio=1, justify="right")

        primary_line = f"[bold]{agent_name}[/bold] · [dim]{agent_type}[/dim] · [cyan]{agent_id}[/cyan]"
        header_grid.add_row(
            primary_line,
            f"[green]ready[/green] · {verbose_label}",
        )

        if description:
            header_grid.add_row(f"[dim]{description}[/dim]", "")

        keybar = Table.grid(expand=True)
        keybar.add_column(justify="left")
        keybar.add_column(justify="left")
        keybar.add_column(justify="left")
        keybar.add_column(justify="left")
        keybar.add_row(
            "[bold]/help[/bold] [dim]Show commands[/dim]",
            "[bold]/details[/bold] [dim]Agent config[/dim]",
            "[bold]/exit[/bold] [dim]Back[/dim]",
            "[bold]Ctrl+T[/bold] [dim]Toggle verbose[/dim]",
        )

        header_grid.add_row(keybar, "")

        self.console.print(
            AIPPanel(header_grid, title="Agent Session", border_style="blue")
        )

    def _render_main_header(
        self, active_agent: Any | None = None, *, full: bool = False
    ) -> None:
        """Render the main AIP environment header."""
        config = self._load_config()

        api_url = self._get_api_url(config)
        status = "Configured" if config.get("api_key") else "Not configured"

        if full:
            lines = [
                f"GL AIP v{self._branding.version} · GDP Labs AI Agents Package",
                f"API: {api_url or 'Not configured'} · Credentials: {status}",
                (
                    f"Verbose: {'on' if self._verbose_enabled else 'off'} "
                    "(Ctrl+T toggles verbose streaming)"
                ),
            ]
            extra: list[str] = []
            self._add_agent_info_to_header(extra, active_agent)
            lines.extend(extra)
            self.console.print(
                AIPPanel("\n".join(lines), title="GL AIP Session", border_style="cyan")
            )
            return

        status_bar = Table.grid(expand=True)
        status_bar.add_column(ratio=2)
        status_bar.add_column(ratio=2)
        status_bar.add_column(ratio=1, justify="right")
        status_bar.add_row(
            "[bold cyan]AIP Palette[/bold cyan]",
            f"[dim]API[/dim]: {api_url or 'Not configured'}",
            f"[dim]Verbose[/dim]: {'on' if self._verbose_enabled else 'off'}",
        )
        status_bar.add_row("[dim]Ctrl+T toggles verbose[/dim]", "", "")
        status_bar.add_row("[dim]Type /help for shortcuts[/dim]", "", "")

        if active_agent is not None:
            agent_id = str(getattr(active_agent, "id", ""))
            agent_name = getattr(active_agent, "name", "") or agent_id
            status_bar.add_row(f"[dim]Active[/dim]: {agent_name} [{agent_id}]", "", "")
        elif self.recent_agents:
            recent = self.recent_agents[0]
            label = recent.get("name") or recent.get("id") or "-"
            status_bar.add_row(
                f"[dim]Recent[/dim]: {label} [{recent.get('id', '-')}]",
                "",
                "",
            )

        self.console.print(AIPPanel(status_bar, border_style="cyan"))

    def _get_api_url(self, config: dict[str, Any]) -> str | None:
        """Get the API URL from various sources."""
        api_url = None
        if isinstance(self.ctx.obj, dict):
            api_url = self.ctx.obj.get("api_url")
        return api_url or config.get("api_url") or os.getenv("AIP_API_URL")

    def _add_agent_info_to_header(
        self, lines: list[str], active_agent: Any | None
    ) -> None:
        """Add agent information to header lines."""
        if active_agent is not None:
            agent_id = str(getattr(active_agent, "id", ""))
            agent_name = getattr(active_agent, "name", "") or agent_id
            lines.append(f"[dim]Active agent[/dim]: {agent_name} [{agent_id}]")
        elif self.recent_agents:
            recent = self.recent_agents[0]
            label = recent.get("name") or recent.get("id") or "-"
            lines.append(f"[dim]Recent agent[/dim]: {label} [{recent.get('id', '-')}]")

    def _show_default_quick_actions(self) -> None:
        self._show_quick_actions(
            [
                (self.STATUS_COMMAND, "Verify the connection"),
                (self.AGENTS_COMMAND, "Pick an agent to inspect or run"),
            ]
        )
        self._default_actions_shown = True

    def _render_home_hint(self) -> None:
        self.console.print(
            AIPPanel(
                "Type `/help` for command palette commands, `/agents` to browse agents, or `/exit` (`/q`) to leave the palette.\n"
                "Press Ctrl+T to toggle verbose output.\n"
                "Press Ctrl+C to cancel the current entry, Ctrl+D to quit immediately.",
                title="✨ Getting Started",
                border_style="cyan",
            )
        )

    def _show_quick_actions(
        self, hints: Iterable[tuple[str, str]], *, title: str = "Quick actions"
    ) -> None:
        hint_list = list(hints)
        if not hint_list:
            return

        grid = Table.grid(expand=True)
        for _ in hint_list:
            grid.add_column(ratio=1, no_wrap=False)

        grid.add_row(
            *[
                f"[bold]{command}[/bold]\n[dim]{description}[/dim]"
                for command, description in hint_list
            ]
        )

        self.console.print(AIPPanel(grid, title=title, border_style="magenta"))

    def _load_config(self) -> dict[str, Any]:
        if self._config_cache is None:
            try:
                self._config_cache = load_config() or {}
            except Exception:
                self._config_cache = {}
        return self._config_cache

    def _resolve_agent_from_ref(
        self, client: Any, available_agents: list[Any], ref: str
    ) -> Any | None:
        ref = ref.strip()
        if not ref:
            return None

        try:
            agent = client.get_agent_by_id(ref)
            if agent:
                return agent
        except Exception:  # pragma: no cover - passthrough
            pass

        matches = [a for a in available_agents if str(getattr(a, "id", "")) == ref]
        if matches:
            return matches[0]

        try:
            found = client.find_agents(name=ref)
        except Exception:  # pragma: no cover - passthrough
            found = []

        if len(found) == 1:
            return found[0]

        return None
