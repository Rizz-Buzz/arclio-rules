import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastmcp import FastMCP
from loguru import logger

from arclio_rules.routes.rules import router as rules_router
from arclio_rules.services.rule_fetch_service import RuleFetchService

app = FastAPI(
    name="arclio-rules", description="Arclio-rules mcp-server created using fastmcp 🚀"
)
origins = []
if "ALLOWED_ORIGIN" in os.environ:
    origins.append(os.environ["ALLOWED_ORIGIN"])
else:
    origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(rules_router)

mcp = FastMCP.from_fastapi(app=app)


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
    rule_fetch_service = RuleFetchService(config={})
    return rule_fetch_service.get_rule(
        company="", category="", rule="", is_main_rule=True
    )


def _use_route_names_as_operation_ids(app: FastAPI) -> None:
    """Simplify operation IDs so that generated API clients have simpler function names.

    Should be called only after all routes have been added.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name


_use_route_names_as_operation_ids(app)


def main():
    """Main function to run the FastMCP server."""

    async def _check_mcp(mcp: FastMCP):
        """Check the MCP instance for available tools and resources.

        Args:
            mcp (FastMCP): The MCP instance to check.
        """
        # List the components that were created
        tools = await mcp.get_tools()
        resources = await mcp.get_resources()
        templates = await mcp.get_resource_templates()
        logger.info(
            f"{len(tools)} Tool(s): {', '.join([t.name for t in tools.values()])}"
        )  # noqa E501
        logger.info(
            f"{len(resources)} Resource(s): {', '.join([r.name for r in resources.values()])}"  # noqa E501 # type: ignore
        )
        logger.info(
            f"{len(templates)} Resource Template(s): {', '.join([t.name for t in templates.values()])}"  # noqa E501
        )

    asyncio.run(_check_mcp(mcp))
    mcp.run()


if __name__ == "__main__":
    main()
