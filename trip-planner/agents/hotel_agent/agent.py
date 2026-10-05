"""Hotel agent (Step 6): model + instructions + MCP tools, in a loop.

Requires the Hotels MCP server running over HTTP:
    cd mcp-servers/hotels && uv run server.py
"""
import os

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

HOTELS_MCP_URL = os.getenv("HOTELS_MCP_URL", "http://127.0.0.1:8004/mcp")

# Azure AI Foundry / Azure OpenAI via LiteLLM (reads AZURE_API_KEY, AZURE_API_BASE, AZURE_API_VERSION)
MODEL = LiteLlm(model=f"azure/{os.environ['AZURE_DEPLOYMENT_NAME']}")

hotels_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url=HOTELS_MCP_URL),
    tool_filter=["search_hotels"],
)

root_agent = LlmAgent(
    name="hotel_agent",
    model=MODEL,
    description="Finds and recommends hotels in a city for given dates.",
    instruction=(
        "You are a hotel-search specialist. "
        "Use the search_hotels tool with an airport code for the city (e.g. AMS for Amsterdam) "
        "and ISO dates (YYYY-MM-DD) for check-in and check-out. "
        "If the city or either date is missing, ask for it. "
        "List EVERY hotel the tool returns, one per line, with these fields exactly as returned: "
        "id, name, area, stars, rating, price_per_night_eur, nights, total_eur. "
        "Then recommend the best option and briefly explain the trade-off between price, rating and location. "
        "Only use data returned by the tool; never invent hotels."
    ),
    tools=[hotels_tools],
)