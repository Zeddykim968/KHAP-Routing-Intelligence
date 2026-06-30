const BASE = "";

// ── Facilities ────────────────────────────────────────────────────────────────

export async function fetchFacilities({ county, type } = {}) {
  const p = new URLSearchParams();
  if (county) p.set("county", county);
  if (type) p.set("type", type);
  p.set("limit", "500");
  const res = await fetch(`${BASE}/api/v3/facilities?${p}`);
  if (!res.ok) throw new Error("Failed to fetch facilities");
  return res.json();
}

export async function fetchCounties() {
  const res = await fetch(`${BASE}/api/v3/facilities/counties`);
  if (!res.ok) throw new Error("Failed to fetch counties");
  const data = await res.json();
  return data.counties;
}

export async function fetchFacilityTypes() {
  const res = await fetch(`${BASE}/api/v3/facilities/types`);
  if (!res.ok) throw new Error("Failed to fetch types");
  const data = await res.json();
  return data.types;
}

export async function fetchFacilityStats(county = null) {
  const p = new URLSearchParams();
  if (county) p.set("county", county);
  const res = await fetch(`${BASE}/api/v3/facilities/stats?${p}`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export async function fetchAccessibilityScores(county = null) {
  const p = new URLSearchParams();
  if (county) p.set("county", county);
  const res = await fetch(`${BASE}/api/v3/analytics/accessibility?${p}`);
  if (!res.ok) throw new Error("Failed to fetch accessibility");
  return res.json();
}

export async function fetchCoverage(lat, lon, county = null) {
  const p = new URLSearchParams({ lat, lon });
  if (county) p.set("county", county);
  const res = await fetch(`${BASE}/api/v3/analytics/coverage?${p}`);
  if (!res.ok) throw new Error("Failed to fetch coverage");
  return res.json();
}

export async function fetchCountyRankings() {
  const res = await fetch(`${BASE}/api/v3/analytics/county-rankings`);
  if (!res.ok) throw new Error("Failed to fetch rankings");
  return res.json();
}

export async function fetchFacilityImpact(lat, lon) {
  const p = new URLSearchParams({ lat, lon });
  const res = await fetch(`${BASE}/api/v3/analytics/impact?${p}`);
  if (!res.ok) throw new Error("Failed to fetch impact");
  return res.json();
}

// ── Routing ───────────────────────────────────────────────────────────────────

export async function fetchRoute(fromLat, fromLon, toLat, toLon) {
  const p = new URLSearchParams({ from_lat: fromLat, from_lon: fromLon, to_lat: toLat, to_lon: toLon });
  const res = await fetch(`${BASE}/api/v3/routing/route?${p}`);
  if (!res.ok) throw new Error("Failed to fetch route");
  return res.json();
}

export async function fetchNearestWithRoutes(lat, lon, type = null) {
  const p = new URLSearchParams({ lat, lon, limit: 5, with_route: true });
  if (type) p.set("facility_type", type);
  const res = await fetch(`${BASE}/api/v3/routing/nearest-facility?${p}`);
  if (!res.ok) throw new Error("Failed to fetch nearest");
  return res.json();
}

export async function fetchTravelTime(fromLat, fromLon, toLat, toLon) {
  const p = new URLSearchParams({ from_lat: fromLat, from_lon: fromLon, to_lat: toLat, to_lon: toLon });
  const res = await fetch(`${BASE}/api/v3/routing/travel-time?${p}`);
  if (!res.ok) throw new Error("Failed to fetch travel time");
  return res.json();
}

// ── GIS ───────────────────────────────────────────────────────────────────────

export async function fetchEmergencyZones(lat, lon) {
  const p = new URLSearchParams({ lat, lon });
  const res = await fetch(`${BASE}/api/v3/gis/emergency-zones?${p}`);
  if (!res.ok) throw new Error("Failed to fetch emergency zones");
  return res.json();
}

export async function fetchCatchment(lat, lon, radiusKm = 15) {
  const p = new URLSearchParams({ lat, lon, radius_km: radiusKm });
  const res = await fetch(`${BASE}/api/v3/gis/catchment?${p}`);
  if (!res.ok) throw new Error("Failed to fetch catchment");
  return res.json();
}

// ── Reports ───────────────────────────────────────────────────────────────────

export async function fetchNationalSummary() {
  const res = await fetch(`${BASE}/api/v3/reports/national-summary`);
  if (!res.ok) throw new Error("Failed to fetch national summary");
  return res.json();
}

export async function fetchCountyReport(county) {
  const p = new URLSearchParams({ county });
  const res = await fetch(`${BASE}/api/v3/reports/county-report?${p}`);
  if (!res.ok) throw new Error("Failed to fetch county report");
  return res.json();
}

export async function fetchEmergencyReadiness() {
  const res = await fetch(`${BASE}/api/v3/reports/emergency-readiness`);
  if (!res.ok) throw new Error("Failed to fetch emergency readiness");
  return res.json();
}

// ── Admin ─────────────────────────────────────────────────────────────────────

export async function fetchSystemHealth() {
  const res = await fetch(`${BASE}/api/v3/admin/health`);
  if (!res.ok) throw new Error("Failed to fetch health");
  return res.json();
}
