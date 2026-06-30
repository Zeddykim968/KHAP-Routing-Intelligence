import React, { useEffect } from "react";
import {
  MapContainer, TileLayer, Marker, Popup,
  Polyline, Circle, useMap,
} from "react-leaflet";
import L from "leaflet";

const FACILITY_COLORS = {
  "District Hospital": "#ef4444",
  "Provincial General Hospital": "#dc2626",
  "National Referral Hospital": "#b91c1c",
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
  "Laboratory (Stand-alone)": "#d946ef",
  default: "#6b7280",
};

const BAND_COLORS = {
  Excellent: "#10b981", Good: "#3b82f6", Moderate: "#f59e0b",
  Poor: "#f97316", Critical: "#ef4444",
};

const FIN_COLORS = {
  "Free/Subsidized": "#10b981", Low: "#3b82f6", Medium: "#f59e0b", High: "#ef4444",
};

const DARK_TILE  = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";
const LIGHT_TILE = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png";

function makeIcon(color, size = 10, ring = false) {
  const border = ring
    ? `border:3px solid ${color};background:transparent;box-shadow:0 0 8px ${color}88`
    : `background:${color};border:2px solid rgba(255,255,255,0.7);box-shadow:0 0 4px rgba(0,0,0,0.5)`;
  return L.divIcon({
    className: "",
    html: `<div style="width:${size}px;height:${size}px;border-radius:50%;${border}"></div>`,
    iconAnchor: [size / 2, size / 2],
  });
}

function userIcon() {
  return L.divIcon({
    className: "",
    html: `<div style="width:16px;height:16px;border-radius:50%;background:#3b82f6;border:3px solid #fff;box-shadow:0 0 12px rgba(59,130,246,0.9)"></div>`,
    iconAnchor: [8, 8],
  });
}

function destinationIcon() {
  return L.divIcon({
    className: "",
    html: `<div style="font-size:22px;line-height:1;filter:drop-shadow(0 2px 4px rgba(0,0,0,0.5))">🏥</div>`,
    iconAnchor: [11, 22],
  });
}

function FlyTo({ target }) {
  const map = useMap();
  useEffect(() => {
    if (target) map.setView(target, 13, { animate: true });
  }, [target?.toString()]);
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
    if (coords && coords.length >= 2) {
      const bounds = L.latLngBounds(coords);
      map.fitBounds(bounds, { padding: [60, 60], animate: true });
    }
  }, [coords]);
  return null;
}

export default function MapView({
  facilities, userLocation, selectedFacility,
  onFacilitySelect, route, activeLayer, accessibilityScores, theme, smartResults,
}) {
  const routeCoords = route?.geometry?.coordinates?.map(([lng, lat]) => [lat, lng]);
  const destination = route?.destination;

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

        {/* Fly to user on first load */}
        {userLocation && <FlyToUser userLocation={userLocation} />}

        {/* Fit map to route when route changes */}
        {routeCoords?.length >= 2 && <FitRoute coords={routeCoords} />}

        {/* User location marker */}
        {userLocation && (
          <>
            <Marker position={[userLocation.lat, userLocation.lon]} icon={userIcon()}>
              <Popup><strong>📍 Your Location</strong></Popup>
            </Marker>

            {/* Coverage rings */}
            {activeLayer === "coverage" && (
              <>
                <Circle center={[userLocation.lat, userLocation.lon]} radius={5000}  pathOptions={{ color: "#10b981", fillOpacity: 0.07, weight: 1.5 }} />
                <Circle center={[userLocation.lat, userLocation.lon]} radius={10000} pathOptions={{ color: "#3b82f6", fillOpacity: 0.05, weight: 1 }} />
                <Circle center={[userLocation.lat, userLocation.lon]} radius={20000} pathOptions={{ color: "#f59e0b", fillOpacity: 0.04, weight: 1 }} />
              </>
            )}
          </>
        )}

        {/* Road route polyline */}
        {routeCoords?.length > 0 && (
          <>
            <Polyline
              positions={routeCoords}
              pathOptions={{ color: "#1d4ed8", weight: 6, opacity: 0.35 }}
            />
            <Polyline
              positions={routeCoords}
              pathOptions={{ color: "#3b82f6", weight: 3, opacity: 0.95, dashArray: null }}
            />
          </>
        )}

        {/* Route destination marker */}
        {destination && destination.latitude && (
          <Marker
            position={[destination.latitude, destination.longitude]}
            icon={destinationIcon()}
          >
            <Popup>
              <strong>{destination.name}</strong><br />
              {destination.type}<br />
              {route?.distance_km} km · {route?.duration_minutes} min drive
            </Popup>
          </Marker>
        )}

        {/* Facility markers */}
        {facilities.map((f) => {
          if (!f.latitude || !f.longitude) return null;
          const color   = FACILITY_COLORS[f.type] || FACILITY_COLORS.default;
          const selected = selectedFacility?.facility_id === f.facility_id;
          const isTop    = smartResults && f.score != null && f.score >= 70;

          return (
            <Marker
              key={f.facility_id}
              position={[f.latitude, f.longitude]}
              icon={makeIcon(color, selected ? 18 : isTop ? 13 : 8, isTop && !selected)}
              eventHandlers={{ click: () => onFacilitySelect(f) }}
            >
              <Popup>
                <div style={{ minWidth: 190 }}>
                  <strong style={{ fontSize: 13 }}>{f.name}</strong><br />
                  <span style={{ color: "#666", fontSize: 12 }}>{f.type}</span><br />
                  <span style={{ fontSize: 12 }}>{f.county} County</span><br />
                  {f.distance_km != null && <><span style={{ fontSize: 12 }}>📍 {f.distance_km} km</span><br /></>}
                  {f.estimated_minutes != null && <><span style={{ fontSize: 12 }}>⏱ {f.estimated_minutes} min drive</span><br /></>}
                  {f.open_24_hours  && <span style={{ fontSize: 11, color: "#10b981" }}>🕐 24hrs &nbsp;</span>}
                  {f.open_weekends  && <span style={{ fontSize: 11, color: "#3b82f6" }}>📅 Weekends &nbsp;</span>}
                  {((f.beds || 0) + (f.cots || 0)) > 0 && (
                    <><br /><span style={{ fontSize: 11 }}>🛏 {(f.beds || 0) + (f.cots || 0)} beds/cots</span></>
                  )}
                  {f.financial_level && (
                    <><br /><span style={{ fontSize: 11, color: FIN_COLORS[f.financial_level] || "#6b7280" }}>💰 {f.financial_level} cost</span></>
                  )}
                  {f.insurance_providers?.length > 0 && (
                    <><br /><span style={{ fontSize: 11 }}>🛡 {f.insurance_providers.slice(0, 3).join(", ")}</span></>
                  )}
                  {f.score != null && (
                    <><br /><span style={{ fontSize: 11, color: "#10b981" }}>⭐ Match score: {f.score}/100</span></>
                  )}
                  {f.match_reason && (
                    <><br /><span style={{ fontSize: 10, color: "#9ca3af", fontStyle: "italic" }}>{f.match_reason}</span></>
                  )}
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>

      <Legend activeLayer={activeLayer} theme={theme} smartResults={smartResults} />
      <StatsBar facilities={facilities} theme={theme} route={route} />
    </div>
  );
}

function Legend({ activeLayer, theme, smartResults }) {
  const dark = theme === "dark";
  const box = {
    position: "absolute", bottom: 48, right: 12, zIndex: 1000,
    background: dark ? "rgba(17,24,39,0.93)" : "rgba(255,255,255,0.96)",
    borderRadius: 8, padding: "10px 14px", fontSize: 12,
    color: dark ? "#e2e8f0" : "#374151",
    backdropFilter: "blur(4px)",
    boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
  };
  const title = { fontWeight: 700, marginBottom: 6, color: "#6b7280", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em" };
  const row   = { display: "flex", alignItems: "center", gap: 8, marginBottom: 3 };
  const dot   = (color, ring = false) => ({
    width: 10, height: 10, borderRadius: "50%", flexShrink: 0,
    ...(ring
      ? { border: `2px solid ${color}`, background: "transparent" }
      : { background: color }),
  });

  if (activeLayer === "emergency" && smartResults) return (
    <div style={box}>
      <div style={title}>Emergency Results</div>
      <div style={row}><div style={dot("#ef4444")} />Best match</div>
      <div style={row}><div style={dot("#3b82f6", true)} />Good match</div>
      <div style={row}><div style={{ ...dot("#3b82f6"), background: "#1d4ed8", height: 4, width: 18, borderRadius: 2 }} />Road route</div>
    </div>
  );

  if (activeLayer === "facilities") return (
    <div style={box}>
      <div style={title}>Facility Type</div>
      {[
        ["Hospital",     "#ef4444"],
        ["Health Centre","#3b82f6"],
        ["Clinic",       "#06b6d4"],
        ["Dispensary",   "#10b981"],
        ["Maternity",    "#ec4899"],
        ["Other",        "#6b7280"],
      ].map(([l, c]) => (
        <div key={l} style={row}><div style={dot(c)} />{l}</div>
      ))}
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
      {[["5 km", "#10b981"], ["10 km", "#3b82f6"], ["20 km", "#f59e0b"]].map(([l, c]) => (
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
      background: dark ? "rgba(17,24,39,0.88)" : "rgba(255,255,255,0.92)",
      backdropFilter: "blur(4px)", padding: "4px 16px",
      display: "flex", gap: 24, fontSize: 12,
      color: dark ? "#9ca3af" : "#6b7280",
      borderTop: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}`,
      flexWrap: "wrap",
    }}>
      <span>🏥 <strong style={{ color: dark ? "#e2e8f0" : "#374151" }}>{facilities.length.toLocaleString()}</strong> facilities</span>
      <span>✅ <strong style={{ color: "#10b981" }}>{operational.toLocaleString()}</strong> operational</span>
      <span>🕐 <strong style={{ color: "#3b82f6" }}>{open24}</strong> open 24h</span>
      {route && (
        <span>🚗 <strong style={{ color: "#f59e0b" }}>{route.distance_km} km</strong> · <strong style={{ color: "#f59e0b" }}>{route.duration_minutes} min</strong></span>
      )}
      <span style={{ marginLeft: "auto", color: "#6b7280" }}>KHAP Routing Intelligence · OSM + PostGIS</span>
    </div>
  );
}
