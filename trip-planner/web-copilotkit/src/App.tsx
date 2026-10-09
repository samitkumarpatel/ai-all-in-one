import { CopilotKit, CopilotChat, useCopilotKit, useRenderTool } from "@copilotkit/react-core/v2";
import "@copilotkit/react-core/v2/styles.css";
import { z } from "zod";
import { catalog } from "./catalog";
import { extractMcpApp, McpAppFrame } from "./mcpApp";
import "./App.css";

// Step 8: draw the show_seat_map tool result (an MCP App) inside the chat, as a sandboxed iframe.
function SeatMapRenderer() {
  const { copilotkit } = useCopilotKit();

  // The app's ui/message becomes a normal user message, and the agent runs again
  function sendToAgent(text: string) {
    const agent = copilotkit.getAgent("default");
    if (!agent) return;
    agent.addMessage({ id: crypto.randomUUID(), role: "user", content: text });
    void copilotkit.runAgent({ agent });
  }

  useRenderTool(
    {
      name: "show_seat_map",
      parameters: z.object({ flight_id: z.string() }),
      render: ({ status, result }) => {
        if (status !== "complete") return <div className="tool-note">Loading seat map…</div>;
        const app = extractMcpApp(result);
        return app ? <McpAppFrame app={app} onMessage={sendToAgent} /> : null;
      },
    },
    [],
  );

  return null;
}

export default function App() {
  return (
    // Passing a catalog turns A2UI rendering on. The runtime URL is proxied by Vite to :4000.
    <CopilotKit runtimeUrl="/api/copilotkit" a2ui={{ catalog }}>
      <SeatMapRenderer />
      <div className="shell">
        <header>
          <h1>✈️ Trip Planner</h1>
          <span>CopilotKit + A2UI + MCP Apps</span>
        </header>
        <main>
          <CopilotChat agentId="default" className="chat" />
        </main>
      </div>
    </CopilotKit>
  );
}
