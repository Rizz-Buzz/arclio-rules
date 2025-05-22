import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP
from routes import rules

from loguru import logger

app = FastAPI(title="Arclio Rules API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rules.router)


@app.get("/")
async def health_check():
    return {"status": "healthy"}


# Mount the MCP server to the FastAPI app
mcp = FastApiMCP(
    app,
    name="FAST-MCP-API for Arclio-Rules-API",
    description="MCP server for the Arclio-Rules-API application",
)
mcp.mount()

if __name__ == "__main__":
    import uvicorn

    host = os.environ["HOST"]
    port = int(os.environ["PORT"])
    reload = os.environ["RELOAD"]
    if not host or not port:
        raise ValueError("HOST and PORT environment variables must be set.")
    logger.info(
        f"Starting server on {host}:{port} with reload={reload}"
    )  # Log the host and port

    uvicorn.run("main:app", host=host, port=port, reload=True)
