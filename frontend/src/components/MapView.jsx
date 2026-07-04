import React, { useEffect, useRef } from "react";
import {
  MapContainer, TileLayer, Marker, Popup,
  Polyline, Circle, useMap,
} from "react-leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import L from "leaflet";

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

const DARK_TILE  = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const LIGHT_TILE = "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png";
const LABEL_TILE = "https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png";

function createClusterIcon(cluster) {
  const count = cluster.getChildCount();
  const size  = count < 10 ? 28 : count < 100 ? 34 : 42;
  const color = count < 10 ? "#10b981" : count < 100 ? "#3b82f6" : "#ef4444";
  return L.divIcon({
    html: `<div style="
      width:${size}px;height:${size}px;border-radius:50%;
      background:${color};
      display:flex;align-items:center;justify-content:center;
      color:#fff;font-weight:700;font-size:${size < 34 ? 11 : 13}px;
      border:2.5px solid rgba(255,255,255,0.85);
      box-shadow:0 2px 10px rgba(0,0,0,0.35);
    ">${count}</div>`,
    className: "",
    iconSize: L.point(size, size, true),
  });
}

function makeIcon(color, size = 10, ring = false, pulse = false) {
  const pulseStyle = pulse
    ? `animation:pulse 1.5s ease-in-out infinite;`
    : "";
  const border = ring
    ? `border:3px solid ${color};background:transparent;box-shadow:0 0 10px ${color}99`
    : `background:${color};border:2px solid rgba(255,255,255,0.75);box-shadow:0 1px 5px rgba(0,0,0,0.4)`;
  return L.divIcon({
    className: "",
    html: `<div style="width:${size}px;height:${size}px;border-radius:50%;${border};${pulseStyle}"></div>`,
    iconAnchor: [size / 2, size / 2],
  });
}

function userIcon() {
  return L.divIcon({
    className: "",
    html: `
      <div style="position:relative;width:20px;height:20px">
        <div style="position:absolute;inset:0;border-radius:50%;background:rgba(59,130,246,0.25);animation:ripple 2s ease-out infinite"></div>
        <div style="position:absolute;top:2px;left:2px;width:16px;height:16px;border-radius:50%;background:#3b82f6;border:3px solid #fff;box-shadow:0 0 12px rgba(59,130,246,0.8)"></div>
      </div>
      <style>
        @keyframes ripple{0%{transform:scale(1);opacity:0.7}100%{transform:scale(2.5);opacity:0}}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.6}}
      </style>
    `,
    iconAnchor: [10, 10],
  });
}

function destinationIcon(name) {
  return L.divIcon({
    className: "",
    html: `
      <div style="text-align:center">
        <div style="font-size:24px;line-height:1;filter:drop-shadow(0 2px 4px rgba(0,0,0,0.6))">🏥</div>
        ${name ? `<div style="background:rgba(0,0,0,0.75);color:#fff;font-size:9px;padding:2px 4px;border-radius:3px;white-space:nowrap;max-width:120px;overflow:hidden;text-overflow:ellipsis;margin-top:2px">${name}</div>` : ""}
      </div>
    `,
    iconAnchor: [12, 28],
  });
}

function FlyTo({ target }) {
  const map = useMap();
  useEffect(() => {
    if (target) map.flyTo(target, 14, { duration: 1.2 });
  }, [JSON.stringify(target)]);
  return null;
}

function FlyToUser({ userLocation }) {
  const map = useMap();
  useEffect(() => {
    if (userLocation) map.setView([userLocation.lat, userLocation.lon], 9);
  }, []);
  return null;
}

function FitRoute({ coords }) {
  const map = useMap();
  useEffect(() => {
    if (coords?.length >= 2) {
      map.fitBounds(L.latLngBounds(coords), { padding: [60, 60], animate: true });
    }
  }, [coords?.length]);
  return null;
}

export default function MapView({
  facilities, userLocation, selectedFacility,
  onFacilitySelect, route, activeLayer,
  accessibilityScores, theme, smartResults,
}) {
  const routeCoords = route?.geometry?.coordinates?.map(([lng, lat]) => [lat, lng]);
  const destination = route?.destination;
  const dark = theme === "dark";

  return (
    <div style={{ flex: 1, position: "relative" }}>
      <MapContainer
        center={[-0.0236, 37.9062]}
        zoom={6}
        style={{ height: "100%", width: "100%" }}
        zoomControl
        preferCanvas={false}
      >
        <TileLayer
          url={dark ? DARK_TILE : LIGHT_TILE}
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          maxZoom={19}
        />
        {!dark && (
          <TileLayer
            url={LABEL_TILE}
            attribution=""
            maxZoom={19}
          />
        )}

        {userLocation && <FlyToUser userLocation={userLocation} />}
        {routeCoords?.length >= 2 && <FitRoute coords={routeCoords} />}
        {selectedFacility?.latitude && !route && (
          <FlyTo target={[selectedFacility.latitude, selectedFacility.longitude]} />
        )}

        {/* User location */}
        {userLocation && (
          <>
            <Marker position={[userLocation.lat, userLocation.lon]} icon={userIcon()} zIndexOffset={1000}>
              <Popup><strong>📍 Your Location</strong></Popup>
            </Marker>
            {activeLayer === "coverage" && (
              <>
                <Circle center={[userLocation.lat, userLocation.lon]} radius={5000}  pathOptions={{ color: "#10b981", fillOpacity: 0.08, weight: 1.5, dashArray: "4 4" }} />
                <Circle center={[userLocation.lat, userLocation.lon]} radius={10000} pathOptions={{ color: "#3b82f6", fillOpacity: 0.05, weight: 1.5, dashArray: "4 4" }} />
                <Circle center={[userLocation.lat, userLocation.lon]} radius={20000} pathOptions={{ color: "#f59e0b", fillOpacity: 0.04, weight: 1,   dashArray: "4 4" }} />
              </>
            )}
          </>
        )}

        {/* Road route — double-stroke for road feel */}
        {routeCoords?.length > 0 && (
          <>
            <Polyline positions={routeCoords} pathOptions={{ color: dark ? "#1e3a5f" : "#1d4ed8", weight: 9,  opacity: 0.4 }} />
            <Polyline positions={routeCoords} pathOptions={{ color: "#60a5fa",                              weight: 4,  opacity: 1,   dashArray: null }} />
          </>
        )}

        {/* Destination pin */}
        {destination?.latitude && (
          <Marker
            position={[destination.latitude, destination.longitude]}
            icon={destinationIcon(destination.name)}
            zIndexOffset={900}
          >
            <Popup>
              <div style={{ minWidth: 180 }}>
                <strong style={{ fontSize: 13 }}>{destination.name}</strong><br />
                <span style={{ color: "#666", fontSize: 12 }}>{destination.type}</span><br />
                {route?.distance_km != null && (
                  <span style={{ fontSize: 12 }}>🚗 {route.distance_km} km · ⏱ {route.duration_minutes} min</span>
                )}
              </div>
            </Popup>
          </Marker>
        )}

        {/* Facility markers — clustered */}
        <MarkerClusterGroup
          chunkedLoading
          iconCreateFunction={createClusterIcon}
          maxClusterRadius={50}
          spiderfyOnMaxZoom
          showCoverageOnHover={false}
          zoomToBoundsOnClick
          disableClusteringAtZoom={14}
        >
          {facilities.map((f) => {
            if (!f.latitude || !f.longitude) return null;
            const color    = FACILITY_COLORS[f.type] || FACILITY_COLORS.default;
            const selected = selectedFacility?.facility_id === f.facility_id;
            const isTop    = smartResults && f.score != null && f.score >= 65;
            const size     = selected ? 20 : isTop ? 14 : 9;

            return (
              <Marker
                key={f.facility_id}
                position={[f.latitude, f.longitude]}
                icon={makeIcon(color, size, isTop && !selected, false)}
                eventHandlers={{ click: () => onFacilitySelect(f) }}
              >
                <Popup>
                  <FacilityPopup f={f} />
                </Popup>
              </Marker>
            );
          })}
        </MarkerClusterGroup>
      </MapContainer>

      <Legend activeLayer={activeLayer} theme={theme} smartResults={smartResults} />
      <StatsBar facilities={facilities} theme={theme} route={route} />
    </div>
  );
}

function FacilityPopup({ f }) {
  const beds = (f.beds || 0) + (f.cots || 0);
  const fl = f.financial_level;
  const flColor = FIN_COLORS[fl] || "#6b7280";

  return (
    <div style={{ minWidth: 200, fontFamily: "system-ui, sans-serif" }}>
      <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 2 }}>{f.name}</div>
      <div style={{ color: "#6b7280", fontSize: 11, marginBottom: 6 }}>
        {f.type} · {f.county} County
        {f.nearest_town ? ` · ${f.nearest_town}` : ""}
      </div>

      <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginBottom: 6 }}>
        <span style={{ background: f.operational_status === "Operational" ? "#d1fae5" : "#fee2e2", color: f.operational_status === "Operational" ? "#065f46" : "#991b1b", borderRadius: 4, padding: "2px 6px", fontSize: 10, fontWeight: 600 }}>
          {f.operational_status || "Unknown"}
        </span>
        {f.open_24_hours && <span style={{ background: "#dbeafe", color: "#1e40af", borderRadius: 4, padding: "2px 6px", fontSize: 10, fontWeight: 600 }}>🕐 24hrs</span>}
        {f.open_weekends && <span style={{ background: "#ede9fe", color: "#5b21b6", borderRadius: 4, padding: "2px 6px", fontSize: 10, fontWeight: 600 }}>📅 Wknds</span>}
      </div>

      {beds > 0 && <div style={{ fontSize: 11, marginBottom: 3 }}>🛏 <strong>{beds}</strong> beds/cots</div>}
      {f.distance_km != null && <div style={{ fontSize: 11, marginBottom: 3 }}>📍 <strong>{f.distance_km} km</strong>{f.estimated_minutes != null ? ` · ⏱ ${f.estimated_minutes} min` : ""}</div>}
      {fl && (
        <div style={{ fontSize: 11, marginBottom: 3 }}>
          💰 <span style={{ color: flColor, fontWeight: 600 }}>{fl} cost</span>
        </div>
      )}
      {(f.insurance_providers || []).length > 0 && (
        <div style={{ fontSize: 10, color: "#6b7280", marginBottom: 3 }}>
          🛡 {f.insurance_providers.slice(0, 3).join(" · ")}
        </div>
      )}
      {f.score != null && (
        <div style={{ fontSize: 11, color: "#10b981", fontWeight: 600, marginTop: 4 }}>
          ⭐ Match: {f.score}/100
          {f.match_reason && <div style={{ color: "#9ca3af", fontWeight: 400, fontStyle: "italic", fontSize: 10 }}>{f.match_reason}</div>}
        </div>
      )}
    </div>
  );
}

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

function StatsBar({ facilities, theme, route }) {
  const dark = theme === "dark";
  const operational = facilities.filter((f) => f.operational_status === "Operational" || f.score != null).length;
  const open24 = facilities.filter((f) => f.open_24_hours).length;
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
        </>
      )}
      <span style={{ marginLeft: "auto", color: "#6b7280", fontSize: 10 }}>
        KHAP v3 · OSM + PostGIS
      </span>
    </div>
  );
}
