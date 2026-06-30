const BASE = "";

// ── Facilities ────────────────────────────────────────────────────────────────

export async function fetchFacilities({ county, type } = {}) {
  const p = new URLSearchParams();
  if (county) p.set("county", county);
  if (type) p.set("type", type);
  p.set("limit", "500");
  const res = await fetch(`${BASE}/recommendations/list?${p}`);
  if (!res.ok) throw new Error("Failed to fetch facilities");
  return res.json();
}

export async function fetchCounties() {
  const res = await fetch(`${BASE}/recommendations/counties`);
  if (!res.ok) throw new Error("Failed to fetch counties");
  const data = await res.json();
  return data.counties;
}

export async function fetchFacilityTypes() {
  const res = await fetch(`${BASE}/recommendations/types`);
  if (!res.ok) throw new Error("Failed to fetch types");
  const data = await res.json();
  return data.types;
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export async function fetchAccessibilityScores(county = null) {
  const res = await fetch(`${BASE}/analytics/counties`);
  if (!res.ok) throw new Error("Failed to fetch accessibility");
  const data = await res.json();
  // Map county rankings into the shape the UI expects
  return {
    counties: (data.counties || []).map((c) => ({
      county: c.county,
      score: c.accessibility_score,
      band: c.accessibility_score >= 70 ? "Excellent"
          : c.accessibility_score >= 45 ? "Good"
          : c.accessibility_score >= 20 ? "Moderate"
          : "Poor",
    })),
  };
}

export async function fetchCoverage(lat, lon, county = null) {
  const p = new URLSearchParams({ lat, lon });
  if (county) p.set("county", county);
  const res = await fetch(`${BASE}/gis/coverage?${p}`);
  if (!res.ok) throw new Error("Failed to fetch coverage");
  const data = await res.json();
  // Adapt to shape Sidebar expects
  return {
    ...data,
    access_message: `${data.total_facilities} facilities within ${data.radius_km}km`,
    access_status: data.total_facilities >= 5 ? "adequate" : "inadequate",
    coverage_bands: {
      within_10km: { count: data.total_facilities },
    },
  };
}

export async function fetchCountyRankings() {
  const res = await fetch(`${BASE}/analytics/counties`);
  if (!res.ok) throw new Error("Failed to fetch rankings");
  const data = await res.json();
  return {
    rankings: (data.counties || []).map((c) => ({
      ...c,
      score: c.accessibility_score,
      band: c.accessibility_score >= 70 ? "Excellent"
          : c.accessibility_score >= 45 ? "Good"
          : c.accessibility_score >= 20 ? "Moderate"
          : "Poor",
    })),
  };
}

export async function fetchNationalSummary() {
  const res = await fetch(`${BASE}/analytics/summary`);
  if (!res.ok) throw new Error("Failed to fetch national summary");
  return res.json();
}

export async function fetchCountyReport(county) {
  const res = await fetch(`${BASE}/analytics/county/${encodeURIComponent(county)}`);
  if (!res.ok) throw new Error("Failed to fetch county report");
  return res.json();
}

// ── Routing ───────────────────────────────────────────────────────────────────

export async function fetchRoute(fromLat, fromLon, toLat, toLon) {
  const p = new URLSearchParams({
    from_lat: fromLat, from_lon: fromLon,
    to_lat: toLat, to_lon: toLon,
  });
  const res = await fetch(`${BASE}/gis/travel-time?${p}`);
  if (!res.ok) throw new Error("Failed to fetch route");
  const data = await res.json();
  return {
    ...data,
    distance_km: data.estimated_road_km,
    duration_minutes: data.estimated_minutes,
    method: "estimated",
  };
}

export async function fetchEmergencyZones(lat, lon) {
  const p = new URLSearchParams({ lat, lon, radius_km: 50 });
  const res = await fetch(`${BASE}/gis/catchment?${p}`);
  if (!res.ok) throw new Error("Failed to fetch emergency zones");
  const data = await res.json();
  // Group catchment facilities into time-based zones
  const zones = { critical: [], urgent: [], standard: [], remote: [] };
  for (const f of (data.catchment || [])) {
    const min = f.estimated_minutes || 999;
    const entry = { ...f, est_response_min: min };
    if (min < 15) zones.critical.push(entry);
    else if (min < 30) zones.urgent.push(entry);
    else if (min < 60) zones.standard.push(entry);
    else zones.remote.push(entry);
  }
  return { zones };
}

// ── Misc (unused but kept for compatibility) ───────────────────────────────────

export async function fetchFacilityStats(county = null) {
  const p = new URLSearchParams();
  if (county) p.set("county", county);
  const res = await fetch(`${BASE}/analytics/summary`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function fetchEmergencyReadiness() {
  const res = await fetch(`${BASE}/analytics/summary`);
  if (!res.ok) throw new Error("Failed to fetch emergency readiness");
  return res.json();
}
