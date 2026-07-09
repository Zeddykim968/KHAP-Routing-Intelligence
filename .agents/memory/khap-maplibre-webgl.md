---
name: MapLibre GL + headless screenshot tool
description: Why MapLibre GL (WebGL-based) throws in the app_preview screenshot tool but is fine for real users
---

The `screenshot` tool's `app_preview` type runs a headless Chrome instance that
cannot create a WebGL context in this sandbox (`Could not create a WebGL
context ... BindToCurrentSequence failed`). MapLibre GL JS requires WebGL to
render, unlike Leaflet (which draws raster `<img>` tiles and has no such
dependency).

**Why:** This is an environment limitation of the screenshot tool itself, not
a code bug. Real desktop/mobile browsers have working WebGL and render
MapLibre normally.

**How to apply:** When migrating a map from Leaflet to MapLibre (or any other
WebGL-based renderer), always wrap map initialization in a try/catch and
listen for the `error` event with `webglcontextcreationerror`, showing a
graceful fallback UI instead of letting the app crash. Don't be alarmed if
`screenshot(app_preview)` shows this fallback — verify via browser console
logs that the specific error is WebGL context creation, then trust that it
works for end users. Do not try to "fix" WebGL support in the sandbox itself.
