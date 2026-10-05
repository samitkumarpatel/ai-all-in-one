# Trip Planner: Build Log

A step-by-step record of the trip-planner demo, built to show MCP, MCP Apps, AI agents, A2A, AG-UI, and A2UI working together.

> ⚠️ These specs and SDKs change quickly. APIs below were checked against current docs, but **none of the code has been run end to end yet**. Treat each step's "Verify" section as the source of truth, and pin your versions once things work.

## Status

| Step | What | Status |
|---|---|---|
| 1 | Flights MCP server | Code written |
| 2 | Flight agent (ADK + Azure model) using the MCP server | Code written |
| 3 | Flight agent exposed over A2A | Code written |
| 4 | First orchestrator (`sub_agents`) | Superseded by Step 6 |
| 5 | AG-UI server + React chat UI with live event log | Code written |
| 6 | Hotel agent + orchestrator calling both agents as tools | Code written |
| 7 | A2UI hotel cards, built two ways: **A** CopilotKit, **B** direct `@a2ui/react` | Code written |
| 8 | MCP App: seat picker as a sandboxed `ui://` iframe | Not started |

## Architecture

```
 Option B: web/ (:5173)            Option A: web-copilotkit/ (:5174)
 own AG-UI client                          │ CopilotKit
 + @a2ui/react renderer                    ▼
        │                          CopilotKit runtime (:4000, Node)
        │ AG-UI (SSE)                      │ AG-UI
        └──────────────┬───────────────────┘
                       ▼
        AG-UI server (:8003)  ── hosts the Orchestrator agent
                       │  A2A (agents as tools) + show_hotels tool (A2UI)
          ┌────────────┴────────────┐
          ▼                         ▼
   Flight agent (:8002)      Hotel agent (:8005)
          │  MCP                    │  MCP
          ▼                         ▼
   Flights MCP (:8001)       Hotels MCP (:8004)
   └─ mock FLIGHTS list      └─ mock HOTELS list
```

Both frontends talk to the **same** Python backend. Only the browser side differs.

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
| Generative UI | A2UI v0.9, fixed schema, basic-catalog components |
| Frontend A | React + Vite + CopilotKit (`@copilotkit/react-core/v2`, `@copilotkit/a2ui-renderer`) + Node runtime |
| Frontend B | React + Vite + TypeScript, hand-written AG-UI client + `@a2ui/react` + `@a2ui/web_core` |

## Ports

| Port | Service | Role |
|---|---|---|
| 8000 | `adk web` | Optional dev UI for debugging agents |
| 8001 | Flights MCP server | MCP server |
| 8002 | Flight agent | A2A server |
| 8003 | AG-UI server (orchestrator) | AG-UI server, A2A client |
| 8004 | Hotels MCP server | MCP server |
| 8005 | Hotel agent | A2A server |
| 4000 | CopilotKit runtime | Option A only |
| 5173 | `web/` React app | Option B |
| 5174 | `web-copilotkit/` React app | Option A |

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
│   └── orchestrator_agent/  (__init__.py, agent.py, a2ui_hotels.py, .env)
├── web/                     Option B (own AG-UI client + @a2ui/react)
│   └── src/ (agui.ts, a2ui.tsx, App.tsx, App.css, index.css, main.tsx)
├── copilot-runtime/         Option A backend (Node)
│   ├── package.json
│   └── server.ts
└── web-copilotkit/          Option A frontend
    ├── vite.config.ts
    └── src/ (catalog.tsx, App.tsx, App.css, index.css, main.tsx)
```

Two files share names across frontends (`App.tsx`, `App.css`) but have different contents. Keep each in its own folder.

## Running everything

Start the backend (1 to 5) first, then **either or both** frontends.

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

# 6. Option B frontend (5173)
cd web && npm run dev

# 7. Option A runtime (4000)
cd copilot-runtime && npm run dev

# 8. Option A frontend (5174)
cd web-copilotkit && npm run dev
```

Note: the Flights server needs the `http` argument, while the Hotels server runs over HTTP by default. Start the A2A agents before using the orchestrator, because it fetches their Agent Cards on use. Restart terminals 4 and 5 after any change to the hotel or orchestrator agents.

**Try it:** ask *"Plan a weekend in Amsterdam from Copenhagen. Fly out 2026-10-10 and come back 2026-10-12."*

## Environment files

Each agent folder has its own `.env` (hidden files, check with `ls -a`), with the same values unless you want different models per agent:

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
- The CopilotKit runtime reads optional `AGUI_URL` (default `http://127.0.0.1:8003/agui`) and `PORT` (default 4000).
- `.gitignore` should contain `__pycache__/`, `.env`, and `node_modules/`. Commit `.env.example` files instead of real keys.

**Azure notes**

- The string after `azure/` is the **deployment name**, not the base model name.
- The endpoint may be the `*.openai.azure.com` or `*.services.ai.azure.com` form. Try the other if one fails.
- Newer models may need a newer `AZURE_API_VERSION`, and GPT-5 / o-series models may need LiteLLM prefixes such as `azure/gpt5_series/<deployment>`.
- Not every model handles tool calling well. If an agent answers without calling a tool, try a stronger deployment.

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

**Files:** `agents/agui_server.py`, `web/`

**Backend:** `ADKAgent` (from `ag_ui_adk`) adapts ADK runs into AG-UI events, and `add_adk_fastapi_endpoint(app, adk_agent, path="/agui")` serves them as a Server-Sent Events stream. Requires google-adk 1.16 or newer.

**Setup:** `cd agents && uv add ag-ui-adk fastapi`

**Frontend (`web/`):** Vite + React + TypeScript.

- `src/agui.ts` is a small custom AG-UI client: it POSTs a run request and parses the SSE event stream.
- `src/App.tsx` is a chat UI mapping events to the screen (`TEXT_MESSAGE_START/CONTENT`, `TOOL_CALL_START`, `RUN_ERROR`), plus a side panel listing every raw event.
- `vite.config.ts` proxies `/agui` to port 8003, so no CORS setup is needed.

**Design choices**

- **Why not just `adk web`?** `adk web` is a developer tool: traces, sessions, evals. A custom UI is needed for end users, branding, rich UI (A2UI, MCP Apps), and agents from other frameworks.
- **No React Router.** It is a single-screen app.

**Test the backend directly:**

```sh
curl -N -X POST http://127.0.0.1:8003/agui \
  -H "Content-Type: application/json" -H "Accept: text/event-stream" \
  -d '{"threadId":"t1","runId":"r1","state":{},"tools":[],"context":[],"forwardedProps":{},
       "messages":[{"id":"m1","role":"user","content":"Flights CPH to AMS on 2026-10-10?"}]}'
```

**Verify:** the reply streams into the chat, the events panel fills, and tool calls show as 🔧 badges.

## Step 6: Hotel agent and multi-agent orchestration

| File | Purpose |
|---|---|
| `mcp-servers/hotels/server.py` | Hotels MCP server: `search_hotels` tool (sorted by price, computes nights and total), `cities://list` and `hotel://{hotel_id}` resources |
| `agents/hotel_agent/` | ADK agent using `search_hotels` over MCP |
| `agents/hotel_a2a.py` | Exposes the Hotel agent over A2A (port 8005) |
| `agents/orchestrator_agent/agent.py` | Calls both specialists as tools |

```python
tools=[AgentTool(agent=flight_agent), AgentTool(agent=hotel_agent)]
```

`RemoteA2aAgent` fetches each agent card, and `AgentTool` presents the remote agent as a tool. The orchestrator gets each result back, so it can merge flights and hotels into one itinerary. The specialists cannot see the user's conversation, so the orchestrator's instruction tells it to pass airport codes and ISO dates in each request.

**Setup:** `cd mcp-servers/hotels && uv init --bare && uv add fastmcp`, then copy `flight_agent/.env` to `hotel_agent/.env`.

**Verify:** both agent cards load (`:8002` and `:8005`), a trip request shows two tool badges (`flight_agent`, `hotel_agent`), and all four backend terminals log activity.

**Known limitation:** the Flights server only has outbound routes from CPH, so there are no return flights.

## Step 7: A2UI hotel cards (two options)

**Goal:** show hotel results as real UI cards instead of text, using the A2UI protocol, built two ways so you can compare them.

### How it works (shared backend)

1. The Hotel agent now lists **every** hotel with all fields (`id, name, area, stars, rating, price_per_night_eur, nights, total_eur`).
2. The orchestrator has a new tool, `show_hotels(hotels_json)`, and is told to call it **exactly once** after the Hotel agent answers.
3. `show_hotels` calls `build_hotel_operations()` in `agents/orchestrator_agent/a2ui_hotels.py`, which returns `{"a2ui_operations": [createSurface, updateComponents, updateDataModel]}` in A2UI v0.9.
4. The AG-UI server streams that tool result to the browser, where a renderer turns it into cards.

### Design decisions

| Decision | Why |
|---|---|
| **Fixed schema** (layout authored in Python, LLM supplies only data) | Deterministic, no LLM-designed UI, fastest to render |
| **Orchestrator renders the cards**, not the Hotel agent | A UI payload sent through `AgentTool` would be flattened to text for the LLM. Specialists return data, the orchestrator turns it into UI |
| **Only basic-catalog components** (Card, Column, Text, Button) | The same payload renders in both frontends |
| **`hotels_json: str` parameter** instead of a typed list | Avoids schema-parsing problems with `list[dict]` across models |
| **Flat data-model keys** (`/hotel0_name`) | Keeps JSON Pointer paths trivial |
| **Fresh surface id per call** (`hotels-<uuid>`) | Surfaces from different questions can coexist without "already exists" errors |
| **Catalog id `copilotkit://trip-planner-catalog`** | Option A registers this id. Option B rewrites it to the basic catalog id |

### Option A: CopilotKit

```
React (CopilotKit) → Node runtime (:4000) → Python AG-UI server (:8003/agui)
```

| File | Role |
|---|---|
| `copilot-runtime/server.ts` | Express + `createCopilotExpressHandler`. Registers the Python server as an `HttpAgent` named `default`, with `a2ui: { injectA2UITool: false, agents: ["default"] }` because our own tool owns the schema |
| `web-copilotkit/src/catalog.tsx` | `createCatalog` with `includeBasicCatalog: true`, overriding **Card** (styled box) and **Button** (local "Booked ✓ (demo)" state) |
| `web-copilotkit/src/App.tsx` | `<CopilotKit runtimeUrl="/api/copilotkit" a2ui={{ catalog }}>` plus `<CopilotChat agentId="default" />` |
| `web-copilotkit/vite.config.ts` | Port 5174, proxy `/api/copilotkit` to :4000 |

Setup:

```sh
cd copilot-runtime
npm install express @ag-ui/client @copilotkit/runtime
npm install -D tsx typescript @types/express @types/node

npm create vite@latest web-copilotkit -- --template react-ts
cd web-copilotkit && npm install
npm install @copilotkit/react-core @copilotkit/a2ui-renderer zod
# then overwrite vite.config.ts and src/{App.tsx,catalog.tsx,App.css,index.css}
```

### Option B: direct `@a2ui/react`

```
React (own AG-UI client + MessageProcessor) → Python AG-UI server (:8003/agui)
```

| File | Role |
|---|---|
| `web/src/a2ui.tsx` | `extractA2uiOperations()` finds `a2ui_operations` in a tool result. `useA2ui()` creates a `MessageProcessor([basicCatalog])`, tracks surfaces, and rewrites `catalogId` to the basic catalog. `Surfaces` renders each `<A2uiSurface>` |
| `web/src/App.tsx` | Same chat and event log as Step 5, plus a `TOOL_CALL_RESULT` handler that feeds operations to the renderer and shows a note when "Book" is clicked |

Setup: `cd web && npm install @a2ui/react @a2ui/web_core`

### Comparison

| | Option A: CopilotKit | Option B: direct renderer |
|---|---|---|
| Extra moving parts | Node runtime + CopilotKit packages | None beyond two npm packages |
| Documented path for A2UI + ADK | Yes | Partly (renderer docs, but AG-UI wiring is custom) |
| Raw AG-UI event view | CopilotKit dev inspector | Built-in event panel (our code) |
| Chat UI | Prebuilt `CopilotChat` | Hand-written |
| Custom components | Via `createCatalog` renderers | Via a custom catalog passed to `MessageProcessor` |
| Best for | Production-style app, later steps (shared state, human-in-the-loop) | Learning how A2UI rides on AG-UI |

### Verify

- A trip request produces `flight_agent` and `hotel_agent` tool badges, a `show_hotels` call, hotel cards, and a short itinerary summary.
- **Option B:** in the event panel, find the `TOOL_CALL_RESULT` for `show_hotels` and check its `content` includes `a2ui_operations`.
- **Option A:** open the CopilotKit dev inspector to see the AG-UI events.

### Things that may go wrong

- **No cards, only text:** the model skipped `show_hotels`. Tighten the orchestrator instruction, or check that the Hotel agent really listed all fields.
- **Repeated tool calls:** models sometimes re-call this kind of tool, which is why the docstring says "do NOT call again".
- **Unverified API details:** the `MessageProcessor` action-handler signature (Option B), whether `createCatalog` accepts only two overrides, and `CopilotChat` props (Option A) follow the docs but have not been run.
- **Option B styling:** if cards look unstyled, check the `@a2ui/react` README for a stylesheet to import.
- **AG-UI 1.0** was announced on September 30, 2026. If event shapes differ from what the hand-written client expects, update `ag-ui-adk`.
- **Book button** is local-only in both options. Neither sends the action back to the agent yet.

---

## Request flow (one trip request)

```
1. Browser                POST (AG-UI run request), directly (B) or via the CopilotKit runtime (A)
2. AG-UI server (:8003)   ADKAgent runs the orchestrator
3. Orchestrator (LLM)     calls flight_agent and hotel_agent as tools
4. A2A                    → Flight agent (:8002), Hotel agent (:8005), found via Agent Cards
5. Specialist (LLM)       converts city names to codes, calls its MCP tool
6. MCP                    → Flights (:8001) / Hotels (:8004) servers filter the mock data
7. Results flow back      specialists summarize; hotel agent lists every hotel with all fields
8. Orchestrator (LLM)     calls show_hotels once; the tool returns A2UI operations
9. AG-UI events stream    TEXT_MESSAGE_CONTENT, TOOL_CALL_*, and the A2UI tool result → browser
10. Renderer              @a2ui/react (B) or CopilotKit's A2UI middleware (A) draws the cards
11. Orchestrator (LLM)    adds a short itinerary summary with an estimated total
```

**Who does what**

| Piece | Contributes | Does not do |
|---|---|---|
| MCP servers | The data (mock) | No reasoning |
| Specialist agents | Reasoning: codes, tool calls, recommendations | Store no data |
| A2A | The link between agents | Doesn't change content |
| Orchestrator | Routing, merging, and choosing to show UI | Doesn't know how searches work |
| `a2ui_hotels.py` | The fixed card layout | No LLM involved |
| AG-UI | Streams the run to the browser | Generates no content |
| Renderer | Draws cards from A2UI data | Contains no travel logic |

## Concepts demonstrated so far

| Concept | Where |
|---|---|
| MCP tools, resources, prompts | Steps 1, 6 |
| MCP elicitation and progress reporting | Step 1 (not used by the agents yet) |
| MCP transports (stdio, Streamable HTTP) | Steps 1, 6 |
| AI agent = model + instructions + tools in a loop | Steps 2, 6, 7 |
| MCP client inside an agent | Steps 2, 6 |
| A2A server and Agent Card | Steps 3, 6 |
| A2A client, opaque agents | Step 6 |
| `sub_agents` (transfer) vs `AgentTool` (call and merge) | Steps 4, 6 |
| AG-UI event streaming to a browser | Step 5 |
| A2UI: `createSurface`, `updateComponents`, `updateDataModel` | Step 7 |
| Declarative UI with a fixed schema and trusted catalog | Step 7 |
| Two AG-UI clients: hand-written vs CopilotKit | Steps 5 and 7 |

## Next steps

8. **MCP App.** A `pick_seat` tool returns a `ui://` HTML seat map that the React app renders in a sandboxed iframe. This is the "open-ended HTML" side of the UI-spec comparison, in contrast to A2UI's declarative approach. Needs research on the MCP Apps client library for React, and on how to pass it through the agent stack.
9. **Optional extras:**
   - Send the Book button's action back to the agent (A2UI action handlers)
   - Re-enable `choose_seat_preference` once elicitation is supported end to end
   - Add a LangGraph agent to show A2A interoperability across frameworks
   - Add return flights to the mock data
   - Try the dynamic-schema A2UI approach (LLM-designed UI) and compare with the fixed one

## Open questions

- Does `AgentTool` wrapping a `RemoteA2aAgent` work in your ADK version? (It follows a third-party cookbook, not ADK's own docs.)
- Do the AG-UI event field names in the hand-written client match what the adapter emits, especially for tool results?
- Does the generated Agent Card include the MCP-derived tools as skills?
- Does ADK's MCP client support elicitation?
- Option A: does `createCatalog` work with only Card and Button overrides, and does `createCopilotExpressHandler` serve the routes `CopilotKit` expects without extra props?
- Option B: what is the exact action-handler signature of `MessageProcessor`, and does `@a2ui/react` need a stylesheet?
- Does ADK's tool-result serialization keep `a2ui_operations` at the top level, or wrap it (the client checks both `a2ui_operations` and `result.a2ui_operations`)?