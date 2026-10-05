// Option A: the A2UI catalog the CopilotKit renderer is allowed to draw.
//
// The backend schema only uses basic-catalog components (Card, Column, Text, Button).
// We override two of them to give the cards our own look, and keep the rest from the basic catalog.
import { useState, type ReactNode } from "react";
import { z } from "zod";
import {
  createCatalog,
  type CatalogDefinitions,
  type CatalogRenderers,
} from "@copilotkit/a2ui-renderer";

// Must match CATALOG_ID in agents/orchestrator_agent/a2ui_hotels.py
export const CATALOG_ID = "copilotkit://trip-planner-catalog";

const definitions = {
  Card: {
    description: "A container card with a single child.",
    props: z.object({
      child: z.string(),
    }),
  },
  Button: {
    description: "An interactive button. Use 'child' with a Text component id for the label.",
    props: z.object({
      child: z.string().describe("The id of the child component (e.g. a Text for the label)."),
      variant: z.enum(["primary", "secondary", "ghost"]).optional(),
      // Union with { event } so the binder resolves this as an action
      action: z
        .union([
          z.object({
            event: z.object({
              name: z.string(),
              context: z.record(z.any()).optional(),
            }),
          }),
          z.null(),
        ])
        .optional(),
    }),
  },
} satisfies CatalogDefinitions;

type Definitions = typeof definitions;

// Local "booked" state, so the click gives visible feedback (demo only, no real booking)
function BookButton({ children }: { children: ReactNode }) {
  const [done, setDone] = useState(false);
  return (
    <button className={`book-btn ${done ? "done" : ""}`} onClick={() => setDone(true)} disabled={done}>
      {done ? "Booked ✓ (demo)" : children}
    </button>
  );
}

export const renderers: CatalogRenderers<Definitions> = {
  Card: ({ props, children }) => (
    <div className="hotel-card">{props.child ? children(props.child) : null}</div>
  ),
  Button: ({ props, children }) => (
    <BookButton>{props.child ? children(props.child) : null}</BookButton>
  ),
};

export const catalog = createCatalog(definitions, renderers, {
  catalogId: CATALOG_ID,
  includeBasicCatalog: true,
});
