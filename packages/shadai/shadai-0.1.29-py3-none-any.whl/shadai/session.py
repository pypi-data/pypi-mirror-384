"""
Session Context Manager
-----------------------
Context manager for managing RAG session lifecycle.
"""

import json
import os
from typing import Optional
from uuid import uuid4

from .client import ShadaiClient
from .exceptions import InvalidArgumentsError


class Session:
    """Internal context manager for RAG session lifecycle.

    Automatically handles session creation, retrieval, and optional deletion.

    Args:
        name: Optional session name to retrieve existing session
        temporal: If True, delete session on context exit (default: False)
        client: ShadaiClient instance
    """

    def __init__(
        self,
        name: Optional[str] = None,
        temporal: bool = False,
        client: Optional[ShadaiClient] = None,
    ) -> None:
        """Initialize session context manager.

        Args:
            name: Optional session name to retrieve
            temporal: Whether to delete session on exit
            client: ShadaiClient instance (required)
        """
        if not client:
            raise ValueError("ShadaiClient instance is required")

        self._name = name
        self._temporal = temporal
        self._client = client
        self._session_data: Optional[dict] = None

    @property
    def uuid(self) -> Optional[str]:
        """Get session UUID."""
        return str(self._session_data.get("uuid")) if self._session_data else None

    @property
    def name(self) -> Optional[str]:
        """Get session name."""
        return self._session_data.get("name") if self._session_data else None

    async def __aenter__(self) -> "Session":
        """Enter context: create or retrieve session.

        Returns:
            Session instance with populated session data
        """
        if self._name:
            # Get existing session or create if doesn't exist
            result = await self._client.call_tool(
                tool_name="session_get_or_create",
                arguments={"name": self._name},
            )
            self._session_data = json.loads(result)
        else:
            # Create new session with generated name
            generated_name = f"session-{uuid4().hex[:8]}"
            result = await self._client.call_tool(
                tool_name="session_create",
                arguments={"name": generated_name},
            )
            self._session_data = json.loads(result)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context: optionally delete session.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        if self._temporal and self.uuid:
            await self._client.call_tool(
                tool_name="session_delete",
                arguments={"session_uuid": self.uuid},
            )
