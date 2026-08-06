import { useState } from "react";
import { fetchNearestFacilities } from "../../services/api";
import styles from "./SearchBar.module.css";

/**
 * SearchBar — two ways to find facilities:
 *   1. Type a location name (Kibera, Westlands, etc.)
 *   2. Use the browser's Geolocation API
 *
 * Props
 * -----
 * onResults(data, origin) — called with API response + resolved origin point
 */
export default function SearchBar({ onResults }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleTextSearch(e) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchNearestFacilities({ q: query.trim() });
      const origin = data.resolved_location
        ? { lat: data.resolved_location.lat, lon: data.resolved_location.lon }
        : null;
      onResults(data, origin);
    } catch (err) {
      setError("Search failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleGPS() {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser.");
      return;
    }
    setLoading(true);
    setError(null);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const origin = { lat: pos.coords.latitude, lon: pos.coords.longitude };
        try {
          const data = await fetchNearestFacilities({ lat: origin.lat, lon: origin.lon });
          onResults(data, origin);
        } catch {
          setError("Could not load facilities for your location.");
        } finally {
          setLoading(false);
        }
      },
      () => {
        setError("Location access denied.");
        setLoading(false);
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  }

  return (
    <div className={styles.wrapper}>
      <form className={styles.form} onSubmit={handleTextSearch}>
        <input
          className={styles.input}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by location or facility name…"
          disabled={loading}
        />
        <button className={styles.btn} type="submit" disabled={loading || !query.trim()}>
          {loading ? "Searching…" : "Search"}
        </button>
        <button className={styles.btnOutline} type="button" onClick={handleGPS} disabled={loading}>
          Use my location
        </button>
      </form>
      {error && <p className={styles.error}>{error}</p>}
    </div>
  );
}
