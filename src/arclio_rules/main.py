import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastmcp import FastMCP
from loguru import logger

from arclio_rules.routes.rules import router as rules_router

# from arclio_rules.services.rule_indexing_service import RuleIndexingService

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


# def get_indexer():
#     """Provide a singleton RuleIndexingService instance."""
#     return RuleIndexingService(config={}, max_cache_size=1000, ttl_seconds=3600)


# @mcp.resource(
#     uri="rule://main-rule",
#     name="MainRule",
#     description="Provides the main rule of the application.",
#     mime_type="application/json",
#     tags={"rules", "main"},
# )
# async def get_main_rule(indexer: RuleIndexingService = Depends(get_indexer)) -> dict:
#     """Get the main rule of the application."""
#     return indexer.get_rule(company="", category="", rule="", is_main_rule=True)


def _use_route_names_as_operation_ids(app: FastAPI) -> None:
    """Simplify operation IDs so that generated API clients have simpler function names."""  # noqa: E501
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name


_use_route_names_as_operation_ids(app)


def main():
    """Main function to run the FastMCP server."""

    async def _check_mcp(mcp: FastMCP):
        """Check the MCP instance for available tools and resources."""
        tools = await mcp.get_tools()
        resources = await mcp.get_resources()
        templates = await mcp.get_resource_templates()
        logger.info(
            f"{len(tools)} Tool(s): {', '.join([t.name for t in tools.values()])}"
        )
        logger.info(
            f"{len(resources)} Resource(s): {', '.join([r.name for r in resources.values()])}"  # pyright: ignore[reportCallIssue, reportArgumentType]  # noqa: E501
        )
        logger.info(
            f"{len(templates)} Resource Template(s): {', '.join([t.name for t in templates.values()])}"  # noqa: E501
        )

    asyncio.run(_check_mcp(mcp))
    mcp.run()


if __name__ == "__main__":
    main()
