const BASE = "";

export async function fetchFacilities({ county, type } = {}) {
  const params = new URLSearchParams();
  if (county) params.set("county", county);
  if (type) params.set("type", type);
  params.set("limit", "500");
  const res = await fetch(`${BASE}/recommendations/list?${params}`);
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

export async function fetchAccessibilityScores(county = null) {
  const params = new URLSearchParams();
  if (county) params.set("county", county);
  const res = await fetch(`${BASE}/api/analytics/accessibility?${params}`);
  if (!res.ok) throw new Error("Failed to fetch accessibility scores");
  return res.json();
}

export async function fetchCoverage(lat, lon, county = null) {
  const params = new URLSearchParams({ lat, lon });
  if (county) params.set("county", county);
  const res = await fetch(`${BASE}/api/analytics/coverage?${params}`);
  if (!res.ok) throw new Error("Failed to fetch coverage");
  return res.json();
}

export async function fetchRoute(fromLat, fromLon, toLat, toLon) {
  const params = new URLSearchParams({
    from_lat: fromLat, from_lon: fromLon,
    to_lat: toLat, to_lon: toLon,
  });
  const res = await fetch(`${BASE}/api/routing/route?${params}`);
  if (!res.ok) throw new Error("Failed to fetch route");
  return res.json();
}

export async function fetchNearestWithRoutes(lat, lon, type = null) {
  const params = new URLSearchParams({ lat, lon, limit: 5 });
  if (type) params.set("facility_type", type);
  const res = await fetch(`${BASE}/api/routing/nearest?${params}`);
  if (!res.ok) throw new Error("Failed to fetch nearest facilities");
  return res.json();
}

export async function fetchGapAnalysis(county = null) {
  const params = new URLSearchParams();
  if (county) params.set("county", county);
  const res = await fetch(`${BASE}/api/analytics/gap-analysis?${params}`);
  if (!res.ok) throw new Error("Failed to fetch gap analysis");
  return res.json();
}

export async function fetchFacilityImpact(lat, lon, county = null) {
  const params = new URLSearchParams({ lat, lon });
  if (county) params.set("county", county);
  const res = await fetch(`${BASE}/api/analytics/impact?${params}`);
  if (!res.ok) throw new Error("Failed to fetch impact analysis");
  return res.json();
}
