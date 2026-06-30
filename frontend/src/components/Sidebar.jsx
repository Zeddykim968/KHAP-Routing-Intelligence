import React, { useState, useEffect } from "react";
import {
  fetchRoute, fetchCoverage, fetchEmergencyZones,
  fetchCountyReport, fetchCountyRankings,
  fetchSmartRecommendations, fetchRoadRoute,
  fetchPopulationServed,
} from "../api/index.js";

const BAND_COLORS = {
  Excellent: "#10b981", Good: "#3b82f6", Moderate: "#f59e0b",
  Poor: "#f97316", Critical: "#ef4444",
};
const ZONE_COLORS = {
  critical: "#ef4444", urgent: "#f97316", standard: "#f59e0b", remote: "#6b7280",
};
const FIN_COLORS = {
  "Free/Subsidized": "#10b981", Low: "#3b82f6", Medium: "#f59e0b", High: "#ef4444",
};

export default function Sidebar({
  counties, selectedCounty, onCountyChange, selectedFacility,
  userLocation, accessibilityScores, nationalSummary,
  activeLayer, onRouteSet, theme,
  emergencyTypes, insuranceProviders,
}) {
  const [travelInfo, setTravelInfo] = useState(null);
  const [coverageInfo, setCoverageInfo] = useState(null);
  const [countyReport, setCountyReport] = useState(null);
  const [rankings, setRankings] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Smart routing state
  const [emergencyType, setEmergencyType] = useState("general");
  const [insurance, setInsurance] = useState("");
  const [financialLevel, setFinancialLevel] = useState("Any");
  const [radiusKm, setRadiusKm] = useState(30);
  const [smartResults, setSmartResults] = useState(null);
  const [routingFacility, setRoutingFacility] = useState(null);

  // Population panel state
  const [popData, setPopData] = useState(null);
  const [popRadius, setPopRadius] = useState(10);

  const dark = theme === "dark";

  const s = {
    sidebar: {
      width: 310, flexShrink: 0, display: "flex", flexDirection: "column",
      overflow: "hidden",
      background: dark ? "#111827" : "#ffffff",
      borderRight: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}`,
    },
    sec: { padding: "12px 14px", borderBottom: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}` },
    label: { fontSize: 10, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6, fontWeight: 700 },
    select: {
      width: "100%", borderRadius: 6, padding: "6px 10px", fontSize: 12,
      background: dark ? "#1f2937" : "#f3f4f6",
      border: `1px solid ${dark ? "#374151" : "#d1d5db"}`,
      color: dark ? "#e2e8f0" : "#111827", marginBottom: 6,
    },
    btn: (color = "#10b981") => ({
      width: "100%", padding: "8px", background: color, color: "#fff",
      border: "none", borderRadius: 6, cursor: "pointer", fontSize: 12,
      fontWeight: 600, marginTop: 4,
    }),
    btn2: {
      width: "100%", padding: "7px",
      background: dark ? "#1f2937" : "#f3f4f6",
      color: dark ? "#e2e8f0" : "#374151",
      border: `1px solid ${dark ? "#374151" : "#d1d5db"}`,
      borderRadius: 6, cursor: "pointer", fontSize: 12, marginTop: 4,
    },
    card: {
      background: dark ? "#1f2937" : "#f9fafb",
      borderRadius: 8, padding: "10px 12px", marginTop: 6,
    },
    resultCard: (highlighted) => ({
      background: highlighted ? (dark ? "#064e3b" : "#ecfdf5") : (dark ? "#1f2937" : "#f9fafb"),
      borderRadius: 8, padding: "10px 12px", marginTop: 6,
      border: highlighted ? "1px solid #10b981" : `1px solid ${dark ? "#374151" : "#e5e7eb"}`,
      cursor: "pointer",
    }),
    name: { fontWeight: 700, fontSize: 13, color: dark ? "#f9fafb" : "#111827", marginBottom: 2 },
    meta: { fontSize: 11, color: dark ? "#9ca3af" : "#6b7280", lineHeight: 1.7 },
    row: {
      display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "4px 0", borderBottom: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}`, fontSize: 12,
      color: dark ? "#e2e8f0" : "#374151",
    },
    badge: (color = "#10b981") => ({
      background: color, color: "#fff",
      borderRadius: 4, padding: "2px 7px", fontSize: 10, fontWeight: 600,
    }),
    scrollable: { flex: 1, overflowY: "auto", padding: "0 14px 14px" },
    infoBox: (color = "#065f46", bg = "#d1fae5") => ({
      background: dark ? color : bg, borderRadius: 6,
      padding: "8px 10px", marginTop: 6, fontSize: 11,
      color: dark ? "#a7f3d0" : color, lineHeight: 1.8,
    }),
    errBox: {
      background: dark ? "#7f1d1d" : "#fee2e2", borderRadius: 6,
      padding: "8px 10px", marginTop: 6, fontSize: 11,
      color: dark ? "#fca5a5" : "#991b1b",
    },
    tag: (color) => ({
      display: "inline-block", background: color + "22", color: color,
      border: `1px solid ${color}44`, borderRadius: 4, padding: "1px 5px",
      fontSize: 10, fontWeight: 600, marginRight: 4, marginTop: 2,
    }),
    scoreBar: (pct, color) => ({
      height: 4, borderRadius: 2, marginTop: 3,
      background: `linear-gradient(to right, ${color} ${pct}%, ${dark ? "#374151" : "#e5e7eb"} ${pct}%)`,
    }),
  };

  async function handleGetRoute() {
    if (!userLocation || !selectedFacility) return;
    setLoading(true); setError(null);
    try {
      const r = await fetchRoadRoute(userLocation.lat, userLocation.lon, selectedFacility.latitude, selectedFacility.longitude);
      onRouteSet(r);
      setTravelInfo(r);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  async function handleCoverage() {
    if (!userLocation) return;
    setLoading(true); setError(null);
    try { setCoverageInfo(await fetchCoverage(userLocation.lat, userLocation.lon)); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  async function handleSmartSearch() {
    if (!userLocation) return;
    setLoading(true); setError(null); setSmartResults(null); setRoutingFacility(null);
    onRouteSet(null);
    try {
      const data = await fetchSmartRecommendations({
        lat: userLocation.lat, lon: userLocation.lon,
        emergencyType, insurance: insurance || null,
        financialLevel: financialLevel === "Any" ? null : financialLevel,
        radiusKm,
      });
      setSmartResults(data);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  async function handleRouteTo(facility) {
    if (!userLocation) return;
    setRoutingFacility(facility.facility_id);
    try {
      const r = await fetchRoadRoute(userLocation.lat, userLocation.lon, facility.latitude, facility.longitude);
      onRouteSet({ ...r, destination: facility });
    } catch (e) { console.error(e); }
  }

  async function handlePopulation() {
    if (!userLocation) return;
    setLoading(true); setError(null);
    try { setPopData(await fetchPopulationServed(userLocation.lat, userLocation.lon, popRadius)); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  async function handleCountyReport() {
    if (!selectedCounty) return;
    setLoading(true); setError(null);
    try { setCountyReport(await fetchCountyReport(selectedCounty)); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  async function handleRankings() {
    setLoading(true); setError(null);
    try { setRankings(await fetchCountyRankings()); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  const selectedEType = (emergencyTypes || []).find((t) => t.id === emergencyType);

  return (
    <div style={s.sidebar}>
      {/* County filter — always visible */}
      <div style={s.sec}>
        <div style={s.label}>Filter by County</div>
        <select style={{ ...s.select, marginBottom: 0 }} value={selectedCounty} onChange={(e) => onCountyChange(e.target.value)}>
          <option value="">All Kenya</option>
          {(counties || []).map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* ── FACILITIES ───────────────────────────────────────────────── */}
      {activeLayer === "facilities" && (
        <>
          {selectedFacility && (
            <div style={s.sec}>
              <div style={s.label}>Selected Facility</div>
              <div style={s.card}>
                <div style={s.name}>{selectedFacility.name}</div>
                <div style={s.meta}>
                  <strong>{selectedFacility.type}</strong><br />
                  {selectedFacility.county} County
                  {selectedFacility.nearest_town && <> · {selectedFacility.nearest_town}</>}<br />
                  {selectedFacility.open_24_hours && "🕐 24hrs  "}
                  {selectedFacility.open_weekends && "📅 Weekends"}<br />
                  {((selectedFacility.beds || 0) + (selectedFacility.cots || 0)) > 0 && (
                    <>🛏 {(selectedFacility.beds || 0) + (selectedFacility.cots || 0)} beds/cots<br /></>
                  )}
                  {selectedFacility.financial_level && (
                    <span style={s.tag(FIN_COLORS[selectedFacility.financial_level] || "#6b7280")}>
                      {selectedFacility.financial_level} cost
                    </span>
                  )}
                  {(selectedFacility.insurance_providers || []).slice(0, 3).map((ins) => (
                    <span key={ins} style={s.tag("#3b82f6")}>{ins}</span>
                  ))}
                </div>
              </div>
              {userLocation && (
                <button style={s.btn()} onClick={handleGetRoute} disabled={loading}>
                  {loading ? "Getting route…" : "🗺 Get Road Directions"}
                </button>
              )}
              {travelInfo && (
                <div style={s.infoBox()}>
                  🚗 Road distance: <strong>{travelInfo.distance_km} km</strong><br />
                  ⏱ Drive time: <strong>{travelInfo.duration_minutes} min</strong><br />
                  📡 {travelInfo.source === "osrm" ? "Live road routing via OSM" : "Estimated (1.35× straight-line)"}
                </div>
              )}
            </div>
          )}
          {!selectedFacility && (
            <div style={{ ...s.sec, color: dark ? "#6b7280" : "#9ca3af", fontSize: 12, textAlign: "center" }}>
              Click a facility on the map to see details
            </div>
          )}
        </>
      )}

      {/* ── EMERGENCY INTELLIGENCE ───────────────────────────────────── */}
      {activeLayer === "emergency" && (
        <div style={{ ...s.sec, flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={s.label}>🚨 Emergency Intelligence</div>

          <div style={s.label}>Emergency Type</div>
          <select style={s.select} value={emergencyType} onChange={(e) => setEmergencyType(e.target.value)}>
            {(emergencyTypes || []).map((t) => (
              <option key={t.id} value={t.id}>{t.icon} {t.label}</option>
            ))}
          </select>

          <div style={s.label}>Insurance Provider</div>
          <select style={s.select} value={insurance} onChange={(e) => setInsurance(e.target.value)}>
            <option value="">Any Insurance</option>
            {(insuranceProviders || []).map((ins) => (
              <option key={ins} value={ins}>{ins}</option>
            ))}
          </select>

          <div style={s.label}>Financial Level</div>
          <select style={s.select} value={financialLevel} onChange={(e) => setFinancialLevel(e.target.value)}>
            {["Any", "Free/Subsidized", "Low", "Medium", "High"].map((l) => (
              <option key={l} value={l}>{l === "Any" ? "Any (all levels)" : l}</option>
            ))}
          </select>

          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
            <div style={{ flex: 1 }}>
              <div style={s.label}>Search Radius</div>
              <input
                type="range" min={5} max={200} step={5} value={radiusKm}
                onChange={(e) => setRadiusKm(Number(e.target.value))}
                style={{ width: "100%" }}
              />
            </div>
            <span style={{ fontSize: 12, color: dark ? "#e2e8f0" : "#374151", minWidth: 40 }}>{radiusKm} km</span>
          </div>

          <button style={s.btn("#ef4444")} onClick={handleSmartSearch} disabled={loading || !userLocation}>
            {loading ? "Searching…" : !userLocation ? "Enable location first" : `🔍 Find Best ${selectedEType?.icon || ""} Hospital`}
          </button>

          {error && <div style={s.errBox}>⚠️ {error}</div>}

          {smartResults && (
            <div style={s.scrollable}>
              <div style={{ ...s.meta, marginTop: 8, marginBottom: 4 }}>
                <strong style={{ color: dark ? "#f9fafb" : "#111827" }}>{smartResults.total_found}</strong> hospitals found
                within {smartResults.query.radius_km} km
                {smartResults.query.insurance_filter && <> · {smartResults.query.insurance_filter}</>}
              </div>
              {smartResults.results.map((f, i) => (
                <div
                  key={f.facility_id}
                  style={s.resultCard(routingFacility === f.facility_id)}
                  onClick={() => handleRouteTo(f)}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div style={{ ...s.name, flex: 1, marginRight: 6 }}>
                      {i === 0 && <span style={{ color: "#f59e0b" }}>⭐ </span>}
                      {f.name}
                    </div>
                    <span style={s.badge(i === 0 ? "#ef4444" : "#6b7280")}>#{i + 1}</span>
                  </div>
                  <div style={{ ...s.scoreBar(f.score, "#10b981") }} title={`Score: ${f.score}`} />
                  <div style={{ ...s.meta, marginTop: 4 }}>
                    <strong>{f.type}</strong> · {f.county}<br />
                    📍 {f.distance_km} km · ⏱ {f.estimated_minutes} min drive<br />
                    {((f.beds || 0) + (f.cots || 0)) > 0 && <>🛏 {(f.beds || 0) + (f.cots || 0)} beds · </>}
                    {f.open_24_hours && "🕐 24h "}
                  </div>
                  <div style={{ marginTop: 4 }}>
                    <span style={s.tag(FIN_COLORS[f.financial_level] || "#6b7280")}>{f.financial_level}</span>
                    {(f.insurance_providers || []).slice(0, 2).map((ins) => (
                      <span key={ins} style={s.tag("#3b82f6")}>{ins}</span>
                    ))}
                  </div>
                  <div style={{ ...s.meta, color: dark ? "#6b7280" : "#9ca3af", marginTop: 3, fontStyle: "italic" }}>
                    {f.match_reason}
                  </div>
                  <div style={{ fontSize: 10, color: "#10b981", marginTop: 3 }}>
                    {routingFacility === f.facility_id ? "✅ Routing on map…" : "Click to get road directions →"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── COVERAGE ─────────────────────────────────────────────────── */}
      {activeLayer === "coverage" && (
        <div style={{ ...s.sec, flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={s.label}>🎯 Coverage Analysis</div>
          <button style={s.btn()} onClick={handleCoverage} disabled={loading || !userLocation}>
            {loading ? "Analysing…" : !userLocation ? "Enable location" : "Analyse from My Location"}
          </button>
          {error && <div style={s.errBox}>⚠️ {error}</div>}
          {coverageInfo && (
            <div style={{ ...s.scrollable, marginTop: 8 }}>
              <div style={s.meta}>{coverageInfo.access_message}</div>
              <div style={{ ...s.row, marginTop: 8 }}>
                <span>Total facilities</span>
                <strong>{coverageInfo.total_facilities}</strong>
              </div>
              <div style={s.row}>
                <span>Beds / cots</span>
                <strong>{coverageInfo.total_beds_and_cots}</strong>
              </div>
              <div style={s.row}>
                <span>Open 24h</span>
                <strong>{coverageInfo.open_24h_facilities}</strong>
              </div>
              {coverageInfo.nearest_facility && (
                <div style={s.card}>
                  <div style={s.label}>Nearest</div>
                  <div style={s.name}>{coverageInfo.nearest_facility.name}</div>
                  <div style={s.meta}>{coverageInfo.nearest_facility.type} · {coverageInfo.nearest_facility.distance_km} km</div>
                </div>
              )}
              {/* Population sub-section */}
              <div style={{ ...s.label, marginTop: 12 }}>Population Monitoring</div>
              <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                <input
                  type="range" min={2} max={50} step={2} value={popRadius}
                  onChange={(e) => setPopRadius(Number(e.target.value))}
                  style={{ flex: 1 }}
                />
                <span style={{ fontSize: 12, color: dark ? "#e2e8f0" : "#374151", minWidth: 40 }}>{popRadius} km</span>
              </div>
              <button style={s.btn("#8b5cf6")} onClick={handlePopulation} disabled={loading}>
                {loading ? "Calculating…" : "👥 Monitor Population Served"}
              </button>
              {popData && (
                <div style={{ marginTop: 8 }}>
                  <div style={s.row}><span>Est. catchment pop.</span><strong>{(popData.catchment.estimated_population || 0).toLocaleString()}</strong></div>
                  <div style={s.row}><span>Operational facilities</span><strong>{popData.catchment.operational_facilities}</strong></div>
                  <div style={s.row}><span>People per facility</span><strong>{(popData.catchment.people_per_facility || 0).toLocaleString()}</strong></div>
                  <div style={s.row}><span>Beds per 1,000 people</span><strong>{popData.catchment.beds_per_1000_people}</strong></div>
                  <div style={s.row}><span>WHO benchmark</span><strong>{popData.catchment.who_beds_benchmark_per_1000} / 1000</strong></div>
                  <div style={{ ...s.infoBox(
                    popData.catchment.benchmark_status.includes("Above") ? "#065f46" : "#7f1d1d",
                    popData.catchment.benchmark_status.includes("Above") ? "#d1fae5" : "#fee2e2"
                  ) }}>
                    {popData.catchment.benchmark_status.includes("Above") ? "✅" : "⚠️"} {popData.catchment.benchmark_status}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── ACCESSIBILITY ─────────────────────────────────────────────── */}
      {activeLayer === "accessibility" && accessibilityScores.length > 0 && (
        <div style={{ ...s.sec, flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={s.label}>County Accessibility Scores</div>
          <div style={s.scrollable}>
            {accessibilityScores.map((item) => (
              <div key={item.county} style={s.row}>
                <span>{item.county}</span>
                <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <span style={{ color: "#9ca3af", fontSize: 11 }}>{item.score}</span>
                  <span style={s.badge(BAND_COLORS[item.band] || "#6b7280")}>{item.band}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── REPORTS ───────────────────────────────────────────────────── */}
      {activeLayer === "reports" && (
        <div style={{ ...s.sec, flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={s.label}>Reports & Intelligence</div>
          {selectedCounty && (
            <button style={s.btn()} onClick={handleCountyReport} disabled={loading}>
              {loading ? "Loading…" : `📋 ${selectedCounty} County Report`}
            </button>
          )}
          <button style={s.btn2} onClick={handleRankings} disabled={loading}>
            🏆 County Rankings
          </button>
          {error && <div style={s.errBox}>⚠️ {error}</div>}
          <div style={s.scrollable}>
            {countyReport && (
              <div style={{ marginTop: 8 }}>
                <div style={s.name}>{countyReport.county} County</div>
                <div style={s.meta}>
                  {countyReport.operational} operational of {countyReport.total_facilities} total<br />
                  🛏 {countyReport.total_beds_and_cots} beds/cots<br />
                  🕐 {countyReport.open_24h_count} open 24h<br />
                  📅 {countyReport.open_weekends_count} open weekends
                </div>
                {countyReport.largest_facility && (
                  <div style={s.card}>
                    <div style={s.label}>Largest Facility</div>
                    <div style={s.name}>{countyReport.largest_facility.name}</div>
                    <div style={s.meta}>{countyReport.largest_facility.type} · {countyReport.largest_facility.beds} beds</div>
                  </div>
                )}
                {(countyReport.open_24h_facilities || []).slice(0, 5).map((f, i) => (
                  <div key={i} style={{ ...s.meta, padding: "3px 0", borderBottom: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}` }}>
                    🕐 {f.name} <span style={{ color: "#6b7280" }}>· {f.type}</span>
                  </div>
                ))}
              </div>
            )}
            {rankings && (
              <div style={{ marginTop: 8 }}>
                <div style={{ ...s.meta, marginBottom: 6 }}>Kenya County Rankings</div>
                {(rankings.rankings || []).map((r) => (
                  <div key={r.county} style={s.row}>
                    <span><span style={{ color: "#6b7280", marginRight: 6 }}>#{r.rank}</span>{r.county}</span>
                    <span style={s.badge(BAND_COLORS[r.band] || "#6b7280")}>{r.score}</span>
                  </div>
                ))}
              </div>
            )}
            {nationalSummary && !countyReport && !rankings && (
              <div style={{ marginTop: 8 }}>
                <div style={s.card}>
                  <strong style={{ color: dark ? "#f9fafb" : "#111827" }}>Kenya National Summary</strong>
                  <div style={s.meta}>
                    Total facilities: {nationalSummary.total_facilities?.toLocaleString()}<br />
                    Operational: {nationalSummary.operational?.toLocaleString()}<br />
                    Total beds: {nationalSummary.total_beds_and_cots?.toLocaleString()}<br />
                    Open 24h: {nationalSummary.open_24h_facilities?.toLocaleString()}<br />
                    Counties covered: {nationalSummary.counties_covered}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
