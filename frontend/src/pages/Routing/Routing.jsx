import { useState } from "react";
import Map from "../../components/Map/Map";
import RouteSummary from "../../components/RouteSummary/RouteSummary";
import { searchFacilities } from "../../services/api";
import { fetchRoute } from "../../services/routing";
import styles from "./Routing.module.css";

/**
 * Routing page — pick a start facility and a destination, see the route.
 *
 * Both endpoints can be searched by name; the user picks from a small
 * dropdown of results, then clicks "Get Route".
 */
export default function Routing() {
  const [startQuery,    setStartQuery]    = useState("");
  const [endQuery,      setEndQuery]      = useState("");
  const [startResults,  setStartResults]  = useState([]);
  const [endResults,    setEndResults]    = useState([]);
  const [startFacility, setStartFacility] = useState(null);
  const [endFacility,   setEndFacility]   = useState(null);
  const [route,         setRoute]         = useState(null);
  const [loading,       setLoading]       = useState(false);
  const [error,         setError]         = useState(null);
  const [noRoute,       setNoRoute]       = useState(false);

  async function search(query, setResults) {
    if (!query.trim()) return;
    const results = await searchFacilities({ q: query, limit: 5 });
    setResults(Array.isArray(results) ? results : []);
  }

  async function getRoute() {
    if (!startFacility || !endFacility) return;
    setLoading(true);
    setRoute(null);
    setNoRoute(false);
    setError(null);
    try {
      const result = await fetchRoute(
        { lat: startFacility.lat, lon: startFacility.lon },
        { lat: endFacility.lat,   lon: endFacility.lon },
      );
      if (result) setRoute(result);
      else        setNoRoute(true);
    } catch (err) {
      setError("Routing failed: " + err.message);
    } finally {
      setLoading(false);
    }
  }

  const mapFacilities = [
    ...(startFacility ? [startFacility] : []),
    ...(endFacility   ? [endFacility]   : []),
  ];

  return (
    <div className={styles.page}>
      <div className={styles.panel}>
        <h2 className={styles.heading}>Route between facilities</h2>

        {/* Start */}
        <label className={styles.label}>Start facility</label>
        <div className={styles.searchRow}>
          <input
            className={styles.input}
            value={startQuery}
            onChange={(e) => setStartQuery(e.target.value)}
            placeholder="Search start facility…"
          />
          <button className={styles.btn} onClick={() => search(startQuery, setStartResults)}>
            Find
          </button>
        </div>
        {startResults.length > 0 && (
          <ul className={styles.results}>
            {startResults.map((f) => (
              <li
                key={f.id}
                className={`${styles.result} ${startFacility?.id === f.id ? styles.selected : ""}`}
                onClick={() => { setStartFacility(f); setStartResults([]); setStartQuery(f.name || ""); }}
              >
                <strong>{f.name}</strong> <span>{f.facility_type}</span>
              </li>
            ))}
          </ul>
        )}

        {/* End */}
        <label className={styles.label}>Destination facility</label>
        <div className={styles.searchRow}>
          <input
            className={styles.input}
            value={endQuery}
            onChange={(e) => setEndQuery(e.target.value)}
            placeholder="Search destination…"
          />
          <button className={styles.btn} onClick={() => search(endQuery, setEndResults)}>
            Find
          </button>
        </div>
        {endResults.length > 0 && (
          <ul className={styles.results}>
            {endResults.map((f) => (
              <li
                key={f.id}
                className={`${styles.result} ${endFacility?.id === f.id ? styles.selected : ""}`}
                onClick={() => { setEndFacility(f); setEndResults([]); setEndQuery(f.name || ""); }}
              >
                <strong>{f.name}</strong> <span>{f.facility_type}</span>
              </li>
            ))}
          </ul>
        )}

        <button
          className={styles.routeBtn}
          disabled={!startFacility || !endFacility || loading}
          onClick={getRoute}
        >
          {loading ? "Calculating…" : "Get Route"}
        </button>

        {error   && <p className={styles.error}>{error}</p>}
        {noRoute && <p className={styles.error}>No drivable route found between these facilities.</p>}
        {route   && <RouteSummary route={route} />}
      </div>

      <div className={styles.mapWrapper}>
        <Map
          facilities={mapFacilities}
          route={route?.route}
          selectedFacility={endFacility}
          center={startFacility ? [startFacility.lat, startFacility.lon] : [-1.2921, 36.8219]}
        />
      </div>
    </div>
  );
}
