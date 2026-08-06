/**
 * api.js — FastAPI request helpers.
 *
 * All requests go through VITE_API_URL (set in .env or .env.local).
 * Falls back to http://localhost:8000 for local development.
 */
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options);
  if (res.status === 404) return null;
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

// ── Facilities ────────────────────────────────────────────────────────────────

/** Paginated list of all facilities. */
export async function fetchFacilities({ skip = 0, limit = 50 } = {}) {
  return request(`/facilities?skip=${skip}&limit=${limit}`);
}

/** Single facility by ID. */
export async function fetchFacility(id) {
  return request(`/facilities/${id}`);
}

/**
 * Nearest facilities to a GPS point.
 *
 * Params
 * ------
 * lon, lat        — GPS coordinate (required)
 * limit           — number of results (default 5)
 * facility_type   — optional filter
 */
export async function fetchNearestFacilities({ lon, lat, q, limit = 5, facility_type } = {}) {
  const params = new URLSearchParams({ limit });
  if (lon != null && lat != null) {
    params.set("lon", lon);
    params.set("lat", lat);
  }
  if (q) params.set("q", q);
  if (facility_type) params.set("facility_type", facility_type);
  return request(`/facilities/nearest?${params}`);
}

// ── Search ────────────────────────────────────────────────────────────────────

/**
 * Full-text search across name, type, and operator.
 *
 * Params: q, facility_type, operator, limit
 */
export async function searchFacilities({ q, facility_type, operator, limit = 20 } = {}) {
  const params = new URLSearchParams({ limit });
  if (q) params.set("q", q);
  if (facility_type) params.set("facility_type", facility_type);
  if (operator) params.set("operator", operator);
  return request(`/search?${params}`);
}

// ── Health ────────────────────────────────────────────────────────────────────

export async function fetchHealth() {
  return request("/health");
}
