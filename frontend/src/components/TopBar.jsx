import React, { useState, useEffect, useRef, useCallback } from "react";
import { suggestFacilities, geocodeLocation } from "../api/index.js";
import { FACILITY_COLORS } from "../constants/facilityTypes.js";

const LAYERS = [
  { id: "facilities",    label: "🏥 Facilities" },
  { id: "accessibility", label: "📊 Accessibility" },
  { id: "coverage",      label: "🎯 Coverage" },
  { id: "emergency",     label: "🚨 Emergency" },
  { id: "reports",       label: "📋 Reports" },
];

function useDebounce(fn, delay) {
  const timer = useRef(null);
  return useCallback((...args) => {
    clearTimeout(timer.current);
    timer.current = setTimeout(() => fn(...args), delay);
  }, [fn, delay]);
}

export default function TopBar({
  activeLayer, onLayerChange, sidebarOpen, onToggleSidebar,
  loading, theme, onThemeToggle, searchQuery, onSearch,
  facilityCount, onSuggestionSelect,
}) {
  const dark = theme === "dark";
  const [suggestions, setSuggestions] = useState([]);
  const [showSugg, setShowSugg]       = useState(false);
  const [sugLoading, setSugLoading]   = useState(false);
  const [activeIdx, setActiveIdx]     = useState(-1);
  const inputRef = useRef(null);
  const dropRef  = useRef(null);

  const fetchSuggestions = useCallback(async (q) => {
    if (!q || q.length < 2) { setSuggestions([]); setShowSugg(false); return; }
    setSugLoading(true);
    try {
      const data = await suggestFacilities(q, 8);
      const facilitySugs = data.suggestions || [];

      // Only hit the geocoder when facility matches are thin — Nominatim is
      // rate-limited (~1 req/sec) so we don't want to fire it on every keystroke.
      let geoSug = null;
      if (facilitySugs.length < 4) {
        const geo = await geocodeLocation(q).catch(() => null);
        if (geo) {
          geoSug = {
            facility_id: `geo:${geo.latitude},${geo.longitude}`,
            name: geo.label,
            type: "Location",
            county: "",
            operational_status: "Operational",
            latitude: geo.latitude,
            longitude: geo.longitude,
            isGeocoded: true,
          };
        }
      }

      const merged = geoSug ? [geoSug, ...facilitySugs] : facilitySugs;
      setSuggestions(merged);
      setShowSugg(merged.length > 0);
    } catch { setSuggestions([]); }
    finally { setSugLoading(false); }
  }, []);

  const debouncedFetch = useDebounce(fetchSuggestions, 280);

  function handleSearchChange(e) {
    const v = e.target.value;
    onSearch(v);
    setActiveIdx(-1);
    debouncedFetch(v);
  }

  function handleSelect(sug) {
    onSearch(sug.name);
    setSuggestions([]);
    setShowSugg(false);
    if (onSuggestionSelect) onSuggestionSelect(sug);
  }

  function handleKeyDown(e) {
    if (!showSugg || !suggestions.length) return;
    if (e.key === "ArrowDown")  { e.preventDefault(); setActiveIdx((i) => Math.min(i + 1, suggestions.length - 1)); }
    if (e.key === "ArrowUp")    { e.preventDefault(); setActiveIdx((i) => Math.max(i - 1, -1)); }
    if (e.key === "Enter" && activeIdx >= 0) { e.preventDefault(); handleSelect(suggestions[activeIdx]); }
    if (e.key === "Escape")     { setShowSugg(false); setActiveIdx(-1); }
  }

  // Close on outside click
  useEffect(() => {
    function handler(e) {
      if (!dropRef.current?.contains(e.target) && !inputRef.current?.contains(e.target)) {
        setShowSugg(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const s = {
    bar: {
      display: "flex", alignItems: "center", flexWrap: "nowrap", gap: 8,
      background: dark ? "#111827" : "#ffffff",
      borderBottom: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}`,
      padding: "0 14px", minHeight: 50, flexShrink: 0, overflowX: "auto",
    },
    logo:  { fontWeight: 800, fontSize: 16, color: "#10b981", letterSpacing: "0.05em", whiteSpace: "nowrap", flexShrink: 0 },
    badge: { fontSize: 10, background: "#10b981", color: "#fff", borderRadius: 4, padding: "2px 6px", fontWeight: 700, flexShrink: 0 },
    searchWrap: { position: "relative", flexShrink: 0 },
    search: {
      background: dark ? "#1f2937" : "#f3f4f6",
      border: `1px solid ${dark ? "#374151" : "#d1d5db"}`,
      color: dark ? "#e2e8f0" : "#111827",
      borderRadius: 6, padding: "5px 10px 5px 30px", fontSize: 12, width: 200,
      outline: "none",
    },
    searchIcon: {
      position: "absolute", left: 9, top: "50%", transform: "translateY(-50%)",
      color: "#6b7280", fontSize: 12, pointerEvents: "none",
    },
    clearBtn: {
      position: "absolute", right: 7, top: "50%", transform: "translateY(-50%)",
      background: "none", border: "none", color: "#6b7280", cursor: "pointer",
      fontSize: 12, padding: 0, lineHeight: 1,
    },
    dropdown: {
      position: "absolute", top: "calc(100% + 4px)", left: 0,
      background: dark ? "#1f2937" : "#fff",
      border: `1px solid ${dark ? "#374151" : "#d1d5db"}`,
      borderRadius: 8, boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
      zIndex: 2000, minWidth: 280, maxHeight: 320, overflowY: "auto",
    },
    suggItem: (active) => ({
      padding: "8px 12px", cursor: "pointer", fontSize: 12,
      background: active ? (dark ? "#374151" : "#f3f4f6") : "transparent",
      color: dark ? "#e2e8f0" : "#111827",
      borderBottom: `1px solid ${dark ? "#374151" : "#f3f4f6"}`,
    }),
    count: { fontSize: 11, color: dark ? "#6b7280" : "#9ca3af", whiteSpace: "nowrap", flexShrink: 0 },
    layerBtn: (active) => ({
      padding: "5px 10px", borderRadius: 6, border: "none", cursor: "pointer",
      fontSize: 11, fontWeight: 500, whiteSpace: "nowrap", flexShrink: 0,
      background: active ? "#10b981" : (dark ? "#1f2937" : "#f3f4f6"),
      color: active ? "#fff" : (dark ? "#9ca3af" : "#6b7280"),
      transition: "all 0.15s",
    }),
    iconBtn: {
      background: dark ? "#1f2937" : "#f3f4f6",
      border: "none", color: dark ? "#9ca3af" : "#6b7280",
      cursor: "pointer", borderRadius: 6, padding: "5px 8px", fontSize: 13,
      flexShrink: 0,
    },
    spinner: {
      width: 8, height: 8, borderRadius: "50%",
      background: "transparent", border: "2px solid #f59e0b",
      borderTopColor: "transparent", flexShrink: 0,
      animation: "spin 0.7s linear infinite",
    },
  };

  return (
    <div style={s.bar}>
      <span style={s.logo}>KHAP</span>
      <span style={s.badge}>v3</span>

      {/* Search with autocomplete */}
      <div style={s.searchWrap} ref={dropRef}>
        <span style={s.searchIcon}>🔍</span>
        <input
          ref={inputRef}
          style={s.search}
          placeholder="Search facilities…"
          value={searchQuery}
          onChange={handleSearchChange}
          onKeyDown={handleKeyDown}
          onFocus={() => suggestions.length > 0 && setShowSugg(true)}
          autoComplete="off"
        />
        {searchQuery && (
          <button style={s.clearBtn} onClick={() => { onSearch(""); setSuggestions([]); setShowSugg(false); }}>✕</button>
        )}
        {showSugg && suggestions.length > 0 && (
          <div style={s.dropdown}>
            {suggestions.map((sug, i) => (
              <div
                key={sug.facility_id}
                style={s.suggItem(i === activeIdx)}
                onMouseEnter={() => setActiveIdx(i)}
                onMouseDown={() => handleSelect(sug)}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  {sug.isGeocoded ? (
                    <span style={{ fontSize: 11, flexShrink: 0 }}>📍</span>
                  ) : (
                    <span style={{
                      width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                      background: FACILITY_COLORS[sug.type] || FACILITY_COLORS.default,
                    }} />
                  )}
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 12 }}>{sug.name}</div>
                    <div style={{ fontSize: 10, color: "#6b7280" }}>
                      {sug.isGeocoded
                        ? "Location (map pin)"
                        : <>{sug.type} · {sug.county}
                            {sug.operational_status !== "Operational" && <span style={{ color: "#f97316" }}> · {sug.operational_status}</span>}
                          </>}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <span style={s.count}>{facilityCount.toLocaleString()} facilities</span>

      {/* Layer buttons */}
      {LAYERS.map((l) => (
        <button key={l.id} style={s.layerBtn(activeLayer === l.id)} onClick={() => onLayerChange(l.id)}>
          {l.label}
        </button>
      ))}

      {loading && (
        <>
          <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
          <div style={s.spinner} />
        </>
      )}
      {sugLoading && <span style={{ fontSize: 10, color: "#6b7280" }}>…</span>}

      <button style={s.iconBtn} onClick={onThemeToggle} title="Toggle theme">
        {theme === "dark" ? "☀️" : "🌙"}
      </button>
      <button style={s.iconBtn} onClick={onToggleSidebar} title={sidebarOpen ? "Hide sidebar" : "Show sidebar"}>
        {sidebarOpen ? "◀" : "▶"}
      </button>
    </div>
  );
}
