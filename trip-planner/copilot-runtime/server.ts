// Option A: CopilotKit runtime (Node). Sits between the React app and the Python AG-UI server.
//
//   React (CopilotKit) --> this runtime (:4000) --> Python AG-UI server (:8003/agui)
import express from "express";
import { HttpAgent } from "@ag-ui/client";
import { CopilotRuntime, InMemoryAgentRunner } from "@copilotkit/runtime/v2";
import { createCopilotExpressHandler } from "@copilotkit/runtime/v2/express";

const AGUI_URL = process.env.AGUI_URL ?? "http://127.0.0.1:8003/agui";
const PORT = Number(process.env.PORT ?? 4000);

const runtime = new CopilotRuntime({
  // "default" is the agent CopilotKit's prebuilt chat uses automatically
  agents: { default: new HttpAgent({ url: AGUI_URL }) },

  // Fixed-schema A2UI: our agent owns the tool that returns `a2ui_operations`,
  // so don't let the runtime inject its own schema-generating tool.
  // The A2UI middleware still detects the operations in the tool result and renders them.
  a2ui: { injectA2UITool: false, agents: ["default"] },

  runner: new InMemoryAgentRunner(),
});

const app = express();

app.use(
  createCopilotExpressHandler({
    runtime,
    basePath: "/api/copilotkit",
    cors: true,
  }),
);

app.listen(PORT, () => {
  console.log(`CopilotKit runtime on http://localhost:${PORT}/api/copilotkit -> ${AGUI_URL}`);
});
