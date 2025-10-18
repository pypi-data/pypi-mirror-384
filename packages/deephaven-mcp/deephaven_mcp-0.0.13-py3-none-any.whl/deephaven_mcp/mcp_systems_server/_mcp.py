"""
Deephaven MCP Systems Tools Module.

This module defines the set of MCP (Multi-Cluster Platform) tool functions for managing and interacting with Deephaven sessions in a multi-server environment. All functions are designed for use as MCP tools and are decorated with @mcp_server.tool().

Key Features:
    - Structured, protocol-compliant error handling: all tools return consistent dict structures with 'success' and 'error' keys as appropriate.
    - Async, coroutine-safe operations for configuration and session management.
    - Detailed logging for all tool invocations, results, and errors.
    - All docstrings are optimized for agentic and programmatic consumption and describe both user-facing and technical details.

Tools Provided:
    - mcp_reload: Reload configuration and clear all sessions atomically.
    - enterprise_systems_status: List all enterprise (Core+) systems with their status and configuration details.
    - sessions_list: List all sessions (community and enterprise) with basic metadata.
    - session_details: Get detailed information about a specific session.
    - session_tables_schema: Retrieve full metadata schemas for one or more tables from a session (requires session_id).
    - session_tables_list: Retrieve names of all tables in a session (lightweight alternative to session_tables_schema).
    - session_script_run: Execute a script on a specified Deephaven session (requires session_id).
    - session_pip_list: Retrieve all installed pip packages (name and version) from a specified Deephaven session using importlib.metadata, returned as a list of dicts.
    - session_table_data: Retrieve table data with flexible formatting (json-row, json-column, csv) and optional row limiting for safe access to large tables.
    - catalog_tables_list: Retrieve catalog table entries from enterprise (Core+) sessions with optional filtering by namespace or table name patterns.
    - catalog_namespaces_list: Retrieve distinct namespaces from enterprise (Core+) catalog for efficient discovery of data domains.
    - catalog_tables_schema: Retrieve full schemas for catalog tables in enterprise (Core+) sessions with flexible filtering by namespace, table names, or custom filters.
    - catalog_table_sample: Retrieve sample data from a catalog table in enterprise (Core+) sessions with flexible formatting and row limiting for safe previewing.
    - session_enterprise_create: Create a new enterprise session with configurable parameters and resource limits.
    - session_enterprise_delete: Delete an existing enterprise session and clean up resources.

Return Types:
    - All tools return structured dict objects, never raise exceptions to the MCP layer.
    - On success, 'success': True. On error, 'success': False and 'error': str.
    - Tools that return multiple items use nested structures (e.g., 'systems', 'sessions', 'schemas' arrays within the main dict).

See individual tool docstrings for full argument, return, and error details.
"""

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, TypeVar, cast

import aiofiles
import pyarrow
from mcp.server.fastmcp import Context, FastMCP

from deephaven_mcp import queries
from deephaven_mcp._exceptions import UnsupportedOperationError
from deephaven_mcp.client import BaseSession, CorePlusSession
from deephaven_mcp.config import (
    ConfigManager,
    get_config_section,
    redact_enterprise_system_config,
)
from deephaven_mcp.formatters import format_table_data
from deephaven_mcp.resource_manager import (
    BaseItemManager,
    CombinedSessionRegistry,
    EnterpriseSessionManager,
    SystemType,
)

T = TypeVar("T")

# Enterprise session management constants
DEFAULT_MAX_CONCURRENT_SESSIONS = 5
"""
Default maximum number of concurrent sessions per enterprise system.

This default is used when session_creation.max_concurrent_sessions is not specified
in the enterprise system configuration. Can be overridden per system in the config.
"""

# Response size estimation constants
# Conservative estimate: ~20 chars + 8 bytes numeric + JSON overhead + safety margin
ESTIMATED_BYTES_PER_CELL = 50
"""
Estimated bytes per table cell for response size calculation.

This rough estimate is used to prevent memory issues when retrieving large tables.
The estimation assumes:
- Average string length: ~20 characters (20 bytes)
- Numeric values: ~8 bytes (int64/double)
- Null values and metadata: ~5 bytes overhead
- JSON formatting overhead: ~15-20 bytes per cell
- Safety margin: 50 bytes total per cell

This conservative estimate helps catch potentially problematic responses before
expensive formatting operations. Can be tuned based on actual data patterns.
"""

_LOGGER = logging.getLogger(__name__)


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict[str, object]]:
    """
    Async context manager for the FastMCP server application lifespan.

    This function manages the startup and shutdown lifecycle of the MCP server. It is responsible for:
      - Instantiating a ConfigManager and CombinedSessionRegistry for Deephaven session configuration and session management.
      - Creating a coroutine-safe asyncio.Lock (refresh_lock) for atomic configuration/session refreshes.
      - Loading and validating the Deephaven session configuration before the server accepts requests.
      - Yielding a context dictionary containing config_manager, session_registry, and refresh_lock for use by all tool functions via dependency injection.
      - Ensuring all session resources are properly cleaned up on shutdown.

    Startup Process:
      - Logs server startup initiation.
      - Creates and initializes a ConfigManager instance.
      - Loads and validates the Deephaven session configuration.
      - Creates a CombinedSessionRegistry for managing both community and enterprise sessions.
      - Creates an asyncio.Lock for coordinating refresh operations.
      - Yields the context dictionary for use by MCP tools.

    Shutdown Process:
      - Logs server shutdown initiation.
      - Closes all active Deephaven sessions via the session registry.
      - Logs completion of server shutdown.

    Args:
        server (FastMCP): The FastMCP server instance (required by the FastMCP lifespan API).

    Yields:
        dict[str, object]: A context dictionary with the following keys for dependency injection into MCP tool requests:
            - 'config_manager' (ConfigManager): Instance for accessing session configuration.
            - 'session_registry' (CombinedSessionRegistry): Instance for managing all session types.
            - 'refresh_lock' (asyncio.Lock): Lock for atomic refresh operations across tools.
    """
    _LOGGER.info(
        "[mcp_systems_server:app_lifespan] Starting MCP server '%s'", server.name
    )
    session_registry = None

    try:
        config_manager = ConfigManager()

        # Make sure config can be loaded before starting
        _LOGGER.info("[mcp_systems_server:app_lifespan] Loading configuration...")
        await config_manager.get_config()
        _LOGGER.info("[mcp_systems_server:app_lifespan] Configuration loaded.")

        session_registry = CombinedSessionRegistry()
        await session_registry.initialize(config_manager)

        # lock for refresh to prevent concurrent refresh operations.
        refresh_lock = asyncio.Lock()

        yield {
            "config_manager": config_manager,
            "session_registry": session_registry,
            "refresh_lock": refresh_lock,
        }
    finally:
        _LOGGER.info(
            "[mcp_systems_server:app_lifespan] Shutting down MCP server '%s'",
            server.name,
        )
        if session_registry is not None:
            await session_registry.close()
        _LOGGER.info(
            "[mcp_systems_server:app_lifespan] MCP server '%s' shut down.", server.name
        )


mcp_server = FastMCP("deephaven-mcp-systems", lifespan=app_lifespan)
"""
FastMCP Server Instance for Deephaven MCP Systems Tools

This object is the singleton FastMCP server for the Deephaven MCP systems toolset. It is responsible for registering and exposing all MCP tool functions defined in this module (such as refresh, enterprise_systems_status, list_sessions, get_session_details, table_schemas, run_script, and pip_packages) to the MCP runtime environment.

Key Details:
    - The server is instantiated with the name 'deephaven-mcp-systems', which uniquely identifies this toolset in the MCP ecosystem.
    - All functions decorated with @mcp_server.tool() are automatically registered as MCP tools and made available for remote invocation.
    - The server manages protocol compliance, tool metadata, and integration with the broader MCP infrastructure.
    - This object should not be instantiated more than once per process/module.

Usage:
    - Do not call methods on mcp_server directly; instead, use the @mcp_server.tool() decorator to register new tools.
    - The MCP runtime will discover and invoke registered tools as needed.

See the module-level docstring for an overview of the available tools and error handling conventions.
"""


# TODO: remove mcp_reload?
@mcp_server.tool()
async def mcp_reload(context: Context) -> dict:
    """
    MCP Tool: Reload configuration and clear all active sessions.

    Reloads the Deephaven session configuration from disk and clears all active session objects.
    Configuration changes (adding, removing, or updating systems) are applied immediately.
    All sessions will be reopened with the new configuration on next access.

    Terminology Note:
    - 'Session' and 'worker' are interchangeable terms - both refer to a running Deephaven instance
    - 'Deephaven Community' and 'Deephaven Core' are interchangeable names for the same product
    - 'Deephaven Enterprise', 'Deephaven Core+', and 'Deephaven CorePlus' are interchangeable names for the same product

    AI Agent Usage:
    - Use this tool after making configuration file changes
    - Check 'success' field to verify reload completed
    - Sessions will be automatically recreated with new configuration on next use
    - Operation is atomic and thread-safe
    - WARNING: All active sessions will be cleared, including those created with create_enterprise_session
    - Use carefully - any work in active sessions will be lost

    Args:
        context (Context): The MCP context object.

    Returns:
        dict: Structured result object with the following keys:
            - 'success' (bool): True if the refresh completed successfully, False otherwise.
            - 'error' (str, optional): Error message if the refresh failed. Omitted on success.
            - 'isError' (bool, optional): Present and True if this is an error response (i.e., success is False).

    Example Successful Response:
        {'success': True}

    Example Error Response:
        {'success': False, 'error': 'Failed to reload configuration: ...', 'isError': True}

    Error Scenarios:
        - Context access errors: Returns error if required context objects (refresh_lock, config_manager, session_registry) are not available
        - Configuration reload errors: Returns error if config_manager.clear_config_cache() fails
        - Session registry errors: Returns error if session_registry operations (close, initialize) fail
    """
    _LOGGER.info(
        "[mcp_systems_server:mcp_reload] Invoked: refreshing session configuration and session cache."
    )
    # Acquire the refresh lock to prevent concurrent refreshes. This does not
    # guarantee atomicity with respect to other config/session operations, but
    # it does ensure that only one refresh runs at a time and reduces race risk.
    try:
        refresh_lock: asyncio.Lock = context.request_context.lifespan_context[
            "refresh_lock"
        ]
        config_manager: ConfigManager = context.request_context.lifespan_context[
            "config_manager"
        ]
        session_registry: CombinedSessionRegistry = (
            context.request_context.lifespan_context["session_registry"]
        )

        async with refresh_lock:
            await config_manager.clear_config_cache()
            await session_registry.close()
            await session_registry.initialize(config_manager)
        _LOGGER.info(
            "[mcp_systems_server:mcp_reload] Success: Session configuration and session cache have been reloaded."
        )
        return {"success": True}
    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:mcp_reload] Failed to refresh session configuration/session cache: {e!r}",
            exc_info=True,
        )
        return {"success": False, "error": str(e), "isError": True}


@mcp_server.tool()
async def enterprise_systems_status(
    context: Context, attempt_to_connect: bool = False
) -> dict:
    """
    MCP Tool: List all enterprise systems with their status and configuration details.

    This tool provides comprehensive status information about all configured enterprise systems in the MCP
    environment. It returns detailed health status using the ResourceLivenessStatus classification system,
    along with explanatory details and configuration information (with sensitive fields redacted for security).

    Terminology Note:
    - 'Session' and 'worker' are interchangeable terms - both refer to a running Deephaven instance
    - 'Deephaven Community' and 'Deephaven Core' are interchangeable names for the same product
    - 'Deephaven Enterprise', 'Deephaven Core+', and 'Deephaven CorePlus' are interchangeable names for the same product

    The tool supports two operational modes:
    1. Default mode (attempt_to_connect=False): Quick status check of existing connections
       - Fast response time, minimal resource usage
       - Suitable for dashboards, monitoring, and non-critical status checks
       - Will report systems as OFFLINE if no connection exists

    2. Connection verification mode (attempt_to_connect=True): Active connection attempt
       - Attempts to establish connections to verify actual availability
       - Higher latency but more accurate status reporting
       - Suitable for troubleshooting and pre-flight checks before critical operations
       - May create new connections if none exist

    Status Classification:
      - "ONLINE": System is healthy and ready for operational use
      - "OFFLINE": System is unresponsive, failed health checks, or not connected
      - "UNAUTHORIZED": Authentication or authorization failures prevent access
      - "MISCONFIGURED": Configuration errors prevent proper system operation
      - "UNKNOWN": Unexpected errors occurred during status determination

    AI Agent Usage:
    - Use attempt_to_connect=False (default) for quick status checks
    - Use attempt_to_connect=True to actively verify system connectivity
    - Check 'systems' array in response for individual system status
    - Use 'detail' field for troubleshooting connection issues
    - Configuration details are included but sensitive fields are redacted

    Args:
        context (Context): The MCP context object.
        attempt_to_connect (bool, optional): If True, actively attempts to connect to each system
            to verify its status. This provides more accurate results but increases latency.
            Default is False (only checks existing connections for faster response).

    Returns:
        dict: Structured result object with keys:
            - 'success' (bool): True if retrieval succeeded, False otherwise.
            - 'systems' (list[dict]): List of system info dicts. Each contains:
                - 'name' (str): System name identifier
                - 'liveness_status' (str): ResourceLivenessStatus ("ONLINE", "OFFLINE", "UNAUTHORIZED", "MISCONFIGURED", "UNKNOWN")
                - 'liveness_detail' (str, optional): Explanation message for the status, useful for troubleshooting
                - 'is_alive' (bool): Simple boolean indicating if the system is responsive
                - 'config' (dict): System configuration with sensitive fields redacted
            - 'error' (str, optional): Error message if retrieval failed.
            - 'isError' (bool, optional): Present and True if this is an error response.

    Example Successful Response:
        {
            'success': True,
            'systems': [
                {
                    'name': 'prod-system',
                    'liveness_status': 'ONLINE',
                    'liveness_detail': 'Connection established successfully',
                    'is_alive': True,
                    'config': {'host': 'prod.example.com', 'port': 10000, 'auth_type': 'anonymous'}
                }
            ]
        }

    Example Error Response:
        {'success': False, 'error': 'Failed to retrieve systems status', 'isError': True}

    Performance Considerations:
        - With attempt_to_connect=False: Typically completes in milliseconds
        - With attempt_to_connect=True: May take seconds due to connection operations
    """
    _LOGGER.info("[mcp_systems_server:enterprise_systems_status] Invoked.")
    try:
        session_registry: CombinedSessionRegistry = (
            context.request_context.lifespan_context["session_registry"]
        )
        config_manager: ConfigManager = context.request_context.lifespan_context[
            "config_manager"
        ]
        # Get all factories (enterprise systems)
        enterprise_registry = await session_registry.enterprise_registry()
        factories = await enterprise_registry.get_all()
        config = await config_manager.get_config()

        try:
            systems_config = get_config_section(config, ["enterprise", "systems"])
        except KeyError:
            systems_config = {}

        systems = []
        for name, factory in factories.items():
            # Use liveness_status() for detailed health information
            status_enum, liveness_detail = await factory.liveness_status(
                ensure_item=attempt_to_connect
            )
            liveness_status = status_enum.name

            # Also get simple is_alive boolean
            is_alive = await factory.is_alive()

            # Redact config for output
            raw_config = systems_config.get(name, {})
            redacted_config = redact_enterprise_system_config(raw_config)

            system_info = {
                "name": name,
                "liveness_status": liveness_status,
                "is_alive": is_alive,
                "config": redacted_config,
            }

            # Include detail if available
            if liveness_detail is not None:
                system_info["liveness_detail"] = liveness_detail

            systems.append(system_info)
        return {"success": True, "systems": systems}
    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:enterprise_systems_status] Failed: {e!r}",
            exc_info=True,
        )
        return {"success": False, "error": str(e), "isError": True}


@mcp_server.tool()
async def sessions_list(context: Context) -> dict:
    """
    MCP Tool: List all sessions with basic metadata.

    Returns basic information about all available sessions (community and enterprise).
    This is a lightweight operation that doesn't connect to sessions or check their status.

    Terminology Note:
    - 'Session' and 'worker' are interchangeable terms - both refer to a running Deephaven instance
    - 'Deephaven Community' and 'Deephaven Core' are interchangeable names for the same product
    - 'Deephaven Enterprise', 'Deephaven Core+', and 'Deephaven CorePlus' are interchangeable names for the same product

    AI Agent Usage:
    - Use this to discover available sessions before calling other session-based tools
    - Use returned 'session_id' values with other tools like run_script, get_table_data
    - Check 'type' field to understand session capabilities (community vs enterprise)
    - For detailed session information, use get_session_details with a specific session_id

    Args:
        context (Context): The MCP context object.

    Returns:
        dict: Structured result object with keys:
            - 'success' (bool): True if retrieval succeeded, False otherwise.
            - 'sessions' (list[dict]): List of session info dicts. Each contains:
                - 'session_id' (str): Fully qualified session identifier for use with other tools
                - 'type' (str): Session type ("COMMUNITY" or "ENTERPRISE")
                - 'source' (str): Source system name
                - 'session_name' (str): Session name within the source
            - 'error' (str, optional): Error message if retrieval failed.
            - 'isError' (bool, optional): Present and True if this is an error response.

    Example Successful Response:
        {
            'success': True,
            'sessions': [
                {
                    'session_id': 'enterprise:prod-system:my-session',
                    'type': 'ENTERPRISE',
                    'source': 'prod-system',
                    'session_name': 'my-session'
                },
                {
                    'session_id': 'community:local-community:default',
                    'type': 'COMMUNITY',
                    'source': 'local-community',
                    'session_name': 'default'
                }
            ]
        }

    Example Error Response:
        {'success': False, 'error': 'Failed to retrieve sessions', 'isError': True}

    Error Scenarios:
        - Context access errors: Returns error if session_registry cannot be accessed from context
        - Registry operation errors: Returns error if session_registry.get_all() fails
        - Session processing errors: Returns error if individual session metadata cannot be extracted
    """
    _LOGGER.info("[mcp_systems_server:sessions_list] Invoked")
    try:
        _LOGGER.debug(
            "[mcp_systems_server:sessions_list] Accessing session registry from context"
        )
        session_registry: CombinedSessionRegistry = (
            context.request_context.lifespan_context["session_registry"]
        )
        _LOGGER.debug(
            "[mcp_systems_server:sessions_list] Retrieving all sessions from registry"
        )
        sessions = await session_registry.get_all()

        _LOGGER.info(
            "[mcp_systems_server:sessions_list] Found %d sessions.", len(sessions)
        )

        results = []
        for fq_name, mgr in sessions.items():
            _LOGGER.debug(
                "[mcp_systems_server:sessions_list] Processing session '%s'", fq_name
            )

            try:
                system_type = mgr.system_type
                system_type_str = system_type.name
                source = mgr.source
                session_name = mgr.name

                results.append(
                    {
                        "session_id": fq_name,
                        "type": system_type_str,
                        "source": source,
                        "session_name": session_name,
                    }
                )
            except Exception as e:
                _LOGGER.warning(
                    f"[mcp_systems_server:sessions_list] Could not process session '{fq_name}': {e!r}"
                )
                results.append({"session_id": fq_name, "error": str(e)})
        return {"success": True, "sessions": results}
    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:sessions_list] Failed: {e!r}", exc_info=True
        )
        return {"success": False, "error": str(e), "isError": True}


async def _get_session_from_context(
    function_name: str, context: Context, session_id: str
) -> BaseSession:
    """
    Get an active session from the MCP context.

    This helper eliminates duplication of the common pattern for accessing
    sessions from the MCP context. It handles the standard flow of:
    1. Extracting session_registry from context
    2. Getting the session_manager for the session_id
    3. Establishing the session connection

    Args:
        function_name (str): Name of calling function for logging purposes
        context (Context): The MCP context object containing lifespan context
        session_id (str): ID of the session to retrieve

    Returns:
        BaseSession: The active session connection

    Raises:
        KeyError: If session_id not found in registry
        Exception: If session cannot be established or context is invalid
    """
    _LOGGER.debug(
        f"[mcp_systems_server:{function_name}] Accessing session registry from context"
    )
    session_registry: CombinedSessionRegistry = (
        context.request_context.lifespan_context["session_registry"]
    )

    _LOGGER.debug(
        f"[mcp_systems_server:{function_name}] Retrieving session manager for '{session_id}'"
    )
    session_manager = await session_registry.get(session_id)

    _LOGGER.debug(
        f"[mcp_systems_server:{function_name}] Establishing session connection for '{session_id}'"
    )
    session: BaseSession = await session_manager.get()

    _LOGGER.info(
        f"[mcp_systems_server:{function_name}] Session established for '{session_id}'"
    )

    return session


async def _get_enterprise_session(
    function_name: str, context: Context, session_id: str
) -> tuple[CorePlusSession | None, dict[str, object] | None]:
    """
    Get and validate an enterprise (Core+) session from context.

    This helper combines session retrieval and validation into a single clean operation,
    consolidating the common pattern of getting a session and verifying it's an enterprise
    (Core+) session. This eliminates code duplication across catalog-related tools.

    Args:
        function_name (str): Name of calling function for logging and error messages.
        context (Context): The MCP context object containing lifespan context with session_registry.
        session_id (str): ID of the session to retrieve (e.g., "enterprise:prod:analytics").

    Returns:
        tuple: A 2-tuple (session, error) where:
            - session (CorePlusSession | None): The validated enterprise session on success, None on failure.
            - error (dict | None): None on success, structured error dict on failure with keys:
                - 'success': False
                - 'error': str (human-readable error message)
                - 'isError': True

    Error Conditions:
        - Session not found in registry
        - Session is not a CorePlusSession (community session provided)
        - Any exception during session retrieval

    Example:
        >>> session, error = await _get_enterprise_session("catalog_tables_schema", context, "enterprise:prod:analytics")
        >>> if error:
        >>>     return error
        >>> session = cast(CorePlusSession, session)  # Type narrowing for mypy
    """
    try:
        # Get session from context
        session = await _get_session_from_context(function_name, context, session_id)

        # Validate it's an enterprise session
        if not isinstance(session, CorePlusSession):
            error_msg = (
                f"{function_name} only works with enterprise (Core+) sessions, "
                f"but session '{session_id}' is {type(session).__name__}"
            )
            _LOGGER.error(f"[mcp_systems_server:{function_name}] {error_msg}")
            return None, {"success": False, "error": error_msg, "isError": True}

        return session, None
    except Exception as e:
        error_msg = f"Failed to get session '{session_id}': {e}"
        _LOGGER.error(f"[mcp_systems_server:{function_name}] {error_msg}")
        return None, {"success": False, "error": error_msg, "isError": True}


async def _get_session_liveness_info(
    mgr: BaseItemManager, session_id: str, attempt_to_connect: bool
) -> tuple[bool, str, str | None]:
    """
    Get session liveness status and availability.

    This function checks the liveness status of a session using the provided manager.
    It can optionally attempt to connect to the session to verify its actual status.

    Args:
        mgr: Session manager for the target session
        session_id: Session identifier for logging purposes
        attempt_to_connect: Whether to attempt connecting to verify status

    Returns:
        tuple: A 3-tuple containing:
            - available (bool): Whether the session is available and responsive
            - liveness_status (str): Status classification ("ONLINE", "OFFLINE", etc.)
            - liveness_detail (str): Detailed explanation of the status
    """
    try:
        status, detail = await mgr.liveness_status(ensure_item=attempt_to_connect)
        liveness_status = status.name
        liveness_detail = detail
        available = await mgr.is_alive()
        _LOGGER.debug(
            f"[mcp_systems_server:session_details] Session '{session_id}' liveness: {liveness_status}, detail: {liveness_detail}"
        )
        return available, liveness_status, liveness_detail
    except Exception as e:
        _LOGGER.warning(
            f"[mcp_systems_server:session_details] Could not check liveness for '{session_id}': {e!r}"
        )
        return False, "OFFLINE", str(e)


async def _get_session_property(
    mgr: BaseItemManager,
    session_id: str,
    available: bool,
    property_name: str,
    getter_func: Callable[[BaseSession], Awaitable[T]],
) -> T | None:
    """
    Safely get a session property.

    Args:
        mgr (BaseItemManager): Session manager
        session_id (str): Session identifier
        available (bool): Whether the session is available
        property_name (str): Name of the property for logging
        getter_func (Callable[[BaseSession], Awaitable[T]]): Async function to get the property from the session

    Returns:
        T | None: The property value or None if unavailable/failed
    """
    if not available:
        return None

    try:
        session = await mgr.get()
        result = await getter_func(session)
        _LOGGER.debug(
            f"[mcp_systems_server:session_details] Session '{session_id}' {property_name}: {result}"
        )
        return result
    except Exception as e:
        _LOGGER.warning(
            f"[mcp_systems_server:session_details] Could not get {property_name} for '{session_id}': {e!r}"
        )
        return None


async def _get_session_programming_language(
    mgr: BaseItemManager, session_id: str, available: bool
) -> str | None:
    """
    Get the programming language of a session.

    This function retrieves the programming language (e.g., "python", "groovy")
    associated with the session. If the session is not available, it returns None
    immediately without attempting to connect.

    Args:
        mgr: Session manager for the target session
        session_id: Session identifier for logging purposes
        available: Whether the session is available (pre-checked)

    Returns:
        str | None: The programming language name (e.g., "python") or None if
                   unavailable/failed to retrieve
    """
    if not available:
        return None

    try:
        session: BaseSession = await mgr.get()
        programming_language = str(session.programming_language)
        _LOGGER.debug(
            f"[mcp_systems_server:session_details] Session '{session_id}' programming_language: {programming_language}"
        )
        return programming_language
    except Exception as e:
        _LOGGER.warning(
            f"[mcp_systems_server:session_details] Could not get programming_language for '{session_id}': {e!r}"
        )
        return None


async def _get_session_versions(
    mgr: BaseItemManager, session_id: str, available: bool
) -> tuple[str | None, str | None]:
    """
    Get Deephaven version information.

    This function retrieves both community (Core) and enterprise (Core+/CorePlus)
    version information from the session. If the session is not available, it returns
    (None, None) immediately without attempting to connect.

    Args:
        mgr: Session manager for the target session
        session_id: Session identifier for logging purposes
        available: Whether the session is available (pre-checked)

    Returns:
        tuple: A 2-tuple containing:
            - community_version (str | None): Deephaven Community/Core version (e.g., "0.24.0")
            - enterprise_version (str | None): Deephaven Enterprise/Core+/CorePlus version
                                              (e.g., "0.24.0") or None if not enterprise
    """
    if not available:
        return None, None

    try:
        session = await mgr.get()
        community_version, enterprise_version = await queries.get_dh_versions(session)
        _LOGGER.debug(
            f"[mcp_systems_server:session_details] Session '{session_id}' versions: community={community_version}, enterprise={enterprise_version}"
        )
        return community_version, enterprise_version
    except Exception as e:
        _LOGGER.warning(
            f"[mcp_systems_server:session_details] Could not get Deephaven versions for '{session_id}': {e!r}"
        )
        return None, None


def _build_table_data_response(
    arrow_table: pyarrow.Table,
    is_complete: bool,
    format: str,
    table_name: str | None = None,
    namespace: str | None = None,
) -> dict:
    """
    Build a standardized table data response with schema, formatting, and metadata.

    This helper consolidates the common pattern of:
    1. Extracting schema from Arrow table
    2. Formatting data with format_table_data
    3. Building response dict with standard fields

    Used by both session table tools and catalog table tools to ensure consistent
    response structure across all table data retrieval operations.

    Args:
        arrow_table (pyarrow.Table): The Arrow table containing the data.
        is_complete (bool): Whether the entire table was retrieved (False if truncated by max_rows).
        format (str): Desired output format (may be optimization strategy or specific format like "csv", "json-row", etc.).
        table_name (str | None): Optional table name to include in response. Recommended for clarity.
        namespace (str | None): Optional namespace to include in response. Use for catalog tables only.

    Returns:
        dict: Standardized response with success=True and fields:
            - success (bool): Always True for this helper (errors handled by callers).
            - format (str): Actual format used (resolved from optimization strategies to specific format).
            - schema (list[dict]): Column definitions with name and type.
            - row_count (int): Number of rows in the response.
            - is_complete (bool): Whether entire table was retrieved.
            - data (varies): Formatted table data (type depends on format).
            - table_name (str, optional): Included if table_name parameter provided.
            - namespace (str, optional): Included if namespace parameter provided (catalog tables).
    """
    # Extract schema
    schema = [
        {"name": field.name, "type": str(field.type)} for field in arrow_table.schema
    ]

    # Format data
    actual_format, formatted_data = format_table_data(arrow_table, format_type=format)

    # Build response
    response = {
        "success": True,
        "format": actual_format,
        "schema": schema,
        "row_count": len(arrow_table),
        "is_complete": is_complete,
        "data": formatted_data,
    }

    # Add optional fields
    if namespace is not None:
        response["namespace"] = namespace
    if table_name is not None:
        response["table_name"] = table_name

    return response


@mcp_server.tool()
async def session_details(
    context: Context, session_id: str, attempt_to_connect: bool = False
) -> dict:
    """
    MCP Tool: Get detailed information about a specific session.

    Returns comprehensive status and configuration information for a specific session,
    including availability status, programming language, and version information.

    Terminology Note:
    - 'Session' and 'worker' are interchangeable terms - both refer to a running Deephaven instance
    - 'Deephaven Community' and 'Deephaven Core' are interchangeable names for the same product
    - 'Deephaven Enterprise', 'Deephaven Core+', and 'Deephaven CorePlus' are interchangeable names for the same product

    AI Agent Usage:
    - Use attempt_to_connect=False (default) for quick status checks
    - Use attempt_to_connect=True to actively verify session connectivity
    - Check 'available' field to determine if session can be used
    - Use 'liveness_status' for detailed status classification
    - Use list_sessions first to discover available session_id values
    - IMPORTANT: attempt_to_connect=True creates resource overhead (open sessions consume MCP server resources and each session maintains connections)
    - Only use attempt_to_connect=True for sessions you actually intend to use, not for general discovery or monitoring

    Args:
        context (Context): The MCP context object.
        session_id (str): The session identifier (fully qualified name) to get details for.
        attempt_to_connect (bool, optional): Whether to attempt connecting to the session
            to verify its status. Defaults to False for faster response.

    Returns:
        dict: Structured result object with keys:
            - 'success' (bool): True if retrieval succeeded, False otherwise.
            - 'session' (dict): Session details including:
                - session_id (fully qualified session name)
                - type ("community" or "enterprise")
                - source (community source or enterprise factory)
                - session_name (session name)
                - available (bool): Whether the session is available
                - liveness_status (str): Status classification ("ONLINE", "OFFLINE", etc.)
                - liveness_detail (str): Detailed explanation of the status
                - programming_language (str, optional): The programming language of the session (e.g., "python", "groovy")
                - programming_language_version (str, optional): Version of the programming language (e.g., "3.9.7")
                - deephaven_community_version (str, optional): Version of Deephaven Community/Core (e.g., "0.24.0")
                - deephaven_enterprise_version (str, optional): Version of Deephaven Enterprise/Core+/CorePlus (e.g., "0.24.0")
                  if the session is an enterprise installation
            - 'error' (str, optional): Error message if retrieval failed.
            - 'isError' (bool, optional): Present and True if this is an error response.

        Note: The version fields (programming_language_version, deephaven_community_version,
        deephaven_enterprise_version) will only be present if the session is available and
        the information could be retrieved successfully. Fields with null values are excluded
        from the response.
    """
    _LOGGER.info(
        f"[mcp_systems_server:session_details] Invoked for session_id: {session_id}"
    )
    try:
        _LOGGER.debug(
            "[mcp_systems_server:session_details] Accessing session registry from context"
        )
        session_registry: CombinedSessionRegistry = (
            context.request_context.lifespan_context["session_registry"]
        )

        # Get the specific session manager directly
        _LOGGER.debug(
            f"[mcp_systems_server:session_details] Retrieving session manager for '{session_id}'"
        )
        try:
            mgr = await session_registry.get(session_id)
            _LOGGER.debug(
                f"[mcp_systems_server:session_details] Successfully retrieved session manager for '{session_id}'"
            )
        except Exception as e:
            return {
                "success": False,
                "error": f"Session with ID '{session_id}' not found: {str(e)}",
                "isError": True,
            }

        try:
            # Get basic metadata
            _LOGGER.debug(
                f"[mcp_systems_server:session_details] Extracting metadata for session '{session_id}'"
            )
            system_type_str = mgr.system_type.name
            source = mgr.source
            session_name = mgr.name
            _LOGGER.debug(
                f"[mcp_systems_server:session_details] Session '{session_id}' metadata: type={system_type_str}, source={source}, name={session_name}"
            )

            # Get liveness status and availability
            _LOGGER.debug(
                f"[mcp_systems_server:session_details] Checking liveness for session '{session_id}' (attempt_to_connect={attempt_to_connect})"
            )
            available, liveness_status, liveness_detail = (
                await _get_session_liveness_info(mgr, session_id, attempt_to_connect)
            )

            # Get session properties using helper functions
            _LOGGER.debug(
                f"[mcp_systems_server:session_details] Retrieving session properties for '{session_id}' (available={available})"
            )
            programming_language = await _get_session_programming_language(
                mgr, session_id, available
            )

            # TODO: should the versions be cached?
            programming_language_version = await _get_session_property(
                mgr,
                session_id,
                available,
                "programming_language_version",
                queries.get_programming_language_version,
            )

            community_version, enterprise_version = await _get_session_versions(
                mgr, session_id, available
            )
            _LOGGER.debug(
                f"[mcp_systems_server:session_details] Completed property retrieval for session '{session_id}'"
            )

            # Build session info dictionary with all potential fields
            session_info_with_nones = {
                "session_id": session_id,
                "type": system_type_str,
                "source": source,
                "session_name": session_name,
                "available": available,
                "liveness_status": liveness_status,
                "liveness_detail": liveness_detail,
                "programming_language": programming_language,
                "programming_language_version": programming_language_version,
                "deephaven_community_version": community_version,
                "deephaven_enterprise_version": enterprise_version,
            }

            # Filter out None values
            session_info = {
                k: v for k, v in session_info_with_nones.items() if v is not None
            }
            _LOGGER.debug(
                f"[mcp_systems_server:session_details] Built session info for '{session_id}' with {len(session_info)} fields"
            )

            return {"success": True, "session": session_info}

        except Exception as e:
            _LOGGER.warning(
                f"[mcp_systems_server:session_details] Could not process session '{session_id}': {e!r}"
            )
            return {
                "success": False,
                "error": f"Error processing session '{session_id}': {str(e)}",
                "isError": True,
            }

    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:session_details] Failed: {e!r}", exc_info=True
        )
        return {"success": False, "error": str(e), "isError": True}


@mcp_server.tool()
async def session_tables_schema(
    context: Context, session_id: str, table_names: list[str] | None = None
) -> dict:
    """
    MCP Tool: Retrieve table schemas as TABULAR METADATA from a Deephaven session.

    **Returns**: Schema information formatted as TABULAR DATA where each row represents a column
    in the source table. This tabular metadata should be displayed as a table to users for easy
    comprehension of table structure.

    Returns complete metadata information for the specified tables including column names, data types,
    and all metadata properties. If no table_names are provided, returns schemas for all available
    tables in the session. This provides the FULL schema with all metadata properties, not just
    simplified name/type pairs.

    Terminology Note:
    - 'Schema' and 'meta table' are interchangeable terms - both refer to table metadata
    - The schema describes the structure and properties of columns in a table
    - 'Session' and 'worker' are interchangeable terms for a running Deephaven instance

    Table Rendering:
    - **This tool returns TABULAR METADATA that MUST be displayed as a table to users**
    - Each row in the result represents one column from the source table
    - The table shows column properties: Name, DataType, IsPartitioning, ComponentType, etc.
    - Present schema data in tabular format (table or grid) for easy comprehension
    - Do NOT present schema data as plain text or unstructured lists

    AI Agent Usage:
    - Call with no table_names to discover all available tables and their full schemas
    - Call with specific table_names list when you know which tables you need
    - Always check the 'success' field in each schema result before using the schema data
    - The 'data' field contains full metadata with properties like Name, DataType, IsPartitioning, etc.
    - Use the returned metadata to construct valid queries and understand table structure
    - Essential before calling session_table_data or session_script_run to understand table structure
    - Individual table failures don't stop processing of other tables
    - This returns FULL metadata, not simplified schema - use for complete table understanding

    Args:
        context (Context): The MCP context object.
        session_id (str): ID of the Deephaven session to query. This argument is required.
        table_names (list[str], optional): List of table names to retrieve schemas for.
            If None, all available tables will be queried. Defaults to None.

    Returns:
        dict: Structured result object with keys:
            - 'success' (bool): True if the operation completed, False if it failed entirely.
            - 'schemas' (list[dict], optional): List of per-table results if operation completed. Each contains:
                - 'success' (bool): True if this table's schema was retrieved successfully
                - 'table' (str): Table name
                - 'data' (list[dict], optional): Full metadata rows if successful. Each dict contains:
                    - 'Name' (str): Column name
                    - 'DataType' (str): Deephaven data type
                    - 'IsPartitioning' (bool, optional): Whether column is used for partitioning
                    - 'ComponentType' (str, optional): Component type for array/vector columns
                    - Additional metadata properties depending on column type
                - 'meta_columns' (list[dict], optional): Schema of the metadata table itself
                - 'row_count' (int, optional): Number of columns in the table
                - 'error' (str, optional): Error message if this table's schema retrieval failed
                - 'isError' (bool, optional): Present and True if this table had an error
            - 'error' (str, optional): Error message if the entire operation failed.
            - 'isError' (bool, optional): Present and True if this is an error response.

    Example Successful Response (mixed results):
        {
            'success': True,
            'schemas': [
                {
                    'success': True,
                    'table': 'MyTable',
                    'data': [{'Name': 'Col1', 'DataType': 'int', ...}, ...],
                    'row_count': 3
                },
                {'success': False, 'table': 'MissingTable', 'error': 'Table not found', 'isError': True}
            ]
        }

    Example Error Response (total failure):
        {'success': False, 'error': 'Failed to connect to session: ...', 'isError': True}

    Example Usage:
        # Get full schemas for all tables in the session
        Tool: session_tables_schema
        Parameters: {
            "session_id": "community:localhost:10000"
        }

        # Get full schemas for specific tables
        Tool: session_tables_schema
        Parameters: {
            "session_id": "community:localhost:10000",
            "table_names": ["trades", "quotes", "orders"]
        }

        # Get full schema for a single table
        Tool: session_tables_schema
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "table_names": ["market_data"]
        }
    """
    _LOGGER.info(
        f"[mcp_systems_server:session_tables_schema] Invoked: session_id={session_id!r}, table_names={table_names!r}"
    )
    schemas = []
    try:
        # Use helper to get session from context
        session = await _get_session_from_context(
            "session_tables_schema", context, session_id
        )

        if table_names is not None:
            selected_table_names = table_names
            _LOGGER.info(
                f"[mcp_systems_server:session_tables_schema] Fetching schemas for specified tables: {selected_table_names!r}"
            )
        else:
            _LOGGER.debug(
                f"[mcp_systems_server:session_tables_schema] Discovering available tables in session '{session_id}'"
            )
            selected_table_names = await session.tables()
            _LOGGER.info(
                f"[mcp_systems_server:session_tables_schema] Fetching schemas for all tables in session: {selected_table_names!r}"
            )

        for table_name in selected_table_names:
            _LOGGER.debug(
                f"[mcp_systems_server:session_tables_schema] Processing table '{table_name}' in session '{session_id}'"
            )
            try:
                meta_arrow_table = await queries.get_session_meta_table(
                    session, table_name
                )

                # Use helper to format result (no namespace for session tables)
                result = _format_meta_table_result(
                    meta_arrow_table, table_name, namespace=None
                )
                schemas.append(result)

                _LOGGER.info(
                    f"[mcp_systems_server:session_tables_schema] Success: Retrieved full schema for table '{table_name}' ({result['row_count']} columns)"
                )
            except Exception as table_exc:
                _LOGGER.error(
                    f"[mcp_systems_server:session_tables_schema] Failed to get schema for table '{table_name}': {table_exc!r}",
                    exc_info=True,
                )
                schemas.append(
                    {
                        "success": False,
                        "table": table_name,
                        "error": str(table_exc),
                        "isError": True,
                    }
                )

        _LOGGER.info(
            f"[mcp_systems_server:session_tables_schema] Returning {len(schemas)} table results"
        )
        return {"success": True, "schemas": schemas, "count": len(schemas)}
    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:session_tables_schema] Failed for session: '{session_id}', error: {e!r}",
            exc_info=True,
        )
        return {"success": False, "error": str(e), "isError": True}


@mcp_server.tool()
async def session_tables_list(context: Context, session_id: str) -> dict:
    """
    MCP Tool: Retrieve the names of all tables in a Deephaven session.

    Returns a simple list of table names without schemas or metadata. This is a lightweight
    alternative to table_schemas when you only need to discover what tables exist in a session.
    Much faster than table_schemas since it doesn't fetch schema information for each table.

    Terminology Note:
    - 'Session' and 'worker' are interchangeable terms - both refer to a running Deephaven instance
    - 'Deephaven Community' and 'Deephaven Core' are interchangeable names for the same product
    - 'Deephaven Enterprise', 'Deephaven Core+', and 'Deephaven CorePlus' are interchangeable names for the same product

    AI Agent Usage:
    - Use this for quick table discovery when you don't need schema details
    - Much faster than table_schemas for large sessions with many tables
    - Follow up with table_schemas or get_table_meta for specific tables you're interested in
    - Works with both Community and Enterprise sessions
    - Check 'count' field to see how many tables exist
    - Always check 'success' field before accessing 'table_names'

    Args:
        context (Context): The MCP context object, required by MCP protocol but not actively used.
        session_id (str): ID of the Deephaven session to query. Must match an existing active session.

    Returns:
        dict: Structured result object with the following keys:
            - 'success' (bool): Always present. True if table names were retrieved successfully, False on any error.
            - 'session_id' (str, optional): The session ID if successful. Useful for confirming which session was queried.
            - 'table_names' (list[str], optional): List of table names if successful. Empty list if session has no tables.
            - 'count' (int, optional): Number of tables found if successful. Convenient for quick checks.
            - 'error' (str, optional): Human-readable error message if retrieval failed. Omitted on success.
            - 'isError' (bool, optional): Present and True only when success=False. Explicit error flag for frameworks.

    Error Scenarios:
        - Invalid session_id: Returns error if session doesn't exist or is not accessible
        - Session connection issues: Returns error if unable to communicate with Deephaven server
        - Session not available: Returns error if session is closed or unavailable

    Example Successful Response:
        {
            'success': True,
            'session_id': 'community:localhost:10000',
            'table_names': ['trades', 'quotes', 'orders'],
            'count': 3
        }

    Example Error Response:
        {
            'success': False,
            'error': 'Session not found: community:localhost:10000',
            'isError': True
        }

    Performance Notes:
        - Very fast operation, typically completes in milliseconds
        - No network data transfer (just metadata query)
        - Safe to call frequently for session monitoring
        - Scales well even with hundreds of tables
    """
    _LOGGER.info(
        f"[mcp_systems_server:session_tables_list] Invoked: session_id={session_id!r}"
    )

    try:
        # Use helper to get session from context
        session = await _get_session_from_context(
            "session_tables_list", context, session_id
        )

        _LOGGER.debug(
            f"[mcp_systems_server:session_tables_list] Retrieving table names from session '{session_id}'"
        )
        table_names = await session.tables()

        _LOGGER.info(
            f"[mcp_systems_server:session_tables_list] Success: Retrieved {len(table_names)} table(s) from session '{session_id}'"
        )

        return {
            "success": True,
            "session_id": session_id,
            "table_names": table_names,
            "count": len(table_names),
        }

    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:session_tables_list] Failed for session: '{session_id}', error: {e!r}",
            exc_info=True,
        )
        return {"success": False, "error": str(e), "isError": True}


@mcp_server.tool()
async def session_script_run(
    context: Context,
    session_id: str,
    script: str | None = None,
    script_path: str | None = None,
) -> dict:
    r"""
    MCP Tool: Execute a script on a specified Deephaven session.

    Executes a script on the specified Deephaven session and returns execution status. The script
    can be provided either as a string in the 'script' parameter or as a file path in the 'script_path'
    parameter. Exactly one of these parameters must be provided.

    AI Agent Usage:
    - Use 'script' parameter for inline script execution
    - Use 'script_path' parameter to execute scripts from files
    - Check 'success' field in response to verify execution completed without errors
    - Script executes in the session's environment with access to session state
    - Any tables or variables created will persist in the session for future use
    - Script language depends on the session's configured programming language

    Args:
        context (Context): The MCP context object.
        session_id (str): ID of the Deephaven session on which to execute the script. This argument is required.
        script (str, optional): The script to execute. Defaults to None.
        script_path (str, optional): Path to a script file to execute. Defaults to None.

    Returns:
        dict: Structured result object with the following keys:
            - 'success' (bool): True if the script executed successfully, False otherwise.
            - 'error' (str, optional): Error message if execution failed. Omitted on success.
            - 'isError' (bool, optional): Present and True if this is an error response (i.e., success is False).

    Example Successful Response:
        {'success': True}

    Example Error Responses:
        {'success': False, 'error': 'Must provide either script or script_path.', 'isError': True}
        {'success': False, 'error': 'Script execution failed: ...', 'isError': True}

    Example Usage:
        # Execute inline Python script
        Tool: session_script_run
        Parameters: {
            "session_id": "community:localhost:10000",
            "script": "from deephaven import new_table\nfrom deephaven.column import int_col\nmy_table = new_table([int_col('ID', [1, 2, 3])])"
        }

        # Execute script from file
        Tool: session_script_run
        Parameters: {
            "session_id": "community:localhost:10000",
            "script_path": "/path/to/analysis_script.py"
        }
    """
    _LOGGER.info(
        f"[mcp_systems_server:session_script_run] Invoked: session_id={session_id!r}, script={'<provided>' if script else None}, script_path={script_path!r}"
    )
    result: dict[str, object] = {"success": False}
    try:
        _LOGGER.debug(
            f"[mcp_systems_server:session_script_run] Validating script parameters for session '{session_id}'"
        )
        if script is None and script_path is None:
            _LOGGER.warning(
                "[mcp_systems_server:session_script_run] No script or script_path provided. Returning error."
            )
            result["error"] = "Must provide either script or script_path."
            result["isError"] = True
            return result

        if script is None:
            _LOGGER.info(
                f"[mcp_systems_server:session_script_run] Reading script from file: {script_path!r}"
            )
            if script_path is None:
                raise RuntimeError(
                    "Internal error: script_path is None after prior guard"
                )  # pragma: no cover
            _LOGGER.debug(
                f"[mcp_systems_server:session_script_run] Opening script file '{script_path}' for reading"
            )
            async with aiofiles.open(script_path) as f:
                script = await f.read()
            _LOGGER.debug(
                f"[mcp_systems_server:session_script_run] Successfully read {len(script)} characters from script file"
            )

        # Use helper to get session from context
        session = await _get_session_from_context(
            "session_script_run", context, session_id
        )
        _LOGGER.info(
            f"[mcp_systems_server:session_script_run] Session established for session: '{session_id}'"
        )

        _LOGGER.info(
            f"[mcp_systems_server:session_script_run] Executing script on session: '{session_id}'"
        )
        _LOGGER.debug(
            f"[mcp_systems_server:session_script_run] Script length: {len(script)} characters"
        )

        await session.run_script(script)

        _LOGGER.info(
            f"[mcp_systems_server:session_script_run] Script executed successfully on session: '{session_id}'"
        )
        result["success"] = True
    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:session_script_run] Failed for session: '{session_id}', error: {e!r}",
            exc_info=True,
        )
        result["error"] = str(e)
        result["isError"] = True
    return result


@mcp_server.tool()
async def session_pip_list(context: Context, session_id: str) -> dict:
    """
    MCP Tool: Retrieve installed pip packages as a TABULAR LIST from a Deephaven session.

    **Returns**: Package information formatted as TABULAR DATA with columns for package name and version.
    This tabular data should be displayed as a table to users for easy scanning of available libraries.

    Queries the specified Deephaven session for installed pip packages using importlib.metadata.
    Returns package names and versions for all Python packages available in the session's environment.

    Table Rendering:
    - **This tool returns TABULAR PACKAGE DATA that MUST be displayed as a table to users**
    - Each row represents one installed package
    - Columns: package (name), version
    - Present as a table for easy scanning of available libraries
    - Do NOT present package data as plain text or unstructured lists

    AI Agent Usage:
    - Use this to understand what libraries are available in a session before running scripts
    - Check 'result' array for list of installed packages with names and versions
    - Useful for determining if specific libraries need to be installed before script execution
    - Essential for generating code that uses available libraries and avoiding import errors
    - Helps inform decisions about which libraries to use when multiple options are available

    Args:
        context (Context): The MCP context object.
        session_id (str): ID of the Deephaven session to query.

    Returns:
        dict: Structured result object with the following keys:
            - 'success' (bool): True if the packages were retrieved successfully, False otherwise.
            - 'result' (list[dict], optional): List of pip package dicts if successful. Each contains:
                - 'package' (str): Package name
                - 'version' (str): Package version
            - 'error' (str, optional): Error message if retrieval failed.
            - 'isError' (bool, optional): Present and True if this is an error response (i.e., success is False).

    Example Successful Response:
        {'success': True, 'result': [{"package": "numpy", "version": "1.25.0"}, ...]}

    Example Error Response:
        {'success': False, 'error': 'Failed to get pip packages: ...', 'isError': True}
    """
    _LOGGER.info(
        f"[mcp_systems_server:session_pip_list] Invoked for session_id: {session_id!r}"
    )
    result: dict = {"success": False}
    try:
        # Use helper to get session from context
        session = await _get_session_from_context(
            "session_pip_list", context, session_id
        )
        _LOGGER.info(
            f"[mcp_systems_server:session_pip_list] Session established for session: '{session_id}'"
        )

        _LOGGER.debug(
            f"[mcp_systems_server:session_pip_list] Querying pip packages for session '{session_id}'"
        )
        arrow_table = await queries.get_pip_packages_table(session)
        _LOGGER.debug(
            f"[mcp_systems_server:session_pip_list] Retrieved pip packages table for session '{session_id}'"
        )
        _LOGGER.info(
            f"[mcp_systems_server:session_pip_list] Pip packages table retrieved successfully for session: '{session_id}'"
        )

        # Convert the Arrow table to a list of dicts
        packages: list[dict[str, str]] = []
        if arrow_table is not None:
            # Convert to pandas DataFrame for easy dict conversion
            df = arrow_table.to_pandas()
            raw_packages = df.to_dict(orient="records")
            # Validate and convert keys to lowercase
            packages = []
            for pkg in raw_packages:
                if (
                    not isinstance(pkg, dict)
                    or "Package" not in pkg
                    or "Version" not in pkg
                ):
                    raise ValueError(
                        "Malformed package data: missing 'Package' or 'Version' key"
                    )
                # Results should have lower case names.  The query had to use Upper case names to avoid invalid column names
                packages.append({"package": pkg["Package"], "version": pkg["Version"]})

        result["success"] = True
        result["result"] = packages
    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:session_pip_list] Failed for session: '{session_id}', error: {e!r}",
            exc_info=True,
        )
        result["error"] = str(e)
        result["isError"] = True
    return result


# Size limits for table data responses
MAX_RESPONSE_SIZE = 50_000_000  # 50MB hard limit
WARNING_SIZE = 5_000_000  # 5MB warning threshold


def _check_response_size(table_name: str, estimated_size: int) -> dict | None:
    """
    Check if estimated response size is within acceptable limits.

    Evaluates the estimated response size against predefined limits to prevent memory
    issues and excessive network traffic. Logs warnings for large responses and
    returns structured error responses for oversized requests.

    Args:
        table_name (str): Name of the table being processed, used for logging context.
        estimated_size (int): Estimated response size in bytes.

    Returns:
        dict | None: Returns None if size is acceptable, or a structured error dict
                     with 'success': False, 'error': str, 'isError': True if the
                     response would exceed MAX_RESPONSE_SIZE (50MB).

    Side Effects:
        - Logs warning message if size exceeds WARNING_SIZE (5MB).
        - No side effects if size is within acceptable limits.
    """
    if estimated_size > WARNING_SIZE:
        _LOGGER.warning(
            f"Large response (~{estimated_size/1_000_000:.1f}MB) for table '{table_name}'. "
            f"Consider reducing max_rows for better performance."
        )

    if estimated_size > MAX_RESPONSE_SIZE:
        return {
            "success": False,
            "error": f"Response would be ~{estimated_size/1_000_000:.1f}MB (max 50MB). Please reduce max_rows.",
            "isError": True,
        }

    return None  # Size is acceptable


@mcp_server.tool()
async def session_table_data(
    context: Context,
    session_id: str,
    table_name: str,
    max_rows: int | None = 1000,
    head: bool = True,
    format: str = "optimize-rendering",
) -> dict:
    r"""
    MCP Tool: Retrieve TABULAR DATA from a specified Deephaven session table.

    **Returns**: Structured table data formatted for optimal AI agent comprehension and rendering.
    The response contains TABULAR DATA that should be displayed as a table to users.

    This tool queries the specified Deephaven session for table data and returns it in the requested format
    with optional row limiting. Supports multiple output formats optimized for AI agent consumption.

    **Format Accuracy for AI Agents** (based on empirical research):
    - markdown-kv: 61% accuracy (highest comprehension, more tokens)
    - markdown-table: 55% accuracy (good balance)
    - json-row/json-column: 50% accuracy
    - yaml: 50% accuracy
    - xml: 45% accuracy
    - csv: 44% accuracy (lowest comprehension, fewest tokens)

    Includes safety limits (50MB max response size) to prevent memory issues.

    Terminology Note:
    - 'Session' and 'worker' are interchangeable terms - both refer to a running Deephaven instance
    - 'Deephaven Community' and 'Deephaven Core' are interchangeable names for the same product
    - 'Deephaven Enterprise', 'Deephaven Core+', and 'Deephaven CorePlus' are interchangeable names for the same product

    Args:
        context (Context): The MCP context object, required by MCP protocol but not actively used.
        session_id (str): ID of the Deephaven session to query. Must match an existing active session.
        table_name (str): Name of the table to retrieve data from. Must exist in the specified session.
        max_rows (int | None, optional): Maximum number of rows to retrieve. Defaults to 1000 for safety.
                                        Set to None to retrieve entire table (use with caution for large tables).
        head (bool, optional): Direction of row retrieval. If True (default), retrieve from beginning.
                              If False, retrieve from end (most recent rows for time-series data).
        format (str, optional): Output format selection. Defaults to "optimize-rendering" for best table display.
                               Options:
                               - "optimize-rendering": (DEFAULT) Always use markdown-table (best for AI agent table display)
                               - "optimize-accuracy": Always use markdown-kv (best comprehension, more tokens)
                               - "optimize-cost": Always use csv (fewer tokens, may be harder to parse)
                               - "optimize-speed": Always use json-column (fastest conversion)
                               - "markdown-table": String with pipe-delimited table (| col1 | col2 |\n| --- | --- |\n| val1 | val2 |)
                               - "markdown-kv": String with record headers and key-value pairs (## Record 1\ncol1: val1\ncol2: val2)
                               - "json-row": List of dicts, one per row: [{col1: val1, col2: val2}, ...]
                               - "json-column": Dict with column names as keys, value arrays: {col1: [val1, val2], col2: [val3, val4]}
                               - "csv": String with comma-separated values, includes header row
                               - "yaml": String with YAML-formatted records list
                               - "xml": String with XML records structure

    Returns:
        dict: Structured result object with the following keys:
            - 'success' (bool): Always present. True if table data was retrieved successfully, False on any error.
            - 'table_name' (str, optional): Name of the retrieved table if successful.
            - 'format' (str, optional): Actual format used for the data if successful. May differ from request when using optimization strategies.
            - 'schema' (list[dict], optional): Array of column definitions if successful. Each dict contains:
                                              {'name': str, 'type': str} describing column name and PyArrow data type
                                              (e.g., 'int64', 'string', 'double', 'timestamp[ns]').
            - 'row_count' (int, optional): Number of rows in the returned data if successful. May be less than max_rows.
            - 'is_complete' (bool, optional): True if entire table was retrieved if successful. False if truncated by max_rows.
            - 'data' (list | dict | str, optional): The actual table data if successful. Type depends on format.
            - 'error' (str, optional): Human-readable error message if retrieval failed. Omitted on success.
            - 'isError' (bool, optional): Present and True only when success=False. Explicit error flag for frameworks.

    Error Scenarios:
        - Invalid session_id: Returns error if session doesn't exist or is not accessible
        - Invalid table_name: Returns error if table doesn't exist in the session
        - Invalid format: Returns error if format is not one of the supported options listed above
        - Response too large: Returns error if estimated response would exceed 50MB limit
        - Session connection issues: Returns error if unable to communicate with Deephaven server
        - Query execution errors: Returns error if table query fails (permissions, syntax, etc.)

    Table Rendering:
        - **This tool returns TABULAR DATA that should be displayed as a table to users**
        - The 'data' field contains formatted table data ready for display
        - Default format (markdown-table) renders well as tables in AI interfaces
        - Always present the returned data in tabular format (table, grid, or structured rows)

    Performance Considerations:
        - Large tables: Use csv format or limit max_rows to avoid memory issues
        - Column analysis: Use json-column format for efficient column-wise operations
        - Row processing: Use json-row format for record-by-record iteration
        - Response size limit: 50MB maximum to prevent memory issues

    AI Agent Usage:
        - Always check 'success' field before accessing data fields
        - Use 'is_complete' to determine if more data exists beyond max_rows limit
        - Parse 'schema' array to understand column types before processing 'data'
        - Use head=True (default) to get rows from table start, head=False to get from table end
        - Start with small max_rows values for large tables to avoid memory issues
        - Use 'optimize-rendering' (default) for best table display in AI interfaces
        - Use 'optimize-accuracy' for highest comprehension (markdown-kv format, more tokens)
        - Use 'optimize-cost' for fewest tokens (csv format, may be harder to parse)
        - Check 'format' field in response to know actual format used

    Example Usage:
        # Get first 1000 rows with default format
        Tool: session_table_data
        Parameters: {
            "session_id": "community:localhost:10000",
            "table_name": "my_table"
        }

        # Get last 500 rows (most recent for time-series)
        Tool: session_table_data
        Parameters: {
            "session_id": "community:localhost:10000",
            "table_name": "trades",
            "max_rows": 500,
            "head": false
        }

        # Get data in CSV format for efficient parsing
        Tool: session_table_data
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "table_name": "market_data",
            "max_rows": 10000,
            "format": "csv"
        }

        # Get data optimized for AI comprehension
        Tool: session_table_data
        Parameters: {
            "session_id": "community:localhost:10000",
            "table_name": "customer_records",
            "max_rows": 100,
            "format": "optimize-accuracy"
        }

        # Get entire small table in JSON row format
        Tool: session_table_data
        Parameters: {
            "session_id": "community:localhost:10000",
            "table_name": "config_settings",
            "max_rows": null,
            "format": "json-row"
        }

        # Get data in markdown table format
        Tool: session_table_data
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "table_name": "summary_stats",
            "max_rows": 50,
            "format": "markdown-table"
        }
    """
    _LOGGER.info(
        f"[mcp_systems_server:session_table_data] Invoked: session_id={session_id!r}, "
        f"table_name={table_name!r}, max_rows={max_rows}, head={head}, format={format!r}"
    )

    result: dict[str, object] = {"success": False}

    try:
        # Use helper to get session from context
        session = await _get_session_from_context(
            "session_table_data", context, session_id
        )

        # Get table data using queries module
        _LOGGER.debug(
            f"[mcp_systems_server:session_table_data] Retrieving table data for '{table_name}'"
        )
        arrow_table, is_complete = await queries.get_table(
            session, table_name, max_rows=max_rows, head=head
        )

        # Check response size before formatting (rough estimation to avoid memory overhead)
        row_count = len(arrow_table)
        col_count = len(arrow_table.schema)
        estimated_size = row_count * col_count * ESTIMATED_BYTES_PER_CELL
        size_error = _check_response_size(table_name, estimated_size)

        if size_error:
            return size_error

        # Build response using helper
        _LOGGER.debug(
            f"[mcp_systems_server:session_table_data] Formatting data with format='{format}'"
        )
        response = _build_table_data_response(
            arrow_table, is_complete, format, table_name=table_name
        )
        result.update(response)

        _LOGGER.info(
            f"[mcp_systems_server:session_table_data] Successfully retrieved {row_count} rows "
            f"from '{table_name}' in '{response['format']}' format"
        )

    except ValueError as e:
        # Format validation error from formatters package
        _LOGGER.error(
            f"[mcp_systems_server:session_table_data] Invalid format parameter: {e!r}"
        )
        result["error"] = str(e)
        result["isError"] = True

    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:session_table_data] Failed for session '{session_id}', "
            f"table '{table_name}': {e!r}",
            exc_info=True,
        )
        result["error"] = str(e)
        result["isError"] = True

    return result


async def _get_catalog_data(
    context: Context,
    session_id: str,
    *,
    distinct_namespaces: bool,
    max_rows: int | None,
    filters: list[str] | None,
    format: str,
    tool_name: str,
) -> dict:
    """
    Retrieve catalog data (tables or namespaces) from an enterprise session.

    This consolidates the common logic between catalog_tables and catalog_namespaces tools.

    Args:
        context (Context): The MCP context object.
        session_id (str): ID of the Deephaven enterprise session to query.
        distinct_namespaces (bool): If True, retrieve distinct namespaces; if False, retrieve full catalog.
        max_rows (int | None): Maximum number of rows to return.
        filters (list[str] | None): Optional filters to apply.
        format (str): Output format for data.
        tool_name (str): Name of the calling tool for logging (e.g., "catalog_tables").

    Returns:
        dict: Result dictionary with success/error information and data.
    """
    result: dict[str, object] = {"success": False}
    data_type = "namespaces" if distinct_namespaces else "catalog entries"

    try:
        # Use helper to get session from context
        session = await _get_session_from_context(tool_name, context, session_id)

        # Get catalog data using queries module (includes enterprise check and filtering)
        _LOGGER.debug(
            f"[mcp_systems_server:{tool_name}] Retrieving {data_type} with filters: {filters}"
        )
        arrow_table, is_complete = await queries.get_catalog_table(
            session,
            max_rows=max_rows,
            filters=filters,
            distinct_namespaces=distinct_namespaces,
        )

        row_count = len(arrow_table)
        _LOGGER.debug(
            f"[mcp_systems_server:{tool_name}] Retrieved {row_count} {data_type} (complete={is_complete})"
        )

        # Estimate response size for safety
        estimated_size = arrow_table.nbytes
        size_check_result = _check_response_size(tool_name, estimated_size)
        if size_check_result:
            return size_check_result

        # Format the data using the formatters package
        _LOGGER.debug(
            f"[mcp_systems_server:{tool_name}] Formatting data with format='{format}'"
        )
        actual_format, formatted_data = format_table_data(arrow_table, format)
        _LOGGER.debug(
            f"[mcp_systems_server:{tool_name}] Data formatted as '{actual_format}'"
        )

        # Extract schema information
        columns = [
            {"name": field.name, "type": str(field.type)}
            for field in arrow_table.schema
        ]

        result.update(
            {
                "success": True,
                "session_id": session_id,
                "format": actual_format,
                "row_count": row_count,
                "is_complete": is_complete,
                "columns": columns,
                "data": formatted_data,
            }
        )

        _LOGGER.info(
            f"[mcp_systems_server:{tool_name}] Successfully retrieved {row_count} {data_type} "
            f"in '{actual_format}' format (complete={is_complete})"
        )

    except UnsupportedOperationError as e:
        # Enterprise-only operation attempted on community session
        _LOGGER.error(
            f"[mcp_systems_server:{tool_name}] Session '{session_id}' is not an enterprise session: {e!r}"
        )
        result["error"] = str(e)
        result["isError"] = True

    except ValueError as e:
        # Format validation error from formatters package
        _LOGGER.error(
            f"[mcp_systems_server:{tool_name}] Invalid format parameter: {e!r}"
        )
        result["error"] = str(e)
        result["isError"] = True

    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:{tool_name}] Failed for session '{session_id}': {e!r}",
            exc_info=True,
        )
        result["error"] = str(e)
        result["isError"] = True

    return result


@mcp_server.tool()
async def catalog_tables_list(
    context: Context,
    session_id: str,
    max_rows: int | None = 10000,
    filters: list[str] | None = None,
    format: str = "optimize-rendering",
) -> dict:
    """
    MCP Tool: Retrieve catalog entries as a TABULAR LIST from a Deephaven Enterprise (Core+) session.

    **Returns**: Catalog table entries formatted as TABULAR DATA for display. Each row represents
    a table available in the enterprise catalog/database. This tabular data should be displayed as a table
    to users for easy browsing of available data sources.

    The catalog (also called database) contains metadata about tables accessible via the `deephaven_enterprise.database`
    package (the `db` variable) in an enterprise session. This includes tables that can be accessed
    using methods like `db.live_table(namespace, table_name)` or `db.historical_table(namespace, table_name)`.
    The catalog includes table names, namespaces, schemas, and other descriptive information. This tool
    enables discovery of available tables and their properties. Only works with enterprise sessions.

    **Format Accuracy for AI Agents** (based on empirical research):
    - markdown-kv: 61% accuracy (highest comprehension, more tokens)
    - markdown-table: 55% accuracy (good balance)
    - json-row/json-column: 50% accuracy
    - yaml: 50% accuracy
    - xml: 45% accuracy
    - csv: 44% accuracy (lowest comprehension, fewest tokens)

    For more information, see:
    - https://deephaven.io
    - https://docs.deephaven.io/pycoreplus/latest/worker/code/deephaven_enterprise.database.html

    Terminology Note:
    - 'Session' and 'worker' are interchangeable terms - both refer to a running Deephaven instance
    - 'ENTERPRISE' sessions run Deephaven Enterprise (also called 'Core+' or 'CorePlus')
    - This tool only works with enterprise sessions; community sessions do not have catalog tables
    - 'Catalog' and 'database' are interchangeable terms - the catalog is the database of available tables

    Table Rendering:
    - **This tool returns TABULAR CATALOG DATA that MUST be displayed as a table to users**
    - Each row represents one table available in the enterprise catalog
    - Columns include: Namespace, TableName, and other catalog metadata
    - Present as a table for easy browsing and discovery of data sources
    - Do NOT present catalog data as plain text or unstructured lists

    AI Agent Usage:
    - Use this to discover what tables are available in the catalog/database via the `db` variable
    - The catalog is the database of available tables in an enterprise session
    - Tables in the catalog can be accessed using `db.live_table(namespace, table_name)` or `db.historical_table(namespace, table_name)`
    - Filter by namespace to find tables in specific data domains
    - Filter by table name patterns to locate specific tables
    - Check 'is_complete' to know if all catalog entries were returned
    - Combine with catalog_tables_schema to get full metadata for discovered tables
    - Essential first step before querying enterprise data sources
    - Use filters to narrow down large catalogs/databases efficiently

    Filter Syntax Reference:
    Filters use Deephaven query language with backticks (`) for string literals.
    Multiple filters are combined with AND logic.

    Common Filter Patterns:
        Exact Match:
            - Namespace exact: "Namespace = `market_data`"
            - Table name exact: "TableName = `daily_prices`"

        String Contains (case-sensitive):
            - Namespace contains: "Namespace.contains(`market`)"
            - Table name contains: "TableName.contains(`price`)"

        String Contains (case-insensitive):
            - Namespace: "Namespace.toLowerCase().contains(`market`)"
            - Table name: "TableName.toLowerCase().contains(`price`)"

        String Starts/Ends With:
            - Starts with: "TableName.startsWith(`daily_`)"
            - Ends with: "TableName.endsWith(`_prices`)"

        Multiple Values (IN):
            - Namespace in list: "Namespace in `market_data`, `reference_data`"
            - Case-insensitive: "Namespace icase in `market_data`, `reference_data`"

        NOT IN:
            - Exclude namespaces: "Namespace not in `test`, `staging`"
            - Case-insensitive: "Namespace icase not in `test`, `staging`"

        Regex Matching:
            - Pattern match: "TableName.matches(`.*_daily_.*`)"

        Comparison Operators:
            - Not equal: "Namespace != `test`"
            - Greater than: "Size > 1000000"
            - Less than: "RowCount < 100"
            - Range: "inRange(RowCount, 100, 10000)"

        Combining Filters (AND logic):
            filters=["Namespace = `market_data`", "TableName.contains(`price`)"]

    Important Notes About Filters:
        - String literals MUST use backticks (`), not single (') or double (") quotes
        - Filters are case-sensitive by default; use .toLowerCase() for case-insensitive matching
        - Multiple filters in the list are combined with AND (all must match)
        - For OR logic, use a single filter with boolean operators
        - Invalid filter syntax will cause the tool to return an error
        - See https://deephaven.io/core/docs/how-to-guides/use-filters/ for complete syntax

    Args:
        context (Context): The MCP context object.
        session_id (str): ID of the Deephaven enterprise session to query.
        max_rows (int | None): Maximum number of catalog entries to return. Default is 10000.
                               Set to None to retrieve entire catalog (use with caution for large deployments).
        filters (list[str] | None): Optional list of Deephaven where clause expressions to filter catalog.
                                    Multiple filters are combined with AND logic. Use backticks (`) for string literals.
        format (str): Output format for catalog data. Default is "optimize-rendering" for best table display.
                     Options: "optimize-rendering" (default, uses markdown-table), "optimize-accuracy" (uses markdown-kv),
                     "optimize-cost" (uses csv), "optimize-speed" (uses json-column), or explicit formats:
                     "json-row", "json-column", "csv", "markdown-table", "markdown-kv", "yaml", "xml".

    Returns:
        dict: Structured result object with keys:
            - 'success' (bool): True if catalog was retrieved successfully, False on error.
            - 'session_id' (str, optional): The session ID if successful.
            - 'format' (str, optional): Actual format used for data if successful (e.g., "json-row").
            - 'row_count' (int, optional): Number of catalog entries returned if successful.
            - 'is_complete' (bool, optional): True if all catalog entries returned, False if truncated by max_rows.
            - 'columns' (list[dict], optional): Schema of catalog table if successful. Each dict contains:
                {'name': str, 'type': str} describing catalog columns like Namespace, TableName, etc.
            - 'data' (list[dict] | dict | str, optional): Catalog data in requested format if successful:
                - json-row: List of dicts, one per catalog entry
                - json-column: Dict mapping column names to arrays of values
                - csv: String with CSV-formatted catalog data
                - markdown-table: String with pipe-delimited table format
                - markdown-kv: String with record headers and key-value pairs
                - yaml: String with YAML-formatted catalog entries
                - xml: String with XML catalog structure
            - 'error' (str, optional): Human-readable error message if retrieval failed. Omitted on success.
            - 'isError' (bool, optional): Present and True only when success=False. Explicit error flag.

    Error Scenarios:
        - Invalid session_id: Returns error if session doesn't exist or is not accessible
        - Community session: Returns error if session is not an enterprise (Core+) session
        - Invalid filters: Returns error if filter syntax is invalid or references non-existent columns
        - Invalid format: Returns error if format is not one of the supported options
        - Response too large: Returns error if estimated response would exceed 50MB limit
        - Session connection issues: Returns error if unable to communicate with Deephaven server
        - Permission errors: Returns error if session lacks permission to access catalog

    Performance Considerations:
        - Default max_rows of 10000 is safe for most enterprise deployments
        - Use filters to reduce result set size for better performance
        - Catalog retrieval is typically fast but scales with number of tables
        - Large catalogs (10000+ tables) may benefit from more specific filters
        - Response size is validated to prevent memory issues (50MB limit)

    Example Usage:
        # Get first 10000 catalog entries
        Tool: catalog_tables_list
        Parameters: {
            "session_id": "enterprise:prod:analytics"
        }

        # Filter by namespace
        Tool: catalog_tables_list
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "filters": ["Namespace = `market_data`"]
        }

        # Filter by table name pattern
        Tool: catalog_tables_list
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "filters": ["TableName.contains(`price`)"]
        }

        # Multiple filters (AND logic)
        Tool: catalog_tables_list
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "filters": ["Namespace = `market_data`", "TableName.toLowerCase().contains(`daily`)"]
        }

        # Get all catalog entries (use with caution)
        Tool: catalog_tables_list
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "max_rows": null
        }

        # CSV format for easy parsing
        Tool: catalog_tables_list
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "filters": ["Namespace = `reference_data`"],
            "format": "csv"
        }
    """
    _LOGGER.info(
        f"[mcp_systems_server:catalog_tables] Invoked: session_id={session_id!r}, "
        f"max_rows={max_rows}, filters={filters!r}, format={format!r}"
    )

    return await _get_catalog_data(
        context,
        session_id,
        distinct_namespaces=False,
        max_rows=max_rows,
        filters=filters,
        format=format,
        tool_name="catalog_tables",
    )


@mcp_server.tool()
async def catalog_namespaces_list(
    context: Context,
    session_id: str,
    max_rows: int | None = 1000,
    filters: list[str] | None = None,
    format: str = "optimize-rendering",
) -> dict:
    """
    MCP Tool: Retrieve catalog namespaces as a TABULAR LIST from a Deephaven Enterprise (Core+) session.

    **Returns**: Namespace information formatted as TABULAR DATA for display. Each row represents
    a data domain available in the enterprise catalog/database. This tabular data should be displayed as a
    table to users for easy browsing of available data domains.

    This tool retrieves the list of distinct namespaces available via the `deephaven_enterprise.database`
    package (the `db` variable) in an enterprise session. These namespaces represent data domains that
    contain tables in the catalog (database) accessible using methods like `db.live_table(namespace, table_name)` or
    `db.historical_table(namespace, table_name)`. This enables efficient discovery of data domains
    before drilling down into specific tables. This is typically the first step in exploring an
    enterprise data catalog. Only works with enterprise sessions.

    **Format Accuracy for AI Agents** (based on empirical research):
    - markdown-kv: 61% accuracy (highest comprehension, more tokens)
    - markdown-table: 55% accuracy (good balance)
    - json-row/json-column: 50% accuracy
    - yaml: 50% accuracy
    - xml: 45% accuracy
    - csv: 44% accuracy (lowest comprehension, fewest tokens)

    For more information, see:
    - https://deephaven.io
    - https://docs.deephaven.io/pycoreplus/latest/worker/code/deephaven_enterprise.database.html

    Terminology Note:
    - 'Session' and 'worker' are interchangeable terms - both refer to a running Deephaven instance
    - 'ENTERPRISE' sessions run Deephaven Enterprise (also called 'Core+' or 'CorePlus')
    - This tool only works with enterprise sessions; community sessions do not have catalog tables
    - 'Namespace' refers to a data domain or organizational grouping of tables
    - 'Catalog' and 'database' are interchangeable terms - the catalog is the database of available tables

    Table Rendering:
    - **This tool returns TABULAR NAMESPACE DATA that MUST be displayed as a table to users**
    - Each row represents one data domain (namespace) in the enterprise catalog
    - Column: Namespace (the name of the data domain)
    - Present as a table for easy browsing and discovery of data domains
    - Do NOT present namespace data as plain text or unstructured lists

    AI Agent Usage:
    - Use this as the first step to discover available data domains in the enterprise catalog/database
    - The catalog is the database of available tables organized by namespaces (data domains)
    - Namespaces represent data domains accessible via `db.live_table(namespace, table_name)` or `db.historical_table(namespace, table_name)`
    - Much faster than retrieving full catalog when you just need to know what domains exist
    - Filter catalog first if you want namespaces from a specific subset of tables
    - Combine with catalog_tables_list to drill down into specific namespaces
    - Essential for top-down data exploration workflow
    - Returns lightweight data (just namespace names) for quick discovery

    Args:
        context (Context): The MCP context object.
        session_id (str): ID of the Deephaven enterprise session to query.
        max_rows (int | None): Maximum number of namespaces to return. Default is 1000.
                               Set to None to retrieve all namespaces (use with caution).
        filters (list[str] | None): Optional list of Deephaven where clause expressions to filter
                                    the catalog before extracting namespaces. Use backticks (`) for string literals.
        format (str): Output format for namespace data. Default is "optimize-rendering" for best table display.
                     Options: "optimize-rendering" (default, uses markdown-table), "optimize-accuracy" (uses markdown-kv),
                     "optimize-cost" (uses csv), "optimize-speed" (uses json-column), or explicit formats:
                     "json-row", "json-column", "csv", "markdown-table", "markdown-kv", "yaml", "xml".

    Returns:
        dict: Structured result object with keys:
            - 'success' (bool): True if namespaces were retrieved successfully, False on error.
            - 'session_id' (str, optional): The session ID if successful.
            - 'format' (str, optional): Actual format used for data if successful (e.g., "json-row").
            - 'row_count' (int, optional): Number of namespaces returned if successful.
            - 'is_complete' (bool, optional): True if all namespaces returned, False if truncated by max_rows.
            - 'columns' (list[dict], optional): Schema of namespace table if successful. Contains:
                {'name': 'Namespace', 'type': 'string'}
            - 'data' (list[dict] | dict | str, optional): Namespace data in requested format if successful:
                - json-row: List of dicts, one per namespace: [{"Namespace": "market_data"}, ...]
                - json-column: Dict mapping column name to array: {"Namespace": ["market_data", ...]}
                - csv: String with CSV-formatted namespace data
                - markdown-table: String with pipe-delimited table format
                - markdown-kv: String with record headers and key-value pairs
                - yaml: String with YAML-formatted namespace list
                - xml: String with XML namespace structure
            - 'error' (str, optional): Human-readable error message if retrieval failed. Omitted on success.
            - 'isError' (bool, optional): Present and True only when success=False. Explicit error flag.

    Error Scenarios:
        - Non-enterprise session: Returns error if session is not an enterprise (Core+) session
        - Session not found: Returns error if session_id does not exist or is not accessible
        - Invalid filter: Returns error if filter syntax is invalid
        - Invalid format: Returns error if format is not one of the supported options
        - Response too large: Returns error if estimated response would exceed 50MB limit
        - Session connection issues: Returns error if unable to communicate with Deephaven server

    Performance Considerations:
        - Default max_rows of 1000 is safe for most enterprise deployments
        - Namespace retrieval is very fast (typically < 1 second)
        - Much more efficient than retrieving full catalog for initial discovery
        - Filters are applied to catalog before extracting namespaces for efficiency

    Example Usage:
        # Get all namespaces (up to 1000)
        Tool: catalog_namespaces_list
        Parameters: {
            "session_id": "enterprise:prod:analytics"
        }

        # Get namespaces from filtered catalog
        Tool: catalog_namespaces_list
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "filters": ["TableName.contains(`daily`)"]
        }

        # CSV format
        Tool: catalog_namespaces_list
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "format": "csv"
        }
    """
    _LOGGER.info(
        f"[mcp_systems_server:catalog_namespaces] Invoked: session_id={session_id!r}, "
        f"max_rows={max_rows}, filters={filters!r}, format={format!r}"
    )

    return await _get_catalog_data(
        context,
        session_id,
        distinct_namespaces=True,
        max_rows=max_rows,
        filters=filters,
        format=format,
        tool_name="catalog_namespaces",
    )


@mcp_server.tool()
async def catalog_tables_schema(
    context: Context,
    session_id: str,
    namespace: str | None = None,
    table_names: list[str] | None = None,
    filters: list[str] | None = None,
    max_tables: int | None = 100,
) -> dict:
    """
    MCP Tool: Retrieve catalog table schemas as TABULAR METADATA from a Deephaven Enterprise (Core+) session.

    **Returns**: Schema information formatted as TABULAR DATA where each row represents a column
    in a catalog/database table. This tabular metadata should be displayed as a table to users for easy
    comprehension of catalog table structures.

    This tool retrieves column schemas for tables in the enterprise catalog (database). The catalog contains
    metadata about tables accessible via the `deephaven_enterprise.database` package (the `db` variable).
    You can filter by namespace, specify exact table names, use custom filters, or discover all schemas
    up to the max_tables limit. This is essential for understanding the structure of catalog tables before
    loading them with `db.live_table()` or `db.historical_table()`. Only works with enterprise sessions.

    For more information, see:
    - https://deephaven.io
    - https://docs.deephaven.io/pycoreplus/latest/worker/code/deephaven_enterprise.database.html

    Terminology Note:
    - 'Session' and 'worker' are interchangeable terms - both refer to a running Deephaven instance
    - 'ENTERPRISE' sessions run Deephaven Enterprise (also called 'Core+' or 'CorePlus')
    - This tool only works with enterprise sessions; community sessions do not have catalog tables
    - 'Namespace' refers to a data domain or organizational grouping of tables in the catalog
    - 'Catalog' and 'database' are interchangeable terms - the catalog is the database of available tables
    - 'Schema' and 'meta table' are interchangeable terms - both refer to table metadata

    Table Rendering:
    - **This tool returns TABULAR SCHEMA METADATA that MUST be displayed as a table to users**
    - Each row in the result represents one column from a catalog table
    - The table shows column properties: Name, DataType, IsPartitioning, ComponentType, etc.
    - Present schema data in tabular format (table or grid) for easy comprehension
    - Do NOT present schema data as plain text or unstructured lists

    AI Agent Usage:
    - Use this to understand catalog/database table structures before loading them into a session
    - The catalog is the database of available tables with their schemas
    - Filter by namespace to get schemas for all tables in a specific data domain
    - Specify table_names when you know exactly which tables you need
    - Use filters for complex discovery patterns (e.g., tables containing specific keywords)
    - Default max_tables=100 prevents accidentally fetching thousands of schemas
    - Set max_tables=None only when you intentionally want all schemas (use with caution)
    - Check 'namespace' field in each result to know which domain the table belongs to
    - Use returned schemas to generate correct `db.live_table(namespace, table_name)` calls
    - Individual table failures don't stop processing of other tables (similar to session_tables_schema)
    - Always check 'success' field in each schema result before using the schema data

    Filter Syntax Reference:
    Filters use Deephaven query language with backticks (`) for string literals.
    Multiple filters are combined with AND logic.

    Common Filter Patterns:
        Exact Match:
            - Namespace exact: "Namespace = `market_data`"
            - Table name exact: "TableName = `daily_prices`"

        String Contains (case-sensitive):
            - Namespace contains: "Namespace.contains(`market`)"
            - Table name contains: "TableName.contains(`price`)"

        String Contains (case-insensitive):
            - Namespace: "Namespace.toLowerCase().contains(`market`)"
            - Table name: "TableName.toLowerCase().contains(`price`)"

        Multiple Values (IN):
            - Namespace in list: "Namespace in `market_data`, `reference_data`"
            - Case-insensitive: "Namespace icase in `market_data`, `reference_data`"

        Combining Filters (AND logic):
            filters=["Namespace = `market_data`", "TableName.contains(`price`)"]

    Args:
        context (Context): The MCP context object, required by MCP protocol but not actively used.
        session_id (str): ID of the Deephaven enterprise session to query. Must be an enterprise (Core+) session.
        namespace (str | None, optional): Filter to tables in this specific namespace. If None, searches all namespaces.
                                         Defaults to None.
        table_names (list[str] | None, optional): List of specific table names to retrieve schemas for.
                                                  If None, retrieves schemas for all tables (up to max_tables limit).
                                                  When specified with namespace, only tables in that namespace are considered.
                                                  Defaults to None.
        filters (list[str] | None, optional): List of Deephaven where clause expressions to filter the catalog.
                                             Multiple filters are combined with AND logic. Use backticks (`) for string literals.
                                             Applied before namespace and table_names filtering. Defaults to None.
        max_tables (int | None, optional): Maximum number of table schemas to retrieve. Defaults to 100 for safety.
                                          Set to None to retrieve all matching schemas (use with extreme caution for large catalogs).
                                          This limit is applied after all filtering.

    Returns:
        dict: Structured result object with keys:
            - 'success' (bool): True if the operation completed, False if it failed entirely.
            - 'schemas' (list[dict], optional): List of per-table schema results if operation completed. Each contains:
                - 'success' (bool): True if this table's schema was retrieved successfully
                - 'namespace' (str): Namespace (data domain) the table belongs to
                - 'table' (str): Table name
                - 'schema' (list[dict], optional): List of column definitions (name/type pairs) if successful
                - 'error' (str, optional): Error message if this table's schema retrieval failed
                - 'isError' (bool, optional): Present and True if this table had an error
            - 'count' (int, optional): Number of schemas returned if successful
            - 'is_complete' (bool, optional): True if all matching tables were processed, False if truncated by max_tables
            - 'error' (str, optional): Error message if the entire operation failed.
            - 'isError' (bool, optional): Present and True if this is an error response.

    Error Scenarios:
        - Non-enterprise session: Returns error if session is not an enterprise (Core+) session
        - Invalid session_id: Returns error if session doesn't exist or is not accessible
        - Invalid filters: Returns error if filter syntax is invalid or references non-existent columns
        - Session connection issues: Returns error if unable to communicate with Deephaven server
        - Catalog access error: Returns error if unable to retrieve catalog table
        - Individual table errors: Reported in per-table results, don't stop overall operation

    Performance Considerations:
        - Default max_tables=100 is safe for most use cases
        - Fetching schemas for 1000+ tables can take significant time (several minutes)
        - Use namespace or filters to narrow down the search space
        - Specify exact table_names when you know what you need for fastest results
        - Each schema fetch requires a separate query to the catalog

    Example Successful Response (mixed results):
        {
            'success': True,
            'schemas': [
                {
                    'success': True,
                    'namespace': 'market_data',
                    'table': 'daily_prices',
                    'schema': [{'name': 'Date', 'type': 'LocalDate'}, {'name': 'Price', 'type': 'double'}]
                },
                {
                    'success': False,
                    'namespace': 'market_data',
                    'table': 'missing_table',
                    'error': 'Table not found in catalog',
                    'isError': True
                }
            ],
            'count': 2,
            'is_complete': True
        }

    Example Error Response (total failure):
        {
            'success': False,
            'error': 'Session is not an enterprise (Core+) session',
            'isError': True
        }

    Example Usage:
        # Get schemas for all tables in a namespace (up to 100)
        Tool: catalog_tables_schema
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "namespace": "market_data"
        }

        # Get schemas for specific tables in a namespace
        Tool: catalog_tables_schema
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "namespace": "market_data",
            "table_names": ["daily_prices", "intraday_quotes"]
        }

        # Filter-based discovery across namespaces
        Tool: catalog_tables_schema
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "filters": ["TableName.contains(`price`)"]
        }

        # Get more than 100 schemas (explicit limit)
        Tool: catalog_tables_schema
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "namespace": "market_data",
            "max_tables": 500
        }

        # Get all schemas (requires explicit None, use with extreme caution)
        Tool: catalog_tables_schema
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "max_tables": None
        }
    """
    _LOGGER.info(
        f"[mcp_systems_server:catalog_tables_schema] Invoked: session_id={session_id!r}, "
        f"namespace={namespace!r}, table_names={table_names!r}, filters={filters!r}, max_tables={max_tables}"
    )

    schemas = []

    try:
        # Get and validate enterprise session
        session, error = await _get_enterprise_session(
            "catalog_tables_schema", context, session_id
        )

        if error:
            return error

        session = cast(CorePlusSession, session)  # Type narrowing for mypy

        _LOGGER.info(
            f"[mcp_systems_server:catalog_tables_schema] Session established for enterprise session: '{session_id}'"
        )

        # Build combined filters list
        combined_filters = []
        if filters:
            combined_filters.extend(filters)
        if namespace:
            combined_filters.append(f"Namespace = `{namespace}`")
        if table_names:
            table_names_quoted = ", ".join(f"`{name}`" for name in table_names)
            combined_filters.append(f"TableName in {table_names_quoted}")

        _LOGGER.debug(
            f"[mcp_systems_server:catalog_tables_schema] Combined filters: {combined_filters!r}"
        )

        # Get catalog table with filters
        # Use max_tables as max_rows to limit catalog query and prevent excessive RAM usage
        _LOGGER.debug(
            f"[mcp_systems_server:catalog_tables_schema] Retrieving catalog table from session '{session_id}' "
            f"(max_rows={max_tables})"
        )
        catalog_arrow_table, is_complete_catalog = await queries.get_catalog_table(
            session,
            max_rows=max_tables,  # Limit catalog query to match max_tables
            filters=combined_filters if combined_filters else None,
            distinct_namespaces=False,
        )

        # Convert to list of dicts for easier processing
        catalog_entries = catalog_arrow_table.to_pylist()
        _LOGGER.info(
            f"[mcp_systems_server:catalog_tables_schema] Retrieved {len(catalog_entries)} catalog entries after filtering"
        )

        # is_complete_catalog already reflects whether the catalog was truncated
        is_complete = is_complete_catalog

        _LOGGER.debug(
            f"[mcp_systems_server:catalog_tables_schema] Processing {len(catalog_entries)} catalog entries "
            f"(is_complete={is_complete})"
        )

        # Fetch schema for each catalog entry
        for entry in catalog_entries:
            # These fields are required - let it fail if they're missing
            catalog_namespace = entry["Namespace"]
            catalog_table_name = entry["TableName"]

            _LOGGER.debug(
                f"[mcp_systems_server:catalog_tables_schema] Processing catalog table "
                f"'{catalog_namespace}.{catalog_table_name}'"
            )

            try:
                # Get schema for catalog table (tries historical_table first, then live_table)
                _LOGGER.debug(
                    f"[mcp_systems_server:catalog_tables_schema] Retrieving schema for "
                    f"'{catalog_namespace}.{catalog_table_name}'"
                )
                arrow_meta_table = await queries.get_catalog_meta_table(
                    session, catalog_namespace, catalog_table_name
                )

                # Use helper to format result (include namespace for catalog tables)
                result = _format_meta_table_result(
                    arrow_meta_table, catalog_table_name, namespace=catalog_namespace
                )
                schemas.append(result)

                _LOGGER.info(
                    f"[mcp_systems_server:catalog_tables_schema] Success: Retrieved full schema for "
                    f"'{catalog_namespace}.{catalog_table_name}' ({result['row_count']} columns)"
                )

            except Exception as table_exc:
                _LOGGER.error(
                    f"[mcp_systems_server:catalog_tables_schema] Failed to get schema for "
                    f"'{catalog_namespace}.{catalog_table_name}': {table_exc!r}",
                    exc_info=True,
                )
                schemas.append(
                    {
                        "success": False,
                        "namespace": catalog_namespace,
                        "table": catalog_table_name,
                        "error": str(table_exc),
                        "isError": True,
                    }
                )

        _LOGGER.info(
            f"[mcp_systems_server:catalog_tables_schema] Completed: Retrieved {len(schemas)} schema(s), "
            f"is_complete={is_complete}"
        )

        return {
            "success": True,
            "schemas": schemas,
            "count": len(schemas),
            "is_complete": is_complete,
        }

    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:catalog_tables_schema] Failed for session: '{session_id}', error: {e!r}",
            exc_info=True,
        )
        return {"success": False, "error": str(e), "isError": True}


@mcp_server.tool()
async def catalog_table_sample(
    context: Context,
    session_id: str,
    namespace: str,
    table_name: str,
    max_rows: int | None = 100,
    head: bool = True,
    format: str = "optimize-rendering",
) -> dict:
    r"""
    MCP Tool: Retrieve sample TABULAR DATA from a catalog table in a Deephaven Enterprise (Core+) session.

    **Returns**: Sample table data formatted as TABULAR DATA for display. This tabular data should be
    displayed as a table to users for previewing catalog table contents.

    This tool loads a catalog table (trying historical_table first, then live_table as fallback) and
    retrieves a sample of its data with flexible formatting options. Use this to preview catalog table
    contents before loading the full table into a session. Only works with enterprise sessions.

    **Format Accuracy for AI Agents** (based on empirical research):
    - markdown-kv: 61% accuracy (highest comprehension, more tokens)
    - markdown-table: 55% accuracy (good balance)
    - json-row/json-column: 50% accuracy
    - yaml: 50% accuracy
    - xml: 45% accuracy
    - csv: 44% accuracy (lowest comprehension, fewest tokens)

    For more information, see:
    - https://deephaven.io
    - https://docs.deephaven.io/pycoreplus/latest/worker/code/deephaven_enterprise.database.html

    Terminology Note:
    - 'Session' and 'worker' are interchangeable terms - both refer to a running Deephaven instance
    - 'ENTERPRISE' sessions run Deephaven Enterprise (also called 'Core+' or 'CorePlus')
    - This tool only works with enterprise sessions; community sessions do not have catalog tables
    - 'Namespace' refers to a data domain or organizational grouping of tables in the catalog
    - 'Catalog' and 'database' are interchangeable terms - the catalog is the database of available tables

    Table Rendering:
    - **This tool returns TABULAR SAMPLE DATA that MUST be displayed as a table to users**
    - The 'data' field contains formatted table data ready for display
    - Use 'markdown-table' or 'markdown-kv' formats for best table rendering in AI interfaces
    - Always present the returned data in tabular format (table, grid, or structured rows)
    - Do NOT present table data as plain text or unstructured content

    AI Agent Usage:
    - Use this to preview catalog/database table contents before loading full tables
    - The catalog is the database of available tables with sample data
    - Default max_rows=100 provides safe preview without overwhelming responses
    - Use head=True (default) to get rows from table start, head=False to get from table end
    - Check 'is_complete' to know if the sample represents the entire table
    - Combine with catalog_tables_schema to understand table structure before sampling
    - Use 'optimize-rendering' (default) for best table display in AI interfaces
    - Use 'optimize-accuracy' for highest comprehension (markdown-kv format, more tokens)
    - Check 'format' field in response to know actual format used

    Args:
        context (Context): The MCP context object.
        session_id (str): ID of the Deephaven enterprise session to query.
        namespace (str): The catalog namespace containing the table.
        table_name (str): Name of the catalog table to sample.
        max_rows (int | None, optional): Maximum number of rows to retrieve. Defaults to 100 for safe sampling.
                                         Set to None to retrieve entire table (use with caution for large tables).
        head (bool, optional): Direction of row retrieval. If True (default), retrieve from beginning.
                              If False, retrieve from end (most recent rows for time-series data).
        format (str, optional): Output format selection. Defaults to "optimize-rendering" for best table display.
                               Options:
                               - "optimize-rendering": (DEFAULT) Always use markdown-table (best for AI agent table display)
                               - "optimize-accuracy": Always use markdown-kv (better comprehension, more tokens)
                               - "optimize-cost": Always use csv (fewer tokens, may be harder to parse)
                               - "optimize-speed": Always use json-column (fastest conversion)
                               - "markdown-table": String with pipe-delimited table (| col1 | col2 |\n| --- | --- |\n| val1 | val2 |)
                               - "markdown-kv": String with record headers and key-value pairs (## Record 1\ncol1: val1\ncol2: val2)
                               - "json-row": List of dicts, one per row
                               - "json-column": Dict with column names as keys, value arrays
                               - "csv": String with comma-separated values, includes header row
                               - "yaml": String with YAML-formatted records list
                               - "xml": String with XML records structure

    Returns:
        dict: Structured result object with the following keys:
            - 'success' (bool): Always present. True if sample was retrieved successfully, False on any error.
            - 'namespace' (str, optional): The catalog namespace if successful.
            - 'table_name' (str, optional): Name of the sampled table if successful.
            - 'format' (str, optional): Actual format used for the data if successful. May differ from request when using optimization strategies.
            - 'schema' (list[dict], optional): Array of column definitions if successful. Each dict contains:
                                              {'name': str, 'type': str} describing column name and PyArrow data type.
            - 'row_count' (int, optional): Number of rows in the returned sample if successful.
            - 'is_complete' (bool, optional): True if entire table was retrieved if successful. False if truncated by max_rows.
            - 'data' (list | dict | str, optional): The actual sample data if successful. Type depends on format.
            - 'error' (str, optional): Human-readable error message if retrieval failed. Omitted on success.
            - 'isError' (bool, optional): Present and True only when success=False. Explicit error flag.

    Error Scenarios:
        - Invalid session_id: Returns error if session doesn't exist or is not accessible
        - Community session: Returns error if session is not an enterprise (Core+) session
        - Invalid namespace: Returns error if namespace doesn't exist in the catalog
        - Invalid table_name: Returns error if table doesn't exist in the namespace
        - Invalid format: Returns error if format is not one of the supported options
        - Response too large: Returns error if estimated response would exceed 50MB limit
        - Session connection issues: Returns error if unable to communicate with Deephaven server
        - Table access errors: Returns error if table cannot be accessed via historical_table or live_table

    Performance Considerations:
        - Default max_rows of 100 is safe for previewing catalog tables
        - Use csv format or limit max_rows for very wide tables
        - Default optimize-rendering format provides good table display
        - Response size limit: 50MB maximum to prevent memory issues

    Example Usage:
        # Sample first 100 rows with default format
        Tool: catalog_table_sample
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "namespace": "market_data",
            "table_name": "daily_prices"
        }

        # Sample last 50 rows (most recent for time-series)
        Tool: catalog_table_sample
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "namespace": "market_data",
            "table_name": "trades",
            "max_rows": 50,
            "head": false
        }

        # Sample with CSV format
        Tool: catalog_table_sample
        Parameters: {
            "session_id": "enterprise:prod:analytics",
            "namespace": "reference_data",
            "table_name": "symbols",
            "max_rows": 200,
            "format": "csv"
        }
    """
    _LOGGER.info(
        f"[mcp_systems_server:catalog_table_sample] Invoked: session_id={session_id!r}, "
        f"namespace={namespace!r}, table_name={table_name!r}, max_rows={max_rows}, head={head}, format={format!r}"
    )

    try:
        # Get and validate enterprise session
        session, error = await _get_enterprise_session(
            "catalog_table_sample", context, session_id
        )

        if error:
            return error

        session = cast(CorePlusSession, session)  # Type narrowing for mypy

        _LOGGER.info(
            f"[mcp_systems_server:catalog_table_sample] Session established for enterprise session: '{session_id}'"
        )

        # Get catalog table data using queries module
        _LOGGER.debug(
            f"[mcp_systems_server:catalog_table_sample] Retrieving catalog table data for '{namespace}.{table_name}'"
        )
        arrow_table, is_complete = await queries.get_catalog_table_data(
            session, namespace, table_name, max_rows=max_rows, head=head
        )

        # Check response size before formatting
        row_count = len(arrow_table)
        col_count = len(arrow_table.schema)
        estimated_size = row_count * col_count * ESTIMATED_BYTES_PER_CELL
        size_error = _check_response_size(f"{namespace}.{table_name}", estimated_size)

        if size_error:
            return size_error

        # Build response using helper
        _LOGGER.debug(
            f"[mcp_systems_server:catalog_table_sample] Formatting {row_count} rows in format '{format}'"
        )
        response = _build_table_data_response(
            arrow_table, is_complete, format, table_name=table_name, namespace=namespace
        )

        _LOGGER.info(
            f"[mcp_systems_server:catalog_table_sample] Success: Retrieved {row_count} rows "
            f"from '{namespace}.{table_name}' (is_complete={is_complete}, format={response['format']})"
        )

        return response

    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:catalog_table_sample] Failed for session: '{session_id}', "
            f"namespace: '{namespace}', table: '{table_name}', error: {e!r}",
            exc_info=True,
        )
        return {"success": False, "error": str(e), "isError": True}


def _format_meta_table_result(
    arrow_meta_table: pyarrow.Table,
    table_name: str,
    namespace: str | None = None,
) -> dict:
    """
    Format a PyArrow meta table into a standardized result dictionary.

    This helper eliminates code duplication between session_tables_schema and
    catalog_tables_schema by providing a single place to format metadata results.

    A "meta table" in Deephaven is a table that describes another table's structure.
    Each row in a meta table represents one column from the original table, with
    properties like Name, DataType, IsPartitioning, ComponentType, etc.

    Args:
        arrow_meta_table (pyarrow.Table): The PyArrow meta table containing column metadata.
            Each row describes one column of the original table.
        table_name (str): Name of the table being described.
        namespace (str | None): Optional namespace for catalog tables. If provided (not None),
            it will be included in the result. Session tables should pass None since they
            don't have namespaces. Defaults to None.

    Returns:
        dict: Formatted result with success status and metadata fields. The structure is:
            {
                "success": True,  # Always True for successful formatting
                "table": str,  # Name of the table
                "format": "json-row",  # Data format (always "json-row" = list of dicts)
                "data": list[dict],  # Full metadata rows with all column properties
                "meta_columns": list[dict],  # Schema of the meta table itself (describes "data" structure)
                "row_count": int,  # Number of rows in meta table = number of columns in original table
                "namespace": str  # Only present if namespace parameter was not None (catalog tables)
            }

            Note: The "namespace" field is conditionally included only when the namespace
            parameter is not None. This keeps session table results clean (no namespace field)
            while catalog table results include the namespace for context.

    Example:
        >>> # For a table with 2 columns (Date and Price)
        >>> result = _format_meta_table_result(meta_table, "daily_prices", "market_data")
        >>> result
        {
            "success": True,
            "table": "daily_prices",
            "namespace": "market_data",
            "format": "json-row",
            "data": [
                {"Name": "Date", "DataType": "LocalDate", "IsPartitioning": False},
                {"Name": "Price", "DataType": "double", "IsPartitioning": False}
            ],
            "meta_columns": [
                {"name": "Name", "type": "string"},
                {"name": "DataType", "type": "string"},
                {"name": "IsPartitioning", "type": "bool"}
            ],
            "row_count": 2
        }
    """
    # Convert to full metadata using to_pylist() for complete information
    # to_pylist() returns native Python types (dict, list, str, int, bool, None)
    # which are JSON-serializable for MCP protocol
    meta_data = arrow_meta_table.to_pylist()

    # Extract schema of the meta table itself
    meta_schema = [
        {"name": field.name, "type": str(field.type)}
        for field in arrow_meta_table.schema
    ]

    result = {
        "success": True,
        "table": table_name,
        "format": "json-row",  # Explicit format for AI agent clarity
        "data": meta_data,
        "meta_columns": meta_schema,
        "row_count": len(arrow_meta_table),
    }

    # Only include namespace for catalog tables (where it's meaningful)
    if namespace is not None:
        result["namespace"] = namespace

    return result


async def _check_session_limits(
    session_registry: CombinedSessionRegistry, system_name: str, max_sessions: int
) -> dict | None:
    """Check if session creation is allowed and within limits.

    Args:
        session_registry (CombinedSessionRegistry): The session registry
        system_name (str): Name of the enterprise system
        max_sessions (int): Maximum concurrent sessions allowed

    Returns:
        dict | None: Error response dict if not allowed, None if allowed
    """
    # Check if session creation is disabled
    if max_sessions == 0:
        error_msg = f"Session creation is disabled for system '{system_name}' (max_concurrent_sessions = 0)"
        _LOGGER.error(f"[mcp_systems_server:_check_session_limits] {error_msg}")
        return {"error": error_msg, "isError": True}

    # Check if current session count would exceed the limit
    current_session_count = await session_registry.count_added_sessions(
        SystemType.ENTERPRISE, system_name
    )
    if current_session_count >= max_sessions:
        error_msg = f"Max concurrent sessions ({max_sessions}) reached for system '{system_name}'"
        _LOGGER.error(f"[mcp_systems_server:_check_session_limits] {error_msg}")
        return {"error": error_msg, "isError": True}

    return None


def _generate_session_name_if_none(
    system_config: dict, session_name: str | None
) -> str:
    """Generate a session name if none provided.

    Args:
        system_config (dict): Enterprise system configuration dict
        session_name (str | None): Provided session name or None

    Returns:
        str: Either the provided session_name or auto-generated name
    """
    if session_name is not None:
        return session_name

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    username = system_config.get("username")
    if username:
        generated = f"mcp-{username}-{timestamp}"
    else:
        generated = f"mcp-session-{timestamp}"

    _LOGGER.debug(
        f"[mcp_systems_server:_generate_session_name_if_none] Auto-generated session name: {generated}"
    )
    return generated


async def _check_session_id_available(
    session_registry: CombinedSessionRegistry, session_id: str
) -> dict | None:
    """Check if session ID is available (not already in use).

    Called during session creation to prevent duplicate session IDs.
    This ensures each session has a unique identifier in the registry.

    Args:
        session_registry (CombinedSessionRegistry): The session registry to check
        session_id (str): The session ID to check for availability

    Returns:
        dict | None: Error response dict if session exists, None if available
    """
    try:
        await session_registry.get(session_id)
        # If we got here, session already exists
        error_msg = f"Session '{session_id}' already exists"
        _LOGGER.error(f"[mcp_systems_server:_check_session_id_available] {error_msg}")
        return {"error": error_msg, "isError": True}
    except KeyError:
        return None  # Good - session doesn't exist yet


async def _get_system_config(
    function_name: str, config_manager: ConfigManager, system_name: str
) -> tuple[dict, dict | None]:
    """Get system config from configuration and validate system exists.

    Retrieves the configuration for the specified enterprise system. Returns both
    the system configuration and any error that occurred during retrieval. This is
    a common validation step used by enterprise session management functions.

    Args:
        function_name (str): Name of the calling function for logging purposes.
            Used to create contextual log messages.
        config_manager (ConfigManager): ConfigManager instance to retrieve configuration.
        system_name (str): Name of the enterprise system to look up in the configuration.

    Returns:
        tuple[dict, dict | None]: A tuple containing (system_config, error_dict):
            - system_config (dict): The enterprise system configuration dict if found,
              or an empty dict {} if the system is not found.
            - error_dict (dict | None): Error response dict with 'error' and 'isError'
              keys if the system is not found, or None if successful.

            Success case: ({"url": "...", "username": "...", ...}, None)
            Error case: ({}, {"error": "Enterprise system 'X' not found...", "isError": True})

    Raises:
        Exception: May raise exceptions for unexpected errors such as issues reading
            the configuration file or invalid configuration structure.

    Example:
        >>> config_mgr = ConfigManager()
        >>> system_config, error = await _get_system_config("session_enterprise_create", config_mgr, "prod")
        >>> if error:
        ...     return error  # System not found
        >>> # Use system_config for session creation
    """
    config = await config_manager.get_config()

    try:
        enterprise_systems_config = get_config_section(
            config, ["enterprise", "systems"]
        )
    except KeyError:
        enterprise_systems_config = {}

    if not enterprise_systems_config or system_name not in enterprise_systems_config:
        error_msg = f"Enterprise system '{system_name}' not found in configuration"
        _LOGGER.error(f"[mcp_systems_server:{function_name}] {error_msg}")
        return {}, {"error": error_msg, "isError": True}

    return enterprise_systems_config[system_name], None


@mcp_server.tool()
async def session_enterprise_create(
    context: Context,
    system_name: str,
    session_name: str | None = None,
    heap_size_gb: float | None = None,
    programming_language: str | None = None,
    auto_delete_timeout: int | None = None,
    server: str | None = None,
    engine: str | None = None,
    extra_jvm_args: list[str] | None = None,
    extra_environment_vars: list[str] | None = None,
    admin_groups: list[str] | None = None,
    viewer_groups: list[str] | None = None,
    timeout_seconds: float | None = None,
    session_arguments: dict[str, Any] | None = None,
) -> dict:
    """
    MCP Tool: Create a new enterprise session with configurable parameters.

    Creates a new enterprise session on the specified enterprise system and registers it in the
    session registry for future use. The session is configured using provided parameters or defaults
    from the enterprise system configuration.

    Terminology Note:
    - 'Session' and 'worker' are interchangeable terms - both refer to a running Deephaven instance
    - 'Deephaven Community' and 'Deephaven Core' are interchangeable names for the same product
    - 'Deephaven Enterprise', 'Deephaven Core+', and 'Deephaven CorePlus' are interchangeable names for the same product

    Parameter Resolution Priority (highest to lowest):
    1. Tool parameters provided in this function call
    2. Enterprise system session_creation defaults from configuration
    3. Deephaven server built-in defaults

    AI Agent Usage:
    - Use this tool only when you need to create a new session
    - Check 'success' field and use returned 'session_id' for subsequent operations
    - Sessions have resource limits and may auto-delete after timeout periods
    - Use delete_enterprise_session tool to clean up when done

    Args:
        context (Context): The MCP context object.
        system_name (str): Name of the enterprise system to create the session on.
            Must match a configured enterprise system name.
        session_name (str | None): Name for the new session. If None, auto-generates
            a timestamp-based name like "mcp-{username}-20241126-1130".
        heap_size_gb (float | None): JVM heap size in gigabytes. If None, uses
            config default or Deephaven default.
        programming_language (str | None): Programming language for the session.
            Supported values: "Python" (default) or "Groovy". If None, uses config default or "Python".
        auto_delete_timeout (int | None): Seconds of inactivity before automatic session deletion.
            If None, uses config default or API default (600 seconds).
        server (str | None): Specific server to run session on.
            If None, uses config default or lets Deephaven auto-select.
        engine (str | None): Engine type for the session.
            If None, uses config default or "DeephavenCommunity".
        extra_jvm_args (list[str] | None): Additional JVM arguments for the session.
            If None, uses config default or standard JVM settings.
        extra_environment_vars (list[str] | None): Environment variables for the session in format
            ["NAME=value", ...]. If None, uses config default environment.
        admin_groups (list[str] | None): User groups with administrative permissions on the session.
            If None, uses config default or creator-only access.
        viewer_groups (list[str] | None): User groups with read-only access to session.
            If None, uses config default or creator-only access.
        timeout_seconds (float | None): Maximum time in seconds to wait for session startup.
            If None, uses config default or 60 seconds.
        session_arguments (dict[str, Any] | None): Additional arguments for pydeephaven.Session constructor.
            If None, uses config default or standard session settings.

    Returns:
        dict: Structured response with session creation details.

        Success response:
        {
            "success": True,
            "session_id": "enterprise:prod-system:analytics-session-001",
            "system_name": "prod-system",
            "session_name": "analytics-session-001",
            "configuration": {
                "heap_size_gb": 8.0,
                "auto_delete_timeout_minutes": 60,
                "server": "server-east-1",
                "engine": "DeephavenCommunity"
            }
        }

        Error response:
        {
            "success": False,
            "error": "Max concurrent sessions (5) reached for system 'prod-system'",
            "isError": True
        }

    Validation and Safety:
        - Verifies enterprise system exists and is accessible
        - Checks max_concurrent_sessions limit from configuration
        - Ensures no session ID conflicts in registry
        - Authenticates with enterprise system before creation
        - Provides detailed error messages for troubleshooting

    Common Error Scenarios:
        - System not found: "Enterprise system 'xyz' not found"
        - Session limit reached: "Max concurrent sessions (N) reached"
        - Name conflict: "Session 'enterprise:sys:name' already exists"
        - Authentication failure: "Failed to authenticate with enterprise system"
        - Resource exhaustion: "Insufficient resources to create session"
        - Network issues: "Failed to connect to enterprise system"

    Example Usage:
        # Create session with auto-generated name and all defaults
        Tool: create_enterprise_session
        Parameters: {
            "system_name": "prod-analytics"
        }

        # Create session with custom name
        Tool: create_enterprise_session
        Parameters: {
            "system_name": "prod-analytics",
            "session_name": "my-analysis-session"
        }

        # Create session with custom heap size and timeout
        Tool: create_enterprise_session
        Parameters: {
            "system_name": "prod-analytics",
            "session_name": "large-data-session",
            "heap_size_gb": 16.0,
            "auto_delete_timeout": 3600
        }

        # Create Groovy session with custom JVM args
        Tool: create_enterprise_session
        Parameters: {
            "system_name": "prod-analytics",
            "programming_language": "Groovy",
            "extra_jvm_args": ["-Xmx8g", "-XX:+UseG1GC"]
        }

        # Create session with environment variables
        Tool: create_enterprise_session
        Parameters: {
            "system_name": "prod-analytics",
            "extra_environment_vars": ["VAR1=/mnt/data", "VAR2=DEBUG"]
        }

        # Create session with specific server and permissions
        Tool: create_enterprise_session
        Parameters: {
            "system_name": "prod-analytics",
            "server": "server-east-1",
            "admin_groups": ["data-engineers"],
            "viewer_groups": ["analysts", "data-scientists"]
        }
    """
    _LOGGER.info(
        f"[mcp_systems_server:session_enterprise_create] Invoked: "
        f"system_name={system_name!r}, session_name={session_name!r}, "
        f"heap_size_gb={heap_size_gb}, auto_delete_timeout={auto_delete_timeout}, "
        f"server={server!r}, engine={engine!r}, "
        f"extra_jvm_args={extra_jvm_args}, extra_environment_vars={extra_environment_vars}, "
        f"admin_groups={admin_groups}, viewer_groups={viewer_groups}, "
        f"timeout_seconds={timeout_seconds}, session_arguments={session_arguments}, "
        f"programming_language={programming_language}"
    )

    result: dict[str, object] = {"success": False}

    try:
        # Get config and session registry
        config_manager: ConfigManager = context.request_context.lifespan_context[
            "config_manager"
        ]
        session_registry: CombinedSessionRegistry = (
            context.request_context.lifespan_context["session_registry"]
        )

        # Get enterprise system configuration
        system_config, error_response = await _get_system_config(
            "create_enterprise_session", config_manager, system_name
        )
        if error_response:
            result.update(error_response)
            return result
        session_creation_config = system_config.get("session_creation", {})
        max_sessions = session_creation_config.get(
            "max_concurrent_sessions", DEFAULT_MAX_CONCURRENT_SESSIONS
        )

        # Check session limits (both enabled and count)
        error_response = await _check_session_limits(
            session_registry, system_name, max_sessions
        )
        if error_response:
            result.update(error_response)
            return result

        # Generate session name if not provided
        session_name = _generate_session_name_if_none(system_config, session_name)

        # Create session ID and check for conflicts
        session_id = BaseItemManager.make_full_name(
            SystemType.ENTERPRISE, system_name, session_name
        )
        error_response = await _check_session_id_available(session_registry, session_id)
        if error_response:
            result.update(error_response)
            return result

        # Resolve configuration parameters
        defaults = session_creation_config.get("defaults", {})
        resolved_config = _resolve_session_parameters(
            heap_size_gb,
            auto_delete_timeout,
            server,
            engine,
            extra_jvm_args,
            extra_environment_vars,
            admin_groups,
            viewer_groups,
            timeout_seconds,
            session_arguments,
            programming_language,
            defaults,
        )

        _LOGGER.debug(
            f"[mcp_systems_server:session_enterprise_create] Resolved configuration: {resolved_config}"
        )

        # Get enterprise factory and create session
        enterprise_registry = await session_registry.enterprise_registry()
        factory_manager = await enterprise_registry.get(system_name)
        factory = await factory_manager.get()

        # Create configuration transformer based on programming language
        configuration_transformer = None
        programming_lang = resolved_config["programming_language"]
        if programming_lang and programming_lang.lower() != "python":

            def language_transformer(config: Any) -> Any:
                config.scriptLanguage = programming_lang
                return config

            configuration_transformer = language_transformer

        _LOGGER.debug(
            f"[mcp_systems_server:session_enterprise_create] Creating session with parameters: "
            f"name={session_name}, heap_size_gb={resolved_config['heap_size_gb']}, "
            f"auto_delete_timeout={resolved_config['auto_delete_timeout']}, "
            f"server={resolved_config['server']}, engine={resolved_config['engine']}, "
            f"programming_language={programming_lang}"
        )

        # Create the session
        session = await factory.connect_to_new_worker(
            name=session_name,
            heap_size_gb=resolved_config["heap_size_gb"],
            auto_delete_timeout=resolved_config["auto_delete_timeout"],
            server=resolved_config["server"],
            engine=resolved_config["engine"],
            extra_jvm_args=resolved_config["extra_jvm_args"],
            extra_environment_vars=resolved_config["extra_environment_vars"],
            admin_groups=resolved_config["admin_groups"],
            viewer_groups=resolved_config["viewer_groups"],
            timeout_seconds=resolved_config["timeout_seconds"],
            configuration_transformer=configuration_transformer,
            session_arguments=resolved_config["session_arguments"],
        )

        # Create an EnterpriseSessionManager and add to registry
        async def creation_function(source: str, name: str) -> CorePlusSession:
            return session

        enterprise_session_manager = EnterpriseSessionManager(
            source=system_name,
            name=session_name,
            creation_function=creation_function,
        )
        session_id = enterprise_session_manager.full_name

        # Add to session registry
        await session_registry.add_session(enterprise_session_manager)

        _LOGGER.info(
            f"[mcp_systems_server:session_enterprise_create] Successfully created session "
            f"'{session_name}' on system '{system_name}' with session ID '{session_id}'"
        )

        result.update(
            {
                "success": True,
                "session_id": session_id,
                "system_name": system_name,
                "session_name": session_name,
                "configuration": {
                    "heap_size_gb": resolved_config["heap_size_gb"],
                    "auto_delete_timeout": resolved_config["auto_delete_timeout"],
                    "server": resolved_config["server"],
                    "engine": resolved_config["engine"],
                },
            }
        )

    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:session_enterprise_create] Failed to create session "
            f"'{session_name}' on system '{system_name}': {e!r}",
            exc_info=True,
        )
        result["error"] = str(e)
        result["isError"] = True

    return result


def _resolve_session_parameters(
    heap_size_gb: float | None,
    auto_delete_timeout: int | None,
    server: str | None,
    engine: str | None,
    extra_jvm_args: list[str] | None,
    extra_environment_vars: list[str] | None,
    admin_groups: list[str] | None,
    viewer_groups: list[str] | None,
    timeout_seconds: float | None,
    session_arguments: dict[str, Any] | None,
    programming_language: str | None,
    defaults: dict,
) -> dict:
    """Resolve session parameters with priority: tool param -> config default -> API default.

    Args:
        heap_size_gb (float | None): Tool parameter value for JVM heap size in GB.
        auto_delete_timeout (int | None): Tool parameter value for session timeout in seconds.
        server (str | None): Tool parameter value for target server.
        engine (str | None): Tool parameter value for engine type.
        extra_jvm_args (list[str] | None): Tool parameter value for additional JVM arguments.
        extra_environment_vars (list[str] | None): Tool parameter value for environment variables.
        admin_groups (list[str] | None): Tool parameter value for admin user groups.
        viewer_groups (list[str] | None): Tool parameter value for viewer user groups.
        timeout_seconds (float | None): Tool parameter value for session startup timeout.
        session_arguments (dict[str, Any] | None): Tool parameter value for pydeephaven.Session constructor.
        programming_language (str | None): Tool parameter value for session language ("Python" or "Groovy").
        defaults (dict): Configuration defaults dictionary from session_creation config.

    Returns:
        dict: Resolved configuration with all parameters using priority order.
    """
    return {
        "heap_size_gb": heap_size_gb or defaults.get("heap_size_gb"),
        "auto_delete_timeout": (
            auto_delete_timeout
            if auto_delete_timeout is not None
            else defaults.get("auto_delete_timeout")
        ),
        "server": server or defaults.get("server"),
        "engine": engine or defaults.get("engine", "DeephavenCommunity"),
        "extra_jvm_args": extra_jvm_args or defaults.get("extra_jvm_args"),
        "extra_environment_vars": extra_environment_vars
        or defaults.get("extra_environment_vars"),
        "admin_groups": admin_groups or defaults.get("admin_groups"),
        "viewer_groups": viewer_groups or defaults.get("viewer_groups"),
        "timeout_seconds": (
            timeout_seconds
            if timeout_seconds is not None
            else defaults.get("timeout_seconds", 60)
        ),
        "session_arguments": session_arguments or defaults.get("session_arguments"),
        "programming_language": programming_language
        or defaults.get("programming_language", "Python"),
    }


@mcp_server.tool()
async def session_enterprise_delete(
    context: Context,
    system_name: str,
    session_name: str,
) -> dict:
    """
    MCP Tool: Delete an existing enterprise session.

    Removes an enterprise session from the specified enterprise system and removes it from the
    session registry. The session becomes inaccessible for future operations.

    Terminology Note:
    - 'Session' and 'worker' are interchangeable terms - both refer to a running Deephaven instance
    - 'Deephaven Community' and 'Deephaven Core' are interchangeable names for the same product
    - 'Deephaven Enterprise', 'Deephaven Core+', and 'Deephaven CorePlus' are interchangeable names for the same product

    AI Agent Usage:
    - Use this tool to clean up sessions when no longer needed
    - Check 'success' field to verify deletion completed
    - This operation is irreversible - deleted sessions cannot be recovered
    - Session will no longer be accessible via other MCP tools after deletion

    Args:
        context (Context): The MCP context object.
        system_name (str): Name of the enterprise system containing the session.
            Must match a configured enterprise system name.
        session_name (str): Name of the session to delete. Must be an existing session.

    Returns:
        dict: Structured response with deletion details.

        Success response:
        {
            "success": True,
            "session_id": "enterprise:prod-system:analytics-session-001",
            "system_name": "prod-system",
            "session_name": "analytics-session-001"
        }

        Error response:
        {
            "success": False,
            "error": "Session 'enterprise:prod-system:nonexistent-session' not found",
            "isError": True
        }

    Validation and Safety:
        - Verifies enterprise system exists in configuration
        - Checks that the specified session exists in registry
        - Properly closes the session before removal
        - Removes session from registry to prevent future access
        - Provides detailed error messages for troubleshooting

    Common Error Scenarios:
        - System not found: "Enterprise system 'xyz' not found"
        - Session not found: "Session 'enterprise:sys:session' not found"
        - Already deleted: "Session 'enterprise:sys:session' not found"
        - Close failure: "Failed to close session"
        - Registry error: "Failed to remove session from registry"

    Note:
        - This operation is irreversible - deleted sessions cannot be recovered
        - Any running queries or tables in the session will be lost
        - Other connections to the same session will lose access
        - Use with caution in production environments
    """
    _LOGGER.info(
        f"[mcp_systems_server:session_enterprise_delete] Invoked: "
        f"system_name={system_name!r}, session_name={session_name!r}"
    )

    result: dict[str, object] = {"success": False}

    try:
        # Get config and session registry
        config_manager: ConfigManager = context.request_context.lifespan_context[
            "config_manager"
        ]
        session_registry: CombinedSessionRegistry = (
            context.request_context.lifespan_context["session_registry"]
        )

        # Verify enterprise system exists in configuration
        _, error_response = await _get_system_config(
            "delete_enterprise_session", config_manager, system_name
        )
        if error_response:
            result.update(error_response)
            return result

        # Create expected session ID
        session_id = BaseItemManager.make_full_name(
            SystemType.ENTERPRISE, system_name, session_name
        )

        _LOGGER.debug(
            f"[mcp_systems_server:session_enterprise_delete] Looking for session '{session_id}'"
        )

        # Check if session exists in registry
        try:
            session_manager = await session_registry.get(session_id)
        except KeyError:
            error_msg = f"Session '{session_id}' not found"
            _LOGGER.error(f"[mcp_systems_server:session_enterprise_delete] {error_msg}")
            result["error"] = error_msg
            result["isError"] = True
            return result

        # Verify it's an EnterpriseSessionManager (safety check)
        if not isinstance(session_manager, EnterpriseSessionManager):
            error_msg = f"Session '{session_id}' is not an enterprise session"
            _LOGGER.error(f"[mcp_systems_server:session_enterprise_delete] {error_msg}")
            result["error"] = error_msg
            result["isError"] = True
            return result

        _LOGGER.debug(
            f"[mcp_systems_server:session_enterprise_delete] Found enterprise session manager for '{session_id}'"
        )

        # Close the session if it's active
        try:
            _LOGGER.debug(
                f"[mcp_systems_server:session_enterprise_delete] Closing session '{session_id}'"
            )
            await session_manager.close()
            _LOGGER.debug(
                f"[mcp_systems_server:session_enterprise_delete] Successfully closed session '{session_id}'"
            )
        except Exception as e:
            _LOGGER.warning(
                f"[mcp_systems_server:session_enterprise_delete] Failed to close session '{session_id}': {e}"
            )
            # Continue with removal even if close failed

        # Remove from session registry
        try:
            removed_manager = await session_registry.remove_session(session_id)
            if removed_manager is None:
                error_msg = (
                    f"Session '{session_id}' was not found in registry during removal"
                )
                _LOGGER.warning(
                    f"[mcp_systems_server:session_enterprise_delete] {error_msg}"
                )
            else:
                _LOGGER.debug(
                    f"[mcp_systems_server:session_enterprise_delete] Removed session '{session_id}' from registry"
                )

        except Exception as e:
            error_msg = f"Failed to remove session '{session_id}' from registry: {e}"
            _LOGGER.error(f"[mcp_systems_server:session_enterprise_delete] {error_msg}")
            result["error"] = error_msg
            result["isError"] = True
            return result

        _LOGGER.info(
            f"[mcp_systems_server:session_enterprise_delete] Successfully deleted session "
            f"'{session_name}' from system '{system_name}' (session ID: '{session_id}')"
        )

        result.update(
            {
                "success": True,
                "session_id": session_id,
                "system_name": system_name,
                "session_name": session_name,
            }
        )

    except Exception as e:
        _LOGGER.error(
            f"[mcp_systems_server:session_enterprise_delete] Failed to delete session "
            f"'{session_name}' from system '{system_name}': {e!r}",
            exc_info=True,
        )
        result["error"] = str(e)
        result["isError"] = True

    return result


# =============================================================================
# TODO: Future MCP Tools to Implement
# =============================================================================

# TODO: Implement session_community_create (if supported)
# @mcp_server.tool()
# async def session_community_create(
#     context: Context,
#     session_name: str,
#     script_path: str | None = None,
# ) -> dict:
#     """
#     MCP Tool: Create a new Deephaven Community (Core) session.
#
#     Creates a new community session if the configuration supports it.
#     Note: Community session creation may not be supported in all deployments.
#
#     Terminology Note:
#     - 'Session' and 'worker' are interchangeable terms for a running Deephaven instance
#     - 'COMMUNITY' sessions run Deephaven Community (also called 'Core')
#
#     Args:
#         context: MCP context
#         session_name: Name for the new session
#         script_path: Optional initialization script path
#
#     Returns:
#         dict: Creation result with session_id and status
#     """
#     pass


# TODO: Implement session_community_delete (if supported)
# @mcp_server.tool()
# async def session_community_delete(
#     context: Context,
#     session_id: str,
# ) -> dict:
#     """
#     MCP Tool: Delete a Deephaven Community (Core) session.
#
#     Deletes an existing community session if the configuration supports it.
#     Note: Community session deletion may not be supported in all deployments.
#
#     Terminology Note:
#     - 'Session' and 'worker' are interchangeable terms for a running Deephaven instance
#     - 'COMMUNITY' sessions run Deephaven Community (also called 'Core')
#
#     Args:
#         context: MCP context
#         session_id: ID of the session to delete
#
#     Returns:
#         dict: Deletion result with success status
#     """
#     pass
