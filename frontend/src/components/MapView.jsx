import React, { useEffect, useRef } from "react";
import {
  MapContainer, TileLayer, Marker, Popup,
  Polyline, Circle, useMap,
} from "react-leaflet";
import L from "leaflet";

const FACILITY_COLORS = {
  "District Hospital": "#ef4444",
  "Provincial General Hospital": "#dc2626",
  "Sub-District Hospital": "#f97316",
  "Other Hospital": "#fb923c",
  "Medical Centre": "#f59e0b",
  "Health Centre": "#3b82f6",
  "Nursing Home": "#8b5cf6",
  "Maternity Home": "#ec4899",
  "Medical Clinic": "#06b6d4",
  "Dispensary": "#10b981",
  "Dental Clinic": "#84cc16",
  "Eye Centre": "#a78bfa",
  default: "#6b7280",
};

const BAND_COLORS = {
  Excellent: "#10b981", Good: "#3b82f6", Moderate: "#f59e0b",
  Poor: "#f97316", Critical: "#ef4444",
};

const DARK_TILE = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const LIGHT_TILE = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";

function makeIcon(color, size = 10) {
  return L.divIcon({
    className: "",
    html: `<div style="width:${size}px;height:${size}px;border-radius:50%;background:${color};border:2px solid rgba(255,255,255,0.7);box-shadow:0 0 4px rgba(0,0,0,0.5)"></div>`,
    iconAnchor: [size / 2, size / 2],
  });
}

function userIcon() {
  return L.divIcon({
    className: "",
    html: `<div style="width:14px;height:14px;border-radius:50%;background:#3b82f6;border:3px solid #fff;box-shadow:0 0 10px rgba(59,130,246,0.8)"></div>`,
    iconAnchor: [7, 7],
  });
}

function TileSwapper({ theme }) {
  const map = useMap();
  return null;
}

function FlyTo({ userLocation }) {
  const map = useMap();
  useEffect(() => {
    if (userLocation) map.setView([userLocation.lat, userLocation.lon], 9);
  }, [userLocation]);
  return null;
}

export default function MapView({
  facilities, userLocation, selectedFacility,
  onFacilitySelect, route, activeLayer, accessibilityScores, theme,
}) {
  const routeCoords = route?.geometry?.coordinates?.map(([lng, lat]) => [lat, lng]);

  return (
    <div style={{ flex: 1, position: "relative" }}>
      <MapContainer
        center={[-0.0236, 37.9062]}
        zoom={6}
        style={{ height: "100%", width: "100%" }}
        zoomControl
      >
        <TileLayer
          url={theme === "dark" ? DARK_TILE : LIGHT_TILE}
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        />
        {userLocation && (
          <>
            <FlyTo userLocation={userLocation} />
            <Marker position={[userLocation.lat, userLocation.lon]} icon={userIcon()}>
              <Popup><strong>Your Location</strong></Popup>
            </Marker>
            {activeLayer === "coverage" && (
              <>
                <Circle center={[userLocation.lat, userLocation.lon]} radius={5000} pathOptions={{ color: "#10b981", fillOpacity: 0.07, weight: 1 }} />
                <Circle center={[userLocation.lat, userLocation.lon]} radius={10000} pathOptions={{ color: "#3b82f6", fillOpacity: 0.05, weight: 1 }} />
                <Circle center={[userLocation.lat, userLocation.lon]} radius={20000} pathOptions={{ color: "#f59e0b", fillOpacity: 0.04, weight: 1 }} />
              </>
            )}
          </>
        )}

        {facilities.map((f) => {
          const color = FACILITY_COLORS[f.type] || FACILITY_COLORS.default;
          const selected = selectedFacility?.facility_id === f.facility_id;
          return (
            <Marker
              key={f.facility_id}
              position={[f.latitude, f.longitude]}
              icon={makeIcon(color, selected ? 16 : 8)}
              eventHandlers={{ click: () => onFacilitySelect(f) }}
            >
              <Popup>
                <div style={{ minWidth: 180 }}>
                  <strong style={{ fontSize: 13 }}>{f.name}</strong><br />
                  <span style={{ color: "#666", fontSize: 12 }}>{f.type}</span><br />
                  <span style={{ fontSize: 12 }}>{f.county} County</span><br />
                  {f.open_24_hours && <span style={{ fontSize: 11, color: "#10b981" }}>🕐 24hrs &nbsp;</span>}
                  {f.open_weekends && <span style={{ fontSize: 11, color: "#3b82f6" }}>📅 Weekends</span>}
                  {f.distance_km != null && <><br /><span style={{ fontSize: 12 }}>📍 {f.distance_km} km</span></>}
                </div>
              </Popup>
            </Marker>
          );
        })}

        {routeCoords?.length > 0 && (
          <Polyline positions={routeCoords} pathOptions={{ color: "#10b981", weight: 4, opacity: 0.9 }} />
        )}
      </MapContainer>

      <Legend activeLayer={activeLayer} theme={theme} />
      <StatsBar facilities={facilities} theme={theme} />
    </div>
  );
}

function Legend({ activeLayer, theme }) {
  const dark = theme === "dark";
  const box = {
    position: "absolute", bottom: 48, right: 12, zIndex: 1000,
    background: dark ? "rgba(17,24,39,0.92)" : "rgba(255,255,255,0.95)",
    borderRadius: 8, padding: "10px 14px", fontSize: 12,
    color: dark ? "#e2e8f0" : "#374151",
    backdropFilter: "blur(4px)",
    boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
  };
  const title = { fontWeight: 700, marginBottom: 6, color: "#6b7280", fontSize: 11, textTransform: "uppercase" };
  const row = (color) => ({ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 });
  const dot = (color) => ({ width: 10, height: 10, borderRadius: "50%", background: color, flexShrink: 0 });

  if (activeLayer === "facilities") return (
    <div style={box}>
      <div style={title}>Facility Type</div>
      {[["Hospital", "#ef4444"], ["Health Centre", "#3b82f6"], ["Clinic", "#06b6d4"], ["Dispensary", "#10b981"], ["Other", "#6b7280"]].map(([l, c]) => (
        <div key={l} style={row(c)}><div style={dot(c)} />{l}</div>
      ))}
    </div>
  );
  if (activeLayer === "accessibility") return (
    <div style={box}>
      <div style={title}>Accessibility</div>
      {Object.entries(BAND_COLORS).map(([b, c]) => (
        <div key={b} style={row(c)}><div style={dot(c)} />{b}</div>
      ))}
    </div>
  );
  if (activeLayer === "coverage") return (
    <div style={box}>
      <div style={title}>Coverage Radius</div>
      {[["5 km", "#10b981"], ["10 km", "#3b82f6"], ["20 km", "#f59e0b"]].map(([l, c]) => (
        <div key={l} style={row(c)}><div style={{ ...dot(c), background: "transparent", border: `2px solid ${c}` }} />{l}</div>
      ))}
    </div>
  );
  return null;
}

function StatsBar({ facilities, theme }) {
  const dark = theme === "dark";
  const operational = facilities.filter((f) => f.operational_status === "Operational").length;
  const open24 = facilities.filter((f) => f.open_24_hours).length;
  return (
    <div style={{
      position: "absolute", bottom: 0, left: 0, right: 0, zIndex: 999,
      background: dark ? "rgba(17,24,39,0.85)" : "rgba(255,255,255,0.9)",
      backdropFilter: "blur(4px)", padding: "4px 16px",
      display: "flex", gap: 24, fontSize: 12,
      color: dark ? "#9ca3af" : "#6b7280",
      borderTop: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}`,
    }}>
      <span>🏥 <strong style={{ color: dark ? "#e2e8f0" : "#374151" }}>{facilities.length}</strong> total</span>
      <span>✅ <strong style={{ color: "#10b981" }}>{operational}</strong> operational</span>
      <span>🕐 <strong style={{ color: "#3b82f6" }}>{open24}</strong> open 24h</span>
      <span style={{ marginLeft: "auto", color: "#6b7280" }}>KHAP Routing Intelligence v3 · Powered by OSM + PostGIS</span>
    </div>
  );
}
