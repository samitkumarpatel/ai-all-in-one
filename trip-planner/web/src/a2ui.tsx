// Option B: render A2UI directly with Google's renderer (@a2ui/react + @a2ui/web_core).
// No CopilotKit. Our own AG-UI client hands A2UI operations to a MessageProcessor.
import { useEffect, useRef, useState } from "react";
import { MessageProcessor } from "@a2ui/web_core/v0_9";
import { A2uiSurface, basicCatalog } from "@a2ui/react/v0_9";

type Operation = Record<string, any>;

/**
 * The backend tool returns `{ a2ui_operations: [...] }`. It arrives as the content of an AG-UI
 * TOOL_CALL_RESULT event (usually a JSON string). Returns the operations, or null if the
 * result is not A2UI.
 */
export function extractA2uiOperations(content: unknown): Operation[] | null {
  try {
    const data = typeof content === "string" ? JSON.parse(content) : (content as any);
    const ops = data?.a2ui_operations ?? data?.result?.a2ui_operations;
    return Array.isArray(ops) ? ops : null;
  } catch {
    return null; // plain-text tool results (flight/hotel agent answers) land here
  }
}

export function useA2ui(onAction: (action: unknown) => void) {
  // Keep the latest callback without recreating the processor
  const actionRef = useRef(onAction);
  actionRef.current = onAction;

  const [processor] = useState(
    () => new MessageProcessor([basicCatalog], ((action: unknown) => actionRef.current(action)) as any),
  );
  const [surfaces, setSurfaces] = useState<any[]>([]);

  useEffect(() => {
    const sync = () => setSurfaces(Array.from(processor.model.surfacesMap.values()));
    const created = processor.onSurfaceCreated(sync);
    const deleted = processor.onSurfaceDeleted(sync);
    sync();
    return () => {
      created.unsubscribe();
      deleted.unsubscribe();
    };
  }, [processor]);

  function apply(operations: Operation[]) {
    // The backend names its own catalog id. This app only has the basic catalog,
    // so point createSurface at it. (The components used are all basic-catalog ones.)
    const messages = operations.map((op) =>
      op.createSurface
        ? { ...op, createSurface: { ...op.createSurface, catalogId: basicCatalog.id } }
        : op,
    );
    processor.processMessages(messages as any);
  }

  return { surfaces, apply };
}

export function Surfaces({ surfaces }: { surfaces: any[] }) {
  if (surfaces.length === 0) return null;
  return (
    <div className="surfaces">
      {surfaces.map((surface) => (
        <A2uiSurface key={surface.id} surface={surface} />
      ))}
    </div>
  );
}
