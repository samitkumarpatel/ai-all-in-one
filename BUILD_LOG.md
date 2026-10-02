# Trip Planner: Build Log

A step-by-step record of the trip-planner demo, built to show MCP, MCP Apps, AI agents, A2A, AG-UI, and A2UI working together.

> ⚠️ These specs and SDKs change quickly. APIs below were checked against current docs, but **none of the code has been run end to end yet**. Treat each step's "Verify" section as the source of truth, and pin your versions once things work.

## Status

| Step | What | Status |
|---|---|---|
| 1 | Flights MCP server | Code written |
| 2 | Flight agent (ADK + Azure model) using the MCP server | Code written |
| 3 | Flight agent exposed over A2A | Code written |
| 4 | Orchestrator agent consuming the Flight agent over A2A | Superseded by Step 6 |
| 5 | AG-UI server + React chat UI with live event log | Code written |
| 6 | Hotel agent + orchestrator calling both agents as tools | Code written |
| 7 | A2UI: Hotel agent returns hotel cards as declarative UI | Not started (needs research) |
| 8 | MCP App: seat picker as a sandboxed `ui://` iframe | Not started |

## Architecture

```
React app (Vite, :5173)
   │  AG-UI (SSE event stream)
   ▼
AG-UI server (:8003)  ── hosts the Orchestrator agent
   │  A2A (agents as tools)
   ├─────────────────────────┐
   ▼                         ▼
Flight agent (:8002)      Hotel agent (:8005)
   │  MCP (Streamable HTTP)  │  MCP (Streamable HTTP)
   ▼                         ▼
Flights MCP server (:8001) Hotels MCP server (:8004)
   └─ mock FLIGHTS list      └─ mock HOTELS list
```

All travel data is **mock data hardcoded in the MCP servers**. No real airline or hotel API is used. To switch to real data, only the MCP servers need to change.

## Tech stack

| Layer | Choice |
|---|---|
| Backend language | Python, `uv` for packages |
| MCP servers | FastMCP |
| Agents | Google ADK |
| Model | Azure AI Foundry / Azure OpenAI through LiteLLM |
| Agent-to-agent | A2A: `to_a2a()` (server), `RemoteA2aAgent` + `AgentTool` (client) |
| Agent-to-frontend | AG-UI via `ag_ui_adk` (`ADKAgent`, `add_adk_fastapi_endpoint`) |
| Frontend | React + Vite + TypeScript, no router, no CopilotKit yet |

## Ports

| Port | Service | Role |
|---|---|---|
| 8000 | `adk web` | Optional dev UI for debugging agents |
| 8001 | Flights MCP server | MCP server |
| 8002 | Flight agent | A2A server |
| 8003 | AG-UI server (orchestrator) | AG-UI server, A2A client |
| 8004 | Hotels MCP server | MCP server |
| 8005 | Hotel agent | A2A server |
| 5173 | React app | AG-UI client |

## Repo layout

```
trip-planner/
├── BUILD_LOG.md
├── mcp-servers/
│   ├── flights/server.py
│   └── hotels/server.py
├── agents/
│   ├── flight_a2a.py
│   ├── hotel_a2a.py
│   ├── agui_server.py
│   ├── flight_agent/        (__init__.py, agent.py, .env)
│   ├── hotel_agent/         (__init__.py, agent.py, .env)
│   └── orchestrator_agent/  (__init__.py, agent.py, .env)
└── web/
    ├── vite.config.ts
    └── src/ (agui.ts, App.tsx, App.css, index.css)
```

## Running everything

Six backend/frontend processes, one per terminal. Start them in this order:

```sh
# 1. Flights MCP (8001)
cd mcp-servers/flights && uv run server.py http

# 2. Hotels MCP (8004)
cd mcp-servers/hotels && uv run server.py

# 3. Flight agent over A2A (8002)
cd agents && uv run uvicorn flight_a2a:a2a_app --host 127.0.0.1 --port 8002

# 4. Hotel agent over A2A (8005)
cd agents && uv run uvicorn hotel_a2a:a2a_app --host 127.0.0.1 --port 8005

# 5. Orchestrator over AG-UI (8003)
cd agents && uv run uvicorn agui_server:app --host 127.0.0.1 --port 8003

# 6. React app (5173)
cd web && npm run dev
```

Note the difference: the Flights server needs the `http` argument, while the Hotels server runs over HTTP by default. Start the A2A agents before using the orchestrator, because it fetches their Agent Cards on use.

**Try it:** open http://localhost:5173 and ask *"Plan a weekend in Amsterdam from Copenhagen. Fly out 2026-10-10 and come back 2026-10-12."*

## Environment files

Each agent folder has its own `.env`, with the same values unless you want different models per agent:

```sh
AZURE_API_KEY=your-azure-key
AZURE_API_BASE=https://<your-resource>.openai.azure.com/
AZURE_API_VERSION=2024-02-01
AZURE_DEPLOYMENT_NAME=<your-deployment-name>

# Optional overrides (defaults are in the code)
# FLIGHTS_MCP_URL=http://127.0.0.1:8001/mcp     (flight agent)
# HOTELS_MCP_URL=http://127.0.0.1:8004/mcp      (hotel agent)
# FLIGHT_AGENT_URL=http://127.0.0.1:8002        (orchestrator)
# HOTEL_AGENT_URL=http://127.0.0.1:8005         (orchestrator)
```

- `adk web` loads `.env` from each agent's folder. The `*_a2a.py` and `agui_server.py` files load the matching `.env` explicitly, because plain uvicorn does not.
- Add `.env` to `.gitignore` and commit `.env.example` files instead.

**Azure notes**

- The string after `azure/` is the **deployment name**, not the base model name.
- The endpoint may be the `*.openai.azure.com` or `*.services.ai.azure.com` form. Try the other if one fails.
- Newer models may need a newer `AZURE_API_VERSION`, and GPT-5 / o-series models may need LiteLLM prefixes such as `azure/gpt5_series/<deployment>`.
- Not every model handles tool calling well. If the agent answers without calling a tool, try a stronger deployment.

---

## Step 1: Flights MCP server

**File:** `mcp-servers/flights/server.py`

| MCP concept | Implemented as |
|---|---|
| Tool (model-controlled) | `search_flights(origin, destination, date)` with progress reporting and log messages |
| Tool with elicitation | `choose_seat_preference(flight_id)` asks the user for window/aisle |
| Resources (app-controlled) | `airports://list` and the template `flight://{flight_id}` |
| Prompt (user-controlled) | `plan_weekend(origin, destination, date)` |
| Transports | stdio (default) and Streamable HTTP (`uv run server.py http`) |

**Setup:** `cd mcp-servers/flights && uv init --bare && uv add fastmcp`

**Test with the MCP Inspector.** Its `latest` tag is now **v2**, which needs Node 22.19+, has changed CLI flags, requires a proxy auth token, and has a "Protocol Era" setting (`legacy` / `modern` / `auto`). This FastMCP server is a legacy-era server, so use `legacy` or `auto`. The v1 line is deprecated (security fixes only) and published as `@v1-latest`:

```sh
npx @modelcontextprotocol/inspector@v1-latest
# or v2: npx @modelcontextprotocol/inspector   (add the server URL in the UI)
```

**Verify:** each tool, resource, and prompt appears and works. Elicitation and progress UI depend on the Inspector version.

## Step 2: Flight agent

**File:** `agents/flight_agent/agent.py`

An AI agent is **model + instructions + tools, in a loop**. This one gets its tools from the Flights MCP server:

- `McpToolset` with `StreamableHTTPConnectionParams` connects to `http://127.0.0.1:8001/mcp`
- `tool_filter=["search_flights"]` exposes only that tool. `choose_seat_preference` is left out because ADK's MCP client may not support server-initiated elicitation
- Model: `LiteLlm(model="azure/<deployment-name>")`

**Setup:** `cd agents && uv init --bare && uv add "google-adk[mcp]" litellm`

**Verify:** run `uv run adk web`, pick `flight_agent`, and ask for a flight. The trace should show a `search_flights` call.

## Step 3: Flight agent over A2A

**File:** `agents/flight_a2a.py`

```python
a2a_app = to_a2a(root_agent, port=8002)
```

`to_a2a()` wraps the ADK agent in an A2A server and **auto-generates the Agent Card** when the app starts. The `port` must match uvicorn's, because it is advertised in the card.

**Setup:** `uv add "google-adk[a2a]" uvicorn`

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

- The agent's **instruction text can end up in the public card**, so keep secrets out of it.
- Whether `McpToolset` tools appear as skills is unverified. Check the generated card.
- To control the card, pass `agent_card=` (an `AgentCard` object or a JSON file path) to `to_a2a()`.

**Verify:** open `http://127.0.0.1:8002/.well-known/agent-card.json` (older versions use `agent.json`), then chat with the agent using the A2A Inspector.

## Step 4: First orchestrator (superseded)

The first orchestrator used `sub_agents=[RemoteA2aAgent(...)]`. With `sub_agents`, ADK **transfers control** to the specialist, whose reply goes straight to the user. That works for one specialist but not for combining two, so Step 6 replaced it with `AgentTool`. Keep this in the README as a contrast between the two patterns.

## Step 5: AG-UI server and React chat

**Files:** `agents/agui_server.py`, `web/` (Vite + React + TypeScript)

**Backend:** `ADKAgent` (from `ag_ui_adk`) adapts ADK runs into AG-UI events, and `add_adk_fastapi_endpoint(app, adk_agent, path="/agui")` serves them as a Server-Sent Events stream. Requires google-adk 1.16 or newer.

**Setup:** `cd agents && uv add ag-ui-adk fastapi`

**Frontend:**

```sh
npm create vite@latest web -- --template react-ts
cd web && npm install
# then copy over vite.config.ts and src/{agui.ts,App.tsx,App.css,index.css}
```

- `src/agui.ts` is a small custom AG-UI client: it POSTs a run request and parses the SSE event stream.
- `src/App.tsx` is a chat UI that maps events to the screen (`TEXT_MESSAGE_START/CONTENT`, `TOOL_CALL_START`, `RUN_ERROR`), plus a side panel listing every raw event.
- `vite.config.ts` proxies `/agui` to port 8003, so no CORS setup is needed.

**Design choices**

- **No CopilotKit yet.** Its React setup needs a separate Node runtime in front of the Python agent, and I was not certain of the current runtime API. A hand-written client makes the events visible, and CopilotKit (or `@ag-ui/client`) can replace it later.
- **No React Router.** It is a single-screen app.
- **Why not just `adk web`?** `adk web` is a developer tool: traces, sessions, evals. A custom UI is needed for end users, branding, rich UI (A2UI, MCP Apps), and agents from other frameworks.

**Test the backend directly:**

```sh
curl -N -X POST http://127.0.0.1:8003/agui \
  -H "Content-Type: application/json" -H "Accept: text/event-stream" \
  -d '{"threadId":"t1","runId":"r1","state":{},"tools":[],"context":[],"forwardedProps":{},
       "messages":[{"id":"m1","role":"user","content":"Flights CPH to AMS on 2026-10-10?"}]}'
```

**Verify:** the reply streams into the chat, the events panel fills, and tool calls show as 🔧 badges. If the chat stays blank while the log fills, compare an event's fields with what `handleEvent` reads (`messageId`, `delta`, `toolCallName`).

## Step 6: Hotel agent and multi-agent orchestration

**New files**

| File | Purpose |
|---|---|
| `mcp-servers/hotels/server.py` | Hotels MCP server: `search_hotels` tool (sorted by price, computes nights and total), `cities://list` and `hotel://{hotel_id}` resources |
| `agents/hotel_agent/` | ADK agent using `search_hotels` over MCP |
| `agents/hotel_a2a.py` | Exposes the Hotel agent over A2A (port 8005) |
| `agents/orchestrator_agent/agent.py` | **Rewritten**: calls both specialists as tools |

Mock hotels cover AMS, BCN, LIS, and LHR, matching the flight destinations.

**Orchestrator pattern**

```python
tools=[AgentTool(agent=flight_agent), AgentTool(agent=hotel_agent)]
```

`RemoteA2aAgent` fetches each agent card, and `AgentTool` presents the remote agent as a tool. The orchestrator gets each result back, so it can merge flights and hotels into one itinerary with a total cost. The specialists cannot see the user's conversation, so the orchestrator's instruction tells it to pass airport codes and ISO dates in each request.

**Setup:**

```sh
cd mcp-servers/hotels && uv init --bare && uv add fastmcp
cd agents && cp flight_agent/.env hotel_agent/.env
```

**Verify**

- Both agent cards load (`:8002` and `:8005`, at `/.well-known/agent-card.json`).
- A trip request shows two tool badges (`flight_agent`, `hotel_agent`) and one combined plan.
- All four backend terminals (both MCP servers, both A2A agents) log activity.

**Known limitation:** the Flights server only has outbound routes from CPH, so there are no return flights. Add reversed routes to `FLIGHTS` if you want them.

---

## Request flow (one trip request)

```
1. Browser                POST /agui with the user message
2. Vite proxy             → :8003
3. AG-UI server           ADKAgent runs the orchestrator
4. Orchestrator (LLM)     calls flight_agent and hotel_agent as tools
5. A2A                    → Flight agent (:8002), Hotel agent (:8005), found via Agent Cards
6. Specialist (LLM)       converts city names to codes, calls its MCP tool
7. MCP                    → Flights (:8001) / Hotels (:8004) servers filter the mock data
8. Results flow back      specialists summarize; orchestrator merges into one plan
9. AG-UI events stream    TEXT_MESSAGE_CONTENT chunks → browser
10. React                 appends chunks to the chat bubble
```

**Who does what**

| Piece | Contributes | Does not do |
|---|---|---|
| MCP servers | The data (mock) | No reasoning |
| Specialist agents | Reasoning: codes, tool calls, recommendations | Store no data |
| A2A | The link between agents | Doesn't change content |
| Orchestrator | Routing and merging | Doesn't know how searches work |
| AG-UI | Streams the run to the browser | Generates no content |
| React | Display | Contains no travel logic |

## Concepts demonstrated so far

| Concept | Where |
|---|---|
| MCP tools, resources, prompts | Steps 1, 6 |
| MCP elicitation and progress reporting | Step 1 (not used by the agents yet) |
| MCP transports (stdio, Streamable HTTP) | Steps 1, 6 |
| AI agent = model + instructions + tools in a loop | Steps 2, 6 |
| MCP client inside an agent | Steps 2, 6 |
| A2A server and Agent Card | Steps 3, 6 |
| A2A client, opaque agents | Step 6 |
| `sub_agents` (transfer) vs `AgentTool` (call and merge) | Steps 4, 6 |
| AG-UI event streaming to a browser | Step 5 |

## Next steps

7. **A2UI.** The Hotel agent returns hotel cards as a declarative UI description (`createSurface`, `updateComponents`, `updateDataModel`, `deleteSurface`), and React renders them from a trusted component catalog. Needs research first: the current spec version, whether a React renderer exists, and how the surface travels (over A2A, AG-UI, or both). A2UI renamed its messages between versions, so pin the version.
8. **MCP App.** A `pick_seat` tool returns a `ui://` HTML seat map that the React app renders in a sandboxed iframe. Needs research on the MCP Apps client library for React.
9. **Optional extras:**
   - Replace the hand-written AG-UI client with CopilotKit or `@ag-ui/client`
   - Re-enable `choose_seat_preference` once elicitation is supported end to end
   - Add a LangGraph agent to show A2A interoperability across frameworks
   - Add return flights to the mock data

## Open questions

- Does `AgentTool` wrapping a `RemoteA2aAgent` work in your ADK version? (It follows a third-party cookbook, not ADK's own docs.)
- Do the AG-UI event field names in `App.tsx` match what the adapter emits, especially when agents are called as tools?
- Does the generated Agent Card include the MCP-derived tools as skills?
- Does ADK's MCP client support elicitation?
- Which React renderers exist for A2UI and MCP Apps, and how do they connect to AG-UI?