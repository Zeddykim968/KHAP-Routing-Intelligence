import { useState } from "react";
import Map from "../../components/Map/Map";
import SearchBar from "../../components/SearchBar/SearchBar";
import FacilityCard from "../../components/FacilityCard/FacilityCard";
import RouteSummary from "../../components/RouteSummary/RouteSummary";
import { fetchNearestFacilities } from "../../services/api";
import { fetchRoute } from "../../services/routing";
import styles from "./Dashboard.module.css";

const DEFAULT_CENTER = [-1.2921, 36.8219]; // Nairobi CBD

/**
 * Dashboard page — the main view.
 *
 * Layout: SearchBar → FacilityCard + RouteSummary → Map
 *
 * State machine
 * -------------
 * - origin          GPS point the user searched from
 * - facilities      list returned by /facilities/nearest
 * - selectedFacility the one the user tapped / was auto-selected
 * - route           OSRM RouteResponse (null until a facility is selected)
 * - routeLoading    spinner state
 * - noRouteFound    OSRM returned 404
 */
export default function Dashboard() {
  const [origin,           setOrigin]           = useState(null);
  const [facilities,       setFacilities]       = useState([]);
  const [selectedFacility, setSelectedFacility] = useState(null);
  const [route,            setRoute]            = useState(null);
  const [routeLoading,     setRouteLoading]     = useState(false);
  const [noRouteFound,     setNoRouteFound]     = useState(false);

  async function selectFacility(facility, fromOrigin) {
    setSelectedFacility(facility);
    setRoute(null);
    setNoRouteFound(false);
    setRouteLoading(true);
    try {
      const result = await fetchRoute(fromOrigin, { lat: facility.lat, lon: facility.lon });
      if (result) setRoute(result);
      else        setNoRouteFound(true);
    } catch {
      setNoRouteFound(true);
    } finally {
      setRouteLoading(false);
    }
  }

  function handleSearchResults(data, searchOrigin) {
    const resolved = searchOrigin || data?.resolved_location;
    setOrigin(resolved);
    setFacilities(data?.facilities ?? []);
    setRoute(null);
    setNoRouteFound(false);
    setSelectedFacility(null);
    // Auto-route to the nearest result
    if (resolved && data?.facilities?.length > 0) {
      selectFacility(data.facilities[0], resolved);
    }
  }

  async function handleMapClick(point) {
    const data = await fetchNearestFacilities({ lon: point.lon, lat: point.lat });
    handleSearchResults(data, point);
  }

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <h1 className={styles.title}>KHAP</h1>
          <p className={styles.subtitle}>Kenya Health Access Platform</p>
        </div>

        <SearchBar onResults={handleSearchResults} />

        {facilities.length === 0 && !selectedFacility && (
          <p className={styles.hint}>
            Search by location or click anywhere on the map to find nearby facilities.
          </p>
        )}

        {selectedFacility && (
          <>
            <RouteSummary route={route} />
            <FacilityCard
              facility={selectedFacility}
              routeLoading={routeLoading}
              noRouteFound={noRouteFound}
            />
          </>
        )}

        {facilities.length > 0 && (
          <div className={styles.facilityList}>
            <p className={styles.listLabel}>{facilities.length} facilities nearby</p>
            {facilities.map((f) => (
              <button
                key={f.id}
                className={`${styles.facilityItem} ${selectedFacility?.id === f.id ? styles.active : ""}`}
                onClick={() => origin && selectFacility(f, origin)}
              >
                <span className={styles.facilityName}>{f.name || "Unnamed"}</span>
                <span className={styles.facilityMeta}>
                  {f.facility_type}
                  {f.distance_m != null && ` · ${(f.distance_m / 1000).toFixed(1)} km`}
                </span>
              </button>
            ))}
          </div>
        )}
      </aside>

      <div className={styles.mapWrapper}>
        <Map
          facilities={facilities}
          origin={origin}
          selectedFacility={selectedFacility}
          route={route?.route}
          onSelectFacility={(f) => origin && selectFacility(f, origin)}
          onMapClick={handleMapClick}
          center={origin ? [origin.lat, origin.lon] : DEFAULT_CENTER}
        />
      </div>
    </div>
  );
}
