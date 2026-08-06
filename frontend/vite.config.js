import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: true,
    // Proxy API calls to FastAPI in development so CORS is not an issue.
    // Set VITE_API_URL in frontend/.env.local to override for a remote backend.
    proxy: {
      "/facilities": "http://localhost:8000",
      "/search":     "http://localhost:8000",
      "/route":      "http://localhost:8000",
      "/health":     "http://localhost:8000",
    },
  },
});
