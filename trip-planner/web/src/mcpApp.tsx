// Step 8: a minimal MCP Apps *host*. Renders a ui:// HTML resource in a sandboxed iframe and talks
// to it with JSON-RPC 2.0 over postMessage. The orchestrator's show_seat_map tool already called the
// MCP tool and read the resource; its result ({ mcp_app: {...} }) arrives in a TOOL_CALL_RESULT event.
//
// Real hosts usually use AppBridge from @modelcontextprotocol/ext-apps/app-bridge. This file writes
// the few messages we need by hand, so the protocol is easy to follow.
import { useEffect, useRef, useState } from "react";

export type McpApp = {
  resourceUri: string;
  html: string;
  toolInput: Record<string, unknown>;
  toolResult: { content: unknown[]; structuredContent?: unknown };
};

type RpcMessage = {
  jsonrpc: "2.0";
  id?: number | string;
  method?: string;
  params?: any;
  result?: unknown;
  error?: { code: number; message: string };
};

const PROTOCOL_VERSION = "2026-01-26";

/** Returns the MCP App carried in a tool result, or null if the result is something else. */
export function extractMcpApp(content: unknown): McpApp | null {
  try {
    const data = typeof content === "string" ? JSON.parse(content) : (content as any);
    const app = data?.mcp_app ?? data?.result?.mcp_app;
    return app?.html ? app : null;
  } catch {
    return null;
  }
}

/** Renders one MCP App. `onMessage` receives text the app wants to post into the chat (ui/message). */
export function McpAppFrame({ app, onMessage }: { app: McpApp; onMessage: (text: string) => void }) {
  const iframe = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState(200);

  useEffect(() => {
    const send = (msg: Omit<RpcMessage, "jsonrpc">) =>
      iframe.current?.contentWindow?.postMessage({ jsonrpc: "2.0", ...msg }, "*");

    function handle(e: MessageEvent) {
      // Only listen to our own iframe
      if (e.source !== iframe.current?.contentWindow) return;
      const msg = e.data as RpcMessage;
      if (msg?.jsonrpc !== "2.0") return;

      switch (msg.method) {
        case "ui/initialize": // view -> host: handshake. Tell the app what this host supports.
          send({
            id: msg.id,
            result: {
              protocolVersion: PROTOCOL_VERSION,
              hostInfo: { name: "trip-planner-web", version: "1.0.0" },
              hostCapabilities: { message: { text: {} } },
              hostContext: {
                theme: matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light",
              },
            },
          });
          break;

        case "ui/notifications/initialized": // view is ready: send the tool input, then the result
          send({ method: "ui/notifications/tool-input", params: { arguments: app.toolInput } });
          send({ method: "ui/notifications/tool-result", params: app.toolResult });
          break;

        case "ui/notifications/size-changed":
          if (msg.params?.height) setHeight(msg.params.height);
          break;

        case "ui/message": {
          // The app asks us to post a user message into the chat
          const content: { type: string; text?: string }[] = msg.params?.content ?? [];
          const text = content
            .filter((c) => c.type === "text")
            .map((c) => c.text)
            .join("\n");
          send({ id: msg.id, result: {} });
          if (text) onMessage(text);
          break;
        }

        default: // any other request: "method not found"
          if (msg.id !== undefined) {
            send({ id: msg.id, error: { code: -32601, message: `Unsupported: ${msg.method}` } });
          }
      }
    }

    window.addEventListener("message", handle);
    return () => window.removeEventListener("message", handle);
  }, [app, onMessage]);

  return (
    <iframe
      ref={iframe}
      className="mcp-app"
      title={app.resourceUri}
      srcDoc={app.html}
      // allow-scripts WITHOUT allow-same-origin: the app runs in an opaque origin, so it cannot read
      // this page, its cookies or storage. postMessage is its only way out.
      sandbox="allow-scripts"
      style={{ height }}
    />
  );
}
