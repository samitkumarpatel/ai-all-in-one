import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy /agui to the Python AG-UI server so the browser sees one origin (no CORS setup needed).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/agui": {
        target: "http://127.0.0.1:8003",
        changeOrigin: true,
      },
    },
  },
});
