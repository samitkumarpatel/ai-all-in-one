# Trip Planner: Build Log

A step-by-step record of the trip-planner demo, built to show MCP, MCP Apps, AI agents, A2A, AG-UI, and A2UI working together.

> ⚠️ These specs and SDKs change quickly. Pin your versions once things work.
>
> **What has been tested (2026-10-10):** the MCP servers, the Agent Card, the orchestrator's `show_seat_map` tool, and **both frontends in a real (headless) browser**. The browser test used a mock AG-UI server that replays real tool results (A2UI cards + the seat-map MCP App), so the hotel cards, the seat map, and seat/book messages going back to the agent all work. **Not tested yet:** the full LLM path (Azure model + A2A calls). That needs your Azure `.env`, so run the "Try it" prompt below to check it.

## Status

| Step | What | Status |
|---|---|---|
| 1 | Flights MCP server | Code written |
| 2 | Flight agent (ADK + Azure model) using the MCP server | Code written |
| 3 | Flight agent exposed over A2A | Code written |
| 4 | First orchestrator (`sub_agents`) | Superseded by Step 6 |
| 5 | AG-UI server + React chat UI with live event log | Code written |
| 6 | Hotel agent + orchestrator calling both agents as tools | Code written, Agent Card checked |
| 7 | A2UI hotel cards, built two ways: **A** CopilotKit, **B** direct `@a2ui/react` | Done, browser-tested |
| 8 | MCP App: seat picker as a sandboxed `ui://` iframe, in both frontends | Done, browser-tested |
| 9 | Docker Compose: the whole stack in Alpine images, with one command | Done, stack-tested |

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
                       │  A2A (agents as tools)
                       │  + show_hotels   (A2UI cards)
                       │  + show_seat_map (MCP App) ──── MCP ────┐
          ┌────────────┴────────────┐                          │
          ▼                         ▼                          │
   Flight agent (:8002)      Hotel agent (:8005)               │
          │  MCP                    │  MCP                     │
          ▼                         ▼                          │
   Flights MCP (:8001) ◄────────────┼──────────────────────────┘
   ├─ mock FLIGHTS list      Hotels MCP (:8004)
   └─ ui://flights/seat-map.html   └─ mock HOTELS list
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
| Interactive tool UI | MCP Apps (spec `2026-01-26`): FastMCP `AppConfig` + `ui://` resource, hand-written iframe host |
| Containers | Docker Compose, Alpine images (`python:3.14-alpine` + `uv`, `node:22-alpine`, `nginx:1.29-alpine`) |
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
├── docker-compose.yml       Runs everything (Step 9). Each service folder has a Dockerfile + .dockerignore
├── mcp-servers/
│   ├── flights/             (server.py, seat_map.html)
│   └── hotels/server.py
├── agents/
│   ├── flight_a2a.py
│   ├── hotel_a2a.py
│   ├── agui_server.py
│   ├── flight_agent/        (__init__.py, agent.py, .env)
│   ├── hotel_agent/         (__init__.py, agent.py, .env)
│   └── orchestrator_agent/  (__init__.py, agent.py, a2ui_hotels.py, mcp_app_seats.py, .env)
├── web/                     Option B (own AG-UI client + @a2ui/react)
│   └── src/ (agui.ts, a2ui.tsx, mcpApp.tsx, App.tsx, App.css, index.css, main.tsx)
├── web/nginx.conf, web-copilotkit/nginx.conf   Serve the built apps in Docker
├── copilot-runtime/         Option A backend (Node)
│   ├── package.json
│   └── server.ts
└── web-copilotkit/          Option A frontend
    ├── vite.config.ts
    └── src/ (catalog.tsx, mcpApp.tsx, App.tsx, App.css, index.css, main.tsx)
```

Some files share names across frontends. `App.tsx` and `App.css` have different contents. `mcpApp.tsx` is the same in both apps, copied so each frontend stays self-contained.

## Running everything

### With Docker (one command)

```sh
cd trip-planner
# Put the Azure secrets in a Docker env file. Default: trip-planner/.env (see "Environment files")
docker compose up --build
# or, with the env file somewhere else:
ENV_FILE=/path/to/azure.env docker compose up --build
```

Then open **http://localhost:5173** (Option B) or **http://localhost:5174** (Option A). Details are in Step 9.

### Without Docker

Start the backend (1 to 5) first, **in this order**, then **either or both** frontends. Each A2A agent lists its MCP tools when it starts, so its MCP server must already be running.

```sh
# 1. Flights MCP (8001)
cd mcp-servers/flights && uv run server.py

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

Notes:

- Both MCP servers run over Streamable HTTP by default. Add `stdio` to run either one over stdio instead.
- Start the A2A agents before using the orchestrator, because it fetches their Agent Cards on use.
- Restart terminals 3 to 5 after changing an agent.

**Try it:** ask *"Plan a weekend in Amsterdam from Copenhagen. Fly out 2026-10-10 and come back 2026-10-12."* You should get flight and hotel badges, hotel cards, and a short itinerary. Then ask *"Show me the seat map for FL101"*, pick a seat, and click **Confirm**.

## Environment files

**With Docker,** use one env file for all three agent containers: `trip-planner/.env`, or any file passed as `ENV_FILE`. It needs only the four `AZURE_*` lines below. The URLs are set in `docker-compose.yml`.

**Without Docker,** each agent folder has its own `.env` (hidden files, check with `ls -a`), with the same values unless you want different models per agent:

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
- `.gitignore` already contains `__pycache__/`, `.env`, and `node_modules/`. Never commit real keys. `.dockerignore` keeps `.env` out of the images, so secrets only enter containers at run time.

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
| Tool with a UI (MCP App, Step 8) | `pick_seat(flight_id)` linked to the `ui://flights/seat-map.html` resource |
| Resources (app-controlled) | `airports://list` and the template `flight://{flight_id}` |
| Prompt (user-controlled) | `plan_weekend(origin, destination, date)` |
| Transports | Streamable HTTP (default) and stdio (`uv run server.py stdio`) |

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

**Return flights:** the mock data has return routes back to CPH (`FL102`, `FL103`, `FL201`, `FL301`, `FL401`). The orchestrator asks the Flight agent for both directions, and the Flight agent always includes flight ids, which the seat map (Step 8) needs.

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
| `web/src/App.tsx` | Same chat and event log as Step 5, plus a `TOOL_CALL_RESULT` handler that feeds operations to the renderer. Clicking **Book** sends "Book hotel H-AMS-2." to the agent as a user message |

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
- **Option B styling:** the cards render with the renderer's default look. For more styling, check the `@a2ui/react` README for a stylesheet to import.
- **AG-UI 1.0** was announced on September 30, 2026. If event shapes differ from what the hand-written client expects, update `ag-ui-adk`.
- **Book button:** Option B sends the action to the agent as a chat message. Option A still only shows "Booked ✓ (demo)" locally, because `catalog.tsx` overrides the Button.

## Step 8: MCP App seat picker

**Goal:** let the user pick a seat on a real seat map, using **MCP Apps**. The tool comes with its own small HTML app, which the browser shows in a sandboxed iframe. This is the "open-ended HTML" side of the comparison, in contrast to A2UI's declarative JSON in Step 7.

### How it works

```
1. Orchestrator (LLM)  calls show_seat_map("FL101")
2. show_seat_map       acts as the MCP client:
                         tools/list      -> pick_seat has _meta.ui.resourceUri = ui://flights/seat-map.html
                         tools/call      -> pick_seat {flight_id} -> {rows, letters, taken}
                         resources/read  -> the HTML
                       returns { mcp_app: { resourceUri, html, toolInput, toolResult } }
3. AG-UI               streams that as a TOOL_CALL_RESULT, the same way as the A2UI cards
4. Browser             finds mcp_app and renders <iframe sandbox="allow-scripts" srcdoc=html>
5. iframe <-> page     JSON-RPC over postMessage (below)
6. User clicks Confirm the app sends ui/message, and the page sends it to the agent as a user message
```

The iframe and the page exchange these messages:

| Direction | Message | Purpose |
|---|---|---|
| app → host | `ui/initialize` (request) | Handshake. The host replies with its capabilities (`message`) and theme |
| app → host | `ui/notifications/initialized` | App is ready |
| host → app | `ui/notifications/tool-input` | The tool arguments (`{flight_id}`) |
| host → app | `ui/notifications/tool-result` | The `pick_seat` result. The app draws the seats from `structuredContent` |
| app → host | `ui/notifications/size-changed` | The app's height, so the iframe fits |
| app → host | `ui/message` (request) | "I'd like seat 1A on flight FL101." goes into the chat |

### Files

| File | Role |
|---|---|
| `mcp-servers/flights/server.py` | `@mcp.tool(app=AppConfig(resource_uri=...))` on `pick_seat`, plus `@mcp.resource("ui://flights/seat-map.html")`. FastMCP gives `ui://` resources the MIME type `text/html;profile=mcp-app` automatically. Taken seats are random but seeded by flight id, so they are the same every time |
| `mcp-servers/flights/seat_map.html` | The app (the "view"). Plain HTML and JS, with no build step and no dependencies. The postMessage code is about 20 lines |
| `agents/orchestrator_agent/mcp_app_seats.py` | `build_seat_map_app()`: the MCP-client half of the host (steps 1 and 2 above), using `fastmcp.Client` |
| `agents/orchestrator_agent/agent.py` | `show_seat_map(flight_id)` tool. Errors such as an unknown flight come back as `{"error": ...}` |
| `web/src/mcpApp.tsx` | The browser half of the host: `extractMcpApp()` and `<McpAppFrame>`, the iframe plus postMessage bridge |
| `web/src/App.tsx` (Option B) | Renders an `McpAppFrame` for each `mcp_app` tool result. `ui/message` text is sent like typed text |
| `web-copilotkit/src/App.tsx` (Option A) | `useRenderTool({ name: "show_seat_map", ... })` draws the same `McpAppFrame` inside `CopilotChat`. `ui/message` uses `agent.addMessage()` and `copilotkit.runAgent()` |

**Setup:** `cd agents && uv add fastmcp` (already in `pyproject.toml`).

### Design decisions

| Decision | Why |
|---|---|
| **Orchestrator shows the app**, not the Flight agent | Same reason as A2UI: a UI sent through A2A would be flattened to text. `pick_seat` stays out of the Flight agent's `tool_filter` |
| **Host split in two:** Python does MCP, the browser does the iframe | The orchestrator is already the MCP client. The browser needs no MCP connection and no extra endpoint, because everything travels in one AG-UI tool result |
| **Hand-written postMessage on both sides** | Every protocol message is visible in about 60 lines. Real hosts use `AppBridge`, and real apps use `App`, from `@modelcontextprotocol/ext-apps` (v2.0.3 at time of writing) |
| **`sandbox="allow-scripts"` without `allow-same-origin`** | The app runs in an opaque origin, so it cannot read the page, its cookies or its storage. `postMessage` is its only way out |
| **`ui/message` instead of `tools/call` from the app** | The seat choice becomes a normal chat turn, so the agent sees it and confirms it. The host does not have to proxy MCP calls |

### Verify

- *"Show me the seat map for FL101"* shows a `show_seat_map` badge and an 8-row seat map with 16 grey (taken) seats.
- Pick a seat and click **Confirm**. The message *"I'd like seat 1A on flight FL101."* appears as your message, and the agent confirms it.
- **Option B:** in the event panel, the `TOOL_CALL_RESULT` for `show_seat_map` has `content` that starts with `{"mcp_app":`.

### Things that may go wrong

- **"Could not show the seat map":** the Flights MCP server (8001) is not running, or the flight id is unknown.
- **Empty seat map ("Waiting for flight data…"):** the handshake failed. Check the browser console for errors from `mcpApp.tsx`.
- **The LLM sees the HTML too.** The whole tool result, about 5 KB of HTML, goes into the model's context. That is fine for a demo. A real host would keep the HTML out of the model's context.
- **CopilotKit `useRenderTool` deps** must not include the agent object, because CopilotKit serialises the deps and the agent has circular references. That is why `sendToAgent` looks up the agent with `copilotkit.getAgent("default")` when it is called.

## Step 9: Docker Compose

**Goal:** run all eight services with one command, using small Alpine-based images.

**File:** `trip-planner/docker-compose.yml`, plus a `Dockerfile` and `.dockerignore` in each service folder.

| Service | Image | Base | Size (approx.) | Host port |
|---|---|---|---|---|
| `flights-mcp` | `mcp-servers/flights/Dockerfile` | `python:3.14-alpine` + `uv` | 265 MB | 8001 |
| `hotels-mcp` | `mcp-servers/hotels/Dockerfile` | `python:3.14-alpine` + `uv` | 265 MB | 8004 |
| `flight-agent`, `hotel-agent`, `orchestrator` | `agents/Dockerfile`: **one image**, a different `command` each | `python:3.14-alpine` + `uv` | 831 MB (mostly google-adk + litellm) | 8002, 8005, 8003 |
| `copilot-runtime` | `copilot-runtime/Dockerfile` | `node:22-alpine` | 446 MB | 4000 |
| `web` (Option B) | `web/Dockerfile`: Vite build, then nginx | `node:22-alpine` → `nginx:1.29-alpine` | 63 MB | 5173 (`WEB_PORT`) |
| `web-copilotkit` (Option A) | `web-copilotkit/Dockerfile`: Vite build, then nginx | `node:22-alpine` → `nginx:1.29-alpine` | 79 MB | 5174 (`WEB_COPILOTKIT_PORT`) |

### How it fits together

- **Start order** comes from healthchecks and `depends_on`: MCP servers → A2A agents (healthy once their Agent Card is served) → orchestrator → frontends. This is the same order as the manual steps, because each A2A agent lists its MCP tools at startup.
- **Service names replace `127.0.0.1`.** The code reads `HOST` (MCP servers), `A2A_HOST` (Agent Card host), and the existing `*_URL` variables. All of these default to the local values, so running without Docker works as before.
- **Python images** install from `uv.lock` (`uv sync --locked`), with dependencies in their own layer, so changing code doesn't reinstall them. Every package has an Alpine (musl) wheel, so nothing is compiled.
- **Frontends** are built once and served by nginx. `nginx.conf` does what the Vite dev proxy does: `/agui` → `orchestrator:8003` (Option B), `/api/copilotkit` → `copilot-runtime:4000` (Option A). `proxy_buffering off` keeps the SSE stream live.
- **Secrets** come from a Docker env file (`env_file: ${ENV_FILE:-.env}`) and go only to the three agent containers. Compose stops with "env file … not found" if the file is missing.

### The `.localhost` aliases (why the agents have two names)

ADK 2.11's A2A client (`RemoteA2aAgent`) refuses Agent Cards served over plain `http` unless the host is a "localhost" name. Without TLS, `http://flight-agent:8002` fails with *"Agent card URL must use https, or http on a loopback host"*. ADK treats any name ending in `.localhost` as local, so the compose file gives the two agents the network aliases `flight-agent.localhost` and `hotel-agent.localhost`. They advertise those names in their cards, and the orchestrator uses them too. For a real deployment, use https instead.

### Verify

Tested on 2026-10-10 with Docker 29 and Compose v5, using dummy Azure values:

- `docker compose up --build` starts all 8 containers in order, and all 5 Python services report healthy.
- `http://localhost:8002/.well-known/agent-card.json` advertises `http://flight-agent.localhost:8002`.
- Inside `orchestrator`, both Agent Cards resolve, and `show_seat_map("FL102")` returns the MCP App from `flights-mcp`.
- `POST http://localhost:5173/agui` streams AG-UI events through nginx (with dummy keys, the run ends in a `RUN_ERROR` from Azure, as expected). `http://localhost:5174/api/copilotkit/info` returns 200.

### Useful commands

```sh
docker compose up --build -d                 # start in the background
docker compose logs -f orchestrator          # follow one service
docker compose up --build -d orchestrator    # rebuild one service after a code change
docker compose down                          # stop and remove everything
WEB_PORT=5180 docker compose up -d           # if 5173 is already in use on your machine
```

Note: from your machine, the Agent Cards on ports 8002 and 8005 advertise `*.localhost` names. Those names work inside Docker. Most browsers and tools also resolve `*.localhost` to 127.0.0.1, so the A2A Inspector can usually use them too.

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
12. Seat map (on request) show_seat_map fetches the MCP App from Flights MCP; the browser shows it in an iframe
13. User picks a seat     the app sends ui/message, which goes back to the orchestrator as a user message
```

**Who does what**

| Piece | Contributes | Does not do |
|---|---|---|
| MCP servers | The data (mock) | No reasoning |
| Specialist agents | Reasoning: codes, tool calls, recommendations | Store no data |
| A2A | The link between agents | Doesn't change content |
| Orchestrator | Routing, merging, and choosing to show UI | Doesn't know how searches work |
| `a2ui_hotels.py` | The fixed card layout | No LLM involved |
| `seat_map.html` (MCP App) | The seat-picker UI and its logic | Doesn't know about agents or AG-UI |
| AG-UI | Streams the run to the browser | Generates no content |
| Renderer / iframe host | Draws cards from A2UI data, and runs the MCP App in a sandbox | Contains no travel logic |

## Concepts demonstrated

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
| MCP Apps: `_meta.ui.resourceUri`, `ui://` resource, sandboxed iframe, postMessage JSON-RPC | Step 8 |
| Declarative UI (A2UI) vs open-ended HTML (MCP Apps) | Steps 7 and 8 |
| UI actions going back to the agent (A2UI Book, MCP App `ui/message`) | Steps 7 and 8 |
| Running a multi-agent system in containers (service discovery, start order, secrets) | Step 9 |

## Next steps (optional extras)

All planned steps are done. Possible extras:

- Run the full LLM path with your Azure `.env` and record the results here
- Send Option A's Book action to the agent too (drop the Button override in `catalog.tsx`, or call the agent from it)
- Switch the MCP App code to the official `@modelcontextprotocol/ext-apps` SDK (`App` in the view, `AppBridge` in the host)
- Keep the MCP App HTML out of the LLM context (for example, send only `resourceUri`, and let the browser fetch the HTML)
- Re-enable `choose_seat_preference` once elicitation is supported end to end
- Add a LangGraph agent to show A2A interoperability across frameworks
- Try the dynamic-schema A2UI approach (LLM-designed UI) and compare with the fixed one

## Open questions

Still open (need the real LLM run):

- Does `AgentTool` wrapping a `RemoteA2aAgent` work end to end in ADK 2.11? (The card resolves, but no A2A call has been made yet.)
- Does ADK's MCP client support elicitation?

Answered on 2026-10-10 (google-adk 2.11, ag-ui-adk 0.8, fastmcp 4.1, CopilotKit 1.77, @a2ui 0.12):

| Question | Answer |
|---|---|
| Do the hand-written client's AG-UI field names match the adapter? | Yes. `TOOL_CALL_RESULT` has `toolCallId` and `content` |
| Is `a2ui_operations` at the top level of the tool result? | Yes. `ag_ui_adk` sends the tool's returned dict as a JSON string, unchanged. Same for `mcp_app` |
| Does the Agent Card list MCP tools as skills? | No. With A2A 1.0, the card has a single skill (the agent itself), and the URL is under `supportedInterfaces` |
| Option A: do `createCatalog` (two overrides) and `createCopilotExpressHandler` work? | Yes. Cards render in `CopilotChat` through the runtime |
| Option B: what is `MessageProcessor`'s action handler? | `(action: ActionPayload) => void`, with `action.name` and `action.context` |