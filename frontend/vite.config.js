import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: "all",
    proxy: {
      "/recommendations": "http://localhost:5000",
      "/ambulance":       "http://localhost:5000",
      "/analytics":       "http://localhost:5000",
      "/gis":             "http://localhost:5000",
      "/smart":           "http://localhost:5000",
      "/ussd":            "http://localhost:5000",
      "/sms":             "http://localhost:5000",
      "/api":             "http://localhost:5000",
    },
  },
  build: { outDir: "dist" },
});
