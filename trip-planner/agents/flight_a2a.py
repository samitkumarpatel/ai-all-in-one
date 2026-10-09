"""Step 3: serve the Flight agent as an A2A server.

Run from the agents/ folder:
    uv run uvicorn flight_a2a:a2a_app --host 127.0.0.1 --port 8002

Agent Card: http://127.0.0.1:8002/.well-known/agent-card.json
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# `adk web` loads .env automatically; plain uvicorn does not, so load it here
# (before importing the agent, which reads env vars at import time).
load_dotenv(Path(__file__).parent / "flight_agent" / ".env")

from google.adk.a2a.utils.agent_to_a2a import to_a2a  # noqa: E402

from flight_agent.agent import root_agent  # noqa: E402

# to_a2a wraps the ADK agent in an A2A app and auto-generates the Agent Card
# from the agent's name, description and tools. The port must match uvicorn's,
# because it is advertised inside the card. The host must also match the URL clients
# fetch the card from (to_a2a defaults to "localhost"; the orchestrator uses 127.0.0.1).
# In Docker, A2A_HOST is the service name ("flight-agent").
a2a_app = to_a2a(root_agent, host=os.getenv("A2A_HOST", "127.0.0.1"), port=8002)

# another way of configuring the card.

# from a2a.types import AgentCard, AgentSkill

# card = AgentCard(
#     name="Flight Agent",
#     description="Finds and recommends flights between airports.",
#     url="http://127.0.0.1:8002",
#     version="1.0.0",
#     capabilities={},
#     default_input_modes=["text/plain"],
#     default_output_modes=["text/plain"],
#     skills=[AgentSkill(
#         id="search_flights",
#         name="Flight search",
#         description="Search flights between two airports on a date.",
#         tags=["travel", "flights"],
#     )],
# )

# a2a_app = to_a2a(root_agent, port=8002, agent_card=card)