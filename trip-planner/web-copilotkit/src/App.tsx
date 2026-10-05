import { CopilotKit, CopilotChat } from "@copilotkit/react-core/v2";
import "@copilotkit/react-core/v2/styles.css";
import { catalog } from "./catalog";
import "./App.css";

export default function App() {
  return (
    // Passing a catalog turns A2UI rendering on. The runtime URL is proxied by Vite to :4000.
    <CopilotKit runtimeUrl="/api/copilotkit" a2ui={{ catalog }}>
      <div className="shell">
        <header>
          <h1>✈️ Trip Planner</h1>
          <span>CopilotKit + A2UI</span>
        </header>
        <main>
          <CopilotChat agentId="default" className="chat" />
        </main>
      </div>
    </CopilotKit>
  );
}
