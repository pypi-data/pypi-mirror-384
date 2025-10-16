#!/usr/bin/env python3
"""Data models for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from glaip_sdk.config.constants import DEFAULT_AGENT_RUN_TIMEOUT


class Agent(BaseModel):
    """Agent model for API responses."""

    id: str
    name: str
    instruction: str | None = None
    description: str | None = None  # Add missing description field
    type: str | None = None
    framework: str | None = None
    version: str | None = None
    tools: list[dict[str, Any]] | None = None  # Backend returns ToolReference objects
    agents: list[dict[str, Any]] | None = None  # Backend returns AgentReference objects
    mcps: list[dict[str, Any]] | None = None  # Backend returns MCPReference objects
    tool_configs: dict[str, Any] | None = (
        None  # Backend returns tool configurations keyed by tool UUID
    )
    agent_config: dict[str, Any] | None = None
    timeout: int = DEFAULT_AGENT_RUN_TIMEOUT
    metadata: dict[str, Any] | None = None
    language_model_id: str | None = None
    a2a_profile: dict[str, Any] | None = None
    created_at: datetime | None = None  # Backend returns creation timestamp
    updated_at: datetime | None = None  # Backend returns last update timestamp
    _client: Any = None

    def _set_client(self, client: Any) -> "Agent":
        """Set the client reference for this resource."""
        self._client = client
        return self

    def run(self, message: str, verbose: bool = False, **kwargs) -> str:
        """Run the agent with a message.

        Args:
            message: The message to send to the agent
            verbose: Enable verbose output and event JSON logging
            **kwargs: Additional arguments passed to run_agent
        """
        if not self._client:
            raise RuntimeError(
                "No client available. Use client.get_agent_by_id() to get a client-connected agent."
            )
        # Automatically pass the agent name for better renderer display
        kwargs.setdefault("agent_name", self.name)
        # Pass verbose flag through to enable event JSON output
        return self._client.run_agent(self.id, message, verbose=verbose, **kwargs)

    async def arun(self, message: str, **kwargs) -> AsyncGenerator[dict, None]:
        """Async run the agent with a message, yielding streaming JSON chunks.

        Args:
            message: The message to send to the agent
            **kwargs: Additional arguments passed to arun_agent

        Yields:
            Dictionary containing parsed JSON chunks from the streaming response

        Raises:
            RuntimeError: When no client is available
            AgentTimeoutError: When agent execution times out
            Exception: For other unexpected errors
        """
        if not self._client:
            raise RuntimeError(
                "No client available. Use client.get_agent_by_id() to get a client-connected agent."
            )
        # Automatically pass the agent name for better context
        kwargs.setdefault("agent_name", self.name)

        async for chunk in self._client.arun_agent(self.id, message, **kwargs):
            yield chunk

    def update(self, **kwargs) -> "Agent":
        """Update agent attributes."""
        if not self._client:
            raise RuntimeError(
                "No client available. Use client.get_agent_by_id() to get a client-connected agent."
            )
        updated_agent = self._client.update_agent(self.id, **kwargs)
        # Update current instance with new data
        for key, value in updated_agent.model_dump().items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def delete(self) -> None:
        """Delete the agent."""
        if not self._client:
            raise RuntimeError(
                "No client available. Use client.get_agent_by_id() to get a client-connected agent."
            )
        self._client.delete_agent(self.id)


class Tool(BaseModel):
    """Tool model for API responses."""

    id: str
    name: str
    tool_type: str | None = None
    description: str | None = None
    framework: str | None = None
    version: str | None = None
    tool_script: str | None = None
    tool_file: str | None = None
    tags: str | list[str] | None = None
    _client: Any = None  # Will hold client reference

    def _set_client(self, client: Any) -> "Tool":
        """Set the client reference for this resource."""
        self._client = client
        return self

    def get_script(self) -> str:
        """Get the tool script content."""
        if self.tool_script:
            return self.tool_script
        elif self.tool_file:
            return f"Script content from file: {self.tool_file}"
        else:
            return "No script content available"

    def update(self, **kwargs) -> "Tool":
        """Update tool attributes.

        Supports both metadata updates and file uploads.
        Pass 'file' parameter to update tool code via file upload.
        """
        if not self._client:
            raise RuntimeError(
                "No client available. Use client.get_tool_by_id() to get a client-connected tool."
            )

        # Check if file upload is requested
        if "file" in kwargs:
            file_path = kwargs.pop("file")  # Remove file from kwargs for metadata
            updated_tool = self._client.tools.update_tool_via_file(
                self.id, file_path, **kwargs
            )
        else:
            # Regular metadata update
            updated_tool = self._client.tools.update_tool(self.id, **kwargs)

        # Update current instance with new data
        for key, value in updated_tool.model_dump().items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def delete(self) -> None:
        """Delete the tool."""
        if not self._client:
            raise RuntimeError(
                "No client available. Use client.get_tool_by_id() to get a client-connected tool."
            )
        self._client.delete_tool(self.id)


class MCP(BaseModel):
    """MCP model for API responses."""

    id: str
    name: str
    description: str | None = None
    config: dict[str, Any] | None = None
    transport: str | None = None  # "sse" or "http"
    authentication: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    _client: Any = None  # Will hold client reference

    def _set_client(self, client: Any) -> "MCP":
        """Set the client reference for this resource."""
        self._client = client
        return self

    def get_tools(self) -> list[dict[str, Any]]:
        """Get tools available from this MCP."""
        if not self._client:
            raise RuntimeError(
                "No client available. Use client.get_mcp_by_id() to get a client-connected MCP."
            )
        # This would delegate to the client's MCP tools endpoint
        # For now, return empty list as placeholder
        return []

    def update(self, **kwargs) -> "MCP":
        """Update MCP attributes."""
        if not self._client:
            raise RuntimeError(
                "No client available. Use client.get_mcp_by_id() to get a client-connected MCP."
            )
        updated_mcp = self._client.update_mcp(self.id, **kwargs)
        # Update current instance with new data
        for key, value in updated_mcp.model_dump().items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def delete(self) -> None:
        """Delete the MCP."""
        if not self._client:
            raise RuntimeError(
                "No client available. Use client.get_mcp_by_id() to get a client-connected MCP."
            )
        self._client.delete_mcp(self.id)


class LanguageModelResponse(BaseModel):
    """Language model response model."""

    name: str
    provider: str
    description: str | None = None
    capabilities: list[str] | None = None
    max_tokens: int | None = None
    supports_streaming: bool = False


class TTYRenderer:
    """Simple TTY renderer for non-Rich environments."""

    def __init__(self, use_color: bool = True):
        """Initialize the TTY renderer.

        Args:
            use_color: Whether to use color output
        """
        self.use_color = use_color

    def render_message(self, message: str, event_type: str = "message") -> None:
        """Render a message with optional color."""
        if event_type == "error":
            print(f"ERROR: {message}", flush=True)
        elif event_type == "done":
            print(f"\n✅ {message}", flush=True)
        else:
            print(message, flush=True)
