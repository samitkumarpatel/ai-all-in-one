import { useRef, useState } from "react";
import { runAgent, type AguiEvent, type ChatMessage } from "./agui";
import "./App.css";

type LogEntry = { n: number; event: AguiEvent };

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [log, setLog] = useState<LogEntry[]>([]);
  const [activity, setActivity] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const threadId = useRef(crypto.randomUUID());
  const counter = useRef(0);

  function handleEvent(event: AguiEvent) {
    // 1) Raw event log (the point of the demo: see AG-UI events live)
    setLog((prev) => [...prev, { n: ++counter.current, event }]);

    // 2) Map events to UI state
    switch (event.type) {
      case "TEXT_MESSAGE_START":
        setMessages((prev) => [...prev, { id: event.messageId, role: "assistant", content: "" }]);
        break;
      case "TEXT_MESSAGE_CONTENT":
        setMessages((prev) =>
          prev.map((m) => (m.id === event.messageId ? { ...m, content: m.content + event.delta } : m)),
        );
        break;
      case "TOOL_CALL_START":
        setActivity((prev) => [...prev, `🔧 ${event.toolCallName}`]);
        break;
      case "RUN_ERROR":
        setError(event.message ?? "Run failed");
        break;
    }
  }

  async function send() {
    const text = input.trim();
    if (!text || running) return;

    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text };
    const history = [...messages, userMsg];

    setMessages(history);
    setInput("");
    setError(null);
    setActivity([]);
    setRunning(true);

    try {
      await runAgent({ threadId: threadId.current, messages: history, onEvent: handleEvent });
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="layout">
      <section className="chat">
        <h1>✈️ Trip Planner</h1>

        <div className="messages">
          {messages.length === 0 && (
            <p className="hint">Try: “I’m in Copenhagen and want a weekend in Amsterdam on 2026-10-10.”</p>
          )}
          {messages.map((m) => (
            <div key={m.id} className={`bubble ${m.role}`}>
              {m.content || "…"}
            </div>
          ))}
          {activity.length > 0 && <div className="activity">{activity.join("  ·  ")}</div>}
          {error && <div className="error">{error}</div>}
        </div>

        <div className="composer">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask about a trip…"
            disabled={running}
          />
          <button onClick={send} disabled={running || !input.trim()}>
            {running ? "Running…" : "Send"}
          </button>
        </div>
      </section>

      <aside className="log">
        <h2>AG-UI events</h2>
        <div className="events">
          {log.map(({ n, event }) => (
            <details key={n}>
              <summary>
                <span className="n">{n}</span> {event.type}
              </summary>
              <pre>{JSON.stringify(event, null, 2)}</pre>
            </details>
          ))}
        </div>
      </aside>
    </div>
  );
}
