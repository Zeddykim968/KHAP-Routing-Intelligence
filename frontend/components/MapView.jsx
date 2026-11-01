"use client";

import { useEffect, useRef, useState } from "react";
import {
  Map as MapLibreMap,
  Marker,
  NavigationControl,
  ScaleControl,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import styles from "./MapView.module.css";

const LIGHT_STYLE = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json";
const DARK_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json";
const DEFAULT_CENTER = [36.8219, -1.2921]; // Nairobi CBD

const PIN_COLORS = {
  hospital: "#d93025",
  clinic: "#1a73e8",
  health_centre: "#188038",
  dispensary: "#188038",
  pharmacy: "#188038",
  dentist: "#007b83",
  laboratory: "#9334e6",
  maternity: "#d01884",
  eye_clinic: "#f9ab00",
};

const PLUS_GLYPH =
  '<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true">' +
  '<path d="M12 5v14M5 12h14" stroke="#fff" stroke-width="3.6" stroke-linecap="round" fill="none"/></svg>';

export default function MapView({
  theme,
  origin,
  facilities,
  selectedId,
  route,
  puck,
  navActive,
  bottomOffset = 0,
  onSelectFacility,
  onMapClick,
  onDropPin,
  onReady,
}) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const markersRef = useRef(new Map());
  const puckMarkerRef = useRef(null);
  const originMarkerRef = useRef(null);
  const appliedThemeRef = useRef(null);
  const handlersRef = useRef({ onSelectFacility, onMapClick, onDropPin });
  handlersRef.current = { onSelectFacility, onMapClick, onDropPin };

  // -1 until the style has loaded — sources/layers cannot be added before that.
  const [styleEpoch, setStyleEpoch] = useState(-1);

  // ── init (once) ────────────────────────────────────────────────────────────
  useEffect(() => {
    // The inline layout script has already chosen the theme before hydration.
    const initialTheme =
      document.documentElement.dataset.theme === "dark" ? "dark" : "light";
    appliedThemeRef.current = initialTheme;

    const map = new MapLibreMap({
      container: containerRef.current,
      style: initialTheme === "dark" ? DARK_STYLE : LIGHT_STYLE,
      center: DEFAULT_CENTER,
      zoom: 12,
      maxPitch: 70,
      attributionControl: { compact: true },
    });

    map.addControl(new NavigationControl({ visualizePitch: true }), "bottom-right");
    map.addControl(new ScaleControl({ maxWidth: 110, unit: "metric" }), "bottom-left");

    map.on("style.load", () => {
      // setStyle wipes sources/layers; DOM markers may go too. Clear ours so
      // the sync effects (re-run via epoch) rebuild everything cleanly.
      puckMarkerRef.current?.remove();
      puckMarkerRef.current = null;
      originMarkerRef.current?.remove();
      originMarkerRef.current = null;
      setStyleEpoch((e) => e + 1);
    });
    map.on("click", (e) => handlersRef.current.onMapClick?.({ lat: e.lngLat.lat, lon: e.lngLat.lng }));
    map.on("contextmenu", (e) => {
      e.preventDefault?.();
      handlersRef.current.onDropPin?.({ lat: e.lngLat.lat, lon: e.lngLat.lng });
    });
    map.on("move", () => {
      if (puckMarkerRef.current) updatePuckHeading(puckMarkerRef.current, map, puckRef.current);
    });

    mapRef.current = map;
    onReady?.(map);

    return () => {
      map.remove();
      mapRef.current = null;
      markersRef.current.clear();
      puckMarkerRef.current = null;
      originMarkerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keep the latest puck available to the move handler without re-binding.
  const puckRef = useRef(puck);
  puckRef.current = puck;

  // ── theme switch (no-op when already applied) ──────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || appliedThemeRef.current === theme) return;
    appliedThemeRef.current = theme;
    map.setStyle(theme === "dark" ? DARK_STYLE : LIGHT_STYLE);
  }, [theme]);

  // ── bottom control offset (kept above the sheet) ───────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.getContainer().style.setProperty("--khap-bottom", `${bottomOffset}px`);
  }, [bottomOffset]);

  // ── facility markers ───────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || styleEpoch < 0) return;
    for (const marker of markersRef.current.values()) marker.remove();
    markersRef.current.clear();

    for (const f of facilities || []) {
      const el = document.createElement("div");
      el.className = styles.pinWrap + (f.id === selectedId ? ` ${styles.pinSelected}` : "");
      el.style.setProperty("--pin", PIN_COLORS[f.facility_type] || "#5f6368");
      el.innerHTML = `<div class="${styles.pinBody}">${PLUS_GLYPH}</div><div class="${styles.pinTail}"></div>`;
      el.addEventListener("click", (ev) => {
        ev.stopPropagation();
        handlersRef.current.onSelectFacility?.(f.id);
      });
      const marker = new Marker({ element: el, anchor: "bottom" })
        .setLngLat([f.longitude, f.latitude])
        .addTo(map);
      markersRef.current.set(f.id, marker);
    }
  }, [facilities, selectedId, styleEpoch]);

  // ── route line ─────────────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || styleEpoch < 0) return;
    if (!map.getSource("khap-route")) {
      map.addSource("khap-route", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
      });
      map.addLayer({
        id: "khap-route-casing",
        type: "line",
        source: "khap-route",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": theme === "dark" ? "#17181a" : "#ffffff",
          "line-width": ["interpolate", ["linear"], ["zoom"], 9, 7, 15, 13],
          "line-opacity": 0.95,
        },
      });
      map.addLayer({
        id: "khap-route-line",
        type: "line",
        source: "khap-route",
        layout: { "line-cap": "round", "line-join": "round" },
        paint: {
          "line-color": theme === "dark" ? "#8ab4f8" : "#1a73e8",
          "line-width": ["interpolate", ["linear"], ["zoom"], 9, 4, 15, 8],
        },
      });
    }
    map.getSource("khap-route").setData(
      route
        ? { type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: route.route } }
        : { type: "FeatureCollection", features: [] }
    );
  }, [route, theme, styleEpoch]);

  // ── origin dot (only when there is no live GPS puck) ───────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || styleEpoch < 0) return;
    originMarkerRef.current?.remove();
    originMarkerRef.current = null;
    if (origin && !puck) {
      const el = document.createElement("div");
      el.className = styles.originDot;
      originMarkerRef.current = new Marker({ element: el })
        .setLngLat([origin.lon, origin.lat])
        .addTo(map);
    }
  }, [origin, puck, styleEpoch]);

  // ── GPS puck ───────────────────────────────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map || styleEpoch < 0) return;
    if (!puck) {
      puckMarkerRef.current?.remove();
      puckMarkerRef.current = null;
      return;
    }
    if (!puckMarkerRef.current) {
      const el = document.createElement("div");
      el.className = styles.puck;
      el.innerHTML = `<div class="${styles.puckCone}"></div><div class="${styles.puckDot}"></div>`;
      puckMarkerRef.current = new Marker({ element: el })
        .setLngLat([puck.lon, puck.lat])
        .addTo(map);
    } else {
      puckMarkerRef.current.setLngLat([puck.lon, puck.lat]);
    }
    puckMarkerRef.current.getElement().classList.toggle(styles.puckNav, !!navActive);
    updatePuckHeading(puckMarkerRef.current, map, puck);
  }, [puck, navActive, styleEpoch]);

  // ── navigation camera (follow + pitch) ─────────────────────────────────────
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (navActive && puck) {
      const bearing =
        Number.isFinite(puck.heading) && puck.heading >= 0 ? puck.heading : map.getBearing();
      map.easeTo({
        center: [puck.lon, puck.lat],
        bearing,
        pitch: 55,
        duration: 900,
        essential: true,
      });
    } else if (map.getBearing() !== 0 || map.getPitch() !== 0) {
      map.easeTo({ bearing: 0, pitch: 0, duration: 500 });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navActive]);

  return <div ref={containerRef} className={styles.map} />;
}

function updatePuckHeading(el, map, puck) {
  if (!el || !puck || !Number.isFinite(puck.heading) || puck.heading < 0) {
    el?.style.setProperty("--heading-cw", "0deg");
    return;
  }
  const cw = (puck.heading - map.getBearing() + 360) % 360;
  el.style.setProperty("--heading-cw", `${cw}deg`);
}
