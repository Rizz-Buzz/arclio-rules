import asyncio

from fastmcp import FastMCP
from loguru import logger

mcp = FastMCP(name="Arclio-rules using fastmcp 🚀")


@mcp.tool()
def add(a: int, b: int) -> dict:
    """Add two numbers"""
    return {
        "result": a + b,
        "sessionId": "session_id",
    }


# Static resource
@mcp.resource("config://version")
def get_version():
    """Get the version of the application.

    Returns:
        string: The version of the application.
    """
    return {
        "version": "1.0.1",
        "sessionId": "session_id",
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


# Dynamic resource template
@mcp.resource("rules://{rule_id}/profile")
def get_inhouse_rules(rule_id: int):
    """Get in-house rules for a specific user.

    Args:
        rule_id (int): The ID of the rule to be fetched.

    Returns:
        dict: A dictionary containing the rule name, content, and status.
    """
    rule = get_inhouse_rule(rule_id=rule_id)
    return {
        "name": f"Rule:{rule_id}",
        "content": rule["content"],
        "status": "active",
        "sessionId": "session_id",
    }


def get_inhouse_rule(rule_id: int) -> dict:
    """Fetch the content of an in-house rule.

    Args:
        rule_id (int): The ID of the rule to be fetched.

    Returns:
        str: The content of the rule.
    """
    # open the file in read mode
    with open(f"inhouse_rules/rule_{rule_id}.md", "r") as file:
        rule = file.read()
    return {
        "content": rule,
        "sessionId": "session_id",
    }


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
    """Main function to run the FastMCP server."""
    asyncio.run(check_mcp(mcp))
    mcp.run()


if __name__ == "__main__":
    main()
