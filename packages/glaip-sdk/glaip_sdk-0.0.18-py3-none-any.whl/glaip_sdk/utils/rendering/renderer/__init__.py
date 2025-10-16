"""Renderer package for modular streaming output.

This package provides modular components for rendering agent execution streams,
with clean separation of concerns between configuration, console handling,
debug output, panel rendering, progress tracking, and event routing.
"""

import io

from rich.console import Console

from glaip_sdk.rich_components import AIPPanel
from glaip_sdk.utils.rendering.renderer.base import RichStreamRenderer
from glaip_sdk.utils.rendering.renderer.config import RendererConfig
from glaip_sdk.utils.rendering.renderer.console import CapturingConsole
from glaip_sdk.utils.rendering.renderer.debug import render_debug_event
from glaip_sdk.utils.rendering.renderer.panels import (
    create_context_panel,
    create_final_panel,
    create_main_panel,
    create_tool_panel,
)
from glaip_sdk.utils.rendering.renderer.progress import (
    format_tool_title,
    is_delegation_tool,
)
from glaip_sdk.utils.rendering.renderer.stream import StreamProcessor


def make_silent_renderer() -> RichStreamRenderer:
    """Create a renderer that suppresses all terminal output.

    Uses an in-memory console and disables live updates/panels.
    """
    cfg = RendererConfig(
        live=False,
        persist_live=False,
        show_delegate_tool_panels=False,
        render_thinking=False,
    )
    return RichStreamRenderer(
        console=Console(file=io.StringIO(), force_terminal=False), cfg=cfg
    )


def make_minimal_renderer() -> RichStreamRenderer:
    """Create a minimal renderer.

    Prints a compact header and the user request panel, but no live updates or tool panels.
    """
    cfg = RendererConfig(
        live=False,
        persist_live=False,
        show_delegate_tool_panels=False,
        render_thinking=False,
    )
    return RichStreamRenderer(console=Console(), cfg=cfg)


def print_panel(
    content: str,
    *,
    title: str | None = None,
    border_style: str = "blue",
    padding: tuple[int, int] = (1, 2),
    console: Console | None = None,
) -> None:
    """Print boxed content using Rich without exposing Console/Panel at call site.

    Args:
        content: The text to display inside the panel.
        title: Optional title for the panel.
        border_style: Rich style string for the border color.
        padding: (vertical, horizontal) padding inside the panel.
        console: Optional Rich Console to print to; created if not provided.
    """
    c = console or Console()
    c.print(AIPPanel(content, title=title, border_style=border_style, padding=padding))


__all__ = [
    # Main classes
    "RichStreamRenderer",
    "RendererConfig",
    "CapturingConsole",
    "StreamProcessor",
    "make_silent_renderer",
    "make_minimal_renderer",
    "print_panel",
    "render_debug_event",
    "create_main_panel",
    "create_tool_panel",
    "create_context_panel",
    "create_final_panel",
    "format_tool_title",
    "is_delegation_tool",
]
