import styles from "./RouteSummary.module.css";

/**
 * RouteSummary — displays route statistics returned by OSRM.
 *
 * Props
 * -----
 * route — RouteResponse object { distance_m, duration_s, route }
 */
export default function RouteSummary({ route }) {
  if (!route) return null;

  const km      = (route.distance_m / 1000).toFixed(2);
  const minutes = Math.round(route.duration_s / 60);
  const hours   = Math.floor(minutes / 60);
  const mins    = minutes % 60;
  const time    = hours > 0 ? `${hours}h ${mins}m` : `${mins} min`;

  return (
    <div className={styles.summary}>
      <div className={styles.stat}>
        <span className={styles.value}>{km}</span>
        <span className={styles.unit}>km</span>
      </div>
      <div className={styles.divider} />
      <div className={styles.stat}>
        <span className={styles.value}>{time}</span>
        <span className={styles.unit}>drive</span>
      </div>
    </div>
  );
}
