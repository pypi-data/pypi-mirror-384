"""Rich display utilities for enhanced output.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from typing import Any

from glaip_sdk.utils.rich_utils import RICH_AVAILABLE


def print_agent_output(output: str, title: str = "Agent Output") -> None:
    """Print agent output with rich formatting.

    Args:
        output: The agent's response text
        title: Title for the output panel
    """
    if RICH_AVAILABLE:
        # Lazy import Rich components
        from rich.console import Console
        from rich.text import Text

        from glaip_sdk.rich_components import AIPPanel

        console = Console()
        panel = AIPPanel(
            Text(output, style="green"),
            title=title,
            border_style="green",
        )
        console.print(panel)
    else:
        print(f"\n=== {title} ===")
        print(output)
        print("=" * (len(title) + 8))


def print_agent_created(agent: Any, title: str = "🤖 Agent Created") -> None:
    """Print agent creation success with rich formatting.

    Args:
        agent: The created agent object
        title: Title for the output panel
    """
    if RICH_AVAILABLE:
        # Lazy import Rich components
        from rich.console import Console

        from glaip_sdk.rich_components import AIPPanel

        console = Console()
        panel = AIPPanel(
            f"[green]✅ Agent '{agent.name}' created successfully![/green]\n\n"
            f"ID: {agent.id}\n"
            f"Model: {getattr(agent, 'model', 'N/A')}\n"
            f"Type: {getattr(agent, 'type', 'config')}\n"
            f"Framework: {getattr(agent, 'framework', 'langchain')}\n"
            f"Version: {getattr(agent, 'version', '1.0')}",
            title=title,
            border_style="green",
        )
        console.print(panel)
    else:
        print(f"✅ Agent '{agent.name}' created successfully!")
        print(f"ID: {agent.id}")
        print(f"Model: {getattr(agent, 'model', 'N/A')}")
        print(f"Type: {getattr(agent, 'type', 'config')}")
        print(f"Framework: {getattr(agent, 'framework', 'langchain')}")
        print(f"Version: {getattr(agent, 'version', '1.0')}")


def print_agent_updated(agent: Any) -> None:
    """Print agent update success with rich formatting.

    Args:
        agent: The updated agent object
    """
    if RICH_AVAILABLE:
        # Lazy import Rich components
        from rich.console import Console

        console = Console()
        console.print(f"[green]✅ Agent '{agent.name}' updated successfully[/green]")
    else:
        print(f"✅ Agent '{agent.name}' updated successfully")


def print_agent_deleted(agent_id: str) -> None:
    """Print agent deletion success with rich formatting.

    Args:
        agent_id: The deleted agent's ID
    """
    if RICH_AVAILABLE:
        # Lazy import Rich components
        from rich.console import Console

        console = Console()
        console.print(f"[green]✅ Agent deleted successfully (ID: {agent_id})[/green]")
    else:
        print(f"✅ Agent deleted successfully (ID: {agent_id})")
