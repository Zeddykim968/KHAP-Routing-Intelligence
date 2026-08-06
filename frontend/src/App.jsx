// Top-level state: insurance filter, origin, search results, the
// currently selected facility, and its route.
// Behavior: as soon as a search returns results, we auto-route to
// the nearest one (like Maps/Uber surfacing a default), but tapping
// any other facility (list or map marker) re-routes to that one.
// The origin can come from three places -- typed text, device GPS,
// or a manual map click/drag -- all of which funnel into the same
// pipeline below, so the rest of the app doesn't need to care which.
import { useState } from "react";
import MapView from "./components/MapView";
import SearchBox from "./components/SearchBox";
import InsuranceFilter from "./components/InsuranceFilter";
import FacilityCard from "./components/FacilityCard";
import { fetchRoute, fetchNearestFacilities } from "./api/client";

const DEFAULT_CENTER = [-1.2921, 36.8219]; // Nairobi, as a fallback

export default function App() {
  const [insurance, setInsurance] = useState([]);
  const [origin, setOrigin] = useState(null);
  const [searchResult, setSearchResult] = useState({ resolved_location: null, facilities: [] });
  const [selectedFacility, setSelectedFacility] = useState(null);
  const [route, setRoute] = useState(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [noRouteFound, setNoRouteFound] = useState(false);

  async function selectFacility(facility, originPoint) {
    setSelectedFacility(facility);
    setRoute(null);
    setNoRouteFound(false);
    setRouteLoading(true);
    try {
      const result = await fetchRoute(originPoint, { lon: facility.lon, lat: facility.lat });
      if (result) {
        setRoute(result);
      } else {
        setNoRouteFound(true); // backend returned 404 -- no path exists, not an error
      }
    } catch (err) {
      console.error("Route request failed:", err);
      setNoRouteFound(true);
    } finally {
      setRouteLoading(false);
    }
  }

  function handleSearchResults(data, searchOrigin) {
    setSearchResult(data);
    setOrigin(searchOrigin);
    setRoute(null);
    setNoRouteFound(false);
    setSelectedFacility(null);
    if (searchOrigin && data.facilities.length > 0) {
      selectFacility(data.facilities[0], searchOrigin); // auto-route to nearest
    }
  }

  function handleFacilityClick(facility) {
    if (!origin) return;
    selectFacility(facility, origin);
  }

  // Fired by MapView on a plain map click OR when the origin marker
  // is dragged and dropped -- either way, "this point is where I am
  // now," so re-run the same pipeline text/GPS search uses.
  async function handleMapClick(point) {
    const data = await fetchNearestFacilities({ lon: point.lon, lat: point.lat, insurance });
    handleSearchResults(data, point);
  }

  return (
    <main style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <InsuranceFilter selected={insurance} onChange={setInsurance} />
      <SearchBox insurance={insurance} onResults={handleSearchResults} />
      <p style={{ fontSize: 13, color: "#555", margin: "4px 0" }}>
        Not sure of the road or area name? Click anywhere on the map to set
        your location, or drag the pin to fine-tune it.
      </p>
      {searchResult.resolved_location && (
        <p style={{ fontSize: 13, color: "#555", margin: "4px 0" }}>
          Showing results near: {searchResult.resolved_location.matched_name}
          {searchResult.resolved_location.place_type &&
            ` (${searchResult.resolved_location.place_type})`}
        </p>
      )}
      <FacilityCard
        facility={selectedFacility}
        route={route}
        loading={routeLoading}
        noRouteFound={noRouteFound}
      />
      <div style={{ flex: 1 }}>
        <MapView
          route={route?.route}
          facilities={searchResult.facilities}
          origin={origin}
          selectedFacilityId={selectedFacility?.facility_id}
          onSelectFacility={handleFacilityClick}
          onMapClick={handleMapClick}
          center={DEFAULT_CENTER}
        />
      </div>
      <ul>
        {searchResult.facilities.map((f) => (
          <li
            key={f.facility_id}
            onClick={() => handleFacilityClick(f)}
            style={{
              cursor: "pointer",
              fontWeight: f.facility_id === selectedFacility?.facility_id ? 700 : 400,
            }}
          >
            {f.name} -- {(f.distance_m / 1000).toFixed(2)} km
            {f.insurance_accepted?.length > 0 && ` (${f.insurance_accepted.join(", ")})`}
          </li>
        ))}
      </ul>
    </main>
  );
}
