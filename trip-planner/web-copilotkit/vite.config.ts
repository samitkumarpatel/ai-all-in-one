import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Port 5174 so this app can run next to the direct-renderer app (5173).
// /api/copilotkit is proxied to the Node CopilotKit runtime.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      "/api/copilotkit": {
        target: "http://127.0.0.1:4000",
        changeOrigin: true,
      },
    },
  },
});
