"""Orchestrator agent: plans the trip, calls remote specialists over A2A (Step 6),
renders hotel options as A2UI cards (Step 7) and shows a seat-map MCP App (Step 8).

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
from .mcp_app_seats import build_seat_map_app

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


async def show_seat_map(flight_id: str) -> dict[str, Any]:
    """Show an interactive seat map (an MCP App) for one flight, e.g. flight_id="FL101".

    The seat map is then visible to the user, who picks a seat in it. Their choice comes back as a
    normal chat message. The returned JSON is a UI descriptor, NOT a status message. Do NOT call this
    tool again for the same flight unless the user asks.
    """
    try:
        return await build_seat_map_app(flight_id)
    except Exception as e:  # e.g. unknown flight id, or the Flights MCP server is not running
        return {"error": f"Could not show the seat map for {flight_id}: {e}"}


root_agent = LlmAgent(
    name="trip_orchestrator",
    model=MODEL,
    description="Plans weekend trips by coordinating flight and hotel specialists.",
    instruction=(
        "You are a trip-planning orchestrator. "
        "Collect the origin, destination and travel dates from the user first if any are missing. "
        "For a trip plan, call flight_agent for flights AND hotel_agent for hotels. "
        "The specialists cannot see this conversation, so put everything they need in each request "
        "(airport codes or city, ISO dates). Ask flight_agent for the outbound flight and, if there is a "
        "return date, the return flight in the same request. Use the outbound date as hotel check-in and "
        "the return date as check-out. "
        "After hotel_agent answers, call show_hotels EXACTLY ONCE with the hotels it returned, as a JSON "
        "array string, copying values exactly. The cards are then shown to the user automatically. "
        "Then reply with a short itinerary: the recommended flights (with their ids), the recommended "
        "hotel, and an estimated total (flight prices plus the hotel total). Do not repeat the full hotel "
        "list, because the cards already show it. End by offering to show a seat map. "
        "When the user wants to choose a seat, call show_seat_map with the flight id (e.g. FL101). "
        "When the user picks a seat or books a hotel through the UI, confirm it in one sentence and say "
        "it is a demo, so nothing is really booked. "
        "Never invent flights, hotels or prices; use only what the specialists return."
    ),
    tools=[AgentTool(agent=flight_agent), AgentTool(agent=hotel_agent), show_hotels, show_seat_map],
)