"""Flight agent (Step 2): model + instructions + MCP tools, in a loop.

Requires the Flights MCP server from Step 1 running over HTTP:
    cd mcp-servers/flights && uv run server.py http
"""
import os

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams

FLIGHTS_MCP_URL = os.getenv("FLIGHTS_MCP_URL", "http://127.0.0.1:8001/mcp")

# Azure AI Foundry / Azure OpenAI deployment, called through LiteLLM.
# LiteLLM reads AZURE_API_KEY, AZURE_API_BASE and AZURE_API_VERSION from the environment (.env).
# The model string is "azure/<your-deployment-name>" (the deployment name, not the base model name).
AZURE_DEPLOYMENT = os.environ["AZURE_DEPLOYMENT_NAME"]
MODEL = LiteLlm(model=f"azure/{AZURE_DEPLOYMENT}")

flights_tools = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url=FLIGHTS_MCP_URL),
    # Expose only search_flights for now. choose_seat_preference uses MCP elicitation,
    # which the agent framework may not support yet. We revisit it in the frontend steps.
    tool_filter=["search_flights"],
)

root_agent = LlmAgent(
    name="flight_agent",
    model=MODEL,
    description="Finds and recommends flights between airports.",
    instruction=(
        "You are a flight-search specialist. "
        "Use the search_flights tool with IATA airport codes (e.g. CPH, AMS) and an ISO date (YYYY-MM-DD). "
        "If the user gives a city name, convert it to its airport code. "
        "If origin, destination, or date is missing, ask for it. "
        "Recommend the best option and briefly explain the trade-off between price and departure time. "
        "Only use data returned by the tool; never invent flights."
    ),
    tools=[flights_tools],
)