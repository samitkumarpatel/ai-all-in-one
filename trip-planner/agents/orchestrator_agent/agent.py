"""Orchestrator agent (Step 4): plans the trip and delegates to remote agents over A2A.

Requires:
    - Flights MCP server  (port 8001)  -> uv run server.py http
    - Flight agent A2A    (port 8002)  -> uv run uvicorn flight_a2a:a2a_app --host 127.0.0.1 --port 8002
"""
import os

from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.lite_llm import LiteLlm

FLIGHT_AGENT_URL = os.getenv("FLIGHT_AGENT_URL", "http://127.0.0.1:8002")

MODEL = LiteLlm(model=f"azure/{os.environ['AZURE_DEPLOYMENT_NAME']}")

# The orchestrator only knows the remote agent through its Agent Card.
# It never sees the Flight agent's model, prompts, or MCP tools (opaque agent).
remote_flight_agent = RemoteA2aAgent(
    name="flight_agent",
    description="Remote specialist that finds and recommends flights between airports.",
    agent_card=f"{FLIGHT_AGENT_URL}/.well-known/agent-card.json",
)

root_agent = LlmAgent(
    name="trip_orchestrator",
    model=MODEL,
    description="Plans weekend trips by coordinating specialist agents.",
    instruction=(
        "You are a trip-planning orchestrator. "
        "For anything about flights, delegate to the flight_agent. "
        "Collect origin, destination and date from the user first if any are missing. "
        "Summarize the specialist's answer clearly for the user. "
        "Do not invent flight details yourself."
    ),
    sub_agents=[remote_flight_agent],
)