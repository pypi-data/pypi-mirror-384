"""
Shadai Tools - High-Level API Wrappers
---------------------------------------
Beautiful, Pythonic interfaces for Shadai AI tools.
"""

import json
import asyncio
import base64
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, List, Optional

from .client import ShadaiClient
from .models import AgentTool

if TYPE_CHECKING:
    from .session import Session

from dotenv import load_dotenv

load_dotenv()


class QueryTool:
    """
    Knowledge Base Query Tool.

    Retrieves relevant information from uploaded documents using RAG
    (Retrieval-Augmented Generation).

    Examples:
        >>> query = QueryTool(client=client, session_uuid="...")
        >>> async for chunk in query("What is machine learning?"):
        ...     print(chunk, end="", flush=True)
    """

    def __init__(self, client: ShadaiClient, session_uuid: str) -> None:
        """
        Initialize Query tool.

        Args:
            client: Shadai client instance
            session_uuid: Your session UUID
        """
        self.client = client
        self.session_uuid = session_uuid

    async def __call__(
        self,
        query: str,
        use_memory: bool = True,
    ) -> AsyncIterator[str]:
        """
        Query the knowledge base with streaming response.

        Args:
            query: Your question or search query
            use_memory: Enable conversation memory

        Yields:
            Text chunks from the knowledge base

        Examples:
            >>> async for chunk in query_tool("Explain transformers"):
            ...     print(chunk, end="")
        """
        async for chunk in self.client.stream_tool(
            tool_name="shadai_query",
            arguments={
                "session_uuid": self.session_uuid,
                "query": query,
                "use_memory": use_memory,
            },
        ):
            yield chunk


class SummarizeTool:
    """
    Document Summarization Tool.

    Generates comprehensive summaries of all documents in a session.

    Examples:
        >>> summarize = SummarizeTool(client=client, session_uuid="...")
        >>> async for chunk in summarize():
        ...     print(chunk, end="", flush=True)
    """

    def __init__(self, client: ShadaiClient, session_uuid: str) -> None:
        """
        Initialize Summarize tool.

        Args:
            client: Shadai client instance
            session_uuid: Your session UUID
        """
        self.client = client
        self.session_uuid = session_uuid

    async def __call__(self, use_memory: bool = True) -> AsyncIterator[str]:
        """
        Generate summary of all session documents.

        Args:
            use_memory: Enable conversation memory

        Yields:
            Text chunks from the summary

        Examples:
            >>> async for chunk in summarize_tool():
            ...     print(chunk, end="")
        """
        async for chunk in self.client.stream_tool(
            tool_name="shadai_summarize",
            arguments={
                "session_uuid": self.session_uuid,
                "use_memory": use_memory,
            },
        ):
            yield chunk


class WebSearchTool:
    """
    Web Search Tool.

    Searches the internet for current information and provides cited answers.

    Examples:
        >>> search = WebSearchTool(client=client, session_uuid="...")
        >>> async for chunk in search("Latest AI developments 2024"):
        ...     print(chunk, end="", flush=True)
    """

    def __init__(self, client: ShadaiClient, session_uuid: str) -> None:
        """
        Initialize Web Search tool.

        Args:
            client: Shadai client instance
            session_uuid: Your session UUID
        """
        self.client = client
        self.session_uuid = session_uuid

    async def __call__(
        self,
        prompt: str,
        use_web_search: bool = True,
        use_memory: bool = True,
    ) -> AsyncIterator[str]:
        """
        Search the web and get an answer.

        Args:
            prompt: Your question or search query
            use_web_search: Enable web search (default: True)
            use_memory: Enable conversation memory

        Yields:
            Text chunks from the search results

        Examples:
            >>> async for chunk in search_tool("Current weather in Paris"):
            ...     print(chunk, end="")
        """
        async for chunk in self.client.stream_tool(
            tool_name="shadai_web_search",
            arguments={
                "session_uuid": self.session_uuid,
                "prompt": prompt,
                "use_web_search": use_web_search,
                "use_memory": use_memory,
            },
        ):
            yield chunk


class EngineTool:
    """
    Shadai Engine Tool.

    Orchestrates multiple tools (knowledge base, summarization, web search)
    to provide comprehensive answers.

    Examples:
        >>> engine = EngineTool(client=client, session_uuid="...")
        >>> async for chunk in engine(
        ...     prompt="Compare my docs with current trends",
        ...     use_knowledge_base=True,
        ...     use_web_search=True
        ... ):
        ...     print(chunk, end="", flush=True)
    """

    def __init__(self, client: ShadaiClient, session_uuid: str) -> None:
        """
        Initialize Engine tool.

        Args:
            client: Shadai client instance
            session_uuid: Your session UUID
        """
        self.client = client
        self.session_uuid = session_uuid

    async def __call__(
        self,
        prompt: str,
        use_knowledge_base: bool = False,
        use_summary: bool = False,
        use_web_search: bool = False,
        use_memory: bool = True,
    ) -> AsyncIterator[str]:
        """
        Execute engine with multiple tool capabilities.

        Args:
            prompt: Your question or prompt
            use_knowledge_base: Enable knowledge base retrieval
            use_summary: Enable document summarization
            use_web_search: Enable web search
            use_memory: Enable conversation memory

        Yields:
            Text chunks from the engine

        Examples:
            >>> async for chunk in engine_tool(
            ...     "What are ML trends?",
            ...     use_knowledge_base=True,
            ...     use_web_search=True
            ... ):
            ...     print(chunk, end="")
        """
        async for chunk in self.client.stream_tool(
            tool_name="shadai_engine",
            arguments={
                "session_uuid": self.session_uuid,
                "prompt": prompt,
                "use_knowledge_base": use_knowledge_base,
                "use_summary": use_summary,
                "use_web_search": use_web_search,
                "use_memory": use_memory,
            },
        ):
            yield chunk


class IngestTool:
    """
    Folder Ingesting Tool.

    Recursively processes all PDF and image files in a folder, uploading them
    to a RAG session for knowledge base ingestion. Supports nested folder structures.

    Examples:
        >>> ingest_tool = IngestTool(client=client, session_uuid="...")
        >>> results = await ingest_tool("/path/to/documents")
        >>> print(f"Processed {len(results['successful'])} files")
    """

    SUPPORTED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}
    MAX_FILE_SIZE_MB = 35
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # 35 MB in bytes
    MAX_BATCH_SIZE_MB = 110
    MAX_BATCH_SIZE_BYTES = MAX_BATCH_SIZE_MB * 1024 * 1024  # 110 MB in bytes

    def __init__(self, client: ShadaiClient, session_uuid: str) -> None:
        """
        Initialize Ingest tool.

        Args:
            client: Shadai client instance
            session_uuid: Your session UUID
        """
        self.client = client
        self.session_uuid = session_uuid

    async def __call__(
        self, folder_path: str, max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Ingest all PDF and image files in a folder (including nested folders).

        Args:
            folder_path: Path to the folder containing files to process
            max_concurrent: Maximum number of concurrent file uploads (default: 5)

        Returns:
            Dictionary with successful uploads, failed uploads, and statistics

        Raises:
            ValueError: If folder path doesn't exist or is not a directory

        Examples:
            >>> results = await ingest_tool("/path/to/docs")
            >>> print(f"Success: {len(results['successful'])}")
            >>> print(f"Failed: {len(results['failed'])}")
        """
        folder = Path(folder_path)

        if not folder.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")

        if not folder.is_dir():
            raise ValueError(f"Path is not a directory: {folder_path}")

        files_to_process = self._find_files(folder=folder)

        if not files_to_process:
            return {
                "successful": [],
                "failed": [],
                "skipped": [],
                "total_files": 0,
                "successful_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
            }

        files_to_upload = []
        skipped_files = []

        for file_path in files_to_process:
            file_size = file_path.stat().st_size
            if file_size > self.MAX_FILE_SIZE_BYTES:
                size_mb = file_size / (1024 * 1024)
                skipped_files.append(
                    {
                        "file_path": str(file_path),
                        "filename": file_path.name,
                        "size": file_size,
                        "size_mb": f"{size_mb:.2f} MB",
                        "reason": f"""
                            File size ({size_mb:.2f} MB) exceeds maximum allowed 
                            size ({self.MAX_FILE_SIZE_MB} MB)
                        """,
                    }
                )
            else:
                files_to_upload.append(file_path)

        results = await self._ingest_files(
            files=files_to_upload, max_concurrent=max_concurrent
        )
        results["skipped"] = skipped_files
        results["skipped_count"] = len(skipped_files)
        results["total_files"] = len(files_to_process)

        return results

    def _find_files(self, folder: Path) -> List[Path]:
        """
        Recursively find all supported files in folder.

        Args:
            folder: Folder path to search

        Returns:
            List of file paths with supported extensions
        """
        files = []
        for item in folder.rglob("*"):
            if item.is_file() and item.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                files.append(item)
        return files

    def _create_batches(self, files: List[Path]) -> List[List[Path]]:
        """
        Batch files into groups with maximum total size of MAX_BATCH_SIZE_BYTES.

        Args:
            files: List of file paths to batch

        Returns:
            List of batches, where each batch is a list of file paths
        """
        batches: List[List[Path]] = []
        current_batch: List[Path] = []
        current_batch_size = 0

        for file_path in files:
            file_size = file_path.stat().st_size

            # If adding this file would exceed the batch limit, start a new batch
            if (
                current_batch
                and (current_batch_size + file_size) > self.MAX_BATCH_SIZE_BYTES
            ):
                batches.append(current_batch)
                current_batch = [file_path]
                current_batch_size = file_size
            else:
                current_batch.append(file_path)
                current_batch_size += file_size

        # Add the last batch if not empty
        if current_batch:
            batches.append(current_batch)

        return batches

    async def _ingest_files(
        self, files: List[Path], max_concurrent: int
    ) -> Dict[str, Any]:
        """
        Ingest multiple files concurrently with batching by size.

        Groups files into batches of up to MAX_BATCH_SIZE_MB (110MB) each,
        then processes each batch as a single API call.

        Args:
            files: List of file paths to process
            max_concurrent: Maximum concurrent batch uploads

        Returns:
            Dictionary with processing results
        """
        # Create batches of files (max 110MB per batch)
        batches = self._create_batches(files=files)

        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = [
            self._ingest_batch(batch=batch, semaphore=semaphore) for batch in batches
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = []
        failed = []

        # Flatten results from all batches
        for batch, result in zip(batches, results):
            if isinstance(result, Exception):
                # All files in the batch failed
                for file_path in batch:
                    failed.append(
                        {
                            "file_path": str(file_path),
                            "filename": file_path.name,
                            "error": str(result),
                        }
                    )
            elif isinstance(result, dict):
                # Extract successful and failed files from batch result
                successful.extend(result.get("successful", []))
                failed.extend(result.get("failed", []))

        return {
            "successful": successful,
            "failed": failed,
            "total_files": len(files),
            "successful_count": len(successful),
            "failed_count": len(failed),
        }

    async def _ingest_batch(
        self, batch: List[Path], semaphore: asyncio.Semaphore
    ) -> Dict[str, Any]:
        """
        Ingest a batch of files: read, encode, and upload as a single API call.

        Args:
            batch: List of file paths to process in this batch
            semaphore: Semaphore for concurrency control

        Returns:
            Dictionary with upload results including successful and failed files

        Raises:
            Exception: If batch processing fails
        """
        async with semaphore:
            try:
                # Prepare all files in the batch
                files_data = []
                for file_path in batch:
                    try:
                        file_data = file_path.read_bytes()
                        file_base64 = base64.b64encode(file_data).decode("utf-8")
                        files_data.append(
                            {
                                "file_base64": file_base64,
                                "filename": file_path.name,
                                "file_path": str(file_path),
                            }
                        )
                    except Exception as e:
                        # If a file fails to read, add it to failed list but continue with others
                        files_data.append(
                            {
                                "file_path": str(file_path),
                                "filename": file_path.name,
                                "error": f"Failed to read file: {str(e)}",
                            }
                        )

                # Call the batch ingest tool
                result = await self.client.call_tool(
                    tool_name="ingest_files_batch",
                    arguments={
                        "session_uuid": self.session_uuid,
                        "files": files_data,
                    },
                )
                return json.loads(result)

            except Exception as e:
                raise Exception(
                    f"Failed to process batch of {len(batch)} files: {str(e)}"
                ) from e


class _AgentOrchestrator:
    """
    Internal orchestrator for Shadai Agent workflow.

    The agent automatically:
    1. Plans which tools to use (via planner)
    2. Executes the selected tools with provided arguments
    3. Synthesizes all outputs into a unified answer (via synthesizer)

    This provides a complete agentic workflow where you provide tools with their
    implementations and arguments, and the agent handles the orchestration.
    """

    def __init__(self, client: ShadaiClient) -> None:
        """
        Initialize Agent orchestrator.

        Args:
            client: Shadai client instance
        """
        self.client = client

    async def __call__(
        self,
        prompt: str,
        tools: List[AgentTool],
        session_uuid: str,
    ) -> AsyncIterator[str]:
        """
        Execute agentic workflow: plan → execute → synthesize.

        Args:
            prompt: User's question or task
            tools: List of AgentTool objects with name, description, implementation, and arguments
            session_uuid: Session UUID for context and memory

        Yields:
            Text chunks from the synthesized final answer
        """
        import inspect
        import json

        # Convert list to dictionary for lookup
        tools_dict: Dict[str, AgentTool] = {tool.name: tool for tool in tools}

        # Step 1: Plan - Get tool selection from server
        tool_definitions = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in tools_dict.values()
        ]

        plan_result = await self.client.call_tool(
            tool_name="shadai_planner",
            arguments={
                "prompt": prompt,
                "available_tools": tool_definitions,
                "session_uuid": session_uuid,
            },
        )
        plan = json.loads(plan_result)

        # Step 2: Execute - Run selected tools locally with inferred arguments
        tool_executions = []

        for tool_item in plan["tool_plan"]:
            tool_name = tool_item["name"]
            # Use inferred arguments from planner
            inferred_args = tool_item.get("arguments", {})

            if tool_name not in tools_dict:
                # Tool not available, record error
                tool_executions.append(
                    {
                        "tool_name": tool_name,
                        "arguments": inferred_args,
                        "output": f"Error: Tool '{tool_name}' not found in provided tools",
                    }
                )
                continue

            tool = tools_dict[tool_name]
            tool_impl = tool.implementation

            # Merge user-provided arguments with inferred arguments (inferred takes precedence)
            final_args = {**tool.arguments, **inferred_args}

            # Execute the tool implementation with final arguments
            try:
                if inspect.iscoroutinefunction(tool_impl):
                    result = await tool_impl(**final_args)
                else:
                    result = tool_impl(**final_args)

                tool_executions.append(
                    {
                        "tool_name": tool_name,
                        "arguments": final_args,
                        "output": str(result),
                    }
                )
            except Exception as e:
                tool_executions.append(
                    {
                        "tool_name": tool_name,
                        "arguments": final_args,
                        "output": f"Error executing tool: {str(e)}",
                    }
                )

        # Step 3: Synthesize - Combine outputs via server
        async for chunk in self.client.stream_tool(
            tool_name="shadai_synthesizer",
            arguments={
                "prompt": prompt,
                "tool_definitions": tool_definitions,
                "tool_executions": tool_executions,
                "session_uuid": session_uuid,
            },
        ):
            yield chunk


class Shadai:
    """
    Main entry point for Shadai AI client.

    Provides convenient access to all Shadai tools with a clean, intuitive API.

    Examples:
        >>> from client.shadai import Shadai, AgentTool
        >>>
        >>> shadai = Shadai(api_key="your-api-key")
        >>>
        >>> # Check server health
        >>> health = await shadai.health()
        >>> print(health)
        >>>
        >>> # Query knowledge base (one-step)
        >>> async for chunk in shadai.query(
        ...     query="What is AI?",
        ...     session_uuid="..."
        ... ):
        ...     print(chunk, end="")
        >>>
        >>> # Use intelligent agent (orchestrates plan → execute → synthesize)
        >>> tools = [
        ...     AgentTool(
        ...         name="my_tool",
        ...         description="Does something",
        ...         implementation=my_function,
        ...         arguments={"param": "value"}
        ...     )
        ... ]
        >>> async for chunk in shadai.agent(
        ...     prompt="Do task",
        ...     tools=tools
        ... ):
        ...     print(chunk, end="")
    """

    def __init__(
        self,
        name: Optional[str] = None,
        temporal: bool = False,
        api_key: Optional[str] = None,
        base_url: str = "http://localhost",
        timeout: int = 30,
    ) -> None:
        """
        Initialize Shadai client with session management.

        Args:
            name: Optional session name to retrieve existing session
            temporal: If True, delete session on context exit (default: False)
            api_key: Your Shadai API key (defaults to SHADAI_API_KEY env var)
            base_url: Base URL of Shadai server
            timeout: Request timeout in seconds

        Examples:
            >>> # Use existing session
            >>> async with Shadai(name="my-session") as shadai:
            ...     async for chunk in shadai.query(query="What is AI?"):
            ...         print(chunk, end="")
            >>>
            >>> # Create temporal session (auto-deleted)
            >>> async with Shadai(temporal=True) as shadai:
            ...     async for chunk in shadai.query(query="What is AI?"):
            ...         print(chunk, end="")
        """
        if not api_key:
            api_key = os.getenv("SHADAI_API_KEY")
            if not api_key:
                raise ValueError("API key not provided")

        self.client = ShadaiClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )
        self._session_name = name
        self._temporal = temporal
        self._session: Optional["Session"] = None

    async def __aenter__(self) -> "Shadai":
        """Enter context: initialize session.

        Returns:
            Shadai instance with active session
        """
        from .session import Session

        self._session = Session(
            name=self._session_name,
            temporal=self._temporal,
            client=self.client,
        )
        await self._session.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context: cleanup session.

        Args:
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised
        """
        if self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)

    async def health(self) -> Dict[str, Any]:
        """
        Check server health.

        Returns:
            Server health information

        Examples:
            >>> health = await shadai.health()
            >>> print(f"Status: {health['status']}")
        """
        return await self.client.health_check()

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools.

        Returns:
            List of tool definitions

        Examples:
            >>> tools = await shadai.list_tools()
            >>> for tool in tools:
            ...     print(tool["name"])
        """
        return await self.client.list_tools()

    async def query(
        self,
        query: str,
        use_memory: bool = True,
    ) -> AsyncIterator[str]:
        """
        Query the knowledge base with streaming response.

        Args:
            query: Your question or search query
            use_memory: Enable conversation memory

        Yields:
            Text chunks from the knowledge base

        Examples:
            >>> async with Shadai(name="my-session") as shadai:
            ...     async for chunk in shadai.query(query="What is ML?"):
            ...         print(chunk, end="")
        """
        if not self._session:
            raise ValueError("Shadai must be used as a context manager")

        query_tool = QueryTool(client=self.client, session_uuid=self._session.uuid)
        async for chunk in query_tool(query=query, use_memory=use_memory):
            yield chunk

    async def summarize(
        self,
        use_memory: bool = True,
    ) -> AsyncIterator[str]:
        """
        Generate summary of all session documents.

        Args:
            use_memory: Enable conversation memory

        Yields:
            Text chunks from the summary

        Examples:
            >>> async with Shadai(name="my-session") as shadai:
            ...     async for chunk in shadai.summarize():
            ...         print(chunk, end="")
        """
        if not self._session:
            raise ValueError("Shadai must be used as a context manager")

        summarize_tool = SummarizeTool(
            client=self.client, session_uuid=self._session.uuid
        )
        async for chunk in summarize_tool(use_memory=use_memory):
            yield chunk

    async def web_search(
        self,
        prompt: str,
        use_web_search: bool = True,
        use_memory: bool = True,
    ) -> AsyncIterator[str]:
        """
        Search the web and get an answer.

        Args:
            prompt: Your question or search query
            use_web_search: Enable web search (default: True)
            use_memory: Enable conversation memory

        Yields:
            Text chunks from the search results

        Examples:
            >>> async with Shadai(name="my-session") as shadai:
            ...     async for chunk in shadai.web_search(prompt="Latest AI news"):
            ...         print(chunk, end="")
        """
        if not self._session:
            raise ValueError("Shadai must be used as a context manager")

        search_tool = WebSearchTool(client=self.client, session_uuid=self._session.uuid)
        async for chunk in search_tool(
            prompt=prompt,
            use_web_search=use_web_search,
            use_memory=use_memory,
        ):
            yield chunk

    async def engine(
        self,
        prompt: str,
        use_knowledge_base: bool = False,
        use_summary: bool = False,
        use_web_search: bool = False,
        use_memory: bool = True,
    ) -> AsyncIterator[str]:
        """
        Execute unified engine with multiple tool capabilities.

        Args:
            prompt: Your question or prompt
            use_knowledge_base: Enable knowledge base retrieval
            use_summary: Enable document summarization
            use_web_search: Enable web search
            use_memory: Enable conversation memory

        Yields:
            Text chunks from the engine

        Examples:
            >>> async with Shadai(name="my-session") as shadai:
            ...     async for chunk in shadai.engine(
            ...         prompt="Analyze my docs",
            ...         use_knowledge_base=True
            ...     ):
            ...         print(chunk, end="")
        """
        if not self._session:
            raise ValueError("Shadai must be used as a context manager")

        engine_tool = EngineTool(client=self.client, session_uuid=self._session.uuid)
        async for chunk in engine_tool(
            prompt=prompt,
            use_knowledge_base=use_knowledge_base,
            use_summary=use_summary,
            use_web_search=use_web_search,
            use_memory=use_memory,
        ):
            yield chunk

    async def agent(
        self,
        prompt: str,
        tools: List[AgentTool],
    ) -> AsyncIterator[str]:
        """
        Execute intelligent agent workflow: plan → execute → synthesize.

        The agent orchestrates a complete workflow:
        1. Plans which tools to use (via planner API)
        2. Executes tools locally with provided arguments
        3. Synthesizes outputs (via synthesizer API)

        Args:
            prompt: User's question or task
            tools: List of AgentTool objects

        Yields:
            Text chunks from the synthesized response

        Examples:
            >>> from shadai import AgentTool
            >>>
            >>> # Define tools
            >>> tools = [
            ...     AgentTool(
            ...         name="search_database",
            ...         description="Search database",
            ...         implementation=search_func,
            ...         arguments={"query": "users", "limit": 10}
            ...     ),
            ...     AgentTool(
            ...         name="generate_report",
            ...         description="Generate report",
            ...         implementation=report_func,
            ...         arguments={"format": "markdown"}
            ...     )
            ... ]
            >>>
            >>> # Agent handles plan → execute → synthesize
            >>> async with Shadai(name="my-session") as shadai:
            ...     async for chunk in shadai.agent(
            ...         prompt="Find and analyze data",
            ...         tools=tools
            ...     ):
            ...         print(chunk, end="")
        """
        if not self._session:
            raise ValueError("Shadai must be used as a context manager")

        orchestrator = _AgentOrchestrator(client=self.client)
        async for chunk in orchestrator(
            prompt=prompt, tools=tools, session_uuid=self._session.uuid
        ):
            yield chunk

    async def ingest(self, folder_path: str) -> Dict[str, Any]:
        """
        Ingest all PDF and image files in a folder (including nested folders).

        Recursively finds all supported files and uploads them to the session
        for RAG knowledge base ingestion. Supports concurrent uploads.

        Args:
            folder_path: Path to the folder containing files to process

        Returns:
            Dictionary with processing results:
            - successful: List of successfully uploaded files
            - failed: List of files that failed to upload
            - total_files: Total number of files processed
            - successful_count: Count of successful uploads
            - failed_count: Count of failed uploads

        Examples:
            >>> async with Shadai(name="my-session") as shadai:
            ...     results = await shadai.ingest(
            ...         folder_path="/path/to/documents"
            ...     )
            ...     print(f"Uploaded {results['successful_count']} files")
            ...     print(f"Failed {results['failed_count']} files")
            ...
            ...     # Show failed files
            ...     for failed in results['failed']:
            ...         print(f"Failed: {failed['filename']} - {failed['error']}")
        """
        if not self._session:
            raise ValueError("Shadai must be used as a context manager")

        ingest_tool = IngestTool(client=self.client, session_uuid=self._session.uuid)
        return await ingest_tool(folder_path=folder_path)
