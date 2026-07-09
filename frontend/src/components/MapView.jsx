import React, { useEffect, useRef, useState, useCallback } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const FACILITY_COLORS = {
  "District Hospital":           "#ef4444",
  "Provincial General Hospital": "#dc2626",
  "National Referral Hospital":  "#b91c1c",
  "Sub-District Hospital":       "#f97316",
  "Other Hospital":              "#fb923c",
  "Medical Centre":              "#f59e0b",
  "Health Centre":               "#3b82f6",
  "Nursing Home":                "#8b5cf6",
  "Maternity Home":              "#ec4899",
  "Medical Clinic":              "#06b6d4",
  "Dispensary":                  "#10b981",
  "Dental Clinic":               "#84cc16",
  "Eye Centre":                  "#a78bfa",
  "Laboratory (Stand-alone)":    "#d946ef",
  default:                       "#6b7280",
};

const BAND_COLORS = {
  Excellent: "#10b981", Good: "#3b82f6", Moderate: "#f59e0b",
  Poor: "#f97316", Critical: "#ef4444",
};

const FIN_COLORS = {
  "Free/Subsidized": "#10b981", Low: "#3b82f6", Medium: "#f59e0b", High: "#ef4444",
};

// ── Base map styles ──────────────────────────────────────────────────────────
// OpenFreeMap: free vector-tile styles, no API key, no per-request billing.
const VECTOR_STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";
const SATELLITE_TILE    = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

// A CSS filter "dark mode" trick: OpenFreeMap ships light vector styles only
// (liberty/positron/bright) — there's no free hosted dark vector style, so we
// invert + hue-rotate the canvas instead of drawing our own dark theme.
const DARK_FILTER = "invert(1) hue-rotate(180deg) brightness(0.95) contrast(0.9) saturate(0.85)";

function buildMatchExpr(colorMap) {
  const expr = ["match", ["get", "type"]];
  for (const [k, v] of Object.entries(colorMap)) {
    if (k === "default") continue;
    expr.push(k, v);
  }
  expr.push(colorMap.default);
  return expr;
}

function facilitiesToGeoJSON(facilities, selectedFacility, smartResults) {
  return {
    type: "FeatureCollection",
    features: facilities
      .filter((f) => f.latitude && f.longitude)
      .map((f) => ({
        type: "Feature",
        geometry: { type: "Point", coordinates: [f.longitude, f.latitude] },
        properties: {
          ...f,
          selected: selectedFacility?.facility_id === f.facility_id,
          isTop: !!(smartResults && f.score != null && f.score >= 65),
        },
      })),
  };
}

function lineGeoJSON(coords) {
  return {
    type: "Feature",
    geometry: { type: "LineString", coordinates: coords },
    properties: {},
  };
}

function facilityPopupHTML(f) {
  const beds    = (f.beds || 0) + (f.cots || 0);
  const fl      = f.financial_level;
  const flColor = FIN_COLORS[fl] || "#6b7280";
  return `
    <div style="min-width:200px;font-family:system-ui,sans-serif">
      <div style="font-weight:700;font-size:13px;margin-bottom:2px">${f.name || ""}</div>
      <div style="color:#6b7280;font-size:11px;margin-bottom:6px">
        ${f.type || ""} · ${f.county || ""} County${f.nearest_town ? ` · ${f.nearest_town}` : ""}
      </div>
      <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:6px">
        <span style="background:${f.operational_status === "Operational" ? "#d1fae5" : "#fee2e2"};color:${f.operational_status === "Operational" ? "#065f46" : "#991b1b"};border-radius:4px;padding:2px 6px;font-size:10px;font-weight:600">
          ${f.operational_status || "Unknown"}
        </span>
        ${f.open_24_hours ? `<span style="background:#dbeafe;color:#1e40af;border-radius:4px;padding:2px 6px;font-size:10px;font-weight:600">🕐 24hrs</span>` : ""}
        ${f.open_weekends ? `<span style="background:#ede9fe;color:#5b21b6;border-radius:4px;padding:2px 6px;font-size:10px;font-weight:600">📅 Wknds</span>` : ""}
      </div>
      ${beds > 0 ? `<div style="font-size:11px;margin-bottom:3px">🛏 <strong>${beds}</strong> beds/cots</div>` : ""}
      ${f.distance_km != null ? `<div style="font-size:11px;margin-bottom:3px">📍 <strong>${f.distance_km} km</strong>${f.estimated_minutes != null ? ` · ⏱ ${f.estimated_minutes} min` : ""}</div>` : ""}
      ${fl ? `<div style="font-size:11px;margin-bottom:3px">💰 <span style="color:${flColor};font-weight:600">${fl} cost</span></div>` : ""}
      ${f.score != null ? `<div style="font-size:11px;color:#10b981;font-weight:600;margin-top:4px">⭐ Match: ${f.score}/100${f.match_reason ? `<div style="color:#9ca3af;font-weight:400;font-style:italic;font-size:10px">${f.match_reason}</div>` : ""}</div>` : ""}
    </div>
  `;
}

// ── Main MapView ──────────────────────────────────────────────────────────────

export default function MapView({
  facilities, userLocation, selectedFacility,
  onFacilitySelect, route, onRouteSet,
  activeLayer, accessibilityScores, theme, smartResults, loading,
  activeStepIdx,
}) {
  const containerRef = useRef(null);
  const mapRef        = useRef(null);
  const styleReady     = useRef(false);
  const userMarkerRef  = useRef(null);
  const destMarkerRef  = useRef(null);
  const stepMarkersRef = useRef([]);
  const dashOffsetRef  = useRef(0);
  const rafRef         = useRef(null);
  const popupRef       = useRef(null);
  const facilitiesRef  = useRef(facilities);
  const onSelectRef    = useRef(onFacilitySelect);

  const [tileMode, setTileMode] = useState(theme); // "dark" | "light" | "satellite"
  const [mapLoaded, setMapLoaded] = useState(false);
  const [mapFailed, setMapFailed] = useState(false);

  facilitiesRef.current = facilities;
  onSelectRef.current = onFacilitySelect;

  useEffect(() => {
    setTileMode((prev) => (prev === "satellite" ? "satellite" : theme));
  }, [theme]);

  const dark  = theme === "dark";
  const isSat = tileMode === "satellite";

  const nextTile = () =>
    setTileMode((m) => (m === "dark" ? "light" : m === "light" ? "satellite" : "dark"));
  const tileModeLabel = { dark: "🌙", light: "☀️", satellite: "🛰" };

  // ── Init map (once) ──────────────────────────────────────────────────────
  useEffect(() => {
    let map;
    try {
      map = new maplibregl.Map({
        container: containerRef.current,
        style: VECTOR_STYLE_URL,
        center: [37.9062, -0.0236],
        zoom: 6,
        attributionControl: true,
      });
    } catch (err) {
      console.error("MapLibre init failed:", err);
      setMapFailed(true);
      return;
    }
    map.on("error", (e) => {
      if (e?.error?.message?.includes("WebGL") || e?.error?.type === "webglcontextcreationerror") {
        console.error("MapLibre WebGL error:", e.error);
        setMapFailed(true);
      }
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: true }), "top-right");

    map.on("load", () => {
      styleReady.current = true;

      // Satellite raster source, hidden by default — toggled via tileMode
      map.addSource("satellite-src", {
        type: "raster",
        tiles: [SATELLITE_TILE],
        tileSize: 256,
        attribution: "&copy; Esri — Esri, Maxar, GeoEye, Earthstar Geographics",
      });
      map.addLayer({
        id: "satellite-layer",
        type: "raster",
        source: "satellite-src",
        layout: { visibility: "none" },
      }, map.getStyle().layers[0]?.id);

      // Facilities cluster source
      map.addSource("facilities-src", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
        cluster: true,
        clusterRadius: 50,
        clusterMaxZoom: 13,
      });

      map.addLayer({
        id: "clusters",
        type: "circle",
        source: "facilities-src",
        filter: ["has", "point_count"],
        paint: {
          "circle-color": [
            "step", ["get", "point_count"],
            "#10b981", 10, "#3b82f6", 100, "#ef4444",
          ],
          "circle-radius": ["step", ["get", "point_count"], 14, 10, 17, 100, 21],
          "circle-stroke-width": 2.5,
          "circle-stroke-color": "rgba(255,255,255,0.85)",
          "circle-opacity": 0.92,
        },
      });
      map.addLayer({
        id: "cluster-count",
        type: "symbol",
        source: "facilities-src",
        filter: ["has", "point_count"],
        layout: {
          "text-field": ["get", "point_count_abbreviated"],
          "text-font": ["Noto Sans Bold"],
          "text-size": 12,
        },
        paint: { "text-color": "#ffffff" },
      });
      map.addLayer({
        id: "facility-points",
        type: "circle",
        source: "facilities-src",
        filter: ["!", ["has", "point_count"]],
        paint: {
          "circle-color": buildMatchExpr(FACILITY_COLORS),
          "circle-radius": [
            "case",
            ["get", "selected"], 11,
            ["get", "isTop"], 8,
            5,
          ],
          "circle-stroke-width": ["case", ["get", "isTop"], 2.5, 1.5],
          "circle-stroke-color": "rgba(255,255,255,0.8)",
        },
      });

      map.on("click", "clusters", (e) => {
        const features = map.queryRenderedFeatures(e.point, { layers: ["clusters"] });
        const clusterId = features[0].properties.cluster_id;
        map.getSource("facilities-src").getClusterExpansionZoom(clusterId, (err, zoom) => {
          if (err) return;
          map.easeTo({ center: features[0].geometry.coordinates, zoom });
        });
      });
      map.on("click", "facility-points", (e) => {
        const f = e.features[0].properties;
        onSelectRef.current?.(f);
        new maplibregl.Popup({ closeButton: true, maxWidth: "260px" })
          .setLngLat(e.features[0].geometry.coordinates)
          .setHTML(facilityPopupHTML(f))
          .addTo(map);
      });
      map.on("mouseenter", "facility-points", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "facility-points", () => (map.getCanvas().style.cursor = ""));
      map.on("mouseenter", "clusters", () => (map.getCanvas().style.cursor = "pointer"));
      map.on("mouseleave", "clusters", () => (map.getCanvas().style.cursor = ""));

      // Route sources/layers
      const emptyLine = { type: "Feature", geometry: { type: "LineString", coordinates: [] }, properties: {} };
      map.addSource("alt-routes-src", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({
        id: "alt-routes-layer", type: "line", source: "alt-routes-src",
        paint: { "line-color": dark ? "#4b5563" : "#9ca3af", "line-width": 4, "line-opacity": 0.55, "line-dasharray": [2, 1.6] },
      });

      map.addSource("route-casing-src", { type: "geojson", data: emptyLine });
      map.addLayer({
        id: "route-casing", type: "line", source: "route-casing-src",
        paint: { "line-color": dark ? "#1e3a5f" : "#1d4ed8", "line-width": 9, "line-opacity": 0.35 },
      });
      map.addSource("route-core-src", { type: "geojson", data: emptyLine });
      map.addLayer({
        id: "route-core", type: "line", source: "route-core-src",
        paint: { "line-color": "#60a5fa", "line-width": 4, "line-opacity": 1 },
      });
      map.addSource("route-flow-src", { type: "geojson", data: emptyLine });
      map.addLayer({
        id: "route-flow", type: "line", source: "route-flow-src",
        paint: { "line-color": "#93c5fd", "line-width": 3, "line-opacity": 0.9, "line-dasharray": [1.2, 1.6] },
      });

      setMapLoaded(true);
    });

    return () => {
      map.remove();
      mapRef.current = null;
      styleReady.current = false;
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Animate "flowing" dashes on the route (traffic-direction feel) ───────
  // MapLibre doesn't expose a strokeDashoffset like SVG, so we fake motion by
  // cycling the dash pattern itself — a small, cheap "marching ants" effect.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;
    const pattern = [
      [0, 1.2, 1.6], [0.4, 1.2, 1.2], [0.8, 1.2, 0.8], [1.2, 1.2, 0.4],
    ];
    let i = 0;
    const id = setInterval(() => {
      if (!map.getLayer("route-flow")) return;
      const [lead, dash, gap] = pattern[i % pattern.length];
      try { map.setPaintProperty("route-flow", "line-dasharray", [dash, gap]); } catch (_) {}
      i++;
    }, 220);
    return () => clearInterval(id);
  }, [mapLoaded]);

  // ── Tile mode: vector base vs satellite raster, plus dark CSS filter ─────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    const baseLayers = map.getStyle().layers
      .filter((l) => l.id !== "satellite-layer");

    if (isSat) {
      map.setLayoutProperty("satellite-layer", "visibility", "visible");
      baseLayers.forEach((l) => {
        if (l.type !== "background") {
          try { map.setLayoutProperty(l.id, "visibility", "none"); } catch (_) {}
        }
      });
    } else {
      map.setLayoutProperty("satellite-layer", "visibility", "none");
      baseLayers.forEach((l) => {
        try { map.setLayoutProperty(l.id, "visibility", "visible"); } catch (_) {}
      });
    }

    const canvas = map.getCanvasContainer();
    canvas.style.filter = !isSat && dark ? DARK_FILTER : "none";
  }, [isSat, dark, mapLoaded]);

  // ── Update facilities source ──────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;
    const src = map.getSource("facilities-src");
    if (src) src.setData(facilitiesToGeoJSON(facilities, selectedFacility, smartResults));
  }, [facilities, selectedFacility, smartResults, mapLoaded]);

  // ── User location marker + fly-to on first fix ────────────────────────────
  const flownToUser = useRef(false);
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded || !userLocation) return;

    if (!userMarkerRef.current) {
      const el = document.createElement("div");
      el.style.width = "20px";
      el.style.height = "20px";
      el.innerHTML = `
        <div style="position:relative;width:20px;height:20px">
          <div style="position:absolute;inset:0;border-radius:50%;background:rgba(59,130,246,0.25);animation:khap-ripple 2s ease-out infinite"></div>
          <div style="position:absolute;top:2px;left:2px;width:16px;height:16px;border-radius:50%;background:#3b82f6;border:3px solid #fff;box-shadow:0 0 12px rgba(59,130,246,0.8)"></div>
        </div>`;
      userMarkerRef.current = new maplibregl.Marker({ element: el, anchor: "center" })
        .setLngLat([userLocation.lon, userLocation.lat])
        .addTo(map);
    } else {
      userMarkerRef.current.setLngLat([userLocation.lon, userLocation.lat]);
    }

    if (!flownToUser.current) {
      flownToUser.current = true;
      map.jumpTo({ center: [userLocation.lon, userLocation.lat], zoom: 9 });
    }
  }, [userLocation, mapLoaded]);

  // ── Fly to selected facility ───────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded || !selectedFacility?.latitude || route) return;
    map.flyTo({ center: [selectedFacility.longitude, selectedFacility.latitude], zoom: 14, duration: 1200 });
  }, [selectedFacility, mapLoaded, route]);

  // ── Route rendering ─────────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    const routeCoords = route?.geometry?.coordinates;
    const altRoutes    = (route?.routes || []).slice(1);
    const destination  = route?.destination;
    const steps        = route?.steps || [];

    map.getSource("alt-routes-src")?.setData({
      type: "FeatureCollection",
      features: altRoutes
        .filter((a) => a.geometry?.coordinates?.length)
        .map((a) => lineGeoJSON(a.geometry.coordinates)),
    });

    if (routeCoords?.length) {
      const line = lineGeoJSON(routeCoords);
      map.getSource("route-casing-src")?.setData(line);
      map.getSource("route-core-src")?.setData(line);
      map.getSource("route-flow-src")?.setData(line);

      const bounds = routeCoords.reduce(
        (b, c) => b.extend(c),
        new maplibregl.LngLatBounds(routeCoords[0], routeCoords[0])
      );
      map.fitBounds(bounds, { padding: 60, duration: 800 });
    } else {
      const empty = { type: "Feature", geometry: { type: "LineString", coordinates: [] }, properties: {} };
      map.getSource("route-casing-src")?.setData(empty);
      map.getSource("route-core-src")?.setData(empty);
      map.getSource("route-flow-src")?.setData(empty);
    }

    // Destination marker
    if (destMarkerRef.current) { destMarkerRef.current.remove(); destMarkerRef.current = null; }
    if (destination?.latitude) {
      const el = document.createElement("div");
      el.style.textAlign = "center";
      el.innerHTML = `
        <div style="font-size:24px;line-height:1;filter:drop-shadow(0 2px 4px rgba(0,0,0,0.6))">🏥</div>
        ${destination.name ? `<div style="background:rgba(0,0,0,0.75);color:#fff;font-size:9px;padding:2px 4px;border-radius:3px;white-space:nowrap;max-width:120px;overflow:hidden;text-overflow:ellipsis;margin-top:2px">${destination.name}</div>` : ""}
      `;
      destMarkerRef.current = new maplibregl.Marker({ element: el, anchor: "bottom" })
        .setLngLat([destination.longitude, destination.latitude])
        .addTo(map);
    }

    // Step dot markers
    stepMarkersRef.current.forEach((m) => m.remove());
    stepMarkersRef.current = steps
      .map((step, i) => {
        if (!step.location || step.type === "depart" || step.type === "arrive") return null;
        const active = i === activeStepIdx;
        const size = active ? 14 : 8;
        const color = active ? "#f59e0b" : "#94a3b8";
        const el = document.createElement("div");
        el.style.width = `${size}px`;
        el.style.height = `${size}px`;
        el.style.borderRadius = "50%";
        el.style.background = color;
        el.style.border = "2px solid #fff";
        el.style.boxShadow = `0 0 6px ${color}88`;
        if (active) el.style.animation = "khap-pulse-dot 1.2s ease-in-out infinite";
        const marker = new maplibregl.Marker({ element: el, anchor: "center" })
          .setLngLat([step.location.lon, step.location.lat])
          .addTo(map);
        return marker;
      })
      .filter(Boolean);
  }, [route, activeStepIdx, mapLoaded]);

  // ── Coverage radius circles (drawn as a GeoJSON polygon layer) ───────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !mapLoaded) return;

    const wantCircles = activeLayer === "coverage" && userLocation;
    const srcId = "coverage-src";

    if (!map.getSource(srcId)) {
      map.addSource(srcId, { type: "geojson", data: { type: "FeatureCollection", features: [] } });
      map.addLayer({
        id: "coverage-fill", type: "fill", source: srcId,
        paint: { "fill-color": ["get", "color"], "fill-opacity": ["get", "opacity"] },
      });
      map.addLayer({
        id: "coverage-line", type: "line", source: srcId,
        paint: { "line-color": ["get", "color"], "line-width": 1.5, "line-dasharray": [2, 2] },
      });
    }

    if (!wantCircles) {
      map.getSource(srcId)?.setData({ type: "FeatureCollection", features: [] });
      return;
    }

    const rings = [
      { km: 5,  color: "#10b981", opacity: 0.08 },
      { km: 10, color: "#3b82f6", opacity: 0.05 },
      { km: 20, color: "#f59e0b", opacity: 0.04 },
    ];
    const features = rings.map(({ km, color, opacity }) => ({
      type: "Feature",
      properties: { color, opacity },
      geometry: circlePolygon(userLocation.lon, userLocation.lat, km),
    }));
    map.getSource(srcId).setData({ type: "FeatureCollection", features });
  }, [activeLayer, userLocation, mapLoaded]);

  return (
    <div style={{ flex: 1, position: "relative" }}>
      <style>{`
        @keyframes khap-ripple { 0% { transform: scale(1); opacity: 0.7; } 100% { transform: scale(2.5); opacity: 0; } }
        @keyframes khap-pulse-dot { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
        @keyframes khap-spin { to { transform: rotate(360deg); } }
        @keyframes khap-pulse { 0%,100% { opacity:.4; transform:scale(.92); } 50% { opacity:1; transform:scale(1); } }
        .maplibregl-popup-content { font-family: system-ui, sans-serif; }
      `}</style>

      {/* ── Loading overlay ── */}
      {loading && facilities.length === 0 && !mapFailed && (
        <div style={{
          position: "absolute", inset: 0, zIndex: 2000,
          background: dark ? "rgba(9,15,23,0.82)" : "rgba(240,244,248,0.82)",
          backdropFilter: "blur(3px)",
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center", gap: 16,
        }}>
          <div style={{
            width: 56, height: 56, borderRadius: "50%",
            border: `4px solid ${dark ? "#1f2937" : "#e5e7eb"}`,
            borderTopColor: "#10b981",
            animation: "khap-spin 0.9s linear infinite",
          }} />
          <div style={{
            color: "#10b981", fontWeight: 700, fontSize: 15,
            letterSpacing: "0.04em",
            animation: "khap-pulse 1.8s ease-in-out infinite",
          }}>
            Loading facilities…
          </div>
          <div style={{
            color: dark ? "#6b7280" : "#9ca3af",
            fontSize: 12, textAlign: "center", maxWidth: 220,
          }}>
            Fetching 7,406 verified<br />Kenyan health facilities
          </div>
        </div>
      )}

      {/* ── Tile mode toggle button ── */}
      <button
        onClick={nextTile}
        title={`Switch tile: currently ${tileMode}`}
        style={{
          position: "absolute", top: 80, right: 12, zIndex: 1100,
          background: dark && !isSat ? "rgba(17,24,39,0.9)" : "rgba(255,255,255,0.95)",
          border: `1px solid ${dark && !isSat ? "#374151" : "#d1d5db"}`,
          borderRadius: 8, padding: "7px 10px", cursor: "pointer",
          fontSize: 18, lineHeight: 1,
          boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
        }}
      >
        {tileModeLabel[tileMode]}
      </button>

      <div ref={containerRef} style={{ height: "100%", width: "100%" }} />

      {mapFailed && (
        <div style={{
          position: "absolute", inset: 0, zIndex: 1900,
          background: dark ? "#0f1923" : "#f0f4f8",
          display: "flex", flexDirection: "column",
          alignItems: "center", justifyContent: "center", gap: 10, padding: 24,
          textAlign: "center",
        }}>
          <div style={{ fontSize: 32 }}>🗺️</div>
          <div style={{ color: dark ? "#e2e8f0" : "#374151", fontWeight: 700, fontSize: 15 }}>
            This browser can't render the map
          </div>
          <div style={{ color: dark ? "#6b7280" : "#9ca3af", fontSize: 12, maxWidth: 340 }}>
            MapLibre GL needs WebGL, which isn't available in this preview environment.
            It works normally in regular desktop/mobile browsers with hardware acceleration enabled.
          </div>
        </div>
      )}

      <Legend activeLayer={activeLayer} theme={theme} smartResults={smartResults} />
      <StatsBar facilities={facilities} theme={theme} route={route} />
    </div>
  );
}

// ── Small geo helper: approximate circle as a GeoJSON polygon ──────────────
function circlePolygon(lon, lat, radiusKm, points = 64) {
  const coords = [];
  const distanceX = radiusKm / (111.32 * Math.cos((lat * Math.PI) / 180));
  const distanceY = radiusKm / 110.57;
  for (let i = 0; i <= points; i++) {
    const theta = (i / points) * (2 * Math.PI);
    coords.push([lon + distanceX * Math.cos(theta), lat + distanceY * Math.sin(theta)]);
  }
  return { type: "Polygon", coordinates: [coords] };
}

// ── Legend ────────────────────────────────────────────────────────────────────

function Legend({ activeLayer, theme, smartResults }) {
  const dark = theme === "dark";
  const box = {
    position: "absolute", bottom: 44, right: 12, zIndex: 1000,
    background: dark ? "rgba(17,24,39,0.95)" : "rgba(255,255,255,0.97)",
    borderRadius: 10, padding: "10px 14px", fontSize: 12,
    color: dark ? "#e2e8f0" : "#374151",
    backdropFilter: "blur(8px)",
    boxShadow: "0 4px 16px rgba(0,0,0,0.18)",
    border: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}`,
  };
  const title = { fontWeight: 700, marginBottom: 7, color: "#6b7280", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.08em" };
  const row   = { display: "flex", alignItems: "center", gap: 7, marginBottom: 4 };
  const dot   = (color, ring = false, size = 10) => ({
    width: size, height: size, borderRadius: "50%", flexShrink: 0,
    ...(ring ? { border: `2px solid ${color}`, background: "transparent" } : { background: color }),
  });

  if (activeLayer === "emergency" && smartResults) return (
    <div style={box}>
      <div style={title}>Emergency Results</div>
      <div style={row}><div style={dot("#ef4444", false, 14)} />Best match (top ranked)</div>
      <div style={row}><div style={dot("#3b82f6", true, 12)} />Good match</div>
      <div style={row}><div style={{ width: 18, height: 4, background: "#60a5fa", borderRadius: 2 }} />Road route</div>
      <div style={row}><span style={{ fontSize: 16 }}>🏥</span>Destination</div>
    </div>
  );

  if (activeLayer === "facilities") return (
    <div style={box}>
      <div style={title}>Facility Type</div>
      {[
        ["Hospital",       "#ef4444"],
        ["Health Centre",  "#3b82f6"],
        ["Clinic",         "#06b6d4"],
        ["Dispensary",     "#10b981"],
        ["Maternity",      "#ec4899"],
        ["Other",          "#6b7280"],
      ].map(([l, c]) => (
        <div key={l} style={row}><div style={dot(c)} />{l}</div>
      ))}
      <div style={{ ...row, marginTop: 4, paddingTop: 4, borderTop: `1px solid ${dark ? "#374151" : "#e5e7eb"}`, color: "#6b7280", fontSize: 10 }}>
        <div style={{ background: "#3b82f6", color: "#fff", borderRadius: "50%", width: 16, height: 16, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 9 }}>12</div>
        Cluster (zoom in)
      </div>
    </div>
  );

  if (activeLayer === "accessibility") return (
    <div style={box}>
      <div style={title}>Accessibility</div>
      {Object.entries(BAND_COLORS).map(([b, c]) => (
        <div key={b} style={row}><div style={dot(c)} />{b}</div>
      ))}
    </div>
  );

  if (activeLayer === "coverage") return (
    <div style={box}>
      <div style={title}>Coverage Radius</div>
      {[["5 km",  "#10b981"], ["10 km", "#3b82f6"], ["20 km", "#f59e0b"]].map(([l, c]) => (
        <div key={l} style={row}><div style={dot(c, true)} />{l}</div>
      ))}
    </div>
  );

  return null;
}

// ── Stats bar ─────────────────────────────────────────────────────────────────

function StatsBar({ facilities, theme, route }) {
  const dark        = theme === "dark";
  const operational = facilities.filter((f) => f.operational_status === "Operational" || f.score != null).length;
  const open24      = facilities.filter((f) => f.open_24_hours).length;
  const altCount    = (route?.routes?.length || 1) - 1;

  return (
    <div style={{
      position: "absolute", bottom: 0, left: 0, right: 0, zIndex: 999,
      background: dark ? "rgba(17,24,39,0.92)" : "rgba(255,255,255,0.94)",
      backdropFilter: "blur(6px)", padding: "5px 16px",
      display: "flex", gap: 20, fontSize: 11,
      color: dark ? "#9ca3af" : "#6b7280",
      borderTop: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}`,
      flexWrap: "wrap", alignItems: "center",
    }}>
      <span>🏥 <strong style={{ color: dark ? "#e2e8f0" : "#374151" }}>{facilities.length.toLocaleString()}</strong> shown</span>
      <span>✅ <strong style={{ color: "#10b981" }}>{operational.toLocaleString()}</strong> operational</span>
      <span>🕐 <strong style={{ color: "#3b82f6" }}>{open24}</strong> open 24h</span>
      {route && (
        <>
          <span>🚗 <strong style={{ color: "#f59e0b" }}>{route.distance_km} km</strong></span>
          <span>⏱ <strong style={{ color: "#f59e0b" }}>{route.duration_minutes} min</strong></span>
          {route.steps?.length > 0 && (
            <span>📍 <strong style={{ color: "#a78bfa" }}>{route.steps.length} steps</strong></span>
          )}
          {altCount > 0 && (
            <span>🔀 <strong style={{ color: "#6b7280" }}>{altCount} alt route{altCount > 1 ? "s" : ""}</strong></span>
          )}
        </>
      )}
      <span style={{ marginLeft: "auto", color: "#6b7280", fontSize: 10 }}>
        KHAP v3 · MapLibre GL + OSM
      </span>
    </div>
  );
}
