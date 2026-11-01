// Same-origin API helpers — Next.js rewrites /api/* to the Django backend.
const BASE = "/api";

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, { cache: "no-store", ...options });
  } catch {
    throw new Error("Cannot reach the KHAP API — is the backend running?");
  }
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* empty or non-JSON body */
  }
  if (!res.ok) {
    const detail = data && data.detail;
    let message = typeof detail === "string" ? detail : null;
    if (!message && data && typeof data === "object") {
      const first = Object.values(data)[0];
      message = Array.isArray(first) ? first[0] : JSON.stringify(data);
    }
    throw new Error(message || `Request failed (HTTP ${res.status})`);
  }
  return data;
}

export function fetchMeta() {
  return request("/meta/");
}

export function fetchNearest(lat, lon, opts = {}) {
  const { limit = 20, type, openNow, emergency } = opts;
  const p = new URLSearchParams();
  p.set("lat", String(lat));
  p.set("lon", String(lon));
  p.set("limit", String(limit));
  if (type && type !== "all") p.set("facility_type", type);
  if (openNow) p.set("open_now", "true");
  if (emergency) p.set("emergency", "true");
  return request(`/facilities/nearest/?${p.toString()}`);
}

export function searchFacilities(q, lat, lon, limit = 12) {
  const p = new URLSearchParams();
  p.set("q", q);
  p.set("limit", String(limit));
  if (lat != null && lon != null) {
    p.set("lat", String(lat));
    p.set("lon", String(lon));
  }
  return request(`/search/?${p.toString()}`);
}

export function fetchFacility(id) {
  return request(`/facilities/${id}/`);
}

export function fetchRoute(start, end) {
  return request("/route/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      start_lat: start.lat,
      start_lon: start.lon,
      end_lat: end.lat,
      end_lon: end.lon,
    }),
  });
}
