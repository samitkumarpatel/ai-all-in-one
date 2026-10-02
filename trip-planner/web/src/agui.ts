// Minimal AG-UI client: POST a run request, then parse the Server-Sent Events stream.
// AG-UI defines the *events*; this file shows what they look like on the wire.

export type AguiEvent = { type: string; [key: string]: any };

export type ChatMessage = { id: string; role: "user" | "assistant"; content: string };

export async function runAgent(opts: {
  threadId: string;
  messages: ChatMessage[];
  onEvent: (event: AguiEvent) => void;
  signal?: AbortSignal;
}): Promise<void> {
  const res = await fetch("/agui", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({
      threadId: opts.threadId,
      runId: crypto.randomUUID(),
      state: {},
      messages: opts.messages,
      tools: [],
      context: [],
      forwardedProps: {},
    }),
    signal: opts.signal,
  });

  if (!res.ok || !res.body) {
    throw new Error(`AG-UI request failed: HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    // SSE frames are separated by a blank line (servers may use \r\n)
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? "";

    for (const frame of frames) {
      const data = frame
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim())
        .join("\n");
      if (data) opts.onEvent(JSON.parse(data));
    }
  }
}
