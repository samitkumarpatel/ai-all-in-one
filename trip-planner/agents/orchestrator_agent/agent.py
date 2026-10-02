"""Orchestrator agent (Step 6): plans the trip by calling remote specialists over A2A.

Requires:
    - Flights MCP server  (8001) -> cd mcp-servers/flights && uv run server.py http
    - Flight agent A2A    (8002) -> uv run uvicorn flight_a2a:a2a_app --host 127.0.0.1 --port 8002
    - Hotels MCP server   (8004) -> cd mcp-servers/hotels && uv run server.py
    - Hotel agent A2A     (8005) -> uv run uvicorn hotel_a2a:a2a_app --host 127.0.0.1 --port 8005
"""
import os

from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool

FLIGHT_AGENT_URL = os.getenv("FLIGHT_AGENT_URL", "http://127.0.0.1:8002")
HOTEL_AGENT_URL = os.getenv("HOTEL_AGENT_URL", "http://127.0.0.1:8005")

MODEL = LiteLlm(model=f"azure/{os.environ['AZURE_DEPLOYMENT_NAME']}")

# The orchestrator knows each specialist only through its Agent Card (opaque agents).
flight_agent = RemoteA2aAgent(
    name="flight_agent",
    description="Remote specialist that finds and recommends flights between airports.",
    agent_card=f"{FLIGHT_AGENT_URL}/.well-known/agent-card.json",
)

hotel_agent = RemoteA2aAgent(
    name="hotel_agent",
    description="Remote specialist that finds and recommends hotels in a city for given dates.",
    agent_card=f"{HOTEL_AGENT_URL}/.well-known/agent-card.json",
)

# AgentTool presents each remote agent as a *tool*. Unlike sub_agents (which transfers control and
# lets the sub-agent answer the user), the orchestrator gets each result back and can merge them.
root_agent = LlmAgent(
    name="trip_orchestrator",
    model=MODEL,
    description="Plans weekend trips by coordinating flight and hotel specialists.",
    instruction=(
        "You are a trip-planning orchestrator. "
        "Collect the origin, destination and travel dates from the user first if any are missing. "
        "For a trip plan, call flight_agent for flights AND hotel_agent for hotels. "
        "The specialists cannot see this conversation, so put everything they need in each request "
        "(airport codes or city, ISO dates). Use the outbound flight date as hotel check-in. "
        "Then combine their answers into one short itinerary with an estimated total cost "
        "(one flight price plus the hotel total). "
        "Never invent flights, hotels or prices; use only what the specialists return."
    ),
    tools=[AgentTool(agent=flight_agent), AgentTool(agent=hotel_agent)],
)
