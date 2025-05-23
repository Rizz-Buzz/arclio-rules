import asyncio

from fastmcp import FastMCP
from loguru import logger
import threading
from typing import Optional

# In-memory session store (thread-safe for concurrent access)
session_store: dict = {}
session_lock = threading.Lock()  # For thread-safe updates

mcp = FastMCP(name="Arclio-rules using fastmcp 🚀")


# Helper function to store/retrieve session data
def store_session_data(session_id: Optional[str], key: str, value: any) -> None:
    if session_id:
        with session_lock:
            if session_id not in session_store:
                session_store[session_id] = {}
            session_store[session_id][key] = value


def get_session_data(session_id: Optional[str], key: str) -> any:
    if session_id and session_id in session_store:
        with session_lock:
            return session_store.get(session_id, {}).get(key)
    return None


@mcp.tool()
def add(a: int, b: int, context: dict = None) -> dict:
    """Add two numbers and track usage per session"""
    session_id = context.get("sessionId") if context else None
    # Increment a counter for this session
    counter_key = "add_usage_count"
    current_count = get_session_data(session_id, counter_key) or 0
    store_session_data(session_id, counter_key, current_count + 1)

    result = a + b
    # Include session info in the response
    return {"result": result, "sessionId": session_id, "usage_count": current_count + 1}


@mcp.resource("config://version")
def get_version() -> dict:
    """Get the version of the application, with session tracking"""
    session_id = context.get("sessionId") if context else None
    # Log access to version resource
    access_key = "version_access_count"
    current_count = get_session_data(session_id, access_key) or 0
    store_session_data(session_id, access_key, current_count + 1)

    return {
        "version": "2.0.1",
        "sessionId": "session_id",
        "access_count": current_count + 1,
    }


@mcp.resource(
    uri="data://app-status",  # Explicit URI (required)
    name="ApplicationStatus",  # Custom name
    description="Provides the current status of the application.",  # Custom description
    mime_type="application/json",  # Explicit MIME type
    tags={"monitoring", "status"},  # Categorization tags
)
def get_application_status() -> dict:
    """Internal function description (ignored if description is provided above)."""
    return {
        "status": "ok",
        "uptime": 12345,
        "version": "2.0.1",
    }


@mcp.resource("rules://{rule_id}/profile")
def get_inhouse_rules(rule_id: int, context: dict = None) -> dict:
    """Get in-house rules for a specific user, with session-specific caching"""
    session_id = context.get("sessionId") if context else None
    # Cache rule content in session to avoid repeated file reads
    cache_key = f"rule_{rule_id}"
    cached_rule = get_session_data(session_id, cache_key)

    if cached_rule:
        rule_content = cached_rule
    else:
        rule_content = get_inhouse_rule(rule_id=rule_id)
        store_session_data(session_id, cache_key, rule_content)

    return {
        "name": f"Rule:{rule_id}",
        "content": rule_content,
        "status": "active",
        "sessionId": session_id,
    }


def get_inhouse_rule(rule_id: int) -> str:
    """Fetch the content of an in-house rule."""
    with open(f"inhouse_rules/rule_{rule_id}.md", "r") as file:
        rule = file.read()
    return rule


async def check_mcp(mcp: FastMCP):
    """Check the MCP instance for available tools and resources.

    Args:
        mcp (FastMCP): The MCP instance to check.
    """
    # List the components that were created
    tools = await mcp.get_tools()
    resources = await mcp.get_resources()
    templates = await mcp.get_resource_templates()

    logger.info(f"{len(tools)} Tool(s): {', '.join([t.name for t in tools.values()])}")
    logger.info(
        f"{len(resources)} Resource(s): {', '.join([r.name for r in resources.values()])}"
    )
    logger.info(
        f"{len(templates)} Resource Template(s): {', '.join([t.name for t in templates.values()])}"  # noqa E501
    )


def main():
    """Main function to run the MCP server."""
    asyncio.run(check_mcp(mcp))
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8008,
        path="/mcp",
    )


if __name__ == "__main__":
    main()
