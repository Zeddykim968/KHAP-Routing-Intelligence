import React, { useState, useEffect, useRef, useCallback } from "react";
import MapView from "./components/MapView.jsx";
import Sidebar from "./components/Sidebar.jsx";
import TopBar from "./components/TopBar.jsx";
import {
  fetchFacilities, fetchCounties,
  fetchAccessibilityScores, fetchNationalSummary,
  fetchEmergencyTypes, fetchInsuranceProviders,
} from "./api/index.js";

function haversineFE(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

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

  // Live tracking & navigation state
  const watchIdRef   = useRef(null);
  const [liveEta, setLiveEta]           = useState(null);   // { km, minutes } — recomputed on each GPS update
  const [activeStepIdx, setActiveStepIdx] = useState(0);    // which turn-by-turn step user is currently on

  // ── Live GPS tracking ────────────────────────────────────────────────────
  useEffect(() => {
    fetchCounties().then(setCounties).catch(console.error);
    fetchEmergencyTypes()
      .then((d) => setEmergencyTypes(d.emergency_types || []))
      .catch(console.error);
    fetchInsuranceProviders()
      .then((d) => setInsuranceProviders(d.insurance_providers || []))
      .catch(console.error);

    if (!navigator.geolocation) {
      setUserLocation({ lat: -1.2921, lon: 36.8219 });
      return;
    }

    // Use watchPosition so the blue dot and ETA update as user moves
    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => setUserLocation({
        lat: pos.coords.latitude,
        lon: pos.coords.longitude,
        accuracy: pos.coords.accuracy,
      }),
      () => setUserLocation({ lat: -1.2921, lon: 36.8219 }),
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 15000 }
    );

    return () => {
      if (watchIdRef.current != null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
      }
    };
  }, []);

  // ── Live ETA + active step auto-advance ─────────────────────────────────
  useEffect(() => {
    if (!route || !userLocation || !route.destination) {
      setLiveEta(null);
      return;
    }

    // Recompute remaining distance to destination
    const dest = route.destination;
    const dist = haversineFE(userLocation.lat, userLocation.lon, dest.latitude, dest.longitude);
    const roadKm  = Math.round(dist * 1.35 * 10) / 10;
    const minutes = Math.round((roadKm / 40) * 60);
    setLiveEta({ km: roadKm, minutes });

    // Auto-advance active step: find the closest upcoming step
    const steps = route.steps || [];
    if (steps.length > 0) {
      let minDist = Infinity;
      let bestIdx = 0;
      steps.forEach((step, i) => {
        if (!step.location) return;
        const d = haversineFE(userLocation.lat, userLocation.lon, step.location.lat, step.location.lon);
        if (d < minDist) { minDist = d; bestIdx = i; }
      });
      setActiveStepIdx(bestIdx);
    }
  }, [userLocation, route]);

  // ── Facility loading ─────────────────────────────────────────────────────
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

  const handleRouteSet = useCallback((r) => {
    setRoute(r);
    setActiveStepIdx(0);
    if (r?.destination) setSelectedFacility(r.destination);
  }, []);

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
            liveEta={liveEta}
            activeStepIdx={activeStepIdx}
          />
        )}
        <MapView
          facilities={mapFacilities}
          userLocation={userLocation}
          selectedFacility={selectedFacility}
          onFacilitySelect={setSelectedFacility}
          route={route}
          onRouteSet={handleRouteSet}
          activeLayer={activeLayer}
          accessibilityScores={accessibilityScores}
          theme={theme}
          smartResults={activeLayer === "emergency" && smartResultFacilities.length > 0}
          loading={loading}
          activeStepIdx={activeStepIdx}
        />
      </div>
    </div>
  );
}
