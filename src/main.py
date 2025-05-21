import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute
from fastapi_mcp import FastApiMCP

from arclio_rules.routes.rules import router as rules_router

from loguru import logger

# Initialise the FastAPI app
app = FastAPI()

origins = []
if "ALLOWED_ORIGIN" in os.environ:
    origins.append(os.environ["ALLOWED_ORIGIN"])


logger.info(f"ALLOWED ORIGINS: {origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(rules_router)


def use_route_names_as_operation_ids(app: FastAPI) -> None:
    """
    Simplify operation IDs so that generated API clients have simpler function
    names.

    Should be called only after all routes have been added.
    """
    for route in app.routes:
        if isinstance(route, APIRoute):
            route.operation_id = route.name  # in this case, 'read_items'


use_route_names_as_operation_ids(app)

mcp = FastApiMCP(app)
mcp.mount()
