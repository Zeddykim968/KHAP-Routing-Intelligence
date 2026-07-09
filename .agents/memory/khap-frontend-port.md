---
name: KHAP frontend port config
description: Where the dashboard's dev server port is defined and why it must stay in sync.
---

The React dashboard's dev port is defined in two places that must agree:
- `frontend/vite.config.js` → `server.port`
- `frontend/package.json` → the `dev` script's `--port` flag (overrides vite.config.js if present)

**Why:** The npm script's `--port` flag takes precedence over `vite.config.js`. When they drift (e.g. script says 5174, config says 5173), the `Start dashboard` workflow — which expects port 5173 — fails with `DIDNT_OPEN_A_PORT` even though Vite itself starts up fine on the other port.

**How to apply:** If the dashboard workflow times out waiting for a port, check both files agree before debugging further (no need to touch Vite/React internals).
