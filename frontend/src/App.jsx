import React, { useState, useEffect, useCallback } from "react";
import MapView from "./components/MapView.jsx";
import Sidebar from "./components/Sidebar.jsx";
import TopBar from "./components/TopBar.jsx";
import { fetchFacilities, fetchCounties, fetchAccessibilityScores } from "./api/index.js";

export default function App() {
  const [facilities, setFacilities] = useState([]);
  const [counties, setCounties] = useState([]);
  const [selectedCounty, setSelectedCounty] = useState("");
  const [selectedFacility, setSelectedFacility] = useState(null);
  const [userLocation, setUserLocation] = useState(null);
  const [route, setRoute] = useState(null);
  const [accessibilityScores, setAccessibilityScores] = useState([]);
  const [activeLayer, setActiveLayer] = useState("facilities");
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    Promise.all([fetchCounties()])
      .then(([c]) => setCounties(c))
      .catch(console.error);

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setUserLocation({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
        () => setUserLocation({ lat: -1.2921, lon: 36.8219 })
      );
    } else {
      setUserLocation({ lat: -1.2921, lon: 36.8219 });
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    fetchFacilities({ county: selectedCounty || undefined })
      .then((data) => setFacilities(data.results || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedCounty]);

  useEffect(() => {
    if (activeLayer === "accessibility") {
      fetchAccessibilityScores(selectedCounty || null)
        .then((data) => setAccessibilityScores(data.counties || []))
        .catch(console.error);
    }
  }, [activeLayer, selectedCounty]);

  const handleFacilitySelect = useCallback((facility) => {
    setSelectedFacility(facility);
    setRoute(null);
  }, []);

  const handleRouteSet = useCallback((routeData) => {
    setRoute(routeData);
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <TopBar
        activeLayer={activeLayer}
        onLayerChange={setActiveLayer}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((v) => !v)}
        loading={loading}
      />
      <div style={{ display: "flex", flex: 1, overflow: "hidden" }}>
        {sidebarOpen && (
          <Sidebar
            counties={counties}
            selectedCounty={selectedCounty}
            onCountyChange={setSelectedCounty}
            selectedFacility={selectedFacility}
            userLocation={userLocation}
            accessibilityScores={accessibilityScores}
            activeLayer={activeLayer}
            onRouteSet={handleRouteSet}
          />
        )}
        <MapView
          facilities={facilities}
          userLocation={userLocation}
          selectedFacility={selectedFacility}
          onFacilitySelect={handleFacilitySelect}
          route={route}
          activeLayer={activeLayer}
          accessibilityScores={accessibilityScores}
        />
      </div>
    </div>
  );
}
