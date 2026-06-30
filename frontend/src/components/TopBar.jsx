import React from "react";

const LAYERS = [
  { id: "facilities", label: "🏥 Facilities" },
  { id: "accessibility", label: "📊 Accessibility" },
  { id: "coverage", label: "🎯 Coverage" },
  { id: "emergency", label: "🚨 Emergency" },
  { id: "reports", label: "📋 Reports" },
];

export default function TopBar({
  activeLayer, onLayerChange, sidebarOpen, onToggleSidebar,
  loading, theme, onThemeToggle, searchQuery, onSearch, facilityCount,
}) {
  const dark = theme === "dark";
  const s = {
    bar: {
      display: "flex", alignItems: "center", flexWrap: "wrap", gap: 8,
      background: dark ? "#111827" : "#ffffff",
      borderBottom: `1px solid ${dark ? "#1f2937" : "#e5e7eb"}`,
      padding: "0 16px", minHeight: 52, flexShrink: 0,
    },
    logo: { fontWeight: 800, fontSize: 16, color: "#10b981", letterSpacing: "0.05em" },
    badge: { fontSize: 10, background: "#10b981", color: "#fff", borderRadius: 4, padding: "2px 6px", fontWeight: 700 },
    search: {
      background: dark ? "#1f2937" : "#f3f4f6",
      border: `1px solid ${dark ? "#374151" : "#d1d5db"}`,
      color: dark ? "#e2e8f0" : "#111827",
      borderRadius: 6, padding: "5px 10px", fontSize: 13, width: 200,
      outline: "none",
    },
    count: { fontSize: 11, color: dark ? "#6b7280" : "#9ca3af", marginRight: "auto" },
    layerBtn: (active) => ({
      padding: "5px 11px", borderRadius: 6, border: "none", cursor: "pointer",
      fontSize: 12, fontWeight: 500,
      background: active ? "#10b981" : (dark ? "#1f2937" : "#f3f4f6"),
      color: active ? "#fff" : (dark ? "#9ca3af" : "#6b7280"),
      transition: "all 0.15s",
    }),
    iconBtn: {
      background: dark ? "#1f2937" : "#f3f4f6",
      border: "none", color: dark ? "#9ca3af" : "#6b7280",
      cursor: "pointer", borderRadius: 6, padding: "5px 10px", fontSize: 13,
    },
    dot: { width: 8, height: 8, borderRadius: "50%", background: "#f59e0b", flexShrink: 0 },
  };

  return (
    <div style={s.bar}>
      <span style={s.logo}>KHAP</span>
      <span style={s.badge}>v3</span>
      <input
        style={s.search}
        placeholder="Search facilities, counties…"
        value={searchQuery}
        onChange={(e) => onSearch(e.target.value)}
      />
      <span style={s.count}>{facilityCount.toLocaleString()} facilities</span>
      {LAYERS.map((l) => (
        <button key={l.id} style={s.layerBtn(activeLayer === l.id)} onClick={() => onLayerChange(l.id)}>
          {l.label}
        </button>
      ))}
      {loading && <div style={s.dot} />}
      <button style={s.iconBtn} onClick={onThemeToggle} title="Toggle theme">
        {theme === "dark" ? "☀️" : "🌙"}
      </button>
      <button style={s.iconBtn} onClick={onToggleSidebar}>
        {sidebarOpen ? "◀" : "▶"}
      </button>
    </div>
  );
}
