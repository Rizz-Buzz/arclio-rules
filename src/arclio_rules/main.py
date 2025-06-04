import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastmcp import FastMCP
from loguru import logger

from arclio_rules.routes.rules import router as rules_router
from arclio_rules.services.rule_storage_service import RuleStorageService


def get_app_info() -> dict:
    """Get the information of the application.

    Returns:
        dict: A dictionary containing the version, name and description of the application.
    """  # noqa: E501
    with open("pyproject.toml", "r") as file:
        data = file.read()
    version = data.split("version = ")[1].split("\n")[0].strip('"')
    name = data.split("name = ")[1].split("\n")[0].strip('"')
    description = data.split("description = ")[1].split("\n")[0].strip('"')
    return {"version": version, "name": name, "description": description}


app = FastAPI(
    name=get_app_info()["name"],
    description=get_app_info()["description"],
)
origins = []
if "ALLOWED_ORIGIN" in os.environ:
    origins.append(os.environ["ALLOWED_ORIGIN"])
else:
    origins.append("*")


logger.info(f"ALLOWED ORIGINS: {origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(rules_router)

mcp = FastMCP.from_fastapi(app=app)


# static resource
@mcp.resource(
    uri="data://app-status",
    name="ApplicationStatus",
    description="Provides the current status of the application.",
    mime_type="application/json",
    tags={"monitoring", "status"},
)
def get_application_status() -> dict:
    """Internal function description (ignored if description is provided above)."""
    return {
        "status": "OK",
        "version": get_app_info()["version"],
        "name": get_app_info()["name"],
        "description": get_app_info()["description"],
    }


# create another mcp resource
@mcp.resource(
    uri="rule://main-rule",
    name="MainRule",
    description="Provides the main rule of the application.",
    mime_type="application/json",
    tags={"rules", "main"},
)
async def get_main_rule() -> dict:
    """Get the main rule of the application."""
    rule_storage_service = RuleStorageService(config={})
    main_rule_content = await rule_storage_service.get_rule_content(
        client_name="", rule_path="index.md"
    )
    if main_rule_content["success"]:
        return {
            "content": main_rule_content["content"],
        }
    else:
        return {
            "content": "Failed to get the main rule of the application.",
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
    # Get the version and status of the application
    app_info = get_app_info()
    logger.info(f"Status: {get_application_status()['status']}")
    logger.info(f"Name: {app_info['name']}")
    logger.info(f"Version: {app_info['version']}")
    logger.info(f"Description: {app_info['description']}\n")

    # List the components that were created
    tools = await mcp.get_tools()
    resources = await mcp.get_resources()
    templates = await mcp.get_resource_templates()
    logger.info(f"{len(tools)} Tool(s): {', '.join([t.name for t in tools.values()])}")  # noqa E501
    logger.info(
        f"{len(resources)} Resource(s): {', '.join([r.name for r in resources.values()])}"  # noqa E501 # type: ignore
    )
    logger.info(
        f"{len(templates)} Resource Template(s): {', '.join([t.name for t in templates.values()])}"  # noqa E501
    )


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """Simplify operation IDs so that generated API clients have simpler function names.

    Should be called only after all routes have been added.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name  # in this case, 'read_items'


use_route_names_as_operation_ids(app)


def main():
    """Main function to run the FastMCP server."""
    asyncio.run(check_mcp(mcp))
    mcp.run()


if __name__ == "__main__":
    main()
