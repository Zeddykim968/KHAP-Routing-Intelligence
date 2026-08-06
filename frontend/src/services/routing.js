/**
 * routing.js — Route request helpers.
 *
 * Wraps the POST /route endpoint.
 * Returns null when OSRM finds no path (404 → expected, not an error).
 */
const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

/**
 * Fetch a driving route between two GPS points.
 *
 * @param {{ lat: number, lon: number }} start  — origin
 * @param {{ lat: number, lon: number }} end    — destination
 * @returns {Promise<RouteResponse|null>}        — null if no route exists
 */
export async function fetchRoute(start, end) {
  const res = await fetch(`${BASE}/route`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      start_lat: start.lat,
      start_lon: start.lon,
      end_lat:   end.lat,
      end_lon:   end.lon,
    }),
  });

  if (res.status === 404) return null;          // no route — expected
  if (!res.ok) throw new Error(`Route error ${res.status}`);
  return res.json();
}
