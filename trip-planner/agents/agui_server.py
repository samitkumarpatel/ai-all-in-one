"""Step 5: serve the orchestrator over AG-UI so a browser can talk to it.

Run from the agents/ folder:
    uv run uvicorn agui_server:app --host 127.0.0.1 --port 8003

AG-UI endpoint: POST http://127.0.0.1:8003/agui  (responds with an SSE stream of AG-UI events)
"""
from pathlib import Path

from dotenv import load_dotenv

# Plain uvicorn doesn't load .env, and the agent reads env vars at import time.
load_dotenv(Path(__file__).parent / "orchestrator_agent" / ".env")

from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint  # noqa: E402
from fastapi import FastAPI  # noqa: E402

from orchestrator_agent.agent import root_agent  # noqa: E402

# ADKAgent is the adapter: it turns ADK runs (tokens, tool calls, transfers)
# into standard AG-UI events.
adk_agent = ADKAgent(
    adk_agent=root_agent,
    app_name="trip_planner",
    user_id="demo_user",
    session_timeout_seconds=3600,
    use_in_memory_services=True,
)

app = FastAPI(title="Trip Planner AG-UI server")
add_adk_fastapi_endpoint(app, adk_agent, path="/agui")