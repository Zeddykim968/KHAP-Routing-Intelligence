const BASE = "";

// ── Facilities ────────────────────────────────────────────────────────────────

export async function fetchFacilities({ county, type } = {}) {
  const p = new URLSearchParams();
  if (county) p.set("county", county);
  if (type) p.set("type", type);
  p.set("limit", "2000");
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

export async function suggestFacilities(q, limit = 8) {
  if (!q || q.trim().length < 1) return { suggestions: [] };
  const p = new URLSearchParams({ q: q.trim(), limit });
  const res = await fetch(`${BASE}/recommendations/suggest?${p}`);
  if (!res.ok) return { suggestions: [] };
  return res.json();
}

// Real geocoding — resolves free-text places (roads, landmarks, estates,
// bus stops) that aren't in the facilities dataset, via Nominatim/OSM.
export async function geocodeLocation(q) {
  if (!q || q.trim().length < 2) return null;
  const p = new URLSearchParams({ q: q.trim() });
  const res = await fetch(`${BASE}/recommendations/geocode?${p}`);
  if (!res.ok) return null;
  const data = await res.json();
  return data.result || null;
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export async function fetchAccessibilityScores() {
  const res = await fetch(`${BASE}/analytics/counties`);
  if (!res.ok) throw new Error("Failed to fetch accessibility");
  const data = await res.json();
  return {
    counties: (data.counties || []).map((c) => ({
      county: c.county,
      score: c.accessibility_score,
      facilities: c.facilities,
      beds: c.beds,
      rank: c.rank,
      band:
        c.accessibility_score >= 70 ? "Excellent"
        : c.accessibility_score >= 45 ? "Good"
        : c.accessibility_score >= 20 ? "Moderate"
        : "Poor",
    })),
  };
}

export async function fetchCoverage(lat, lon, radius = 10) {
  const p = new URLSearchParams({ lat, lon, radius_km: radius });
  const res = await fetch(`${BASE}/gis/coverage?${p}`);
  if (!res.ok) throw new Error("Failed to fetch coverage");
  const data = await res.json();
  return {
    ...data,
    access_message: `${data.total_facilities} facilities within ${data.radius_km} km`,
    access_status: data.total_facilities >= 5 ? "adequate" : "inadequate",
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
      band:
        c.accessibility_score >= 70 ? "Excellent"
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

// ── Smart Routing ─────────────────────────────────────────────────────────────

export async function fetchEmergencyTypes() {
  const res = await fetch(`${BASE}/smart/emergency-types`);
  if (!res.ok) throw new Error("Failed to fetch emergency types");
  return res.json();
}

export async function fetchInsuranceProviders() {
  const res = await fetch(`${BASE}/smart/insurance-providers`);
  if (!res.ok) throw new Error("Failed to fetch insurance providers");
  return res.json();
}

export async function fetchSmartRecommendations({
  lat, lon, emergencyType, insurance, financialLevel, radiusKm = 50, limit = 10,
} = {}) {
  const p = new URLSearchParams();
  if (lat != null) p.set("lat", lat);
  if (lon != null) p.set("lon", lon);
  if (emergencyType) p.set("emergency_type", emergencyType);
  if (insurance) p.set("insurance", insurance);
  if (financialLevel && financialLevel !== "Any") p.set("financial_level", financialLevel);
  p.set("radius_km", radiusKm);
  p.set("limit", limit);
  const res = await fetch(`${BASE}/smart/recommend?${p}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "No facilities found");
  }
  return res.json();
}

export async function fetchRoadRoute(fromLat, fromLon, toLat, toLon) {
  const p = new URLSearchParams({ from_lat: fromLat, from_lon: fromLon, to_lat: toLat, to_lon: toLon });
  const res = await fetch(`${BASE}/smart/road-route?${p}`);
  if (!res.ok) throw new Error("Failed to fetch road route");
  return res.json();
}

export async function fetchNearestFacility(lat, lon, emergencyType = "general") {
  const p = new URLSearchParams({ lat, lon, emergency_type: emergencyType, limit: 3 });
  const res = await fetch(`${BASE}/smart/nearest?${p}`);
  if (!res.ok) throw new Error("Failed to find nearest facility");
  return res.json();
}

export async function fetchPopulationServed(lat, lon, radiusKm = 10) {
  const p = new URLSearchParams({ lat, lon, radius_km: radiusKm });
  const res = await fetch(`${BASE}/smart/population-served?${p}`);
  if (!res.ok) throw new Error("Failed to fetch population data");
  return res.json();
}

export async function fetchCountyCentroids() {
  const res = await fetch(`${BASE}/api/counties/centroids`);
  if (!res.ok) return { counties: [] };
  return res.json();
}

export async function fetchPlatformStats() {
  const res = await fetch(`${BASE}/api/stats`);
  if (!res.ok) return null;
  return res.json();
}

// ── Legacy aliases ────────────────────────────────────────────────────────────

export async function fetchRoute(fromLat, fromLon, toLat, toLon) {
  return fetchRoadRoute(fromLat, fromLon, toLat, toLon);
}

export async function fetchEmergencyZones(lat, lon) {
  const p = new URLSearchParams({ lat, lon, radius_km: 50 });
  const res = await fetch(`${BASE}/gis/catchment?${p}`);
  if (!res.ok) throw new Error("Failed to fetch emergency zones");
  const data = await res.json();
  const zones = { critical: [], urgent: [], standard: [], remote: [] };
  for (const f of data.catchment || []) {
    const min = f.estimated_minutes || 999;
    const entry = { ...f, est_response_min: min };
    if (min < 15) zones.critical.push(entry);
    else if (min < 30) zones.urgent.push(entry);
    else if (min < 60) zones.standard.push(entry);
    else zones.remote.push(entry);
  }
  return { zones };
}

export async function fetchFacilityStats() {
  return fetchNationalSummary();
}
