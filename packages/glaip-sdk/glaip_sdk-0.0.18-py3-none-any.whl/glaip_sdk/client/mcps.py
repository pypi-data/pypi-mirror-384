#!/usr/bin/env python3
"""MCP client for AIP SDK.

Authors:
    Raymond Christopher (raymond.christopher@gdplabs.id)
"""

import logging
from typing import Any

from glaip_sdk.client.base import BaseClient
from glaip_sdk.config.constants import (
    DEFAULT_MCP_TRANSPORT,
    DEFAULT_MCP_TYPE,
)
from glaip_sdk.models import MCP
from glaip_sdk.utils.client_utils import create_model_instances, find_by_name

# API endpoints
MCPS_ENDPOINT = "/mcps/"
MCPS_CONNECT_ENDPOINT = "/mcps/connect"
MCPS_CONNECT_TOOLS_ENDPOINT = "/mcps/connect/tools"

# Set up module-level logger
logger = logging.getLogger("glaip_sdk.mcps")


class MCPClient(BaseClient):
    """Client for MCP operations."""

    def __init__(self, *, parent_client: BaseClient | None = None, **kwargs):
        """Initialize the MCP client.

        Args:
            parent_client: Parent client to adopt session/config from
            **kwargs: Additional arguments for standalone initialization
        """
        super().__init__(parent_client=parent_client, **kwargs)

    def list_mcps(self) -> list[MCP]:
        """List all MCPs."""
        data = self._request("GET", MCPS_ENDPOINT)
        return create_model_instances(data, MCP, self)

    def get_mcp_by_id(self, mcp_id: str) -> MCP:
        """Get MCP by ID."""
        data = self._request("GET", f"{MCPS_ENDPOINT}{mcp_id}")
        return MCP(**data)._set_client(self)

    def find_mcps(self, name: str | None = None) -> list[MCP]:
        """Find MCPs by name."""
        # Backend doesn't support name query parameter, so we fetch all and filter client-side
        data = self._request("GET", MCPS_ENDPOINT)
        mcps = create_model_instances(data, MCP, self)
        return find_by_name(mcps, name, case_sensitive=False)

    def create_mcp(
        self,
        name: str,
        description: str | None = None,
        config: dict[str, Any] | None = None,
        **kwargs,
    ) -> MCP:
        """Create a new MCP."""
        # Use the helper method to build a properly structured payload
        payload = self._build_create_payload(
            name=name,
            description=description,
            config=config,
            **kwargs,
        )

        # Create the MCP and fetch full details
        full_mcp_data = self._post_then_fetch(
            id_key="id",
            post_endpoint=MCPS_ENDPOINT,
            get_endpoint_fmt=f"{MCPS_ENDPOINT}{{id}}",
            json=payload,
        )
        return MCP(**full_mcp_data)._set_client(self)

    def update_mcp(self, mcp_id: str, **kwargs) -> MCP:
        """Update an existing MCP.

        Automatically chooses between PUT (full update) and PATCH (partial update)
        based on the provided fields:
        - Uses PUT if name, config, and transport are all provided (full update)
        - Uses PATCH otherwise (partial update)
        """
        # Check if all required fields for full update are provided
        required_fields = {"name", "config", "transport"}
        provided_fields = set(kwargs.keys())

        if required_fields.issubset(provided_fields):
            # All required fields provided - use full update (PUT)
            method = "PUT"
        else:
            # Partial update - use PATCH
            method = "PATCH"

        data = self._request(method, f"{MCPS_ENDPOINT}{mcp_id}", json=kwargs)
        return MCP(**data)._set_client(self)

    def delete_mcp(self, mcp_id: str) -> None:
        """Delete an MCP."""
        self._request("DELETE", f"{MCPS_ENDPOINT}{mcp_id}")

    def _build_create_payload(
        self,
        name: str,
        description: str | None = None,
        transport: str = DEFAULT_MCP_TRANSPORT,
        config: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Build payload for MCP creation with proper metadata handling.

        CENTRALIZED PAYLOAD BUILDING LOGIC:
        - Sets proper defaults and required fields
        - Handles config serialization consistently
        - Processes transport and other metadata properly

        Args:
            name: MCP name
            description: MCP description (optional)
            transport: MCP transport protocol (defaults to stdio)
            config: MCP configuration dictionary
            **kwargs: Additional parameters

        Returns:
            Complete payload dictionary for MCP creation
        """
        # Prepare the creation payload with required fields
        payload: dict[str, Any] = {
            "name": name.strip(),
            "type": DEFAULT_MCP_TYPE,  # MCPs are always server type
            "transport": transport,
        }

        # Add description if provided
        if description:
            payload["description"] = description.strip()

        # Handle config - ensure it's properly serialized
        if config:
            payload["config"] = config

        # Add any other kwargs (excluding already handled ones)
        excluded_keys = {"type"}  # type is handled above
        for key, value in kwargs.items():
            if key not in excluded_keys:
                payload[key] = value

        return payload

    def _build_update_payload(
        self,
        current_mcp: MCP,
        name: str | None = None,
        description: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Build payload for MCP update with proper current state preservation.

        Args:
            current_mcp: Current MCP object to update
            name: New MCP name (None to keep current)
            description: New description (None to keep current)
            **kwargs: Additional parameters (config, transport, etc.)

        Returns:
            Complete payload dictionary for MCP update

        Notes:
            - Preserves current values as defaults when new values not provided
            - Handles config updates properly
        """
        # Prepare the update payload with current values as defaults
        update_data = {
            "name": name if name is not None else current_mcp.name,
            "type": DEFAULT_MCP_TYPE,  # Required by backend, MCPs are always server type
            "transport": kwargs.get(
                "transport", getattr(current_mcp, "transport", DEFAULT_MCP_TRANSPORT)
            ),
        }

        # Handle description with proper None handling
        if description is not None:
            update_data["description"] = description.strip()
        elif hasattr(current_mcp, "description") and current_mcp.description:
            update_data["description"] = current_mcp.description

        # Handle config with proper merging
        if "config" in kwargs:
            update_data["config"] = kwargs["config"]
        elif hasattr(current_mcp, "config") and current_mcp.config:
            # Preserve existing config if present
            update_data["config"] = current_mcp.config

        # Add any other kwargs (excluding already handled ones)
        excluded_keys = {"transport", "config"}
        for key, value in kwargs.items():
            if key not in excluded_keys:
                update_data[key] = value

        return update_data

    def get_mcp_tools(self, mcp_id: str) -> list[dict[str, Any]]:
        """Get tools available from an MCP."""
        data = self._request("GET", f"{MCPS_ENDPOINT}{mcp_id}/tools")
        return data or []

    def test_mcp_connection(self, config: dict[str, Any]) -> dict[str, Any]:
        """Test MCP connection using configuration.

        Args:
            config: MCP configuration dictionary

        Returns:
            dict: Connection test result

        Raises:
            Exception: If connection test fails
        """
        try:
            response = self._request("POST", MCPS_CONNECT_ENDPOINT, json=config)
            return response
        except Exception as e:
            logger.error(f"Failed to test MCP connection: {e}")
            raise

    def test_mcp_connection_from_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Test MCP connection using configuration (alias for test_mcp_connection).

        Args:
            config: MCP configuration dictionary

        Returns:
            dict: Connection test result
        """
        return self.test_mcp_connection(config)

    def get_mcp_tools_from_config(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Fetch tools from MCP configuration without saving.

        Args:
            config: MCP configuration dictionary

        Returns:
            list: List of available tools from the MCP

        Raises:
            Exception: If tool fetching fails
        """
        try:
            response = self._request("POST", MCPS_CONNECT_TOOLS_ENDPOINT, json=config)
            if response is None:
                return []
            return response.get("tools", []) or []
        except Exception as e:
            logger.error(f"Failed to get MCP tools from config: {e}")
            raise
