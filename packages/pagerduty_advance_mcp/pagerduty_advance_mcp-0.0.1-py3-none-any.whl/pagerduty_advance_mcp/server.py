import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import typer
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pagerduty import RestApiV2Client

from pagerduty_advance_mcp.client import get_client
from pagerduty_advance_mcp.tools import tools

logging.basicConfig(level=logging.WARNING)


app = typer.Typer()

MCP_SERVER_INSTRUCTIONS = """
You are connected to the PagerDuty AI Agent.

The AI agent can help with tasks such as generating runbooks, suggesting next steps for incident resolution,
recommending best practices for incident management, providing insights on incident trends and patterns,
and analyzing incident response effectiveness, and providing on-call support information.

You can use tools to ask questions about incident resolution, incident management,
generating runbooks to aid incident in any ways, and more.
"""


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[RestApiV2Client]:
    """Lifespan context manager for the MCP server.

    Args:
        server: The MCP server instance
    Returns:
        An asynchronous iterator yielding the MCP Client.
    """
    try:
        yield get_client()
    finally:
        pass


def add_tool(mcp_instance: FastMCP, tool: Callable) -> None:
    """Add a tool with appropriate safety annotations that indicate it's dangerous.

    Args:
        mcp_instance: The MCP server instance
        tool: The tool function to add
    """
    mcp_instance.add_tool(
        tool,
        annotations=ToolAnnotations(
            readOnlyHint=False, destructiveHint=True, idempotentHint=False
        ),
    )


@app.command()
def run() -> None:
    """Run the MCP server with the specified configuration.

    Args:
        enable_write_tools: Flag to enable write tools
    """
    mcp = FastMCP(
        "PagerDuty Advance MCP Server",
        lifespan=app_lifespan,
        instructions=MCP_SERVER_INSTRUCTIONS,
    )

    for tool in tools:
        add_tool(mcp, tool)

    mcp.run()
