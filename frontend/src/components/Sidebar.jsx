import React, { useState } from "react";
import {
  fetchRoute, fetchCoverage, fetchEmergencyZones,
  fetchCountyReport, fetchEmergencyReadiness, fetchCountyRankings,
  fetchFacilityStats,
} from "../api/index.js";

const BAND_COLORS = {
  Excellent: "#10b981", Good: "#3b82f6", Moderate: "#f59e0b",
  Poor: "#f97316", Critical: "#ef4444",
};
const ZONE_COLORS = {
  critical: "#ef4444", urgent: "#f97316", standard: "#f59e0b", remote: "#6b7280",
};

export default function Sidebar({
  counties, selectedCounty, onCountyChange, selectedFacility,
  userLocation, accessibilityScores, nationalSummary,
  activeLayer, onRouteSet, theme,
}) {
  const [travelInfo, setTravelInfo] = useState(null);
  const [coverageInfo, setCoverageInfo] = useState(null);
  const [emergencyZones, setEmergencyZones] = useState(null);
  const [countyReport, setCountyReport] = useState(null);
  const [rankings, setRankings] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const dark = theme === "dark";
  const s = {
    sidebar: {
      width: 300, flexShrink: 0, display: "flex", flexDirection: "column",
      overflow: "hidden",
      background: dark ? "#111827" : "#ffffff",
      borderRight: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}`,
    },
    sec: { padding: "12px 16px", borderBottom: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}` },
    label: { fontSize: 11, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6, fontWeight: 700 },
    select: {
      width: "100%", borderRadius: 6, padding: "7px 10px", fontSize: 13,
      background: dark ? "#1f2937" : "#f3f4f6",
      border: `1px solid ${dark ? "#374151" : "#d1d5db"}`,
      color: dark ? "#e2e8f0" : "#111827",
    },
    btn: {
      width: "100%", padding: "8px", background: "#10b981", color: "#fff",
      border: "none", borderRadius: 6, cursor: "pointer", fontSize: 13,
      fontWeight: 600, marginTop: 6,
    },
    btn2: {
      width: "100%", padding: "8px",
      background: dark ? "#1f2937" : "#f3f4f6",
      color: dark ? "#e2e8f0" : "#374151",
      border: `1px solid ${dark ? "#374151" : "#d1d5db"}`,
      borderRadius: 6, cursor: "pointer", fontSize: 13, marginTop: 6,
    },
    card: {
      background: dark ? "#1f2937" : "#f9fafb",
      borderRadius: 8, padding: "10px 12px", marginTop: 8,
    },
    name: { fontWeight: 700, fontSize: 14, color: dark ? "#f9fafb" : "#111827", marginBottom: 4 },
    meta: { fontSize: 12, color: dark ? "#9ca3af" : "#6b7280", lineHeight: 1.7 },
    row: {
      display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "5px 0", borderBottom: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}`, fontSize: 13,
      color: dark ? "#e2e8f0" : "#374151",
    },
    badge: (band) => ({
      background: BAND_COLORS[band] || "#6b7280", color: "#fff",
      borderRadius: 4, padding: "2px 7px", fontSize: 11, fontWeight: 600,
    }),
    scrollable: { flex: 1, overflowY: "auto", padding: "0 16px 16px" },
    travelBox: {
      background: dark ? "#065f46" : "#d1fae5", borderRadius: 6,
      padding: "8px 10px", marginTop: 8, fontSize: 12,
      color: dark ? "#a7f3d0" : "#065f46", lineHeight: 1.8,
    },
    statBox: {
      background: dark ? "#1f2937" : "#f3f4f6", borderRadius: 6,
      padding: "10px", marginTop: 8, fontSize: 12,
      color: dark ? "#d1d5db" : "#374151",
    },
    zoneRow: (zone) => ({
      display: "flex", justifyContent: "space-between",
      padding: "4px 0", fontSize: 12,
      borderBottom: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}`,
    }),
  };

  async function handleGetRoute() {
    if (!userLocation || !selectedFacility) return;
    setLoading(true);
    try {
      const r = await fetchRoute(userLocation.lat, userLocation.lon, selectedFacility.latitude, selectedFacility.longitude);
      onRouteSet(r);
      setTravelInfo(r);
    } catch (e) { console.error(e); } finally { setLoading(false); }
  }

  async function handleCoverage() {
    if (!userLocation) return;
    setLoading(true);
    try { setCoverageInfo(await fetchCoverage(userLocation.lat, userLocation.lon, selectedCounty || null)); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }

  async function handleEmergency() {
    if (!userLocation) return;
    setLoading(true);
    try { setEmergencyZones(await fetchEmergencyZones(userLocation.lat, userLocation.lon)); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }

  async function handleCountyReport() {
    if (!selectedCounty) return;
    setLoading(true);
    try { setCountyReport(await fetchCountyReport(selectedCounty)); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }

  async function handleRankings() {
    setLoading(true);
    try { setRankings(await fetchCountyRankings()); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  }

  return (
    <div style={s.sidebar}>
      <div style={s.sec}>
        <div style={s.label}>Filter by County</div>
        <select style={s.select} value={selectedCounty} onChange={(e) => onCountyChange(e.target.value)}>
          <option value="">All Kenya</option>
          {counties.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* FACILITIES tab */}
      {activeLayer === "facilities" && selectedFacility && (
        <div style={s.sec}>
          <div style={s.label}>Selected Facility</div>
          <div style={s.card}>
            <div style={s.name}>{selectedFacility.name}</div>
            <div style={s.meta}>
              <strong>{selectedFacility.type}</strong><br />
              {selectedFacility.county} County<br />
              {selectedFacility.nearest_town && `📍 Near ${selectedFacility.nearest_town}`}<br />
              {selectedFacility.open_24_hours && "🕐 Open 24 hours  "}
              {selectedFacility.open_weekends && "📅 Weekends"}
            </div>
          </div>
          {userLocation && (
            <button style={s.btn} onClick={handleGetRoute} disabled={loading}>
              {loading ? "Getting route…" : "🗺 Get Road Route"}
            </button>
          )}
          {travelInfo && (
            <div style={s.travelBox}>
              🚗 Road distance: <strong>{travelInfo.distance_km} km</strong><br />
              ⏱ Travel time: <strong>{travelInfo.duration_minutes} min</strong><br />
              📡 {travelInfo.method === "osrm" ? "Live road routing" : "Estimated"}
            </div>
          )}
        </div>
      )}

      {/* COVERAGE tab */}
      {activeLayer === "coverage" && (
        <div style={s.sec}>
          <div style={s.label}>Coverage Analysis</div>
          <button style={s.btn} onClick={handleCoverage} disabled={loading || !userLocation}>
            {loading ? "Analysing…" : "🎯 Analyse from My Location"}
          </button>
          {coverageInfo && (
            <div style={{ marginTop: 8 }}>
              <div style={{ ...s.meta, marginBottom: 6, color: BAND_COLORS[coverageInfo.access_status?.includes("adequate") ? "Good" : "Critical"] || "#9ca3af" }}>
                {coverageInfo.access_message}
              </div>
              {Object.entries(coverageInfo.coverage_bands || {}).map(([band, data]) => (
                <div key={band} style={s.row}>
                  <span>{band.replace("within_", "Within ").replace("km", " km")}</span>
                  <strong>{data.count} facilities</strong>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* EMERGENCY tab */}
      {activeLayer === "emergency" && (
        <div style={s.sec}>
          <div style={s.label}>Emergency Response Zones</div>
          <button style={s.btn} onClick={handleEmergency} disabled={loading || !userLocation}>
            {loading ? "Calculating…" : "🚨 Calculate Response Zones"}
          </button>
          {emergencyZones && (
            <div style={{ marginTop: 8 }}>
              {Object.entries(emergencyZones.zones || {}).map(([zone, facilities]) => (
                <div key={zone} style={s.zoneRow(zone)}>
                  <span style={{ color: ZONE_COLORS[zone] || "#9ca3af", fontWeight: 600 }}>
                    {zone === "critical" ? "< 15 min" : zone === "urgent" ? "15–30 min" : zone === "standard" ? "30–60 min" : "> 60 min"}
                  </span>
                  <span>{facilities.length} facilities</span>
                </div>
              ))}
              {emergencyZones.zones?.critical?.[0] && (
                <div style={{ ...s.meta, marginTop: 8 }}>
                  Nearest: <strong>{emergencyZones.zones.critical[0].name}</strong>
                  {" "}({emergencyZones.zones.critical[0].est_response_min} min)
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ACCESSIBILITY tab */}
      {activeLayer === "accessibility" && accessibilityScores.length > 0 && (
        <div style={{ ...s.sec, flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={s.label}>County Accessibility Scores</div>
          <div style={s.scrollable}>
            {accessibilityScores.map((item) => (
              <div key={item.county} style={s.row}>
                <span>{item.county}</span>
                <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <span style={{ color: "#9ca3af", fontSize: 12 }}>{item.score}</span>
                  <span style={s.badge(item.band)}>{item.band}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* REPORTS tab */}
      {activeLayer === "reports" && (
        <div style={{ ...s.sec, flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={s.label}>Reports & Intelligence</div>
          {selectedCounty && (
            <button style={s.btn} onClick={handleCountyReport} disabled={loading}>
              {loading ? "Loading…" : `📋 ${selectedCounty} County Report`}
            </button>
          )}
          <button style={s.btn2} onClick={handleRankings} disabled={loading}>
            🏆 County Rankings
          </button>
          <div style={s.scrollable}>
            {countyReport && (
              <div style={{ marginTop: 8 }}>
                <div style={s.meta}>
                  <strong>{countyReport.county}</strong><br />
                  {countyReport.operational_facilities} operational facilities<br />
                  Accessibility: <span style={{ color: BAND_COLORS[countyReport.accessibility?.band] }}><strong>{countyReport.accessibility?.band}</strong></span>
                  {" "}(score: {countyReport.accessibility?.score})<br />
                  Coverage gaps: {countyReport.coverage_gaps}<br />
                  Critical load facilities: {countyReport.load_analysis?.critical}
                </div>
                {countyReport.recommended_new_facility_sites?.length > 0 && (
                  <>
                    <div style={{ ...s.label, marginTop: 10 }}>Top New Facility Sites</div>
                    {countyReport.recommended_new_facility_sites.map((site, i) => (
                      <div key={i} style={s.statBox}>
                        📍 {site.latitude.toFixed(3)}, {site.longitude.toFixed(3)}<br />
                        +{site.estimated_people_gaining_access?.toLocaleString()} people gaining access
                      </div>
                    ))}
                  </>
                )}
              </div>
            )}
            {rankings && (
              <div style={{ marginTop: 8 }}>
                {rankings.rankings?.map((r) => (
                  <div key={r.county} style={s.row}>
                    <span><span style={{ color: "#6b7280", marginRight: 6 }}>#{r.rank}</span>{r.county}</span>
                    <span style={s.badge(r.band)}>{r.score}</span>
                  </div>
                ))}
              </div>
            )}
            {nationalSummary && !countyReport && !rankings && (
              <div style={{ marginTop: 8 }}>
                <div style={s.statBox}>
                  <strong>Kenya National Summary</strong><br />
                  Total facilities: {nationalSummary.total_facilities}<br />
                  Coverage gaps: {nationalSummary.coverage_gaps?.total_uncovered_cells}<br />
                  Est. without access: {nationalSummary.coverage_gaps?.estimated_population_without_access?.toLocaleString()}<br />
                  Best county: {nationalSummary.accessibility_summary?.best_county}<br />
                  Worst county: {nationalSummary.accessibility_summary?.worst_county}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
