# Trip Planner: Build Log

A step-by-step record of the trip-planner demo, built to show MCP, MCP Apps, AI agents, A2A, AG-UI, and A2UI working together.

> ⚠️ These specs and SDKs change quickly. Versions and APIs below were checked against current docs but **not all were run end to end**. Treat each step's "Verify" section as the source of truth, and pin your versions.

## Status

| Step | What | Status |
|---|---|---|
| 1 | Flights MCP server | Code written |
| 2 | Flight agent (ADK + Azure model) using the MCP server | Code written |
| 3 | Flight agent exposed over A2A | Code written |
| 4 | Orchestrator agent consuming the Flight agent over A2A | Code written |
| 5 | Hotel agent (second A2A specialist) | Not started |
| 6 | React frontend + AG-UI | Not started |
| 7 | A2UI (declarative UI from the Hotel agent) | Not started |
| 8 | MCP App (seat picker) | Not started |

## Architecture (target)

```
React app (user)
   │  AG-UI (streaming events, shared state)
   ▼
Orchestrator agent
   │  A2A (opaque remote agents)
   ├──────────────────────┐
   ▼                      ▼
Flight agent           Hotel agent
   │  MCP                 │  MCP
   ▼                      ▼
Flights MCP server     Hotels MCP server
```

What exists today (Steps 1 to 4):

```
adk web (dev UI, :8000)
   └─ Orchestrator agent
         │  A2A
         ▼
      Flight agent (uvicorn, :8002)
         │  MCP (Streamable HTTP)
         ▼
      Flights MCP server (:8001)
```

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python (backend), React + Vite + TypeScript (planned frontend) |
| MCP server | FastMCP |
| Agents | Google ADK |
| Model | Azure AI Foundry / Azure OpenAI, called through LiteLLM |
| A2A | ADK's `to_a2a()` (server) and `RemoteA2aAgent` (client) |
| Package manager | `uv` |

## Ports

| Port | Service |
|---|---|
| 8000 | `adk web` (dev UI, runs the orchestrator) |
| 8001 | Flights MCP server |
| 8002 | Flight agent (A2A server) |

## Repo layout

```
trip-planner/
├── mcp-servers/
│   └── flights/
│       └── server.py
└── agents/
    ├── flight_a2a.py
    ├── flight_agent/
    │   ├── __init__.py
    │   ├── agent.py
    │   └── .env
    └── orchestrator_agent/
        ├── __init__.py
        ├── agent.py
        └── .env
```

---

## Step 1: Flights MCP server

**Goal:** a server exposing flight data through MCP, covering every server primitive.

**File:** `mcp-servers/flights/server.py`

| MCP concept | Implemented as |
|---|---|
| Tool (model-controlled) | `search_flights(origin, destination, date)` with progress reporting and log messages |
| Tool with elicitation | `choose_seat_preference(flight_id)` asks the user for window/aisle |
| Resource (app-controlled) | `airports://list` and the template `flight://{flight_id}` |
| Prompt (user-controlled) | `plan_weekend(origin, destination, date)` |
| Transports | stdio (default) and Streamable HTTP (`uv run server.py http`) |

**Setup**

```sh
cd mcp-servers/flights
uv init --bare
uv add fastmcp
```

**Run and test**

```sh
# Streamable HTTP, endpoint http://127.0.0.1:8001/mcp
uv run server.py http

# Inspector (see the Inspector note below)
npx @modelcontextprotocol/inspector@v1-latest
```

**Inspector note:** the Inspector's `latest` tag is now **v2**, which needs Node 22.19+, has changed CLI flags, requires a proxy auth token, and has a "Protocol Era" setting (`legacy` / `modern` / `auto`). The FastMCP server here is a legacy-era server, so use `legacy` or `auto`. The v1 line is deprecated (security fixes only) and published as `@v1-latest`.

**Verify:** each tool, resource, and prompt shows up and works in the Inspector. Elicitation and progress UI depend on the Inspector version.

---

## Step 2: Flight agent

**Goal:** an AI agent, defined as **model + instructions + tools in a loop**, that gets its tools from the MCP server.

**File:** `agents/flight_agent/agent.py` (plus an `__init__.py` that imports `agent`)

- `McpToolset` with `StreamableHTTPConnectionParams` connects to `http://127.0.0.1:8001/mcp`
- `tool_filter=["search_flights"]` exposes only that tool. `choose_seat_preference` is excluded because ADK's MCP client may not support server-initiated elicitation
- Model: `LiteLlm(model="azure/<deployment-name>")`

**Setup**

```sh
cd agents
uv init --bare
uv add "google-adk[mcp]" litellm
```

**Run and test**

```sh
cd mcp-servers/flights && uv run server.py http      # terminal 1
cd agents && uv run adk web                          # terminal 2
```

Pick `flight_agent` and ask: *"Find me a flight from Copenhagen to Amsterdam on 2026-10-10."* The trace should show a `search_flights` call.

**Azure notes**

- The string after `azure/` is the **deployment name**, not the base model name.
- The endpoint may be the `*.openai.azure.com` or `*.services.ai.azure.com` form. Try the other if one fails.
- Newer models may need a newer `AZURE_API_VERSION`.
- LiteLLM may need prefixes such as `azure/gpt5_series/<deployment>` or `azure/o_series/<deployment>` for GPT-5 and o-series models.
- Not every model handles tool calling well. If the model answers without calling the tool, try a stronger deployment.

### Environment files

`flight_agent/.env` and `orchestrator_agent/.env` can hold the same values:

```sh
AZURE_API_KEY=your-azure-key
AZURE_API_BASE=https://<your-resource>.openai.azure.com/
AZURE_API_VERSION=2024-02-01
AZURE_DEPLOYMENT_NAME=<your-deployment-name>

# Optional overrides
# FLIGHTS_MCP_URL=http://127.0.0.1:8001/mcp     (flight agent)
# FLIGHT_AGENT_URL=http://127.0.0.1:8002        (orchestrator)
```

`adk web` loads `.env` from each agent's own folder. Add `.env` to `.gitignore` and commit `.env.example` files instead.

---

## Step 3: Expose the Flight agent over A2A

**Goal:** make the Flight agent reachable by other agents, regardless of their framework.

**File:** `agents/flight_a2a.py`

```python
a2a_app = to_a2a(root_agent, port=8002)
```

`to_a2a()` wraps the ADK agent in an A2A server and **auto-generates the Agent Card** at startup.

**Setup**

```sh
cd agents
uv add "google-adk[a2a]" uvicorn
```

**Run**

```sh
uv run uvicorn flight_a2a:a2a_app --host 127.0.0.1 --port 8002
```

The `port` passed to `to_a2a()` must match the uvicorn port, because it is advertised inside the card. Plain uvicorn doesn't load `.env`, so `flight_a2a.py` loads `flight_agent/.env` explicitly before importing the agent.

**How the Agent Card is generated**

| Card field | Source |
|---|---|
| `name` | The agent's `name` |
| `description` | The agent's `description` |
| `url` | `host` and `port` arguments of `to_a2a()` |
| `skills` | One entry for the agent itself (description and instruction text), plus one per tool |
| Input/output modes | `text/plain` in ADK's sample output |
| `capabilities` | Empty in ADK's sample output |

Caveats:

- The agent's **instruction text can end up in the public card**, so don't put secrets in it.
- Whether tools from `McpToolset` appear as skills is unverified. Check the generated card.
- To control the card, pass `agent_card=` (an `AgentCard` object or a path to a JSON file) to `to_a2a()`.

**Verify**

1. Open `http://127.0.0.1:8002/.well-known/agent-card.json` (some older versions use `agent.json`).
2. Chat with the agent using the A2A Inspector, a separate tool from the A2A project.

---

## Step 4: Orchestrator agent

**Goal:** an agent that plans trips and delegates flight questions to the remote Flight agent over A2A.

**File:** `agents/orchestrator_agent/agent.py` (plus `__init__.py`)

```python
flight_agent = RemoteA2aAgent(
    name="flight_agent",
    description="...",
    agent_card=f"{FLIGHT_AGENT_URL}/.well-known/agent-card.json",
)
root_agent = LlmAgent(..., sub_agents=[flight_agent])
```

The orchestrator knows the Flight agent **only through its Agent Card**. It never sees its model, prompts, or MCP tools. That is what "opaque agent" means in A2A.

**Run (three terminals)**

```sh
# 1. MCP server (8001)
cd mcp-servers/flights && uv run server.py http

# 2. Flight agent as an A2A server (8002)
cd agents && uv run uvicorn flight_a2a:a2a_app --host 127.0.0.1 --port 8002

# 3. Dev UI, which runs the orchestrator (8000)
cd agents && uv run adk web
```

In the dev UI, pick **`orchestrator_agent`** and ask: *"I'm in Copenhagen and want a weekend in Amsterdam on 2026-10-10. What flights are there?"*

**Who runs how**

| Agent | A2A role | How it runs |
|---|---|---|
| Flight agent | Server | `uvicorn` on :8002 |
| Orchestrator | Client | Hosted by `adk web` on :8000 |

Picking `flight_agent` in the dev UI talks to it in-process and does **not** use A2A. Only `orchestrator_agent` exercises the protocol.

**Behavior note:** `sub_agents` uses transfer, so the sub-agent's reply may go straight to the user. For combined itineraries (flights + hotels), switch to calling each specialist as a tool so the orchestrator can merge results.

**Verify**

- The trace shows a transfer to `flight_agent`.
- Terminal 2 logs an incoming request.
- Start terminal 2 before using the orchestrator, because the card is fetched on use.

---

## Concepts demonstrated so far

| Concept | Where |
|---|---|
| MCP tools, resources, prompts | Step 1 |
| MCP elicitation and progress reporting | Step 1 (elicitation is not used by the agent yet) |
| MCP transports (stdio, Streamable HTTP) | Step 1 |
| AI agent = model + instructions + tools in a loop | Steps 2 and 4 |
| MCP client inside an agent | Step 2 |
| A2A server and Agent Card | Step 3 |
| A2A client and opaque agents | Step 4 |

## Next steps

5. **Hotel agent:** a second A2A specialist with its own MCP server, ideally on a different framework (for example LangGraph) to show interoperability.
6. **Frontend:** React + Vite + TypeScript with AG-UI (CopilotKit). The orchestrator gets its own HTTP server that speaks AG-UI, which replaces `adk web`.
7. **A2UI:** the Hotel agent returns a declarative UI surface that React renders from a trusted component catalog.
8. **MCP App:** a `pick_seat` tool returning a `ui://` seat map rendered in a sandboxed iframe.

## Open questions

- Does the generated Agent Card include the MCP-derived tools as skills?
- Does ADK's MCP client support elicitation, so `choose_seat_preference` can be re-enabled?
- Which React renderers exist for A2UI and MCP Apps, and how does CopilotKit wire them in?
