import React, { useEffect, useRef } from "react";
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  Circle,
  useMap,
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
  "default": "#6b7280",
};

const BAND_COLORS = {
  Excellent: "#10b981",
  Good: "#3b82f6",
  Moderate: "#f59e0b",
  Poor: "#f97316",
  Critical: "#ef4444",
};

function makeIcon(color, size = 10) {
  return L.divIcon({
    className: "",
    html: `<div style="
      width:${size}px;height:${size}px;
      border-radius:50%;
      background:${color};
      border:2px solid rgba(255,255,255,0.6);
      box-shadow:0 0 4px rgba(0,0,0,0.5);
    "></div>`,
    iconAnchor: [size / 2, size / 2],
  });
}

function userIcon() {
  return L.divIcon({
    className: "",
    html: `<div style="
      width:14px;height:14px;
      border-radius:50%;
      background:#3b82f6;
      border:3px solid #fff;
      box-shadow:0 0 8px rgba(59,130,246,0.8);
    "></div>`,
    iconAnchor: [7, 7],
  });
}

function FlyToUser({ userLocation }) {
  const map = useMap();
  useEffect(() => {
    if (userLocation) {
      map.setView([userLocation.lat, userLocation.lon], 9);
    }
  }, [userLocation, map]);
  return null;
}

export default function MapView({
  facilities, userLocation, selectedFacility,
  onFacilitySelect, route, activeLayer, accessibilityScores,
}) {
  const routeCoords = route?.geometry?.coordinates?.map(([lng, lat]) => [lat, lng]);

  return (
    <div style={{ flex: 1, position: "relative" }}>
      <MapContainer
        center={[-0.0236, 37.9062]}
        zoom={6}
        style={{ height: "100%", width: "100%", background: "#1a2332" }}
        zoomControl={true}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/">CARTO</a>'
        />

        {userLocation && (
          <>
            <FlyToUser userLocation={userLocation} />
            <Marker position={[userLocation.lat, userLocation.lon]} icon={userIcon()}>
              <Popup>
                <strong>Your Location</strong><br />
                {userLocation.lat.toFixed(4)}, {userLocation.lon.toFixed(4)}
              </Popup>
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
          const isSelected = selectedFacility?.facility_id === f.facility_id;
          return (
            <Marker
              key={f.facility_id}
              position={[f.latitude, f.longitude]}
              icon={makeIcon(color, isSelected ? 14 : 8)}
              eventHandlers={{ click: () => onFacilitySelect(f) }}
            >
              <Popup>
                <div style={{ minWidth: 180 }}>
                  <strong style={{ fontSize: 13 }}>{f.name}</strong><br />
                  <span style={{ color: "#666", fontSize: 12 }}>{f.type}</span><br />
                  <span style={{ fontSize: 12 }}>{f.county} County</span><br />
                  {f.open_24_hours && <span style={{ fontSize: 11, color: "#10b981" }}>🕐 Open 24hrs &nbsp;</span>}
                  {f.open_weekends && <span style={{ fontSize: 11, color: "#3b82f6" }}>📅 Weekends</span>}
                  {f.distance_km && <><br /><span style={{ fontSize: 12 }}>📍 {f.distance_km} km away</span></>}
                </div>
              </Popup>
            </Marker>
          );
        })}

        {routeCoords && routeCoords.length > 0 && (
          <Polyline
            positions={routeCoords}
            pathOptions={{ color: "#10b981", weight: 4, opacity: 0.85 }}
          />
        )}
      </MapContainer>

      <Legend activeLayer={activeLayer} />
    </div>
  );
}

function Legend({ activeLayer }) {
  if (activeLayer === "facilities") {
    const topTypes = [
      ["District / Provincial Hospital", "#ef4444"],
      ["Health Centre", "#3b82f6"],
      ["Medical Clinic", "#06b6d4"],
      ["Dispensary", "#10b981"],
      ["Other", "#6b7280"],
    ];
    return (
      <div style={{
        position: "absolute", bottom: 24, right: 12, zIndex: 1000,
        background: "rgba(17,24,39,0.9)", borderRadius: 8, padding: "10px 14px",
        fontSize: 12, color: "#e2e8f0", backdropFilter: "blur(4px)",
      }}>
        <div style={{ fontWeight: 700, marginBottom: 6, color: "#9ca3af", fontSize: 11, textTransform: "uppercase" }}>Facility Type</div>
        {topTypes.map(([label, color]) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: color, flexShrink: 0 }} />
            {label}
          </div>
        ))}
      </div>
    );
  }

  if (activeLayer === "accessibility") {
    return (
      <div style={{
        position: "absolute", bottom: 24, right: 12, zIndex: 1000,
        background: "rgba(17,24,39,0.9)", borderRadius: 8, padding: "10px 14px",
        fontSize: 12, color: "#e2e8f0", backdropFilter: "blur(4px)",
      }}>
        <div style={{ fontWeight: 700, marginBottom: 6, color: "#9ca3af", fontSize: 11, textTransform: "uppercase" }}>Accessibility</div>
        {Object.entries(BAND_COLORS).map(([band, color]) => (
          <div key={band} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", background: color, flexShrink: 0 }} />
            {band}
          </div>
        ))}
      </div>
    );
  }

  if (activeLayer === "coverage") {
    return (
      <div style={{
        position: "absolute", bottom: 24, right: 12, zIndex: 1000,
        background: "rgba(17,24,39,0.9)", borderRadius: 8, padding: "10px 14px",
        fontSize: 12, color: "#e2e8f0", backdropFilter: "blur(4px)",
      }}>
        <div style={{ fontWeight: 700, marginBottom: 6, color: "#9ca3af", fontSize: 11, textTransform: "uppercase" }}>Coverage Radius</div>
        {[["5 km", "#10b981"], ["10 km", "#3b82f6"], ["20 km", "#f59e0b"]].map(([label, color]) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
            <div style={{ width: 10, height: 10, borderRadius: "50%", border: `2px solid ${color}`, flexShrink: 0 }} />
            {label}
          </div>
        ))}
      </div>
    );
  }

  return null;
}
