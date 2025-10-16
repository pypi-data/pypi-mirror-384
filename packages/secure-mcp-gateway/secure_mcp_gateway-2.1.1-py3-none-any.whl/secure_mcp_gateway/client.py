"""MCP Gateway client module."""

import hashlib
import json
import sys
import threading
import time
from datetime import datetime

import redis as external_cache_server
from mcp import ClientSession, StdioServerParameters

# https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/client/stdio/__init__.py
from mcp.client.stdio import stdio_client

from secure_mcp_gateway.services.oauth.integration import (
    inject_oauth_into_args,
    inject_oauth_into_env,
    prepare_oauth_for_server,
)
from secure_mcp_gateway.utils import get_common_config, logger
from secure_mcp_gateway.version import __version__

logger.info(f"Initializing Enkrypt Secure MCP Gateway Client Module v{__version__}")

common_config = get_common_config()

ENKRYPT_LOG_LEVEL = common_config.get("enkrypt_log_level", "INFO").lower()
IS_DEBUG_LOG_LEVEL = ENKRYPT_LOG_LEVEL == "debug"

# --- Cache Configuration ---
ENKRYPT_MCP_USE_EXTERNAL_CACHE = common_config.get(
    "enkrypt_mcp_use_external_cache", False
)
ENKRYPT_CACHE_HOST = common_config.get("enkrypt_cache_host", "localhost")
ENKRYPT_CACHE_PORT = int(common_config.get("enkrypt_cache_port", "6379"))
ENKRYPT_CACHE_DB = int(common_config.get("enkrypt_cache_db", "0"))
ENKRYPT_CACHE_PASSWORD = common_config.get("enkrypt_cache_password", None)

# Cache expiration times (in hours)
ENKRYPT_TOOL_CACHE_EXPIRATION = int(
    common_config.get("enkrypt_tool_cache_expiration", 4)
)  # 4 hours
ENKRYPT_GATEWAY_CACHE_EXPIRATION = int(
    common_config.get("enkrypt_gateway_cache_expiration", 24)
)  # 24 hours (1 day)

local_cache = {}
local_cache_lock = threading.Lock()

# Add local registries for gateway config and servers
local_key_map = {}
local_server_registry = {}
local_gateway_config_registry = set()


# --- Cache connection ---
def initialize_cache():
    """
    Initializes and tests the connection to the Redis cache server.

    This function creates a Redis client instance with the configured connection parameters
    and verifies the connection is working. If external cache is disabled, it returns None.

    Returns:
        Redis: A configured Redis client instance if external cache is enabled
        None: If external cache is disabled or connection fails

    Raises:
        ConnectionError: If unable to connect to the Redis server when external cache is enabled
    """
    # Initialize Cache client
    cache_client = external_cache_server.Redis(
        host=ENKRYPT_CACHE_HOST,
        port=ENKRYPT_CACHE_PORT,
        db=ENKRYPT_CACHE_DB,
        password=ENKRYPT_CACHE_PASSWORD,
        decode_responses=True,  # Automatically decode responses to strings
    )

    # Test Cache connection
    try:
        cache_client.ping()
        logger.info(
            f"[external_cache] Successfully connected to External Cache at {ENKRYPT_CACHE_HOST}:{ENKRYPT_CACHE_PORT}"
        )
    except external_cache_server.ConnectionError as e:
        logger.error(f"[external_cache] Failed to connect to External Cache: {e}")
        logger.error(
            "[external_cache] Exiting as External Cache is required for this gateway"
        )
        sys.exit(1)  # Exit if External Cache is unavailable

    return cache_client


# --- Cache key patterns with hashing ---
def hash_key(key):
    """
    Creates an MD5 hash of the given key for secure cache storage.

    Args:
        key (str): The key to be hashed

    Returns:
        str: MD5 hash of the input key
    """
    return hashlib.md5(key.encode()).hexdigest()


def get_server_hashed_key(id, server_name):
    """
    Generates a hashed cache key for server tools.


    Args:
        id (str): ID includes project_id, user_id, and mcp_config_id context.
        server_name (str): Name of the server

    Returns:
        str: Hashed cache key for the server tools
    """
    raw_key = f"{id}-{server_name}-tools"
    return hash_key(raw_key)


def get_gateway_config_hashed_key(id):
    """
    Generates a hashed cache key for gateway configuration.

    Args:
        id (str): The ID of the Gateway or User

    Returns:
        str: Hashed cache key for the gateway configuration
    """
    raw_key = f"{id}-mcp-config"
    return hash_key(raw_key)


def get_hashed_key(key):
    """
    Generates a hashed cache key for key to gateway/user ID mapping.

    Args:
        key (str): The Gateway/API key

    Returns:
        str: Hashed cache key for the API key mapping
    """
    raw_key = f"gateway_key-{key}"
    return hash_key(raw_key)


# --- Registry cache keys for gateway/user-server and gateway/user tracking ---
def get_gateway_servers_registry_hashed_key(id):
    """
    Generates a hashed cache key for the servers registry.

    Args:
        id (str): The ID of the Gateway or User
    Returns:
        str: Hashed cache key for the gateway/user's servers registry
    """
    return hash_key(f"registry:{id}:servers")


def get_gateway_registry_hashed_key():
    """
    Generates a hashed cache key for the global gateway/user registry.
    Returns:
        str: Hashed cache key for the gateway/user registry
    """
    return hash_key("registry:gateway/user")


# --- Tool forwarding function ---
# This discovers tools and also invokes a specific tool if tool_name is provided
async def get_server_metadata_only(server_name, gateway_config=None):
    """
    Gets only server metadata (description, name, version) without discovering tools.

    This function is used for config servers that already have tools defined,
    but we need to get their dynamic description for validation.

    Args:
        server_name (str): Name of the server
        gateway_config (dict): Gateway/user's configuration containing server details

    Returns:
        dict: Server metadata including description, name, and version
    """
    if not gateway_config:
        logger.error("[get_server_metadata_only] Error: No gateway_config provided")
        raise ValueError("No gateway configuration provided")

    mcp_config = gateway_config.get("mcp_config", [])
    server_entry = next(
        (s for s in mcp_config if s.get("server_name") == server_name), None
    )
    if not server_entry:
        raise ValueError(f"No config found for server: {server_name}")

    config = server_entry["config"]
    command = config["command"]
    command_args = config["args"]
    env = config.get("env", None)

    logger.info(
        f"[get_server_metadata_only] Getting metadata for server: {server_name}"
    )

    # Prepare OAuth for this server if configured
    # Extract project_id and mcp_config_id from gateway_config
    project_id = gateway_config.get("project_id")
    mcp_config_id = gateway_config.get("mcp_config_id")

    oauth_data, oauth_error = await prepare_oauth_for_server(
        server_name=server_name,
        server_entry=server_entry,
        config_id=mcp_config_id,
        project_id=project_id,
    )

    if oauth_error:
        logger.error(
            f"[get_server_metadata_only] OAuth preparation failed for {server_name}: {oauth_error}"
        )
        # Continue without OAuth - let the server handle authentication failure
    elif oauth_data:
        logger.info(
            f"[get_server_metadata_only] OAuth configured for {server_name}, injecting credentials"
        )
        # Inject OAuth environment variables
        env = inject_oauth_into_env(env, oauth_data)
        # Inject OAuth header arguments for remote servers
        command_args = inject_oauth_into_args(command_args, oauth_data)

    if IS_DEBUG_LOG_LEVEL:
        logger.debug(f"[get_server_metadata_only] Command: {command}")
        logger.debug(f"[get_server_metadata_only] Command args: {command_args}")
        # Mask sensitive environment variables
        from secure_mcp_gateway.utils import mask_sensitive_data

        masked_env = mask_sensitive_data(env or {}) if env else None
        logger.debug(f"[get_server_metadata_only] Env: {masked_env}")

    async with stdio_client(
        StdioServerParameters(command=command, args=command_args, env=env)
    ) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize and capture server metadata ONLY
            init_result = await session.initialize()

            # Extract server description from initialization response
            server_info = getattr(init_result, "serverInfo", {})
            if hasattr(server_info, "description"):
                server_description = server_info.description
            else:
                server_description = getattr(server_info, "description", "")

            if hasattr(server_info, "name"):
                server_name_from_server = server_info.name
            else:
                server_name_from_server = getattr(server_info, "name", "unknown")

            if hasattr(server_info, "version"):
                server_version = server_info.version
            else:
                server_version = getattr(server_info, "version", "unknown")

            logger.info(
                f"[get_server_metadata_only] Connected successfully to {server_name}"
            )
            logger.info("[get_server_metadata_only] 🔍 Dynamic Server Metadata:")
            logger.info(
                f"[get_server_metadata_only]   📝 Description: '{server_description}'"
            )
            logger.info(
                f"[get_server_metadata_only]   🏷️  Name: '{server_name_from_server}'"
            )
            logger.info(f"[get_server_metadata_only]   📦 Version: '{server_version}'")

            # Return only metadata, NO tool discovery
            return {
                "server_metadata": {
                    "description": server_description,
                    "name": server_name_from_server,
                    "version": server_version,
                }
            }


async def forward_tool_call(server_name, tool_name, args=None, gateway_config=None):
    """
    Forwards tool calls to the appropriate MCP server.

    This function handles both tool discovery (when tool_name is None) and tool invocation.
    It uses the gateway/user's configuration to determine the correct server and connection details.

    Args:
        server_name (str): Name of the server to call
        tool_name (str): Name of the tool to call (None for discovery)
        args (dict, optional): Arguments to pass to the tool
        gateway_config (dict): Gateway/user's configuration containing server details

    Returns:
        dict/ListToolsResult: Tool discovery results or tool call response

    Raises:
        ValueError: If gateway_config is missing or server not found
    """
    if not gateway_config:
        logger.error("[forward_tool_call] Error: No gateway_config provided")
        raise ValueError("No gateway configuration provided")

    mcp_config = gateway_config.get("mcp_config", [])
    server_entry = next(
        (s for s in mcp_config if s.get("server_name") == server_name), None
    )
    if not server_entry:
        raise ValueError(f"No config found for server: {server_name}")

    config = server_entry["config"]
    command = config["command"]
    command_args = config["args"]
    env = config.get("env", None)

    logger.info(
        f"[forward_tool_call] Starting tool call for server: {server_name} and tool: {tool_name}"
    )

    # Prepare OAuth for this server if configured
    # Extract project_id and mcp_config_id from gateway_config
    project_id = gateway_config.get("project_id")
    mcp_config_id = gateway_config.get("mcp_config_id")

    oauth_data, oauth_error = await prepare_oauth_for_server(
        server_name=server_name,
        server_entry=server_entry,
        config_id=mcp_config_id,
        project_id=project_id,
    )

    if oauth_error:
        logger.error(
            f"[forward_tool_call] OAuth preparation failed for {server_name}: {oauth_error}"
        )
        # Continue without OAuth - let the server handle authentication failure
    elif oauth_data:
        logger.info(
            f"[forward_tool_call] OAuth configured for {server_name}, injecting credentials"
        )
        # Inject OAuth environment variables
        env = inject_oauth_into_env(env, oauth_data)
        # Inject OAuth header arguments for remote servers
        command_args = inject_oauth_into_args(command_args, oauth_data)

    if IS_DEBUG_LOG_LEVEL:
        logger.debug(f"[forward_tool_call] Command: {command}")
        logger.debug(f"[forward_tool_call] Command args: {command_args}")
        # Mask sensitive environment variables
        from secure_mcp_gateway.utils import mask_sensitive_data

        masked_env = mask_sensitive_data(env or {}) if env else None
        logger.debug(f"[forward_tool_call] Env: {masked_env}")

    async with stdio_client(
        StdioServerParameters(command=command, args=command_args, env=env)
    ) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize and capture server metadata
            init_result = await session.initialize()

            # Extract server description from initialization response
            # InitializeResult is a Pydantic model, so we access attributes directly
            server_info = getattr(init_result, "serverInfo", {})
            if hasattr(server_info, "description"):
                server_description = server_info.description
            else:
                server_description = getattr(server_info, "description", "")

            if hasattr(server_info, "name"):
                server_name_from_server = server_info.name
            else:
                server_name_from_server = getattr(server_info, "name", "unknown")

            if hasattr(server_info, "version"):
                server_version = server_info.version
            else:
                server_version = getattr(server_info, "version", "unknown")

            # Store the dynamic server metadata for later use
            session._server_description = server_description
            session._server_name = server_name_from_server
            session._server_version = server_version
            session._server_info = server_info

            logger.info(f"[forward_tool_call] Connected successfully to {server_name}")
            logger.info("[forward_tool_call] 🔍 Dynamic Server Metadata:")
            logger.info(f"[forward_tool_call]   📝 Description: '{server_description}'")
            logger.info(f"[forward_tool_call]   🏷️  Name: '{server_name_from_server}'")
            logger.info(f"[forward_tool_call]   📦 Version: '{server_version}'")

            # If tool_name is None, this is a discovery request
            if tool_name is None:
                logger.info(
                    "[forward_tool_call] Starting tool discovery as tool_name is None"
                )
                # Request tool listing from the MCP server
                tools_result = await session.list_tools()
                try:
                    # Safely print the tools result to avoid async context issues
                    tools_summary = f"[forward_tool_call] Discovered {len(getattr(tools_result or {}, 'tools', []))} tools for {server_name}"
                    logger.info(tools_summary)
                    if IS_DEBUG_LOG_LEVEL and tools_result is not None:
                        logger.debug(
                            f"[forward_tool_call] Tool details for {server_name}: {tools_result}"
                        )
                except Exception as e:
                    logger.error(
                        f"[forward_tool_call] Tools discovered for {server_name}, but encountered error when printing details: {e}"
                    )

                # Return tools result with dynamic server metadata
                return {
                    "tools": tools_result,
                    "server_metadata": {
                        "description": server_description,
                        "name": server_name_from_server,
                        "version": server_version,
                        "server_info": server_info,
                    },
                }

            # Normal tool call
            logger.info(f"[forward_tool_call] Calling specific tool: {tool_name}")
            return await session.call_tool(tool_name, arguments=args)


# --- Cache management functions ---


def set_local_cache(key, value, expires_in_seconds):
    """
    Stores a value in the local in-memory cache with expiration.

    Args:
        key (str): The cache key
        value: The value to cache
        expires_in_seconds (int): Time in seconds until the cache entry expires
    """
    expires_at = time.time() + expires_in_seconds
    with local_cache_lock:
        local_cache[key] = (value, expires_at)


def get_local_cache(key):
    """
    Retrieves a value from the local in-memory cache.

    Args:
        key (str): The cache key

    Returns:
        tuple: (value, expiration_time) if found and not expired, None otherwise
    """
    with local_cache_lock:
        item = local_cache.get(key)
        if not item:
            return None
        value, expires_at = item
        if time.time() > expires_at:
            del local_cache[key]
            return None
        return value, expires_at


def get_cached_tools(cache_client, id, server_name):
    """
    Retrieves cached tools for a specific gateway/user and server.

    Args:
        cache_client: The cache client instance
        id (str): ID of the Gateway or User
        server_name (str): Name of the server

    Returns:
        tuple: (tools_data, expiration_time) if found and not expired, None otherwise
    """
    key = get_server_hashed_key(id, server_name)
    if not ENKRYPT_MCP_USE_EXTERNAL_CACHE:
        return get_local_cache(key)

    if cache_client is None:
        return None

    cached_data = cache_client.get(key)
    if not cached_data:
        return None
    try:
        tool_data = json.loads(cached_data)
        if IS_DEBUG_LOG_LEVEL:
            logger.debug(
                f"[external_cache] Using cached tools for id '{id}', server '{server_name}' with key hash: {key}"
            )
        return tool_data
    except json.JSONDecodeError:
        logger.error(
            f"[external_cache] Error deserializing tools cache for hash key: {key}"
        )
        return None


def cache_tools(cache_client, id, server_name, tools):
    """
    Caches tools for a specific gateway/user and server.

    Args:
        cache_client: The cache client instance
        id (str): ID of the Gateway or User
        server_name (str): Name of the server
        tools: The tools data to cache
    """
    expires_in_seconds = int(ENKRYPT_TOOL_CACHE_EXPIRATION * 3600)
    key = get_server_hashed_key(id, server_name)
    if not ENKRYPT_MCP_USE_EXTERNAL_CACHE:
        set_local_cache(key, tools, expires_in_seconds)
        # Also set the server name in the local_server_registry as set of server in id
        if id not in local_server_registry:
            local_server_registry[id] = set()
        local_server_registry[id].add(server_name)
        return

    if cache_client is None:
        return

    raw_key = f"{id}-{server_name}-tools"  # For logging only

    # Convert ListToolsResult to a serializable format if needed
    if hasattr(tools, "__class__") and tools.__class__.__name__ == "ListToolsResult":
        # Extract data from ListToolsResult into a serializable dictionary
        serializable_tools = {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema,
                }
                for tool in getattr(tools, "tools", [])
            ]
        }
        # Add any other attributes that might be useful
        serialized_data = json.dumps(serializable_tools)
    else:
        # Try to serialize directly
        try:
            serialized_data = json.dumps(tools)
        except TypeError as e:
            logger.error(f"[external_cache] Warning: Cannot serialize tools - {e}")
            logger.error("[external_cache] Using simplified tool representation")

            # Fall back to a simplified format if serialization fails
            # This handles cases where tools has complex objects inside
            if (
                isinstance(tools, dict)
                and "tools" in tools
                and isinstance(tools["tools"], list)
            ):
                # Handle case where tools is a dict with a tools list
                simplified = {
                    "tools": [
                        {
                            "name": t.get("name")
                            if isinstance(t, dict)
                            else getattr(t, "name", str(t)),
                            "description": t.get("description")
                            if isinstance(t, dict)
                            else getattr(t, "description", ""),
                            "inputSchema": t.get("inputSchema")
                            if isinstance(t, dict)
                            else getattr(t, "inputSchema", {}),
                        }
                        for t in tools["tools"]
                    ]
                }
            elif hasattr(tools, "__iter__") and not isinstance(tools, (str, bytes)):
                # Handle case where tools is an iterable (list, etc.)
                simplified = {
                    "tools": [
                        {
                            "name": t.get("name")
                            if isinstance(t, dict)
                            else getattr(t, "name", str(t)),
                            "description": t.get("description")
                            if isinstance(t, dict)
                            else getattr(t, "description", ""),
                            "inputSchema": t.get("inputSchema")
                            if isinstance(t, dict)
                            else getattr(t, "inputSchema", {}),
                        }
                        for t in tools
                    ]
                }
            else:
                # Fall back to an empty dict if we can't make sense of the structure
                simplified = {"tools": []}

            serialized_data = json.dumps(simplified)

    # Store in External Cache with expiration
    cache_client.setex(key, expires_in_seconds, serialized_data)

    if IS_DEBUG_LOG_LEVEL:
        expiration_time = datetime.fromtimestamp(
            time.time() + expires_in_seconds
        ).strftime("%Y-%m-%d %H:%M:%S")
        logger.debug(
            f"[external_cache] Cached tools for gateway/user '{id}', server '{server_name}' with key '{raw_key}' (hash: {key}) until {expiration_time}"
        )

    # Maintain a registry of servers for this gateway/user
    registry_key = get_gateway_servers_registry_hashed_key(id)
    cache_client.sadd(registry_key, server_name)
    cache_client.expire(registry_key, expires_in_seconds)

    # Register the gateway/user in the gateway/user registry if not already there
    gateway_registry = get_gateway_registry_hashed_key()
    cache_client.sadd(gateway_registry, id)


def get_cached_gateway_config(cache_client, id):
    """
    Retrieves cached gateway configuration.

    Args:
        cache_client: The cache client instance
        id (str): ID of the Gateway or User

    Returns:
        tuple: (config_data, expiration_time) if found and not expired, None otherwise
    """
    config_key = get_gateway_config_hashed_key(id)
    if not ENKRYPT_MCP_USE_EXTERNAL_CACHE:
        return get_local_cache(config_key)

    if cache_client is None:
        return None

    cached_data = cache_client.get(config_key)
    if not cached_data:
        return None
    try:
        config_data = json.loads(cached_data)
        if IS_DEBUG_LOG_LEVEL:
            logger.debug(
                f"[external_cache] Using cached config for id '{id}' with key hash: {config_key}"
            )
        return config_data
    except json.JSONDecodeError:
        logger.error(
            f"[external_cache] Error deserializing config cache for hash key: {config_key}"
        )
        return None


def cache_gateway_config(cache_client, id, config):
    """
    Caches gateway configuration.

    Args:
        cache_client: The cache client instance
        id (str): ID of the Gateway or User
        config (dict): The gateway configuration to cache
    """
    expires_in_seconds = int(ENKRYPT_GATEWAY_CACHE_EXPIRATION * 3600)
    config_key = get_gateway_config_hashed_key(id)
    if not ENKRYPT_MCP_USE_EXTERNAL_CACHE:
        set_local_cache(config_key, config, expires_in_seconds)
        local_gateway_config_registry.add(id)
        return

    if cache_client is None:
        return
    serialized_data = json.dumps(config)
    cache_client.setex(config_key, expires_in_seconds, serialized_data)
    if IS_DEBUG_LOG_LEVEL:
        expiration_time = datetime.fromtimestamp(
            time.time() + expires_in_seconds
        ).strftime("%Y-%m-%d %H:%M:%S")
        logger.debug(
            f"[external_cache] Cached gateway config for '{id}' with key '{id}-mcp-config' (hash: {config_key}) until {expiration_time}"
        )
    gateway_registry = get_gateway_registry_hashed_key()
    cache_client.sadd(gateway_registry, id)


def cache_key_to_id(cache_client, gateway_key, id):
    """
    Caches the mapping between a key and gateway/user ID.

    Args:
        cache_client: The cache client instance
        gateway_key (str): The key for gateway/user
        id (str): ID of the Gateway or User
    """
    expires_in_seconds = int(ENKRYPT_GATEWAY_CACHE_EXPIRATION * 3600)
    key = get_hashed_key(gateway_key)
    if not ENKRYPT_MCP_USE_EXTERNAL_CACHE:
        local_key_map[key] = id
        return

    if cache_client is None:
        return

    cache_client.setex(key, expires_in_seconds, id)
    if IS_DEBUG_LOG_LEVEL:
        logger.debug(
            f"[external_cache] Cached key mapping with key 'gateway_key-****{gateway_key[-4:]}' (hash: {key})"
        )


def get_id_from_key(cache_client, gateway_key):
    """
    Retrieves the gateway/user ID associated with a key.

    Args:
        cache_client: The cache client instance
        gateway_key (str): The key for gateway/user

    Returns:
        str: The associated gateway/user ID if found, None otherwise
    """
    key = get_hashed_key(gateway_key)
    if not ENKRYPT_MCP_USE_EXTERNAL_CACHE:
        return local_key_map.get(key)

    if cache_client is None:
        return None

    id = cache_client.get(key)
    if id:
        if IS_DEBUG_LOG_LEVEL:
            logger.debug(f"[external_cache] Found id for key with hash: {key}")
    return id


def clear_cache_for_servers(cache_client, id, server_name=None):
    """
    Clears tool cache for specific or all servers for a gateway/user.

    Args:
        cache_client: The cache client instance
        id (str): ID of the Gateway or User
        server_name (str, optional): Name of the server to clear cache for

    Returns:
        int: Number of cache entries cleared
    """
    if IS_DEBUG_LOG_LEVEL:
        logger.debug(
            f"[clear_cache_for_servers] Clearing cache for servers for gateway/user: {id} with current local_server_registry: {local_server_registry}"
        )

    count = 0
    # Local cache clear
    if server_name:
        if IS_DEBUG_LOG_LEVEL:
            logger.info(
                f"[clear_cache_for_servers] Clearing cache for server: {server_name}"
            )
        key = get_server_hashed_key(id, server_name)
        if key in local_cache:
            del local_cache[key]
            count += 1
            if id in local_server_registry:
                local_server_registry[id].discard(server_name)
    else:
        if IS_DEBUG_LOG_LEVEL:
            logger.debug(
                "[clear_cache_for_servers] Clearing cache for all servers for gateway/user"
            )
        # Clear all servers for a gateway/user
        if id in local_server_registry:
            if IS_DEBUG_LOG_LEVEL:
                logger.debug(
                    f"[clear_cache_for_servers] Clearing cache for all servers for gateway/user found in local_server_registry: {id}"
                )
            for server_name in list(local_server_registry[id]):
                if IS_DEBUG_LOG_LEVEL:
                    logger.debug(
                        f"[clear_cache_for_servers] Clearing cache for server: {server_name}"
                    )
                key = get_server_hashed_key(id, server_name)
                if key in local_cache:
                    if IS_DEBUG_LOG_LEVEL:
                        logger.debug(
                            f"[clear_cache_for_servers] Clearing cache for server: {server_name} found in local_cache"
                        )
                    del local_cache[key]
                    count += 1
            local_server_registry[id].clear()
        else:
            if IS_DEBUG_LOG_LEVEL:
                logger.debug(
                    f"[clear_cache_for_servers] Clearing cache for all servers for gateway/user not found in local_server_registry: {id}"
                )

    if cache_client is None:
        return count

    # External cache clear
    count = 0  # Resetting as it is external cache
    if server_name:
        key = get_server_hashed_key(id, server_name)
        if cache_client.exists(key):
            cache_client.delete(key)
            registry_key = get_gateway_servers_registry_hashed_key(id)
            cache_client.srem(registry_key, server_name)
            count += 1
        return count
    else:
        registry_key = get_gateway_servers_registry_hashed_key(id)
        servers = (
            cache_client.smembers(registry_key)
            if cache_client.exists(registry_key)
            else []
        )
        for server_name in servers:
            key = get_server_hashed_key(id, server_name)
            if cache_client.exists(key):
                cache_client.delete(key)
                count += 1
        cache_client.delete(registry_key)
        return count


def clear_gateway_config_cache(cache_client, id, gateway_key):
    """
    Clears all cache entries for a gateway/user, including config, tools, and key mapping.

    Args:
        cache_client: The cache client instance
        id (str): ID of the Gateway or User
        gateway_key (str): The gateway/user's key

    Returns:
        bool: True if any cache entries were cleared
    """
    if IS_DEBUG_LOG_LEVEL:
        logger.debug(
            "[clear_gateway_config_cache] Clearing all cache entries for gateway/user"
        )
    # 1. Clear all tool caches for the gateway/user
    registry_key = get_gateway_servers_registry_hashed_key(id)
    if IS_DEBUG_LOG_LEVEL:
        logger.debug(
            f"[clear_gateway_config_cache] Clearing all tool caches for gateway/user: {id} with registry key: {registry_key}"
        )
    servers = (
        cache_client.smembers(registry_key)
        if cache_client and cache_client.exists(registry_key)
        else []
    )
    if IS_DEBUG_LOG_LEVEL:
        logger.debug(
            f"[clear_gateway_config_cache] Clearing all tool caches for gateway/user: {id} with servers: {servers}"
        )
    for server_name in servers:
        tool_key = get_server_hashed_key(id, server_name)
        if IS_DEBUG_LOG_LEVEL:
            logger.debug(
                f"[clear_gateway_config_cache] Clearing tool cache for server: {server_name} with tool_key: {tool_key}"
            )
        if cache_client and cache_client.exists(tool_key):
            cache_client.delete(tool_key)
    if cache_client and cache_client.exists(registry_key):
        cache_client.delete(registry_key)

    # 2. Clear gateway config cache (local and external cache)
    config_key = get_gateway_config_hashed_key(id)
    if config_key in local_cache:
        del local_cache[config_key]
        local_gateway_config_registry.discard(id)
    if cache_client and cache_client.exists(config_key):
        cache_client.delete(config_key)

    # 3. Remove key mapping if gateway_key is provided
    if gateway_key:
        gateway_key_hash = get_hashed_key(gateway_key)
        if cache_client and cache_client.exists(gateway_key_hash):
            cache_client.delete(gateway_key_hash)
        if gateway_key_hash in local_key_map:
            del local_key_map[gateway_key_hash]

    # 4. Remove gateway/user from gateway/user registry (local and external cache)
    if cache_client:
        gateway_registry = get_gateway_registry_hashed_key()
        cache_client.srem(gateway_registry, id)
    local_server_registry.pop(id, None)

    return True


def get_cache_statistics(cache_client):
    """
    Retrieves statistics about the current cache state.

    Args:
        cache_client: The cache client instance

    Returns:
        dict: Cache statistics including:
            - total_gateways: Number of gateway/users in cache
            - total_tool_caches: Number of tool caches
            - total_config_caches: Number of config caches
            - cache_type: Type of cache being used
    """
    if not ENKRYPT_MCP_USE_EXTERNAL_CACHE:
        total_gateways = len(local_gateway_config_registry)
        total_tool_caches = sum(len(s) for s in local_server_registry.values())
        total_config_caches = len(local_gateway_config_registry)
        return {
            "total_gateways": total_gateways,
            "total_tool_caches": total_tool_caches,
            "total_config_caches": total_config_caches,
            "cache_type": "local",
        }

    if cache_client is None:
        return {
            "total_gateways": 0,
            "total_tool_caches": 0,
            "total_config_caches": 0,
            "cache_type": "none",
        }

    gateway_registry = get_gateway_registry_hashed_key()
    total_gateways = cache_client.scard(gateway_registry)
    total_tool_caches = 0
    total_config_caches = 0
    gateways = cache_client.smembers(gateway_registry)
    for id in gateways:
        config_key = get_gateway_config_hashed_key(id)
        if cache_client.exists(config_key):
            total_config_caches += 1
        servers_registry = get_gateway_servers_registry_hashed_key(id)
        if cache_client.exists(servers_registry):
            server_count = cache_client.scard(servers_registry)
            total_tool_caches += server_count
    return {
        "total_gateways": total_gateways,
        "total_tool_caches": total_tool_caches,
        "total_config_caches": total_config_caches,
        "cache_type": "external_cache",
    }
