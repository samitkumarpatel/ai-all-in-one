"""MCP App (Step 8): fetch the seat-map app from the Flights MCP server and pass it to the browser.

An MCP Apps *host* does three things with a tool that has `_meta.ui.resourceUri`:
    1. calls the tool                      (tools/call)
    2. reads the linked ui:// resource     (resources/read)  -> HTML
    3. renders the HTML in a sandboxed iframe and sends it the tool result over postMessage

In this demo the host role is split in two. This file does steps 1 and 2 on the server, because the
orchestrator is the MCP client. It returns everything as one `mcp_app` tool result. The browser
(web/src/mcpApp.tsx) finds `mcp_app` in the AG-UI TOOL_CALL_RESULT event and does step 3.

This mirrors the A2UI hotel cards: specialists and MCP servers return data, the orchestrator turns
it into UI, and AG-UI carries that UI to the browser.
"""
import os
from typing import Any

from fastmcp import Client

FLIGHTS_MCP_URL = os.getenv("FLIGHTS_MCP_URL", "http://127.0.0.1:8001/mcp")
TOOL_NAME = "pick_seat"


async def build_seat_map_app(flight_id: str) -> dict[str, Any]:
    async with Client(FLIGHTS_MCP_URL) as client:
        # The tool definition says which UI belongs to it
        tool = next(t for t in await client.list_tools() if t.name == TOOL_NAME)
        resource_uri = tool.meta["ui"]["resourceUri"]

        tool_input = {"flight_id": flight_id}
        result = await client.call_tool(TOOL_NAME, tool_input)
        html = (await client.read_resource(resource_uri))[0].text

    return {
        "mcp_app": {
            "resourceUri": resource_uri,
            "html": html,
            "toolInput": tool_input,
            # Sent to the iframe as-is in ui/notifications/tool-result (a standard CallToolResult)
            "toolResult": {
                "content": [c.model_dump(mode="json", exclude_none=True) for c in result.content],
                "structuredContent": result.structured_content,
            },
        }
    }
