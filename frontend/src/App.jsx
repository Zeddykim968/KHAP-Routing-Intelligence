import React, { useState, useEffect } from "react";
import MapView from "./components/MapView.jsx";
import Sidebar from "./components/Sidebar.jsx";
import TopBar from "./components/TopBar.jsx";
import {
  fetchFacilities, fetchCounties,
  fetchAccessibilityScores, fetchNationalSummary,
  fetchEmergencyTypes, fetchInsuranceProviders,
} from "./api/index.js";

export default function App() {
  const [facilities, setFacilities]           = useState([]);
  const [counties, setCounties]               = useState([]);
  const [selectedCounty, setSelectedCounty]   = useState("");
  const [selectedFacility, setSelectedFacility] = useState(null);
  const [userLocation, setUserLocation]       = useState(null);
  const [route, setRoute]                     = useState(null);
  const [accessibilityScores, setAccessibilityScores] = useState([]);
  const [nationalSummary, setNationalSummary] = useState(null);
  const [activeLayer, setActiveLayer]         = useState("facilities");
  const [theme, setTheme]                     = useState("dark");
  const [loading, setLoading]                 = useState(true);
  const [sidebarOpen, setSidebarOpen]         = useState(true);
  const [searchQuery, setSearchQuery]         = useState("");
  const [emergencyTypes, setEmergencyTypes]   = useState([]);
  const [insuranceProviders, setInsuranceProviders] = useState([]);
  const [smartResultFacilities, setSmartResultFacilities] = useState([]);

  useEffect(() => {
    fetchCounties().then(setCounties).catch(console.error);
    fetchEmergencyTypes()
      .then((d) => setEmergencyTypes(d.emergency_types || []))
      .catch(console.error);
    fetchInsuranceProviders()
      .then((d) => setInsuranceProviders(d.insurance_providers || []))
      .catch(console.error);

    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setUserLocation({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
        ()    => setUserLocation({ lat: -1.2921, lon: 36.8219 })
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
      fetchAccessibilityScores()
        .then((data) => setAccessibilityScores(data.counties || []))
        .catch(console.error);
    }
    if (activeLayer === "reports") {
      fetchNationalSummary().then(setNationalSummary).catch(console.error);
    }
    if (activeLayer !== "emergency") {
      setSmartResultFacilities([]);
    }
  }, [activeLayer, selectedCounty]);

  const handleRouteSet = (r) => {
    setRoute(r);
    if (r?.destination) setSelectedFacility(r.destination);
  };

  // When a suggestion is selected from the search bar, select that facility
  const handleSuggestionSelect = (sug) => {
    if (sug.latitude && sug.longitude) {
      setSelectedFacility(sug);
      setActiveLayer("facilities");
    }
  };

  const filteredFacilities = searchQuery
    ? facilities.filter((f) =>
        (f.name   || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (f.county || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
        (f.type   || "").toLowerCase().includes(searchQuery.toLowerCase())
      )
    : facilities;

  const mapFacilities =
    activeLayer === "emergency" && smartResultFacilities.length > 0
      ? smartResultFacilities
      : filteredFacilities;

  return (
    <div style={{
      display: "flex", flexDirection: "column", height: "100vh",
      background: theme === "dark" ? "#0f1923" : "#f0f4f8",
    }}>
      <TopBar
        activeLayer={activeLayer}
        onLayerChange={setActiveLayer}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((v) => !v)}
        loading={loading}
        theme={theme}
        onThemeToggle={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
        searchQuery={searchQuery}
        onSearch={setSearchQuery}
        facilityCount={mapFacilities.length}
        onSuggestionSelect={handleSuggestionSelect}
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
            nationalSummary={nationalSummary}
            activeLayer={activeLayer}
            onRouteSet={handleRouteSet}
            theme={theme}
            emergencyTypes={emergencyTypes}
            insuranceProviders={insuranceProviders}
            onSmartResults={setSmartResultFacilities}
          />
        )}
        <MapView
          facilities={mapFacilities}
          userLocation={userLocation}
          selectedFacility={selectedFacility}
          onFacilitySelect={setSelectedFacility}
          route={route}
          activeLayer={activeLayer}
          accessibilityScores={accessibilityScores}
          theme={theme}
          smartResults={activeLayer === "emergency" && smartResultFacilities.length > 0}
          loading={loading}
        />
      </div>
    </div>
  );
}
