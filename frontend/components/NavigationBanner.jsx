"use client";

import { X } from "lucide-react";
import { formatArrival, formatDistance, formatDuration, formatStepDistance } from "@/lib/format";
import { stepIcon } from "@/lib/labels";
import styles from "./NavigationBanner.module.css";

export default function NavigationBanner({
  step,
  distToManeuver,
  remaining_m,
  remaining_s,
  onExit,
}) {
  const Icon = stepIcon(step?.icon);

  return (
    <div className={styles.banner} role="status" aria-live="polite">
      <span className={styles.icon}>
        <Icon size={30} />
      </span>

      <div className={styles.mid}>
        <div className={styles.dist}>
          {distToManeuver != null ? formatStepDistance(distToManeuver) : formatDuration(remaining_s)}
        </div>
        <div className={styles.instr}>{step?.instruction || "Continue on the route"}</div>
      </div>

      <div className={styles.right}>
        <div className={styles.eta}>{formatArrival(remaining_s)}</div>
        <div className={styles.rem}>{formatDistance(remaining_m)} left</div>
      </div>

      <button className={styles.exit} onClick={onExit} aria-label="Exit navigation">
        <X size={20} />
      </button>
    </div>
  );
}
