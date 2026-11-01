"use client";

import { Accessibility, Crosshair, MapPin, Siren, TriangleAlert } from "lucide-react";
import { formatDistance, openState } from "@/lib/format";
import { TYPE_LABELS } from "@/lib/labels";
import styles from "./FacilityList.module.css";

function SkeletonRow() {
  return (
    <div className={`${styles.row} ${styles.skeleton}`} aria-hidden="true">
      <div className={`${styles.skLine} ${styles.skWide}`} />
      <div className={`${styles.skLine} ${styles.skMid}`} />
      <div className={`${styles.skLine} ${styles.skNarrow}`} />
    </div>
  );
}

export default function FacilityList({
  items,
  status,
  error,
  selectedId,
  onSelect,
  onRetry,
  hasOrigin,
  filtered,
  onClearFilters,
}) {
  if (status === "loading") {
    return (
      <div className={styles.list}>
        <div className={styles.head}>Looking for nearby facilities…</div>
        <SkeletonRow />
        <SkeletonRow />
        <SkeletonRow />
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className={styles.state}>
        <TriangleAlert size={28} />
        <p>{error || "Could not load facilities."}</p>
        <button className={styles.stateBtn} onClick={onRetry}>
          Try again
        </button>
      </div>
    );
  }

  if (!items?.length) {
    if (!hasOrigin) {
      return (
        <div className={styles.state}>
          <Crosshair size={28} />
          <p>Set your starting point to see facilities around you.</p>
          <p className={styles.hint}>Right-click the map, or allow location access.</p>
        </div>
      );
    }
    return (
      <div className={styles.state}>
        <MapPin size={28} />
        <p>
          {filtered
            ? "No facilities match these filters nearby."
            : "No facilities found nearby."}
        </p>
        {filtered && (
          <button className={styles.stateBtn} onClick={onClearFilters}>
            Clear filters
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={`${styles.list} khap-scroll`} role="list">
      <div className={styles.head}>
        {items.length} {items.length === 1 ? "facility" : "facilities"} nearby
        <span className={styles.headSub}>sorted by distance</span>
      </div>

      {items.map((f) => {
        const st = f.is_open === true || f.is_open === false ? openState(f.is_open) : null;
        const ins = f.insurances || [];
        return (
          <button
            key={f.id}
            className={`${styles.row} ${f.id === selectedId ? styles.rowActive : ""}`}
            onClick={() => onSelect(f)}
            role="listitem"
          >
            <div className={styles.top}>
              <span className={styles.name}>{f.name}</span>
              <span className={styles.dist}>{formatDistance(f.distance_m)}</span>
            </div>

            <div className={styles.meta}>
              <span className={styles.type}>{TYPE_LABELS[f.facility_type] || f.facility_type}</span>
              {st && (
                <>
                  <span className={styles.dot} />
                  <span className={st.tone === "closed" ? styles.closed : styles.open}>
                    {st.label}
                  </span>
                </>
              )}
              {f.is_emergency && (
                <>
                  <span className={styles.dot} />
                  <span className={styles.emg}>
                    <Siren size={13} /> Emergency
                  </span>
                </>
              )}
              {f.wheelchair_accessible && (
                <>
                  <span className={styles.dot} />
                  <Accessibility size={14} />
                </>
              )}
            </div>

            {f.services?.length > 0 && (
              <div className={styles.chips}>
                {f.services.slice(0, 3).map((s) => (
                  <span key={s.slug} className={styles.chip}>
                    {s.name}
                  </span>
                ))}
                {f.services.length > 3 && (
                  <span className={styles.chipMore}>+{f.services.length - 3} more</span>
                )}
              </div>
            )}

            {ins.length > 0 && (
              <div className={styles.ins}>
                Accepts {ins.slice(0, 3).map((i) => i.name).join(", ")}
                {ins.length > 3 ? ` +${ins.length - 3} more` : ""}
              </div>
            )}
          </button>
        );
      })}
    </div>
  );
}
