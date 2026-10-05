"""Orchestrator agent (Step 7): plans the trip, calls remote specialists over A2A,
and renders hotel options as A2UI cards.

Requires:
    - Flights MCP server  (8001) -> cd mcp-servers/flights && uv run server.py http
    - Flight agent A2A    (8002) -> uv run uvicorn flight_a2a:a2a_app --host 127.0.0.1 --port 8002
    - Hotels MCP server   (8004) -> cd mcp-servers/hotels && uv run server.py
    - Hotel agent A2A     (8005) -> uv run uvicorn hotel_a2a:a2a_app --host 127.0.0.1 --port 8005
"""
import json
import os
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool

from .a2ui_hotels import build_hotel_operations

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


def show_hotels(hotels_json: str) -> dict[str, Any]:
    """Render hotel options as cards in the user's UI (A2UI fixed schema).

    Pass a JSON array string. Each item has the keys: id, name, area, stars, rating,
    price_per_night_eur, nights, total_eur. Copy the values exactly from the hotel agent's answer.

    After this tool returns, the cards are already visible to the user. The returned JSON is a UI
    descriptor, NOT a status message. Do NOT call this tool again for the same results.
    """
    try:
        hotels = json.loads(hotels_json)
    except json.JSONDecodeError as e:
        return {"error": f"hotels_json is not valid JSON: {e}"}

    if not isinstance(hotels, list) or not hotels:
        return {"error": "hotels_json must be a non-empty JSON array of hotel objects"}

    return build_hotel_operations([h for h in hotels if isinstance(h, dict)])


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
        "After hotel_agent answers, call show_hotels EXACTLY ONCE with the hotels it returned, as a JSON "
        "array string, copying values exactly. The cards are then shown to the user automatically. "
        "Finally reply with a short itinerary: the recommended flight, the recommended hotel, and an "
        "estimated total (one flight price plus the hotel total). Do not repeat the full hotel list, "
        "because the cards already show it. "
        "Never invent flights, hotels or prices; use only what the specialists return."
    ),
    tools=[AgentTool(agent=flight_agent), AgentTool(agent=hotel_agent), show_hotels],
)