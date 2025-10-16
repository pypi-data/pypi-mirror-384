"""
Shadai Client - Official Python SDK for Shadai AI
==================================================

Beautiful, Pythonic client for interacting with Shadai AI services.

Quick Start:
    >>> from shadai import Shadai, tool
    >>>
    >>> # Ingest documents from a folder
    >>> async with Shadai(name="my-session") as shadai:
    ...     async for chunk in shadai.ingest(folder_path="/path/to/docs"):
    ...         print(chunk, end="", flush=True)
    >>>
    >>> # Query knowledge base with session management
    >>> async with Shadai(name="my-session") as shadai:
    ...     async for chunk in shadai.query(query="What is machine learning?"):
    ...         print(chunk, end="", flush=True)
    >>>
    >>> # Create temporal session (auto-deleted)
    >>> async with Shadai(temporal=True) as shadai:
    ...     async for chunk in shadai.query(query="What is AI?"):
    ...         print(chunk, end="", flush=True)
    >>>
    >>> # Define tools with automatic schema inference
    >>> @tool
    ... def search_database(query: str, limit: int = 10) -> str:
    ...     '''Search the database for records.
    ...
    ...     Args:
    ...         query: Search query string
    ...         limit: Maximum number of results to return
    ...     '''
    ...     return "results"
    >>>
    >>> # Use intelligent agent (plan → execute → synthesize)
    >>> async with Shadai(name="my-session") as shadai:
    ...     async for chunk in shadai.agent(
    ...         prompt="Find top 5 users",
    ...         tools=[search_database]
    ...     ):
    ...         print(chunk, end="", flush=True)

Documentation: https://docs.shadai.com
GitHub: https://github.com/shadai/shadai-client
"""

from .__version__ import __author__, __description__, __version__
from .client import ShadaiClient
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    InvalidArgumentsError,
    ServerError,
    ShadaiError,
    ToolNotFoundError,
)
from .models import AgentTool, Tool, ToolDefinition, ToolRegistry, tool
from .tools import (
    EngineTool,
    IngestTool,
    QueryTool,
    Shadai,
    SummarizeTool,
    WebSearchTool,
)

__all__ = [
    # Main client
    "Shadai",
    # Low-level client
    "ShadaiClient",
    # Tool classes
    "QueryTool",
    "SummarizeTool",
    "WebSearchTool",
    "EngineTool",
    "IngestTool",
    "AgentTool",
    # Tool utilities
    "tool",
    # Models
    "Tool",
    "ToolDefinition",
    "ToolRegistry",
    # Exceptions
    "ShadaiError",
    "AuthenticationError",
    "ConnectionError",
    "ToolNotFoundError",
    "InvalidArgumentsError",
    "ServerError",
    # Version info
    "__version__",
    "__author__",
    "__description__",
]
