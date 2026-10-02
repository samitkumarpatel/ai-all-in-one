"""Step 6: serve the Hotel agent as an A2A server.

Run from the agents/ folder:
    uv run uvicorn hotel_a2a:a2a_app --host 127.0.0.1 --port 8005

Agent Card: http://127.0.0.1:8005/.well-known/agent-card.json
"""
from pathlib import Path

from dotenv import load_dotenv

# Plain uvicorn doesn't load .env; the agent reads env vars at import time.
load_dotenv(Path(__file__).parent / "hotel_agent" / ".env")

from google.adk.a2a.utils.agent_to_a2a import to_a2a  # noqa: E402

from hotel_agent.agent import root_agent  # noqa: E402

# The port must match uvicorn's, because it is advertised inside the Agent Card.
a2a_app = to_a2a(root_agent, port=8005)
