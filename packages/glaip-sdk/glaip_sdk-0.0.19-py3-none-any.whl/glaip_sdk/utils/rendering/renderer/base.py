"""Base renderer class that orchestrates all rendering components.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from time import monotonic
from typing import Any

from rich.console import Console as RichConsole
from rich.console import Group
from rich.live import Live
from rich.markdown import Markdown
from rich.text import Text

from glaip_sdk.rich_components import AIPPanel
from glaip_sdk.utils.rendering.formatting import (
    format_main_title,
    get_spinner_char,
    is_step_finished,
)
from glaip_sdk.utils.rendering.models import RunStats, Step
from glaip_sdk.utils.rendering.renderer.config import RendererConfig
from glaip_sdk.utils.rendering.renderer.debug import render_debug_event
from glaip_sdk.utils.rendering.renderer.panels import (
    create_final_panel,
    create_main_panel,
    create_tool_panel,
)
from glaip_sdk.utils.rendering.renderer.progress import (
    format_elapsed_time,
    format_tool_title,
    format_working_indicator,
    get_spinner,
    is_delegation_tool,
)
from glaip_sdk.utils.rendering.renderer.stream import StreamProcessor
from glaip_sdk.utils.rendering.steps import StepManager

# Configure logger
logger = logging.getLogger("glaip_sdk.run_renderer")

# Constants
LESS_THAN_1MS = "[<1ms]"


@dataclass
class RendererState:
    """Internal state for the renderer."""

    buffer: list[str] | None = None
    final_text: str = ""
    streaming_started_at: float | None = None
    printed_final_panel: bool = False
    finalizing_ui: bool = False
    final_duration_seconds: float | None = None
    final_duration_text: str | None = None

    def __post_init__(self) -> None:
        """Initialize renderer state after dataclass creation.

        Ensures buffer is initialized as an empty list if not provided.
        """
        if self.buffer is None:
            self.buffer = []


class RichStreamRenderer:
    """Live, modern terminal renderer for agent execution with rich visual output."""

    def __init__(
        self,
        console: RichConsole | None = None,
        *,
        cfg: RendererConfig | None = None,
        verbose: bool = False,
    ) -> None:
        """Initialize the renderer.

        Args:
            console: Rich console instance
            cfg: Renderer configuration
            verbose: Whether to enable verbose mode
        """
        self.console = console or RichConsole()
        self.cfg = cfg or RendererConfig()
        self.verbose = verbose

        # Initialize components
        self.stream_processor = StreamProcessor()
        self.state = RendererState()

        # Initialize step manager and other state
        self.steps = StepManager()
        # Live display instance (single source of truth)
        self.live: Live | None = None

        # Context and tool tracking
        self.context_order: list[str] = []
        self.context_parent: dict[str, str] = {}
        self.tool_order: list[str] = []
        self.context_panels: dict[str, list[str]] = {}
        self.context_meta: dict[str, dict[str, Any]] = {}
        self.tool_panels: dict[str, dict[str, Any]] = {}

        # Timing
        self._started_at: float | None = None

        # Header/text
        self.header_text: str = ""
        # Track per-step server start times for accurate elapsed labels
        self._step_server_start_times: dict[str, float] = {}

        # Output formatting constants
        self.OUTPUT_PREFIX: str = "**Output:**\n"

    def on_start(self, meta: dict[str, Any]) -> None:
        """Handle renderer start event."""
        if self.cfg.live:
            # Defer creating Live to _ensure_live so tests and prod both work
            pass

        # Set up initial state
        self._started_at = monotonic()
        self.stream_processor.streaming_started_at = self._started_at

        # Print compact header and user request (parity with old renderer)
        self._render_header(meta)
        self._render_user_query(meta)

    def _render_header(self, meta: dict[str, Any]) -> None:
        """Render the agent header with metadata."""
        parts = self._build_header_parts(meta)
        self.header_text = " ".join(parts)

        if not self.header_text:
            return

        # Use a rule-like header for readability with fallback
        if not self._render_header_rule():
            self._render_header_fallback()

    def _build_header_parts(self, meta: dict[str, Any]) -> list[str]:
        """Build header text parts from metadata."""
        parts: list[str] = ["🤖"]
        agent_name = meta.get("agent_name", "agent")
        if agent_name:
            parts.append(agent_name)

        model = meta.get("model", "")
        if model:
            parts.extend(["•", model])

        run_id = meta.get("run_id", "")
        if run_id:
            parts.extend(["•", run_id])

        return parts

    def _render_header_rule(self) -> bool:
        """Render header as a rule. Returns True if successful."""
        try:
            self.console.rule(self.header_text)
            return True
        except Exception:  # pragma: no cover - defensive fallback
            logger.exception("Failed to render header rule")
            return False

    def _render_header_fallback(self) -> None:
        """Fallback header rendering."""
        try:
            self.console.print(self.header_text)
        except Exception:
            logger.exception("Failed to print header fallback")

    def _render_user_query(self, meta: dict[str, Any]) -> None:
        """Render the user query panel."""
        query = meta.get("input_message") or meta.get("query") or meta.get("message")
        if not query:
            return

        self.console.print(
            AIPPanel(
                Markdown(f"**Query:** {query}"),
                title="User Request",
                border_style="#d97706",
                padding=(0, 1),
            )
        )

    def on_event(self, ev: dict[str, Any]) -> None:
        """Handle streaming events from the backend."""
        # Reset event tracking
        self.stream_processor.reset_event_tracking()

        # Track streaming start time
        if self.state.streaming_started_at is None:
            self.state.streaming_started_at = monotonic()

        # Extract event metadata
        metadata = self.stream_processor.extract_event_metadata(ev)
        kind = metadata["kind"]
        context_id = metadata["context_id"]
        content = metadata["content"]

        # Render debug event panel if verbose mode is enabled
        if self.verbose:
            render_debug_event(ev, self.console, self.state.streaming_started_at)

        # Update timing
        self.stream_processor.update_timing(context_id)

        # Handle different event types
        if kind == "status":
            self._handle_status_event(ev)
        elif kind == "content":
            self._handle_content_event(content)
        elif kind == "final_response":
            self._handle_final_response_event(content, metadata)
        elif kind in {"agent_step", "agent_thinking_step"}:
            self._handle_agent_step_event(ev)
        else:
            # Update live display for unhandled events
            self._ensure_live()

    def _handle_status_event(self, ev: dict[str, Any]) -> None:
        """Handle status events."""
        status = ev.get("status")
        if status == "streaming_started":
            self.state.streaming_started_at = monotonic()

    def _handle_content_event(self, content: str) -> None:
        """Handle content streaming events."""
        if content:
            self.state.buffer.append(content)
            self._ensure_live()

    def _handle_final_response_event(
        self, content: str, metadata: dict[str, Any]
    ) -> None:
        """Handle final response events."""
        if content:
            self.state.buffer.append(content)
            self.state.final_text = content

            meta_payload = metadata.get("metadata") or {}
            self._update_final_duration(meta_payload.get("time"))

            self._ensure_live()

            # In verbose mode, show the final result in a panel
            if self.verbose and content.strip():
                final_panel = create_final_panel(
                    content,
                    title=self._final_panel_title(),
                    theme=self.cfg.theme,
                )
                self.console.print(final_panel)
                self.state.printed_final_panel = True

    def _handle_agent_step_event(self, ev: dict[str, Any]) -> None:
        """Handle agent step events."""
        # Extract tool information
        (
            tool_name,
            tool_args,
            tool_out,
            tool_calls_info,
        ) = self.stream_processor.parse_tool_calls(ev)

        # Track tools and sub-agents
        self.stream_processor.track_tools_and_agents(
            tool_name, tool_calls_info, is_delegation_tool
        )

        # Handle tool execution
        self._handle_agent_step(ev, tool_name, tool_args, tool_out, tool_calls_info)

        # Update live display
        self._ensure_live()

    def _finish_running_steps(self) -> None:
        """Mark any running steps as finished to avoid lingering spinners."""
        for st in self.steps.by_id.values():
            if not is_step_finished(st):
                st.finish(None)

    def _finish_tool_panels(self) -> None:
        """Mark unfinished tool panels as finished."""
        try:
            items = list(self.tool_panels.items())
        except Exception:  # pragma: no cover - defensive guard
            logger.exception("Failed to iterate tool panels during cleanup")
            return

        for _sid, meta in items:
            if meta.get("status") != "finished":
                meta["status"] = "finished"

    def _stop_live_display(self) -> None:
        """Stop live display and clean up."""
        self._shutdown_live()

    def _print_final_panel_if_needed(self) -> None:
        """Print final result panel if verbose mode and content available."""
        if self.verbose and not self.state.printed_final_panel:
            body = ("".join(self.state.buffer) or "").strip()
            if body:
                final_panel = create_final_panel(
                    body,
                    title=self._final_panel_title(),
                    theme=self.cfg.theme,
                )
                self.console.print(final_panel)
                self.state.printed_final_panel = True

    def on_complete(self, stats: RunStats) -> None:
        """Handle completion event."""
        self.state.finalizing_ui = True

        if isinstance(stats, RunStats):
            duration = None
            try:
                if stats.finished_at is not None and stats.started_at is not None:
                    duration = max(
                        0.0, float(stats.finished_at) - float(stats.started_at)
                    )
            except Exception:
                duration = None

            if duration is not None:
                self._update_final_duration(duration, overwrite=True)

        # Mark any running steps as finished to avoid lingering spinners
        self._finish_running_steps()

        # Mark unfinished tool panels as finished
        self._finish_tool_panels()

        # Final refresh
        self._ensure_live()

        # Stop live display
        self._stop_live_display()

        # Print final panel if needed
        self._print_final_panel_if_needed()

    def _ensure_live(self) -> None:
        """Ensure live display is updated."""
        if not self._ensure_live_stack():
            return

        self._start_live_if_needed()

        if self.live:
            self._refresh_live_panels()

    def _ensure_live_stack(self) -> bool:
        """Guarantee the console exposes the internal live stack Rich expects."""
        live_stack = getattr(self.console, "_live_stack", None)
        if isinstance(live_stack, list):
            return True

        try:
            self.console._live_stack = []  # type: ignore[attr-defined]
            return True
        except Exception:
            # If the console forbids attribute assignment we simply skip the live
            # update for this cycle and fall back to buffered printing.
            logger.debug(
                "Console missing _live_stack; skipping live UI initialisation",
                exc_info=True,
            )
            return False

    def _start_live_if_needed(self) -> None:
        """Create and start a Live instance when configuration allows."""
        if self.live is not None or not self.cfg.live:
            return

        try:
            self.live = Live(
                console=self.console,
                refresh_per_second=1 / self.cfg.refresh_debounce,
                transient=not self.cfg.persist_live,
            )
            self.live.start()
        except Exception:
            self.live = None

    def _refresh_live_panels(self) -> None:
        """Render panels and push them to the active Live display."""
        if not self.live:
            return

        main_panel = self._render_main_panel()
        steps_renderable = self._render_steps_text()
        steps_panel = AIPPanel(
            steps_renderable,
            title="Steps",
            border_style="blue",
        )
        tool_panels = self._render_tool_panels()
        panels = self._build_live_panels(main_panel, steps_panel, tool_panels)

        self.live.update(Group(*panels))

    def _build_live_panels(
        self,
        main_panel: Any,
        steps_panel: Any,
        tool_panels: list[Any],
    ) -> list[Any]:
        """Assemble the panel order for the live display."""
        if self.verbose:
            return [main_panel, steps_panel, *tool_panels]

        panels: list[Any] = [steps_panel]
        if tool_panels:
            panels.extend(tool_panels)
        panels.append(main_panel)
        return panels

    def _render_main_panel(self) -> Any:
        """Render the main content panel."""
        body = "".join(self.state.buffer).strip()
        if not self.verbose:
            final_content = (self.state.final_text or "").strip()
            if final_content:
                title = self._final_panel_title()
                return create_final_panel(
                    final_content,
                    title=title,
                    theme=self.cfg.theme,
                )
        # Dynamic title with spinner + elapsed/hints
        title = self._format_enhanced_main_title()
        return create_main_panel(body, title, self.cfg.theme)

    def _final_panel_title(self) -> str:
        """Compose title for the final result panel including duration."""
        title = "Final Result"
        if self.state.final_duration_text:
            title = f"{title} · {self.state.final_duration_text}"
        return title

    def apply_verbosity(self, verbose: bool) -> None:
        """Update verbose behaviour at runtime."""
        if self.verbose == verbose:
            return

        self.verbose = verbose
        self.cfg.style = "debug" if verbose else "pretty"

        desired_live = not verbose
        if desired_live != self.cfg.live:
            self.cfg.live = desired_live
            if not desired_live:
                self._shutdown_live()
            else:
                self._ensure_live()

        if self.cfg.live:
            self._ensure_live()

    def _maybe_insert_thinking_gap(
        self, task_id: str | None, context_id: str | None
    ) -> None:
        """Insert thinking gap if needed."""
        # Implementation would track thinking states
        pass

    def _ensure_tool_panel(
        self, name: str, args: Any, task_id: str, context_id: str
    ) -> str:
        """Ensure a tool panel exists and return its ID."""
        formatted_title = format_tool_title(name)
        is_delegation = is_delegation_tool(name)
        tool_sid = f"tool_{name}_{task_id}_{context_id}"

        if tool_sid not in self.tool_panels:
            self.tool_panels[tool_sid] = {
                "title": formatted_title,
                "status": "running",
                "started_at": monotonic(),
                "server_started_at": self.stream_processor.server_elapsed_time,
                "chunks": [],
                "args": args or {},
                "output": None,
                "is_delegation": is_delegation,
            }
            # Add Args section once
            if args:
                try:
                    args_content = (
                        "**Args:**\n```json\n"
                        + json.dumps(args, indent=2)
                        + "\n```\n\n"
                    )
                except Exception:
                    args_content = f"**Args:**\n{args}\n\n"
                self.tool_panels[tool_sid]["chunks"].append(args_content)
            self.tool_order.append(tool_sid)

        return tool_sid

    def _start_tool_step(
        self,
        task_id: str,
        context_id: str,
        tool_name: str,
        tool_args: Any,
        _tool_sid: str,
    ) -> Step | None:
        """Start or get a step for a tool."""
        if is_delegation_tool(tool_name):
            st = self.steps.start_or_get(
                task_id=task_id,
                context_id=context_id,
                kind="delegate",
                name=tool_name,
                args=tool_args,
            )
        else:
            st = self.steps.start_or_get(
                task_id=task_id,
                context_id=context_id,
                kind="tool",
                name=tool_name,
                args=tool_args,
            )

        # Record server start time for this step if available
        if st and self.stream_processor.server_elapsed_time is not None:
            self._step_server_start_times[st.step_id] = (
                self.stream_processor.server_elapsed_time
            )

        return st

    def _process_additional_tool_calls(
        self,
        tool_calls_info: list[tuple[str, Any, Any]],
        tool_name: str,
        task_id: str,
        context_id: str,
    ) -> None:
        """Process additional tool calls to avoid duplicates."""
        for call_name, call_args, _ in tool_calls_info or []:
            if call_name and call_name != tool_name:
                self._process_single_tool_call(
                    call_name, call_args, task_id, context_id
                )

    def _process_single_tool_call(
        self, call_name: str, call_args: Any, task_id: str, context_id: str
    ) -> None:
        """Process a single additional tool call."""
        self._ensure_tool_panel(call_name, call_args, task_id, context_id)

        st2 = self._create_step_for_tool_call(call_name, call_args, task_id, context_id)

        if self.stream_processor.server_elapsed_time is not None and st2:
            self._step_server_start_times[st2.step_id] = (
                self.stream_processor.server_elapsed_time
            )

    def _create_step_for_tool_call(
        self, call_name: str, call_args: Any, task_id: str, context_id: str
    ) -> Any:
        """Create appropriate step for tool call."""
        if is_delegation_tool(call_name):
            return self.steps.start_or_get(
                task_id=task_id,
                context_id=context_id,
                kind="delegate",
                name=call_name,
                args=call_args,
            )
        else:
            return self.steps.start_or_get(
                task_id=task_id,
                context_id=context_id,
                kind="tool",
                name=call_name,
                args=call_args,
            )

    def _detect_tool_completion(
        self, metadata: dict, content: str
    ) -> tuple[bool, str | None, Any]:
        """Detect if a tool has completed and return completion info."""
        tool_info = metadata.get("tool_info", {}) if isinstance(metadata, dict) else {}

        if tool_info.get("status") == "finished" and tool_info.get("name"):
            return True, tool_info.get("name"), tool_info.get("output")
        elif content and isinstance(content, str) and content.startswith("Completed "):
            # content like "Completed google_serper"
            tname = content.replace("Completed ", "").strip()
            if tname:
                output = (
                    tool_info.get("output") if tool_info.get("name") == tname else None
                )
                return True, tname, output
        elif metadata.get("status") == "finished" and tool_info.get("name"):
            return True, tool_info.get("name"), tool_info.get("output")

        return False, None, None

    def _get_tool_session_id(
        self, finished_tool_name: str, task_id: str, context_id: str
    ) -> str:
        """Generate tool session ID."""
        return f"tool_{finished_tool_name}_{task_id}_{context_id}"

    def _calculate_tool_duration(self, meta: dict[str, Any]) -> float | None:
        """Calculate tool duration from metadata."""
        server_now = self.stream_processor.server_elapsed_time
        server_start = meta.get("server_started_at")
        dur = None

        try:
            if isinstance(server_now, (int, float)) and server_start is not None:
                dur = max(0.0, float(server_now) - float(server_start))
            else:
                started_at = meta.get("started_at")
                if started_at is not None:
                    started_at_float = float(started_at)
                    dur = max(0.0, float(monotonic()) - started_at_float)
        except (TypeError, ValueError):
            logger.exception("Failed to calculate tool duration")
            return None

        return dur

    def _update_tool_metadata(self, meta: dict[str, Any], dur: float | None) -> None:
        """Update tool metadata with duration information."""
        if dur is not None:
            meta["duration_seconds"] = dur
            meta["server_finished_at"] = (
                self.stream_processor.server_elapsed_time
                if isinstance(self.stream_processor.server_elapsed_time, int | float)
                else None
            )
            meta["finished_at"] = monotonic()

    def _add_tool_output_to_panel(
        self, meta: dict[str, Any], finished_tool_output: Any, finished_tool_name: str
    ) -> None:
        """Add tool output to panel metadata."""
        if finished_tool_output is not None:
            meta["chunks"].append(
                self._format_output_block(finished_tool_output, finished_tool_name)
            )
            meta["output"] = finished_tool_output

    def _mark_panel_as_finished(self, meta: dict[str, Any], tool_sid: str) -> None:
        """Mark panel as finished and ensure visibility."""
        if meta.get("status") != "finished":
            meta["status"] = "finished"

            dur = self._calculate_tool_duration(meta)
            self._update_tool_metadata(meta, dur)

        # Ensure this finished panel is visible in this frame
        self.stream_processor.current_event_finished_panels.add(tool_sid)

    def _finish_tool_panel(
        self,
        finished_tool_name: str,
        finished_tool_output: Any,
        task_id: str,
        context_id: str,
    ) -> None:
        """Finish a tool panel and update its status."""
        tool_sid = self._get_tool_session_id(finished_tool_name, task_id, context_id)
        if tool_sid not in self.tool_panels:
            return

        meta = self.tool_panels[tool_sid]
        self._mark_panel_as_finished(meta, tool_sid)
        self._add_tool_output_to_panel(meta, finished_tool_output, finished_tool_name)

    def _get_step_duration(
        self, finished_tool_name: str, task_id: str, context_id: str
    ) -> float | None:
        """Get step duration from tool panels."""
        tool_sid = f"tool_{finished_tool_name}_{task_id}_{context_id}"
        return self.tool_panels.get(tool_sid, {}).get("duration_seconds")

    def _finish_delegation_step(
        self,
        finished_tool_name: str,
        finished_tool_output: Any,
        task_id: str,
        context_id: str,
        step_duration: float | None,
    ) -> None:
        """Finish a delegation step."""
        self.steps.finish(
            task_id=task_id,
            context_id=context_id,
            kind="delegate",
            name=finished_tool_name,
            output=finished_tool_output,
            duration_raw=step_duration,
        )

    def _finish_tool_step_type(
        self,
        finished_tool_name: str,
        finished_tool_output: Any,
        task_id: str,
        context_id: str,
        step_duration: float | None,
    ) -> None:
        """Finish a regular tool step."""
        self.steps.finish(
            task_id=task_id,
            context_id=context_id,
            kind="tool",
            name=finished_tool_name,
            output=finished_tool_output,
            duration_raw=step_duration,
        )

    def _finish_tool_step(
        self,
        finished_tool_name: str,
        finished_tool_output: Any,
        task_id: str,
        context_id: str,
    ) -> None:
        """Finish the corresponding step for a completed tool."""
        step_duration = self._get_step_duration(finished_tool_name, task_id, context_id)

        if is_delegation_tool(finished_tool_name):
            self._finish_delegation_step(
                finished_tool_name,
                finished_tool_output,
                task_id,
                context_id,
                step_duration,
            )
        else:
            self._finish_tool_step_type(
                finished_tool_name,
                finished_tool_output,
                task_id,
                context_id,
                step_duration,
            )

    def _should_create_snapshot(self, tool_sid: str) -> bool:
        """Check if a snapshot should be created."""
        return self.cfg.append_finished_snapshots and not self.tool_panels.get(
            tool_sid, {}
        ).get("snapshot_printed")

    def _get_snapshot_title(self, meta: dict[str, Any], finished_tool_name: str) -> str:
        """Get the title for the snapshot."""
        adjusted_title = meta.get("title") or finished_tool_name

        # Add elapsed time to title
        dur = meta.get("duration_seconds")
        if isinstance(dur, int | float):
            elapsed_str = self._format_snapshot_duration(dur)
            adjusted_title = f"{adjusted_title}  · {elapsed_str}"

        return adjusted_title

    def _format_snapshot_duration(self, dur: int | float) -> str:
        """Format duration for snapshot title."""
        try:
            # Handle invalid types
            if not isinstance(dur, (int, float)):
                return "<1ms"

            if dur >= 1:
                return f"{dur:.2f}s"
            elif int(dur * 1000) > 0:
                return f"{int(dur * 1000)}ms"
            else:
                return "<1ms"
        except (TypeError, ValueError, OverflowError):
            return "<1ms"

    def _clamp_snapshot_body(self, body_text: str) -> str:
        """Clamp snapshot body to configured limits."""
        max_lines = int(self.cfg.snapshot_max_lines or 0)
        lines = body_text.splitlines()
        if max_lines > 0 and len(lines) > max_lines:
            lines = lines[:max_lines] + ["… (truncated)"]
            body_text = "\n".join(lines)

        max_chars = int(self.cfg.snapshot_max_chars or 0)
        if max_chars > 0 and len(body_text) > max_chars:
            suffix = "\n… (truncated)"
            body_text = body_text[: max_chars - len(suffix)] + suffix

        return body_text

    def _create_snapshot_panel(
        self, adjusted_title: str, body_text: str, finished_tool_name: str
    ) -> Any:
        """Create the snapshot panel."""
        return create_tool_panel(
            title=adjusted_title,
            content=body_text or "(no output)",
            status="finished",
            theme=self.cfg.theme,
            is_delegation=is_delegation_tool(finished_tool_name),
        )

    def _print_and_mark_snapshot(self, tool_sid: str, snapshot_panel: Any) -> None:
        """Print snapshot and mark as printed."""
        self.console.print(snapshot_panel)
        self.tool_panels[tool_sid]["snapshot_printed"] = True

    def _create_tool_snapshot(
        self, finished_tool_name: str, task_id: str, context_id: str
    ) -> None:
        """Create and print a snapshot for a finished tool."""
        tool_sid = f"tool_{finished_tool_name}_{task_id}_{context_id}"

        if not self._should_create_snapshot(tool_sid):
            return

        meta = self.tool_panels[tool_sid]
        adjusted_title = self._get_snapshot_title(meta, finished_tool_name)

        # Compose body from chunks and clamp
        body_text = "".join(meta.get("chunks") or [])
        body_text = self._clamp_snapshot_body(body_text)

        snapshot_panel = self._create_snapshot_panel(
            adjusted_title, body_text, finished_tool_name
        )

        self._print_and_mark_snapshot(tool_sid, snapshot_panel)

    def _handle_agent_step(
        self,
        event: dict[str, Any],
        tool_name: str | None,
        tool_args: Any,
        _tool_out: Any,
        tool_calls_info: list[tuple[str, Any, Any]],
    ) -> None:
        """Handle agent step event."""
        metadata = event.get("metadata", {})
        task_id = event.get("task_id")
        context_id = event.get("context_id")
        content = event.get("content", "")

        # Create steps and panels for the primary tool
        if tool_name:
            tool_sid = self._ensure_tool_panel(
                tool_name, tool_args, task_id, context_id
            )
            self._start_tool_step(task_id, context_id, tool_name, tool_args, tool_sid)

        # Handle additional tool calls
        self._process_additional_tool_calls(
            tool_calls_info, tool_name, task_id, context_id
        )

        # Check for tool completion
        (
            is_tool_finished,
            finished_tool_name,
            finished_tool_output,
        ) = self._detect_tool_completion(metadata, content)

        if is_tool_finished and finished_tool_name:
            self._finish_tool_panel(
                finished_tool_name, finished_tool_output, task_id, context_id
            )
            self._finish_tool_step(
                finished_tool_name, finished_tool_output, task_id, context_id
            )
            self._create_tool_snapshot(finished_tool_name, task_id, context_id)

    def _spinner(self) -> str:
        """Return spinner character."""
        return get_spinner()

    def _format_working_indicator(self, started_at: float | None) -> str:
        """Format working indicator."""
        return format_working_indicator(
            started_at,
            self.stream_processor.server_elapsed_time,
            self.state.streaming_started_at,
        )

    def close(self) -> None:
        """Gracefully stop any live rendering and release resources."""
        self._shutdown_live()

    def __del__(self) -> None:
        """Destructor that ensures live rendering is properly shut down.

        This is a safety net to prevent resource leaks if the renderer
        is not explicitly stopped.
        """
        # Destructors must never raise
        try:
            self._shutdown_live(reset_attr=False)
        except Exception:  # pragma: no cover - destructor safety net
            pass

    def _shutdown_live(self, reset_attr: bool = True) -> None:
        """Stop the live renderer without letting exceptions escape."""
        live = getattr(self, "live", None)
        if not live:
            if reset_attr and not hasattr(self, "live"):
                self.live = None
            return

        try:
            live.stop()
        except Exception:
            logger.exception("Failed to stop live display")
        finally:
            if reset_attr:
                self.live = None

    def _get_analysis_progress_info(self) -> dict[str, Any]:
        total_steps = len(self.steps.order)
        completed_steps = sum(
            1 for sid in self.steps.order if is_step_finished(self.steps.by_id[sid])
        )
        current_step = None
        for sid in self.steps.order:
            if not is_step_finished(self.steps.by_id[sid]):
                current_step = sid
                break
        # Prefer server elapsed time when available
        elapsed = 0.0
        if isinstance(self.stream_processor.server_elapsed_time, int | float):
            elapsed = float(self.stream_processor.server_elapsed_time)
        elif self._started_at is not None:
            elapsed = monotonic() - self._started_at
        progress_percent = (
            int((completed_steps / total_steps) * 100) if total_steps else 0
        )
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "current_step": current_step,
            "progress_percent": progress_percent,
            "elapsed_time": elapsed,
            "has_running_steps": self._has_running_steps(),
        }

    def _format_enhanced_main_title(self) -> str:
        base = format_main_title(
            header_text=self.header_text,
            has_running_steps=self._has_running_steps(),
            get_spinner_char=get_spinner_char,
        )
        # Add elapsed time and subtle progress hints for long operations
        info = self._get_analysis_progress_info()
        elapsed = info.get("elapsed_time", 0.0)
        if elapsed and elapsed > 0:
            base += f" · {format_elapsed_time(elapsed)}"
        if info.get("total_steps", 0) > 1 and info.get("has_running_steps"):
            if elapsed > 60:
                base += " 🐌"
            elif elapsed > 30:
                base += " ⚠️"
        return base

    # Modern interface only — no legacy helper shims below

    def _refresh(self, _force: bool | None = None) -> None:
        # In the modular renderer, refreshing simply updates the live group
        self._ensure_live()

    def _has_running_steps(self) -> bool:
        """Check if any steps are still running."""
        for _sid, st in self.steps.by_id.items():
            if not is_step_finished(st):
                return True
        return False

    def _get_step_icon(self, step_kind: str) -> str:
        """Get icon for step kind."""
        if step_kind == "tool":
            return "⚙️"
        elif step_kind == "delegate":
            return "🤝"
        elif step_kind == "agent":
            return "🧠"
        return ""

    def _format_step_status(self, step: Step) -> str:
        """Format step status with elapsed time or duration."""
        if is_step_finished(step):
            if step.duration_ms is None:
                return LESS_THAN_1MS
            elif step.duration_ms >= 1000:
                return f"[{step.duration_ms / 1000:.2f}s]"
            elif step.duration_ms > 0:
                return f"[{step.duration_ms}ms]"
            return LESS_THAN_1MS
        else:
            # Calculate elapsed time for running steps
            elapsed = self._calculate_step_elapsed_time(step)
            if elapsed >= 1:
                return f"[{elapsed:.2f}s]"
            ms = int(elapsed * 1000)
            return f"[{ms}ms]" if ms > 0 else LESS_THAN_1MS

    def _calculate_step_elapsed_time(self, step: Step) -> float:
        """Calculate elapsed time for a running step."""
        server_elapsed = self.stream_processor.server_elapsed_time
        server_start = self._step_server_start_times.get(step.step_id)

        if isinstance(server_elapsed, int | float) and isinstance(
            server_start, int | float
        ):
            return max(0.0, float(server_elapsed) - float(server_start))

        try:
            return max(0.0, float(monotonic() - step.started_at))
        except Exception:
            return 0.0

    def _get_step_display_name(self, step: Step) -> str:
        """Get display name for a step."""
        if step.name and step.name != "step":
            return step.name
        return "thinking..." if step.kind == "agent" else f"{step.kind} step"

    def _check_parallel_tools(self) -> dict[tuple[str | None, str | None], list]:
        """Check for parallel running tools."""
        running_by_ctx: dict[tuple[str | None, str | None], list] = {}
        for sid in self.steps.order:
            st = self.steps.by_id[sid]
            if st.kind == "tool" and not is_step_finished(st):
                key = (st.task_id, st.context_id)
                running_by_ctx.setdefault(key, []).append(st)
        return running_by_ctx

    def _render_steps_text(self) -> Text:
        """Render the steps panel content."""
        if not (self.steps.order or self.steps.children):
            return Text("No steps yet", style="dim")

        running_by_ctx = self._check_parallel_tools()
        lines: list[str] = []

        for sid in self.steps.order:
            st = self.steps.by_id[sid]
            status_br = self._format_step_status(st)
            display_name = self._get_step_display_name(st)
            tail = " ✓" if is_step_finished(st) else ""

            # Add parallel indicator for running tools
            if st.kind == "tool" and not is_step_finished(st):
                key = (st.task_id, st.context_id)
                if len(running_by_ctx.get(key, [])) > 1:
                    status_br = status_br.replace("]", " 🔄]")

            icon = self._get_step_icon(st.kind)
            lines.append(f"{icon} {display_name} {status_br}{tail}")

        return Text("\n".join(lines), style="dim")

    def _should_skip_finished_panel(self, sid: str, status: str) -> bool:
        """Check if a finished panel should be skipped."""
        if status != "finished":
            return False

        if getattr(self.cfg, "append_finished_snapshots", False):
            return True

        return (
            not self.state.finalizing_ui
            and sid not in self.stream_processor.current_event_finished_panels
        )

    def _update_final_duration(
        self, duration: float | None, *, overwrite: bool = False
    ) -> None:
        """Store formatted duration for eventual final panels."""
        if duration is None:
            return

        try:
            duration_val = max(0.0, float(duration))
        except Exception:
            return

        existing = self.state.final_duration_seconds

        if not overwrite and existing is not None:
            return

        if overwrite and existing is not None:
            duration_val = max(existing, duration_val)

        self.state.final_duration_seconds = duration_val
        self.state.final_duration_text = self._format_elapsed_time(duration_val)

    def _calculate_elapsed_time(self, meta: dict[str, Any]) -> str:
        """Calculate elapsed time string for running tools."""
        server_elapsed = self.stream_processor.server_elapsed_time
        server_start = meta.get("server_started_at")

        if isinstance(server_elapsed, int | float) and isinstance(
            server_start, int | float
        ):
            elapsed = max(0.0, float(server_elapsed) - float(server_start))
        else:
            elapsed = max(0.0, monotonic() - (meta.get("started_at") or 0.0))

        return self._format_elapsed_time(elapsed)

    def _format_elapsed_time(self, elapsed: float) -> str:
        """Format elapsed time as a readable string."""
        if elapsed >= 1:
            return f"{elapsed:.2f}s"
        elif int(elapsed * 1000) > 0:
            return f"{int(elapsed * 1000)}ms"
        else:
            return "<1ms"

    def _calculate_finished_duration(self, meta: dict[str, Any]) -> str | None:
        """Calculate duration string for finished tools."""
        dur = meta.get("duration_seconds")
        if isinstance(dur, int | float):
            return self._format_elapsed_time(dur)

        try:
            server_now = self.stream_processor.server_elapsed_time
            server_start = meta.get("server_started_at")
            if isinstance(server_now, int | float) and isinstance(
                server_start, int | float
            ):
                dur = max(0.0, float(server_now) - float(server_start))
            elif meta.get("started_at") is not None:
                dur = max(0.0, float(monotonic() - meta.get("started_at")))
        except Exception:
            dur = None

        return self._format_elapsed_time(dur) if isinstance(dur, int | float) else None

    def _process_running_tool_panel(
        self, title: str, meta: dict[str, Any], body: str
    ) -> tuple[str, str]:
        """Process a running tool panel."""
        elapsed_str = self._calculate_elapsed_time(meta)
        adjusted_title = f"{title}  · {elapsed_str}"
        chip = f"⏱ {elapsed_str}"

        if not body:
            body = chip
        else:
            body = f"{body}\n\n{chip}"

        return adjusted_title, body

    def _process_finished_tool_panel(self, title: str, meta: dict[str, Any]) -> str:
        """Process a finished tool panel."""
        duration_str = self._calculate_finished_duration(meta)
        return f"{title}  · {duration_str}" if duration_str else title

    def _create_tool_panel_for_session(
        self, sid: str, meta: dict[str, Any]
    ) -> AIPPanel | None:
        """Create a single tool panel for the session."""
        title = meta.get("title") or "Tool"
        status = meta.get("status") or "running"
        chunks = meta.get("chunks") or []
        is_delegation = bool(meta.get("is_delegation"))

        if self._should_skip_finished_panel(sid, status):
            return None

        body = "".join(chunks)
        adjusted_title = title

        if status == "running":
            adjusted_title, body = self._process_running_tool_panel(title, meta, body)
        elif status == "finished":
            adjusted_title = self._process_finished_tool_panel(title, meta)

        return create_tool_panel(
            title=adjusted_title,
            content=body,
            status=status,
            theme=self.cfg.theme,
            is_delegation=is_delegation,
        )

    def _render_tool_panels(self) -> list[AIPPanel]:
        """Render tool execution output panels."""
        panels: list[AIPPanel] = []
        for sid in self.tool_order:
            meta = self.tool_panels.get(sid) or {}
            panel = self._create_tool_panel_for_session(sid, meta)
            if panel:
                panels.append(panel)

        return panels

    def _format_dict_or_list_output(self, output_value: dict | list) -> str:
        """Format dict/list output as pretty JSON."""
        try:
            return (
                self.OUTPUT_PREFIX
                + "```json\n"
                + json.dumps(output_value, indent=2)
                + "\n```\n"
            )
        except Exception:
            return self.OUTPUT_PREFIX + str(output_value) + "\n"

    def _clean_sub_agent_prefix(self, output: str, tool_name: str | None) -> str:
        """Clean sub-agent name prefix from output."""
        if not (tool_name and is_delegation_tool(tool_name)):
            return output

        sub = tool_name
        if tool_name.startswith("delegate_to_"):
            sub = tool_name.replace("delegate_to_", "")
        elif tool_name.startswith("delegate_"):
            sub = tool_name.replace("delegate_", "")
        prefix = f"[{sub}]"
        if output.startswith(prefix):
            return output[len(prefix) :].lstrip()

        return output

    def _format_json_string_output(self, output: str) -> str:
        """Format string that looks like JSON."""
        try:
            parsed = json.loads(output)
            return (
                self.OUTPUT_PREFIX
                + "```json\n"
                + json.dumps(parsed, indent=2)
                + "\n```\n"
            )
        except Exception:
            return self.OUTPUT_PREFIX + output + "\n"

    def _format_string_output(self, output: str, tool_name: str | None) -> str:
        """Format string output with optional prefix cleaning."""
        s = output.strip()
        s = self._clean_sub_agent_prefix(s, tool_name)

        # If looks like JSON, pretty print it
        if (s.startswith("{") and s.endswith("}")) or (
            s.startswith("[") and s.endswith("]")
        ):
            return self._format_json_string_output(s)

        return self.OUTPUT_PREFIX + s + "\n"

    def _format_other_output(self, output_value: Any) -> str:
        """Format other types of output."""
        try:
            return self.OUTPUT_PREFIX + json.dumps(output_value, indent=2) + "\n"
        except Exception:
            return self.OUTPUT_PREFIX + str(output_value) + "\n"

    def _format_output_block(self, output_value: Any, tool_name: str | None) -> str:
        """Format an output value for panel display."""
        if isinstance(output_value, dict | list):
            return self._format_dict_or_list_output(output_value)
        elif isinstance(output_value, str):
            return self._format_string_output(output_value, tool_name)
        else:
            return self._format_other_output(output_value)
