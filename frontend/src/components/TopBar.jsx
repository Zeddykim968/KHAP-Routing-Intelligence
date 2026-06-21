import React from "react";

const LAYERS = [
  { id: "facilities", label: "🏥 Facilities" },
  { id: "accessibility", label: "📊 Accessibility" },
  { id: "coverage", label: "🎯 Coverage" },
];

const styles = {
  bar: {
    display: "flex",
    alignItems: "center",
    background: "#111827",
    borderBottom: "1px solid #1f2937",
    padding: "0 16px",
    height: 52,
    gap: 12,
    flexShrink: 0,
  },
  logo: {
    fontWeight: 700,
    fontSize: 16,
    color: "#10b981",
    letterSpacing: "0.05em",
    marginRight: 8,
  },
  version: {
    fontSize: 11,
    color: "#6b7280",
    marginRight: "auto",
  },
  layerBtn: (active) => ({
    padding: "5px 12px",
    borderRadius: 6,
    border: "none",
    cursor: "pointer",
    fontSize: 13,
    fontWeight: 500,
    background: active ? "#10b981" : "#1f2937",
    color: active ? "#fff" : "#9ca3af",
    transition: "all 0.15s",
  }),
  toggleBtn: {
    marginLeft: 8,
    background: "#1f2937",
    border: "none",
    color: "#9ca3af",
    cursor: "pointer",
    borderRadius: 6,
    padding: "5px 10px",
    fontSize: 13,
  },
  loading: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: "#f59e0b",
    marginLeft: 8,
    animation: "pulse 1s infinite",
  },
};

export default function TopBar({ activeLayer, onLayerChange, sidebarOpen, onToggleSidebar, loading }) {
  return (
    <div style={styles.bar}>
      <span style={styles.logo}>KHAP</span>
      <span style={styles.version}>Kenya Health Access Platform v2.0</span>
      {LAYERS.map((l) => (
        <button
          key={l.id}
          style={styles.layerBtn(activeLayer === l.id)}
          onClick={() => onLayerChange(l.id)}
        >
          {l.label}
        </button>
      ))}
      {loading && <div style={styles.loading} />}
      <button style={styles.toggleBtn} onClick={onToggleSidebar}>
        {sidebarOpen ? "◀ Hide" : "▶ Show"}
      </button>
    </div>
  );
}
