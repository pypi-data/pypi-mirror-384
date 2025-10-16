"""Configuration types for the renderer package.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RendererConfig:
    """Configuration for the RichStreamRenderer."""

    # Style and layout
    theme: str = "dark"  # dark|light
    style: str = "pretty"  # pretty|debug|minimal

    # Performance
    think_threshold: float = 0.7
    refresh_debounce: float = 0.25
    render_thinking: bool = True
    live: bool = True
    persist_live: bool = True

    # Debug visibility toggles
    show_delegate_tool_panels: bool = False

    # Scrollback/append options
    append_finished_snapshots: bool = False
    snapshot_max_chars: int = 12000
    snapshot_max_lines: int = 200
