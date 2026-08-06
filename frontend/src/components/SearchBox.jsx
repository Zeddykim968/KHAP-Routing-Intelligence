// Two ways in: type a place name, or use the browser's geolocation.
// Reports BOTH the search results and the resolved origin point to
// the parent -- App needs the origin later to draw routes.
import { useState } from "react";
import { fetchNearestFacilities } from "../api/client";

export default function SearchBox({ insurance, onResults }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  async function searchByText() {
    if (!text) return;
    setLoading(true);
    try {
      const data = await fetchNearestFacilities({ q: text, insurance });
      onResults(data, data.resolved_location);
    } finally {
      setLoading(false);
    }
  }

  function searchByLocation() {
    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const origin = {
          lon: pos.coords.longitude,
          lat: pos.coords.latitude,
          accuracy: pos.coords.accuracy, // metres -- how precise this fix actually is
        };
        const data = await fetchNearestFacilities({ ...origin, insurance });
        onResults(data, origin);
        setLoading(false);
      },
      () => setLoading(false),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  }

  return (
    <div>
      <input
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="e.g. Kilimani, Nairobi"
      />
      <button onClick={searchByText} disabled={loading}>Search</button>
      <button onClick={searchByLocation} disabled={loading}>Use my location</button>
    </div>
  );
}
