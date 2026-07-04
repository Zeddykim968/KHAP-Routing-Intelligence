import React, { useState } from "react";
import {
  fetchRoute, fetchCoverage, fetchEmergencyZones,
  fetchCountyReport, fetchCountyRankings,
  fetchSmartRecommendations, fetchRoadRoute,
  fetchPopulationServed, fetchNearestFacility,
} from "../api/index.js";

const BAND_COLORS = {
  Excellent: "#10b981", Good: "#3b82f6", Moderate: "#f59e0b",
  Poor: "#f97316", Critical: "#ef4444",
};
const FIN_COLORS = {
  "Free/Subsidized": "#10b981", Low: "#3b82f6", Medium: "#f59e0b", High: "#ef4444",
};
const STEP_ICONS = {
  depart: "▶", arrive: "🏥", turn: "⤴", continue: "↑", fork: "⑂", merge: "⊃",
  roundabout: "⟳", rotary: "⟳",
};

export default function Sidebar({
  counties, selectedCounty, onCountyChange, selectedFacility,
  userLocation, accessibilityScores, nationalSummary,
  activeLayer, onRouteSet, theme, emergencyTypes, insuranceProviders,
  onSmartResults,
}) {
  const [travelInfo, setTravelInfo]     = useState(null);
  const [coverageInfo, setCoverageInfo] = useState(null);
  const [countyReport, setCountyReport] = useState(null);
  const [rankings, setRankings]         = useState(null);
  const [loading, setLoading]           = useState(false);
  const [error, setError]               = useState(null);
  const [showSteps, setShowSteps]       = useState(false);

  const [emergencyType, setEmergencyType]   = useState("general");
  const [insurance, setInsurance]           = useState("");
  const [financialLevel, setFinancialLevel] = useState("Any");
  const [radiusKm, setRadiusKm]             = useState(30);
  const [smartResults, setSmartResults]     = useState(null);
  const [routingFacility, setRoutingFacility] = useState(null);

  const [popData, setPopData]   = useState(null);
  const [popRadius, setPopRadius] = useState(10);

  const dark = theme === "dark";

  const s = {
    sidebar: {
      width: 300, flexShrink: 0, display: "flex", flexDirection: "column",
      overflow: "hidden",
      background: dark ? "#111827" : "#ffffff",
      borderRight: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}`,
    },
    sec:   { padding: "12px 14px", borderBottom: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}` },
    label: { fontSize: 10, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 5, fontWeight: 700 },
    select: {
      width: "100%", borderRadius: 6, padding: "6px 10px", fontSize: 12,
      background: dark ? "#1f2937" : "#f3f4f6",
      border: `1px solid ${dark ? "#374151" : "#d1d5db"}`,
      color: dark ? "#e2e8f0" : "#111827", marginBottom: 6, outline: "none",
    },
    btn: (color = "#10b981") => ({
      width: "100%", padding: "8px", background: color, color: "#fff",
      border: "none", borderRadius: 6, cursor: "pointer", fontSize: 12,
      fontWeight: 600, marginTop: 4, opacity: 1,
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
      border: `1px solid ${dark ? "#374151" : "#e5e7eb"}`,
    },
    resultCard: (highlighted) => ({
      background: highlighted ? (dark ? "#064e3b" : "#ecfdf5") : (dark ? "#1f2937" : "#f9fafb"),
      borderRadius: 8, padding: "10px 12px", marginTop: 6,
      border: highlighted ? "1px solid #10b981" : `1px solid ${dark ? "#374151" : "#e5e7eb"}`,
      cursor: "pointer", transition: "all 0.15s",
    }),
    name:   { fontWeight: 700, fontSize: 13, color: dark ? "#f9fafb" : "#111827", marginBottom: 2 },
    meta:   { fontSize: 11, color: dark ? "#9ca3af" : "#6b7280", lineHeight: 1.7 },
    row: {
      display: "flex", justifyContent: "space-between", alignItems: "center",
      padding: "4px 0", borderBottom: `1px solid ${dark ? "#1f2937" : "#f3f4f6"}`,
      fontSize: 12, color: dark ? "#e2e8f0" : "#374151",
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
      display: "inline-block", background: color + "22", color,
      border: `1px solid ${color}44`, borderRadius: 4, padding: "1px 5px",
      fontSize: 10, fontWeight: 600, marginRight: 3, marginTop: 2,
    }),
    scoreBar: (pct, color) => ({
      height: 3, borderRadius: 2, marginTop: 4,
      background: `linear-gradient(to right, ${color} ${pct}%, ${dark ? "#374151" : "#e5e7eb"} ${pct}%)`,
    }),
    stepRow: {
      display: "flex", alignItems: "flex-start", gap: 8, padding: "5px 0",
      borderBottom: `1px solid ${dark ? "#1f2937" : "#f3f4f6"}`, fontSize: 11,
      color: dark ? "#d1d5db" : "#374151",
    },
    stepIcon: (type) => ({
      width: 22, height: 22, borderRadius: "50%", flexShrink: 0,
      background: type === "arrive" ? "#10b981" : type === "depart" ? "#3b82f6" : dark ? "#374151" : "#e5e7eb",
      color: type === "arrive" || type === "depart" ? "#fff" : dark ? "#9ca3af" : "#6b7280",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontSize: 11, fontWeight: 700,
    }),
  };

  async function handleGetRoute() {
    if (!userLocation || !selectedFacility) return;
    setLoading(true); setError(null); setShowSteps(false);
    try {
      const r = await fetchRoadRoute(
        userLocation.lat, userLocation.lon,
        selectedFacility.latitude, selectedFacility.longitude
      );
      onRouteSet({ ...r, destination: selectedFacility });
      setTravelInfo(r);
      setShowSteps(true);
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
    if (onSmartResults) onSmartResults([]);
    try {
      const data = await fetchSmartRecommendations({
        lat: userLocation.lat, lon: userLocation.lon,
        emergencyType, insurance: insurance || null,
        financialLevel: financialLevel === "Any" ? null : financialLevel,
        radiusKm,
      });
      setSmartResults(data);
      if (onSmartResults) onSmartResults(data.results || []);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  async function handleRouteTo(facility) {
    if (!userLocation) return;
    setRoutingFacility(facility.facility_id);
    setTravelInfo(null);
    try {
      const r = await fetchRoadRoute(
        userLocation.lat, userLocation.lon,
        facility.latitude, facility.longitude
      );
      onRouteSet({ ...r, destination: facility });
      setTravelInfo(r);
      setShowSteps(true);
    } catch (e) { console.error(e); } finally { setRoutingFacility(null); }
  }

  async function handleNearestHospital() {
    if (!userLocation) return;
    setLoading(true); setError(null);
    try {
      const data = await fetchNearestFacility(userLocation.lat, userLocation.lon, emergencyType);
      const top = data.results?.[0];
      if (top) {
        setSmartResults({ results: data.results, total_found: data.total, query: { radius_km: 200 } });
        if (onSmartResults) onSmartResults(data.results);
        await handleRouteTo(top);
      }
    } catch (e) { setError(e.message); } finally { setLoading(false); }
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
      {/* County filter */}
      <div style={s.sec}>
        <div style={s.label}>Filter by County</div>
        <select style={{ ...s.select, marginBottom: 0 }} value={selectedCounty} onChange={(e) => onCountyChange(e.target.value)}>
          <option value="">All Kenya (47 counties)</option>
          {(counties || []).map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* ── FACILITIES ─────────────────────────────────────────── */}
      {activeLayer === "facilities" && (
        <>
          {selectedFacility ? (
            <div style={s.sec}>
              <div style={s.label}>Selected Facility</div>
              <div style={s.card}>
                <div style={s.name}>{selectedFacility.name}</div>
                <div style={s.meta}>
                  <strong>{selectedFacility.type}</strong><br />
                  {selectedFacility.county} County
                  {selectedFacility.nearest_town && <> · {selectedFacility.nearest_town}</>}<br />
                  {selectedFacility.open_24_hours && "🕐 Open 24hrs  "}
                  {selectedFacility.open_weekends && "📅 Weekends"}<br />
                  {((selectedFacility.beds || 0) + (selectedFacility.cots || 0)) > 0 && (
                    <>🛏 {(selectedFacility.beds || 0) + (selectedFacility.cots || 0)} beds/cots<br /></>
                  )}
                </div>
                <div style={{ marginTop: 6 }}>
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

              {/* Route summary */}
              {travelInfo && (
                <div style={{ marginTop: 8 }}>
                  <div style={s.infoBox()}>
                    🚗 <strong>{travelInfo.distance_km} km</strong> road distance<br />
                    ⏱ <strong>{travelInfo.duration_minutes} min</strong> drive time<br />
                    📡 {travelInfo.source === "osrm" ? "Live routing via OpenStreetMap" : "Straight-line estimate (×1.35)"}
                  </div>

                  {/* Turn-by-turn steps */}
                  {travelInfo.steps?.length > 0 && (
                    <>
                      <button
                        style={{ ...s.btn2, marginTop: 6, textAlign: "left" }}
                        onClick={() => setShowSteps((v) => !v)}
                      >
                        {showSteps ? "▲ Hide" : "▼ Show"} turn-by-turn ({travelInfo.steps.length} steps)
                      </button>
                      {showSteps && (
                        <div style={{ marginTop: 6, maxHeight: 220, overflowY: "auto" }}>
                          {travelInfo.steps.map((step, i) => (
                            <div key={i} style={s.stepRow}>
                              <div style={s.stepIcon(step.type)}>
                                {step.icon || STEP_ICONS[step.type] || "↑"}
                              </div>
                              <div style={{ flex: 1 }}>
                                <div>{step.instruction}</div>
                                {step.distance_km > 0 && (
                                  <div style={{ color: "#6b7280", fontSize: 10 }}>
                                    {step.distance_km} km · {step.duration_min} min
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div style={{ ...s.sec, color: dark ? "#6b7280" : "#9ca3af", fontSize: 12, textAlign: "center", lineHeight: 1.8 }}>
              <div style={{ fontSize: 24, marginBottom: 8 }}>🗺</div>
              Click any facility on the map<br />
              to view details & get directions
            </div>
          )}
        </>
      )}

      {/* ── EMERGENCY INTELLIGENCE ──────────────────────────────── */}
      {activeLayer === "emergency" && (
        <div style={{ ...s.sec, flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", borderBottom: "none" }}>
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
              <div style={s.label}>Search Radius — {radiusKm} km</div>
              <input
                type="range" min={5} max={200} step={5} value={radiusKm}
                onChange={(e) => setRadiusKm(Number(e.target.value))}
                style={{ width: "100%" }}
              />
            </div>
          </div>

          <div style={{ display: "flex", gap: 6 }}>
            <button style={{ ...s.btn("#ef4444"), flex: 2 }} onClick={handleSmartSearch} disabled={loading || !userLocation}>
              {loading ? "Searching…" : !userLocation ? "Enable location" : `🔍 Find ${selectedEType?.icon || "🏥"}`}
            </button>
            <button style={{ ...s.btn("#1d4ed8"), flex: 1, fontSize: 11 }} onClick={handleNearestHospital} disabled={loading || !userLocation} title="Route to nearest now">
              🚑 Nearest
            </button>
          </div>

          {error && <div style={s.errBox}>⚠️ {error}</div>}

          {/* Route summary while in emergency mode */}
          {travelInfo && (
            <div style={{ ...s.infoBox(), marginTop: 8 }}>
              🚗 <strong>{travelInfo.distance_km} km</strong> · ⏱ <strong>{travelInfo.duration_minutes} min</strong>
              {travelInfo.steps?.length > 0 && (
                <>
                  <button
                    style={{ ...s.btn2, marginTop: 4, padding: "3px 8px", fontSize: 10, width: "auto" }}
                    onClick={() => setShowSteps((v) => !v)}
                  >
                    {showSteps ? "▲ Hide" : "▼ Show"} directions ({travelInfo.steps.length} steps)
                  </button>
                  {showSteps && (
                    <div style={{ marginTop: 4, maxHeight: 160, overflowY: "auto" }}>
                      {travelInfo.steps.map((step, i) => (
                        <div key={i} style={{ ...s.stepRow, padding: "3px 0" }}>
                          <div style={{ ...s.stepIcon(step.type), width: 18, height: 18, fontSize: 9 }}>
                            {step.icon || "↑"}
                          </div>
                          <div style={{ fontSize: 10 }}>{step.instruction}{step.distance_km > 0 ? ` (${step.distance_km} km)` : ""}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {smartResults && (
            <div style={s.scrollable}>
              <div style={{ ...s.meta, marginTop: 8, marginBottom: 4 }}>
                <strong style={{ color: dark ? "#f9fafb" : "#111827" }}>{smartResults.total_found}</strong> facilities found
                {smartResults.query?.radius_km && <> within {smartResults.query.radius_km} km</>}
                {smartResults.query?.insurance_filter && <> · {smartResults.query.insurance_filter}</>}
              </div>
              {(smartResults.results || []).map((f, i) => (
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
                    <span style={s.badge(i === 0 ? "#ef4444" : i < 3 ? "#3b82f6" : "#6b7280")}>#{i + 1}</span>
                  </div>
                  <div style={s.scoreBar(f.score, "#10b981")} title={`Score: ${f.score}`} />
                  <div style={{ ...s.meta, marginTop: 4 }}>
                    <strong>{f.type}</strong> · {f.county}<br />
                    📍 {f.distance_km} km · ⏱ {f.estimated_minutes} min<br />
                    {((f.beds || 0) + (f.cots || 0)) > 0 && <>🛏 {(f.beds || 0) + (f.cots || 0)} beds · </>}
                    {f.open_24_hours && "🕐 24h "}
                  </div>
                  <div style={{ marginTop: 4 }}>
                    <span style={s.tag(FIN_COLORS[f.financial_level] || "#6b7280")}>{f.financial_level}</span>
                    {(f.insurance_providers || []).slice(0, 2).map((ins) => (
                      <span key={ins} style={s.tag("#3b82f6")}>{ins}</span>
                    ))}
                  </div>
                  <div style={{ ...s.meta, color: dark ? "#6b7280" : "#9ca3af", marginTop: 3, fontStyle: "italic", fontSize: 10 }}>
                    {f.match_reason}
                  </div>
                  <div style={{ fontSize: 10, color: "#10b981", marginTop: 3, fontWeight: 600 }}>
                    {routingFacility === f.facility_id ? "🔄 Routing…" : "Click → get directions"}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── COVERAGE ──────────────────────────────────────────────── */}
      {activeLayer === "coverage" && (
        <div style={{ ...s.sec, flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", borderBottom: "none" }}>
          <div style={s.label}>🎯 Coverage Analysis</div>
          <button style={s.btn()} onClick={handleCoverage} disabled={loading || !userLocation}>
            {loading ? "Analysing…" : !userLocation ? "Enable location" : "Analyse from My Location"}
          </button>
          {error && <div style={s.errBox}>⚠️ {error}</div>}
          {coverageInfo && (
            <div style={{ ...s.scrollable, marginTop: 8 }}>
              <div style={s.meta}>{coverageInfo.access_message}</div>
              {[
                ["Total facilities", coverageInfo.total_facilities],
                ["Beds / cots", coverageInfo.total_beds_and_cots],
                ["Open 24h", coverageInfo.open_24h_facilities],
              ].map(([l, v]) => (
                <div key={l} style={{ ...s.row, marginTop: l === "Total facilities" ? 8 : 0 }}>
                  <span>{l}</span><strong>{v}</strong>
                </div>
              ))}
              {coverageInfo.nearest_facility && (
                <div style={s.card}>
                  <div style={s.label}>Nearest Facility</div>
                  <div style={s.name}>{coverageInfo.nearest_facility.name}</div>
                  <div style={s.meta}>{coverageInfo.nearest_facility.type} · 📍 {coverageInfo.nearest_facility.distance_km} km</div>
                </div>
              )}
              {coverageInfo.facilities?.slice(0, 5).map((f, i) => (
                <div key={i} style={{ ...s.meta, padding: "4px 0", borderBottom: `1px solid ${dark ? "#1f2937" : "#f3f4f6"}` }}>
                  {i + 1}. {f.name} <span style={{ color: "#6b7280" }}>· {f.type} · {f.distance_km} km</span>
                </div>
              ))}

              {/* Population monitoring */}
              <div style={{ ...s.label, marginTop: 14 }}>Population Monitoring</div>
              <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                <input
                  type="range" min={2} max={50} step={2} value={popRadius}
                  onChange={(e) => setPopRadius(Number(e.target.value))}
                  style={{ flex: 1 }}
                />
                <span style={{ fontSize: 12, color: dark ? "#e2e8f0" : "#374151", minWidth: 40 }}>{popRadius} km</span>
              </div>
              <button style={s.btn("#8b5cf6")} onClick={handlePopulation} disabled={loading}>
                {loading ? "Calculating…" : "👥 Population Served"}
              </button>
              {popData && (
                <div style={{ marginTop: 8 }}>
                  {[
                    ["Est. catchment pop.", (popData.catchment.estimated_population || 0).toLocaleString()],
                    ["Operational facilities", popData.catchment.operational_facilities],
                    ["People per facility", (popData.catchment.people_per_facility || 0).toLocaleString()],
                    ["Beds per 1,000 people", popData.catchment.beds_per_1000_people],
                    ["WHO benchmark", `${popData.catchment.who_beds_benchmark_per_1000} / 1000`],
                  ].map(([l, v]) => (
                    <div key={l} style={s.row}><span>{l}</span><strong>{v}</strong></div>
                  ))}
                  <div style={s.infoBox(
                    popData.catchment.benchmark_status.includes("Above") ? "#065f46" : "#7f1d1d",
                    popData.catchment.benchmark_status.includes("Above") ? "#d1fae5" : "#fee2e2"
                  )}>
                    {popData.catchment.benchmark_status.includes("Above") ? "✅" : "⚠️"} {popData.catchment.benchmark_status}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── ACCESSIBILITY ──────────────────────────────────────────── */}
      {activeLayer === "accessibility" && (
        <div style={{ ...s.sec, flex: 1, overflow: "hidden", display: "flex", flexDirection: "column", borderBottom: "none" }}>
          <div style={s.label}>County Accessibility Rankings</div>
          {accessibilityScores.length === 0 && (
            <div style={{ ...s.meta, textAlign: "center", marginTop: 20 }}>Loading scores…</div>
          )}
          <div style={s.scrollable}>
            {accessibilityScores.map((item, i) => (
              <div key={item.county} style={{ ...s.row, alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, flex: 1, minWidth: 0 }}>
                  <span style={{ color: "#6b7280", fontSize: 10, minWidth: 20 }}>#{i + 1}</span>
                  <span style={{ fontSize: 12, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.county}</span>
                </div>
                <div style={{ display: "flex", gap: 6, alignItems: "center", flexShrink: 0 }}>
                  <span style={{ color: "#9ca3af", fontSize: 10 }}>{item.score}</span>
                  <span style={s.badge(BAND_COLORS[item.band] || "#6b7280")}>{item.band}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── REPORTS ──────────────────────────────────────────────── */}
      {activeLayer === "reports" && (
        <div style={{ ...s.sec, flex: 1, overflow: "hidden", display: "flex", flexDirection: "column", borderBottom: "none" }}>
          <div style={s.label}>Reports & Intelligence</div>
          {selectedCounty && (
            <button style={s.btn()} onClick={handleCountyReport} disabled={loading}>
              {loading ? "Loading…" : `📋 ${selectedCounty} County Report`}
            </button>
          )}
          <button style={s.btn2} onClick={handleRankings} disabled={loading}>
            🏆 All County Rankings
          </button>
          {error && <div style={s.errBox}>⚠️ {error}</div>}
          <div style={s.scrollable}>
            {countyReport && (
              <div style={{ marginTop: 8 }}>
                <div style={s.name}>{countyReport.county} County</div>
                <div style={s.meta}>
                  {countyReport.operational} operational of {countyReport.total_facilities} total<br />
                  🛏 {countyReport.total_beds_and_cots?.toLocaleString()} beds/cots<br />
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
                {Object.entries(countyReport.facility_type_breakdown || {}).slice(0, 6).map(([type, count]) => (
                  <div key={type} style={s.row}>
                    <span style={{ fontSize: 11 }}>{type}</span>
                    <strong>{count}</strong>
                  </div>
                ))}
                <div style={{ ...s.label, marginTop: 10 }}>Open 24h Facilities</div>
                {(countyReport.open_24h_facilities || []).slice(0, 6).map((f, i) => (
                  <div key={i} style={{ ...s.meta, padding: "3px 0", borderBottom: `1px solid ${dark ? "#1f2937" : "#f3f4f6"}` }}>
                    🕐 {f.name} <span style={{ color: "#6b7280" }}>· {f.type}</span>
                  </div>
                ))}
              </div>
            )}
            {rankings && (
              <div style={{ marginTop: 8 }}>
                <div style={{ ...s.meta, marginBottom: 6, fontWeight: 600 }}>Kenya County Rankings</div>
                {(rankings.rankings || []).map((r) => (
                  <div key={r.county} style={s.row}>
                    <span><span style={{ color: "#6b7280", marginRight: 6, fontSize: 10 }}>#{r.rank}</span>{r.county}</span>
                    <span style={s.badge(BAND_COLORS[r.band] || "#6b7280")}>{r.score}</span>
                  </div>
                ))}
              </div>
            )}
            {nationalSummary && !countyReport && !rankings && (
              <div style={{ marginTop: 8 }}>
                <div style={s.card}>
                  <strong style={{ color: dark ? "#f9fafb" : "#111827" }}>Kenya National Summary</strong>
                  <div style={{ ...s.meta, marginTop: 6 }}>
                    {[
                      ["Total facilities", nationalSummary.total_facilities?.toLocaleString()],
                      ["Operational", nationalSummary.operational?.toLocaleString()],
                      ["Total beds", nationalSummary.total_beds_and_cots?.toLocaleString()],
                      ["Open 24h", nationalSummary.open_24h_facilities?.toLocaleString()],
                      ["Counties covered", nationalSummary.counties_covered],
                      ["Operational rate", `${nationalSummary.operational_rate_pct}%`],
                    ].map(([l, v]) => (
                      <div key={l} style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
                        <span>{l}</span><strong>{v}</strong>
                      </div>
                    ))}
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
