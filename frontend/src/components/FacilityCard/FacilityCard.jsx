import styles from "./FacilityCard.module.css";

/**
 * FacilityCard — shows details for the selected facility.
 *
 * Props
 * -----
 * facility      — facility object (null = nothing selected)
 * routeLoading  — bool, show spinner while route is loading
 * noRouteFound  — bool, show "no route" message
 */
export default function FacilityCard({ facility, routeLoading, noRouteFound }) {
  if (!facility) return null;

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h3 className={styles.name}>{facility.name || "Unnamed Facility"}</h3>
        {facility.facility_type && (
          <span className={styles.badge}>{facility.facility_type}</span>
        )}
      </div>

      <div className={styles.details}>
        {facility.operator && (
          <p className={styles.detail}>
            <span className={styles.label}>Operator</span>
            {facility.operator}
          </p>
        )}
        {facility.phone && (
          <p className={styles.detail}>
            <span className={styles.label}>Phone</span>
            <a href={`tel:${facility.phone}`}>{facility.phone}</a>
          </p>
        )}
        {facility.website && (
          <p className={styles.detail}>
            <span className={styles.label}>Website</span>
            <a href={facility.website} target="_blank" rel="noreferrer">
              {facility.website}
            </a>
          </p>
        )}
        {facility.emergency && (
          <p className={styles.detail}>
            <span className={styles.label}>Emergency</span>
            {facility.emergency}
          </p>
        )}
        {facility.opening_hours && (
          <p className={styles.detail}>
            <span className={styles.label}>Hours</span>
            {facility.opening_hours}
          </p>
        )}
        {facility.wheelchair && (
          <p className={styles.detail}>
            <span className={styles.label}>Wheelchair</span>
            {facility.wheelchair}
          </p>
        )}
        {facility.distance_m != null && (
          <p className={styles.detail}>
            <span className={styles.label}>Distance</span>
            {(facility.distance_m / 1000).toFixed(2)} km
          </p>
        )}
      </div>

      {routeLoading && <p className={styles.status}>Calculating route…</p>}
      {noRouteFound && (
        <p className={styles.noRoute}>
          No drivable route found to this facility.
        </p>
      )}
    </div>
  );
}
