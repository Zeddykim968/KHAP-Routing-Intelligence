// Display formatting helpers for distances, durations, and opening status.

export function formatDistance(m) {
  if (m == null || Number.isNaN(m)) return "";
  if (m < 950) return `${Math.max(10, Math.round(m / 10) * 10)} m`;
  if (m < 10_000) return `${(m / 1000).toFixed(1)} km`;
  return `${Math.round(m / 1000)} km`;
}

export function formatStepDistance(m) {
  if (m == null || Number.isNaN(m)) return "";
  if (m < 1000) return `${Math.max(10, Math.round(m / 10) * 10)} m`;
  return `${(m / 1000).toFixed(1)} km`;
}

export function formatDuration(s) {
  if (s == null || Number.isNaN(s)) return "";
  const minutes = Math.max(1, Math.round(s / 60));
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m ? `${h} hr ${m} min` : `${h} hr`;
}

export function formatArrival(s) {
  const when = new Date(Date.now() + (s || 0) * 1000);
  return when.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export function openState(isOpen) {
  if (isOpen === true) return { label: "Open now", tone: "open" };
  if (isOpen === false) return { label: "Closed", tone: "closed" };
  return { label: "Hours unknown", tone: "unknown" };
}

export function formatSpeed(mps) {
  return `${Math.round(mps * 3.6)} km/h`;
}
