import React, { useState } from "react";
import { fetchRoute, fetchNearestWithRoutes, fetchCoverage } from "../api/index.js";

const BAND_COLORS = {
  Excellent: "#10b981",
  Good: "#3b82f6",
  Moderate: "#f59e0b",
  Poor: "#f97316",
  Critical: "#ef4444",
};

const styles = {
  sidebar: {
    width: 300,
    background: "#111827",
    borderRight: "1px solid #1f2937",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    flexShrink: 0,
  },
  section: {
    padding: "12px 16px",
    borderBottom: "1px solid #1f2937",
  },
  label: {
    fontSize: 11,
    color: "#6b7280",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    marginBottom: 6,
    fontWeight: 600,
  },
  select: {
    width: "100%",
    background: "#1f2937",
    border: "1px solid #374151",
    color: "#e2e8f0",
    padding: "7px 10px",
    borderRadius: 6,
    fontSize: 13,
  },
  btn: {
    width: "100%",
    padding: "8px 12px",
    background: "#10b981",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: 13,
    fontWeight: 600,
    marginTop: 6,
  },
  secondaryBtn: {
    width: "100%",
    padding: "8px 12px",
    background: "#1f2937",
    color: "#e2e8f0",
    border: "1px solid #374151",
    borderRadius: 6,
    cursor: "pointer",
    fontSize: 13,
    marginTop: 6,
  },
  facilityCard: {
    background: "#1f2937",
    borderRadius: 8,
    padding: "10px 12px",
    marginTop: 8,
  },
  facilityName: { fontWeight: 600, fontSize: 14, color: "#f9fafb", marginBottom: 4 },
  facilityMeta: { fontSize: 12, color: "#9ca3af", lineHeight: 1.6 },
  scoreRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "5px 0",
    borderBottom: "1px solid #1f2937",
    fontSize: 13,
  },
  badge: (band) => ({
    background: BAND_COLORS[band] || "#6b7280",
    color: "#fff",
    borderRadius: 4,
    padding: "2px 7px",
    fontSize: 11,
    fontWeight: 600,
  }),
  scrollable: {
    flex: 1,
    overflowY: "auto",
    padding: "0 16px 16px",
  },
  travelInfo: {
    background: "#065f46",
    borderRadius: 6,
    padding: "8px 10px",
    marginTop: 8,
    fontSize: 12,
    color: "#a7f3d0",
    lineHeight: 1.7,
  },
  coverageInfo: {
    marginTop: 8,
  },
  coverageBand: {
    display: "flex",
    justifyContent: "space-between",
    padding: "4px 0",
    fontSize: 13,
    borderBottom: "1px solid #1f2937",
  },
};

export default function Sidebar({
  counties, selectedCounty, onCountyChange,
  selectedFacility, userLocation, accessibilityScores, activeLayer, onRouteSet,
}) {
  const [travelInfo, setTravelInfo] = useState(null);
  const [coverageInfo, setCoverageInfo] = useState(null);
  const [loadingRoute, setLoadingRoute] = useState(false);

  async function handleGetRoute() {
    if (!userLocation || !selectedFacility) return;
    setLoadingRoute(true);
    try {
      const routeData = await fetchRoute(
        userLocation.lat, userLocation.lon,
        selectedFacility.latitude, selectedFacility.longitude,
      );
      onRouteSet(routeData);
      setTravelInfo(routeData);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingRoute(false);
    }
  }

  async function handleCheckCoverage() {
    if (!userLocation) return;
    try {
      const data = await fetchCoverage(userLocation.lat, userLocation.lon, selectedCounty || null);
      setCoverageInfo(data);
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <div style={styles.sidebar}>
      <div style={styles.section}>
        <div style={styles.label}>Filter by County</div>
        <select
          style={styles.select}
          value={selectedCounty}
          onChange={(e) => onCountyChange(e.target.value)}
        >
          <option value="">All Kenya</option>
          {counties.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {activeLayer === "facilities" && selectedFacility && (
        <div style={styles.section}>
          <div style={styles.label}>Selected Facility</div>
          <div style={styles.facilityCard}>
            <div style={styles.facilityName}>{selectedFacility.name}</div>
            <div style={styles.facilityMeta}>
              {selectedFacility.type}<br />
              {selectedFacility.county} County<br />
              {selectedFacility.nearest_town && `Near ${selectedFacility.nearest_town}`}<br />
              {selectedFacility.open_24_hours && "🕐 Open 24 hours"}{" "}
              {selectedFacility.open_weekends && "📅 Open weekends"}
            </div>
          </div>
          {userLocation && (
            <button style={styles.btn} onClick={handleGetRoute} disabled={loadingRoute}>
              {loadingRoute ? "Getting route..." : "🗺 Get Road Route"}
            </button>
          )}
          {travelInfo && (
            <div style={styles.travelInfo}>
              🚗 Road distance: <strong>{travelInfo.distance_km} km</strong><br />
              ⏱ Travel time: <strong>{travelInfo.duration_minutes} min</strong><br />
              📡 Method: {travelInfo.method === "osrm" ? "Live road routing" : "Estimated"}
            </div>
          )}
        </div>
      )}

      {activeLayer === "coverage" && (
        <div style={styles.section}>
          <div style={styles.label}>Coverage from Your Location</div>
          <button style={styles.btn} onClick={handleCheckCoverage}>
            🎯 Analyse Coverage
          </button>
          {coverageInfo && (
            <div style={styles.coverageInfo}>
              <div style={{ ...styles.facilityMeta, marginBottom: 6, marginTop: 8 }}>
                Status: <strong style={{ color: coverageInfo.access_status === "adequate_access" ? "#10b981" : "#ef4444" }}>
                  {coverageInfo.access_message}
                </strong>
              </div>
              {Object.entries(coverageInfo.coverage_bands).map(([band, data]) => (
                <div key={band} style={styles.coverageBand}>
                  <span style={{ color: "#9ca3af" }}>{band.replace("within_", "Within ").replace("km", " km")}</span>
                  <strong>{data.count} facilities</strong>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeLayer === "accessibility" && accessibilityScores.length > 0 && (
        <div style={{ ...styles.section, flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={styles.label}>Accessibility Scores by County</div>
          <div style={styles.scrollable}>
            {accessibilityScores.map((item) => (
              <div key={item.county} style={styles.scoreRow}>
                <span style={{ color: "#e2e8f0" }}>{item.county}</span>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ color: "#9ca3af", fontSize: 12 }}>{item.score}</span>
                  <span style={styles.badge(item.band)}>{item.band}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
