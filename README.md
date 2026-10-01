# AI Protocols Playground: MCP, MCP Apps, A2A, AG-UI, A2UI

Hands-on demos for the protocols behind modern AI agents. Each section explains the concept, then points to the demo in this repo.

> ⚠️ These specs evolve quickly (A2UI, for example, renamed its messages between versions). Pin the versions you use and check the official docs.

## Table of Contents

- [The Big Picture](#the-big-picture)
- [MCP (Model Context Protocol)](#mcp-model-context-protocol)
- [MCP Apps](#mcp-apps)
- [AI Agents](#ai-agents)
- [A2A (Agent2Agent)](#a2a-agent2agent)
- [AG-UI (Agent–User Interaction)](#ag-ui-agentuser-interaction)
- [A2UI (Agent-to-UI)](#a2ui-agent-to-ui)
- [UI Spec Comparison](#ui-spec-comparison)

---

## The Big Picture

These protocols sit at different layers of an agentic app. They complement each other rather than compete.

| Layer | Protocol | Connects |
|---|---|---|
| Agent ↔ tools / data | **MCP** | LLM app → external systems |
| Agent ↔ agent | **A2A** | Agent → agent (different vendors / frameworks) |
| Agent ↔ user app | **AG-UI** | Agent backend → frontend, via event streaming |
| Agent → UI content | **A2UI / MCP Apps / MCP-UI / Open-JSON-UI** | *What* UI gets rendered |

**Rule of thumb:** MCP = agent-to-tool, A2A = agent-to-agent, AG-UI = agent-to-user-app, A2UI = the UI payload itself.

---

## MCP (Model Context Protocol)

An **open protocol**, created by Anthropic (Nov 2024) and now governed under the Linux Foundation, that standardizes how AI applications connect to external tools, data, and prompts.

The LLM *application* (host + client) connects to MCP *servers*. The model itself doesn't speak MCP; the app does.

### What this demo covers

- **Local servers**: `stdio` transport
- **Remote servers**: Streamable HTTP transport
- **SDKs**: official SDKs (TypeScript, Python, Java, C#, Kotlin, Go, ...), [FastMCP](https://gofastmcp.com) (Python), and Spring AI (Java)
- **MCP Inspector**: debug and test servers interactively
- **MCP Registry**: discover published servers

### Transports

| Transport | Use for | Notes |
|---|---|---|
| `stdio` | Local servers | Client launches the server as a subprocess |
| Streamable HTTP | Remote (and local) servers | Replaced the older HTTP+SSE transport |

### Server primitives

| Primitive | Controlled by | Purpose |
|---|---|---|
| **Tools** | Model | Let the AI act on external systems. Each tool defines an operation with an input and output schema |
| **Resources** | Application | Read-only data, identified by URI, that the app retrieves and provides as context |
| **Prompts** | User | Reusable prompt templates (like slash commands) for a domain, showing how to best use the server |

```python
from fastmcp import FastMCP

mcp = FastMCP("demo")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@mcp.resource("config://settings")
def settings() -> dict:
    return {"theme": "dark"}

@mcp.prompt(title="Code Review")
def review(code: str) -> str:
    return f"Please review this code:\n\n{code}"
```

### Client features

Features the *client* offers to servers:

- **Elicitation**: the server asks the user for input mid-operation
- **Sampling**: the server asks the client's LLM to generate a completion
- **Roots**: the client tells the server which filesystem/URI boundaries it may work in

### Other capabilities

- **Progress reporting & monitoring**: progress notifications for long operations (plus logging and cancellation)
- **Authorization**: OAuth-based auth for remote servers
- **Tasks**: newer, experimental support for long-running operations

---

## MCP Apps

An official MCP extension that lets a tool return an **interactive UI** along with its data.

- The UI is HTML served as a `ui://` resource
- The host renders it in a **sandboxed iframe**
- It grew out of the community **MCP-UI** project and OpenAI's Apps SDK, which converged on one standard

**Mental model:** a tool returns data *and* a mini web app to display it.

---

## AI Agents

An agent is commonly defined as:

> **Model + instructions + tools, running in a loop** (plan → act → observe), often with memory.

Without tools and the loop, you just have a prompted LLM.

---

## A2A (Agent2Agent)

An **open protocol** from Google (now under the Linux Foundation) that standardizes how agents built on different frameworks and platforms communicate.

- Agents collaborate as **opaque** peers: they don't share internal memory, tools, or prompts
- Each agent keeps its own stack
- Many SDKs available, plus an **A2A Inspector** for debugging
- Built on JSON-RPC 2.0 over HTTP(S), SSE for streaming, push notifications for long-running jobs, and gRPC in newer versions

### How A2A works

**Discovery → Interaction → Execution**

1. **Discovery**: the client agent fetches the remote agent's **Agent Card**
2. **Interaction**: the client sends messages and receives tasks, streamed updates, and artifacts
3. **Execution**: the remote agent's **Agent Executor** runs the logic

### Core concepts

| Concept | Description |
|---|---|
| **Agent Card** | JSON describing the agent: what it can do, its URL, auth, etc. |
| **Task** | Unit of work with a lifecycle (submitted, working, completed, ...) |
| **Message** | A turn of communication between client and agent |
| **Part** | A piece of content in a message or artifact (text, file, data) |
| **Artifact** | An output produced by the agent |
| **Agent Executor** | SDK concept: server-side class where agent logic runs (`execute`, `cancel`) and which publishes events to the task |

### Agent Card

Served at a well-known URL: `/.well-known/agent-card.json` (older versions used `agent.json`).

```json
{
  "name": "Weather Agent",
  "description": "Answers weather questions",
  "url": "https://example.com/a2a",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true
  },
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text"],
  "skills": [
    {
      "id": "forecast",
      "name": "Weather forecast",
      "description": "Returns a forecast for a city",
      "tags": ["weather"]
    }
  ],
  "securitySchemes": {
    "oauth2": { "type": "oauth2" }
  }
}
```

> The exact schema varies by spec version. Check the A2A docs for yours.

### A2A client

In the protocol, "client" is a **role**: the agent that sends requests to a remote agent. A chat interface or CLI can host that role, which is how this repo's demo client lets you interact with agents.

---

## AG-UI (Agent–User Interaction)

An **open, lightweight protocol** that connects an agent backend to a frontend app. It's built for streaming, shared state, and human-in-the-loop interaction.

- Created by the CopilotKit team
- **CopilotKit** is its main client framework
- Integrated by many agent frameworks (LangGraph, CrewAI, Google ADK, and more)
- **AG-UI Dojo**: interactive playground for the protocol's features

### What it defines

AG-UI defines **what the events are**, with about 16 standard types:

- Run lifecycle (started, finished, error)
- Streaming text messages
- Tool calls
- State snapshots and deltas

**Transport is flexible**: SSE, WebSockets, and others.

---

## A2UI (Agent-to-UI)

An **open generative-UI protocol** from Google that lets agents produce rich, interactive interfaces across web, mobile, and desktop.

**Key idea:** A2UI is **declarative data, not code**. The agent sends JSON describing components, and the client renders them with its own native widgets from a **trusted catalog**. This is safer than letting an agent send HTML.

**Transport-agnostic**: it can travel over A2A, AG-UI, MCP, or plain HTTP.

### Core messages

| Message | Purpose |
|---|---|
| `createSurface` | Create a new surface and specify its component catalog |
| `updateComponents` | Add or update UI components in a surface |
| `updateDataModel` | Update application state |
| `deleteSurface` | Remove a UI surface |

> These names match the newer spec version. Earlier versions used `beginRendering`, `surfaceUpdate`, and `dataModelUpdate`. Pin the version in your demo.

### Component catalog

| Category | Components | Role |
|---|---|---|
| **Layout** | Row, Column, List | Arrange other components |
| **Display** | Text, Image, Icon, Video, Divider, AudioPlayer | Show information |
| **Interactive** | Button, TextField, CheckBox, DateTimeInput, Slider, ChoicePicker | Collect user input |
| **Container** | Card, Tabs, Modal | Group and organize content |

**Tooling:** [A2UI Composer](https://a2ui-composer.ag-ui.com) for building and previewing A2UI surfaces.

---

## UI Spec Comparison

| Approach | Specs | How it works | Trade-off |
|---|---|---|---|
| **Declarative** | A2UI, Open-JSON-UI | Agent sends a description; client renders natively | Safer and consistent with the app's look, but limited to the catalog |
| **Open-ended** | MCP Apps, MCP-UI | Agent/tool sends real HTML, rendered in a sandbox | Maximum flexibility, but needs sandboxing |
| **Custom** | Your own spec | You define the schema | Fits your needs, but isn't portable |

---

## Resources

- MCP: <https://modelcontextprotocol.io>
- A2A: <https://a2a-protocol.org>
- AG-UI: <https://docs.ag-ui.com>
- A2UI: <https://a2ui.org>
