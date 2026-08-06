// The "Uber/Maps"-style info panel: which facility is selected, what
// it offers, and -- once the route comes back -- real road distance
// and a rough ETA. Also handles the "no route exists" case explicitly.
export default function FacilityCard({ facility, route, loading, noRouteFound }) {
  if (!facility) return null;

  const straightKm = (facility.distance_m / 1000).toFixed(1);
  const routeKm = route ? (route.distance_m / 1000).toFixed(1) : null;
  // Rough ETA from an assumed average urban speed -- NOT traffic-aware,
  // and not based on road class. Swap for a real speed-profile-based
  // duration (computed server-side from highway tags) if you need
  // this to be accurate.
  const etaMin = route ? Math.round((route.distance_m / 1000) / 30 * 60) : null;

  return (
    <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12, margin: "8px 0" }}>
      <h3 style={{ margin: 0 }}>{facility.name}</h3>
      <p style={{ margin: "4px 0", color: "#666" }}>{facility.facility_type}</p>
      {facility.insurance_accepted?.length > 0 && (
        <p style={{ margin: "4px 0", fontSize: 13 }}>
          Accepts: {facility.insurance_accepted.join(", ")}
        </p>
      )}
      {loading && <p>Finding route...</p>}
      {!loading && route && (
        <p style={{ margin: "4px 0", fontWeight: 600 }}>
          {routeKm} km by road -- ~{etaMin} min
        </p>
      )}
      {!loading && noRouteFound && (
        <p style={{ margin: "4px 0", color: "#b45309" }}>
          No road route found to this facility -- straight-line distance is{" "}
          {straightKm} km, but it may be in a disconnected part of the mapped
          road network.
        </p>
      )}
      {!loading && !route && !noRouteFound && (
        <p style={{ margin: "4px 0", fontSize: 13, color: "#888" }}>
          {straightKm} km away (straight-line)
        </p>
      )}
    </div>
  );
}
