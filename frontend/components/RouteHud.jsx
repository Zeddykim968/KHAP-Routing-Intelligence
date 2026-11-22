"use client";

import { useEffect, useRef } from "react";
import { ArrowLeft, Bike, Car, Footprints, MapPin, Navigation, Play, Square } from "lucide-react";
import { formatArrival, formatDistance, formatDuration, formatSpeed, formatStepDistance } from "@/lib/format";
import { stepIcon } from "@/lib/labels";
import styles from "./RouteHud.module.css";

// Same three modes OpenRouteService exposes on its free profiles.
const TRAVEL_MODES = [
  { id: "driving", label: "Drive", Icon: Car, copy: "via fastest route" },
  { id: "walking", label: "Walk", Icon: Footprints, copy: "via walking route" },
  { id: "cycling", label: "Cycle", Icon: Bike, copy: "via cycling route" },
];

export default function RouteHud({
  route,
  facility,
  progress,
  navActive,
  simActive,
  onBack,
  onStart,
  onSimulate,
  onExitNav,
  travelMode = "driving",
  routeBusy = false,
  onTravelMode,
}) {
  const activeRef = useRef(null);

  // Keep the current maneuver visible while navigating.
  useEffect(() => {
    if (navActive && activeRef.current) {
      activeRef.current.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }, [navActive, progress?.stepIndex]);

  const remaining = progress ? progress.remaining_m : route.distance_m;
  const remainingS = progress ? progress.remaining_s : route.duration_s;
  const frac = progress ? progress.frac : 0;
  const steps = route.steps || [];
  const mode = TRAVEL_MODES.find((m) => m.id === travelMode) || TRAVEL_MODES[0];

  return (
    <div className={styles.wrap}>
      <div className={styles.modes} role="tablist" aria-label="Travel mode">
        {TRAVEL_MODES.map(({ id, label, Icon }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={travelMode === id}
            className={`${styles.modeTab} ${travelMode === id ? styles.modeOn : ""}`}
            onClick={() => onTravelMode?.(id)}
            disabled={!!navActive || routeBusy}
          >
            <Icon size={17} aria-hidden="true" />
            {label}
          </button>
        ))}
        {routeBusy && <span className={styles.modeBusy}>Updating…</span>}
      </div>

      <div className={styles.summary}>
        <div className={styles.eta}>
          <div className={styles.arrival}>{formatArrival(remainingS)}</div>
          <div className={styles.sub}>{formatDuration(remainingS)}</div>
        </div>
        <div className={styles.distBlock}>
          <div className={styles.bigDist}>{formatDistance(remaining)}</div>
          <div className={styles.sub}>
            {mode.copy}
            {progress?.speed != null && navActive ? ` · ${formatSpeed(progress.speed)}` : ""}
          </div>
        </div>
        <span className={styles.dot} />
        <div className={styles.distBlock}>
          <div className={styles.bigDist}>{facility ? shortName(facility.name) : "Destination"}</div>
          <div className={styles.sub}>destination</div>
        </div>
      </div>

      {navActive && (
        <div className={styles.track} role="progressbar" aria-valuenow={Math.round(frac * 100)}>
          <div className={styles.fill} style={{ width: `${Math.min(100, frac * 100)}%` }} />
        </div>
      )}

      <div className={styles.controls}>
        {!navActive ? (
          <button className={styles.primary} onClick={onStart}>
            <Navigation size={17} /> Start
          </button>
        ) : (
          <button className={styles.exitBtn} onClick={onExitNav}>
            Exit
          </button>
        )}
        <button
          className={simActive ? styles.simOn : styles.sim}
          onClick={onSimulate}
          aria-pressed={simActive}
        >
          {simActive ? (
            <>
              <Square size={15} /> Stop drive
            </>
          ) : (
            <>
              <Play size={15} /> Simulate drive
            </>
          )}
        </button>
        {!navActive && (
          <button className={styles.backBtn} onClick={onBack} aria-label="Back">
            <ArrowLeft size={18} />
          </button>
        )}
      </div>

      <div className={`${styles.steps} khap-scroll`}>
        <div className={styles.destRow}>
          <MapPin size={17} />
          <span>{facility ? facility.name : "Destination"}</span>
          <span className={styles.destDist}>{formatDistance(route.distance_m)}</span>
        </div>

        {steps.map((s, i) => {
          const Icon = stepIcon(s.icon);
          const active = navActive && progress ? i === progress.stepIndex : false;
          return (
            <div
              key={i}
              ref={active ? activeRef : undefined}
              className={`${styles.step} ${active ? styles.stepActive : ""}`}
            >
              <span className={styles.stepIcon}>
                <Icon size={active ? 20 : 16} />
              </span>
              <span className={styles.stepText}>{s.instruction}</span>
              <span className={styles.stepDist}>{formatStepDistance(s.distance_m)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function shortName(name) {
  if (!name) return "";
  const words = name.split(/\s+/);
  if (words.length <= 2) return name;
  return words.slice(0, 2).join(" ") + "…";
}
