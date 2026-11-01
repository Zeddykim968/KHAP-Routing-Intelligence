"use client";

import { Clock, Siren } from "lucide-react";
import { TYPE_LABELS } from "@/lib/labels";
import styles from "./CategoryChips.module.css";

const ORDER = [
  "hospital",
  "clinic",
  "health_centre",
  "dispensary",
  "pharmacy",
  "dentist",
  "laboratory",
  "maternity",
  "eye_clinic",
];

export default function CategoryChips({
  value,
  onChange,
  openNow,
  emergency,
  onToggleOpenNow,
  onToggleEmergency,
}) {
  return (
    <div className={styles.scroller} role="toolbar" aria-label="Filters">
      <button
        className={`${styles.chip} ${value === "all" ? styles.active : ""}`}
        onClick={() => onChange("all")}
      >
        All
      </button>
      {ORDER.map((t) => (
        <button
          key={t}
          className={`${styles.chip} ${value === t ? styles.active : ""}`}
          onClick={() => onChange(value === t ? "all" : t)}
        >
          {TYPE_LABELS[t] || t}
        </button>
      ))}
      <span className={styles.sep} aria-hidden="true" />
      <button
        className={`${styles.chip} ${openNow ? styles.active : ""}`}
        onClick={onToggleOpenNow}
        aria-pressed={openNow}
      >
        <Clock size={14} /> Open now
      </button>
      <button
        className={`${styles.chip} ${styles.emergency} ${emergency ? styles.active : ""}`}
        onClick={onToggleEmergency}
        aria-pressed={emergency}
      >
        <Siren size={14} /> Emergency
      </button>
    </div>
  );
}
