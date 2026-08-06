// Thin fetch wrapper around the backend endpoints.
const API_URL = import.meta.env.VITE_API_URL;

// Returns the route object, or null if no route exists between the
// two points (backend returns 404 for this -- it's an expected
// outcome for disconnected parts of the road graph, not an error).
export async function fetchRoute(start, end) {
  const res = await fetch(`${API_URL}/route`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      start_lon: start.lon, start_lat: start.lat,
      end_lon: end.lon, end_lat: end.lat,
    }),
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error("Route request failed");
  return res.json();
}

export async function fetchNearestFacilities({ lon, lat, q, insurance, limit = 3 }) {
  const params = new URLSearchParams({ limit });
  if (lon != null && lat != null) {
    params.set("lon", lon);
    params.set("lat", lat);
  } else if (q) {
    params.set("q", q);
  }
  if (insurance && insurance.length > 0) {
    params.set("insurance", insurance.join(","));
  }
  const res = await fetch(`${API_URL}/facilities/nearest?${params}`);
  if (!res.ok) throw new Error("Facility search failed");
  return res.json();
}

export async function fetchInsuranceProviders() {
  const res = await fetch(`${API_URL}/facilities/insurance-providers`);
  if (!res.ok) throw new Error("Failed to load insurance providers");
  const data = await res.json();
  return data.providers;
}
