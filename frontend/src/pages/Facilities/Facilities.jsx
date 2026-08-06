import { useState, useEffect } from "react";
import FacilityCard from "../../components/FacilityCard/FacilityCard";
import { fetchFacilities, searchFacilities } from "../../services/api";
import styles from "./Facilities.module.css";

const FACILITY_TYPES = ["hospital", "clinic", "health_centre", "dispensary", "pharmacy"];

/**
 * Facilities page — browsable, filterable list of all facilities.
 */
export default function Facilities() {
  const [facilities,    setFacilities]    = useState([]);
  const [selected,      setSelected]      = useState(null);
  const [loading,       setLoading]       = useState(false);
  const [page,          setPage]          = useState(0);
  const [total,         setTotal]         = useState(0);
  const [typeFilter,    setTypeFilter]    = useState("");
  const [searchQuery,   setSearchQuery]   = useState("");
  const LIMIT = 30;

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, typeFilter]);

  async function load() {
    setLoading(true);
    try {
      let data;
      if (typeFilter || searchQuery) {
        data = await searchFacilities({ q: searchQuery || undefined, facility_type: typeFilter || undefined, limit: LIMIT });
        setFacilities(Array.isArray(data) ? data : []);
        setTotal(Array.isArray(data) ? data.length : 0);
      } else {
        data = await fetchFacilities({ skip: page * LIMIT, limit: LIMIT });
        setFacilities(data?.facilities ?? []);
        setTotal(data?.total ?? 0);
      }
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e) {
    e.preventDefault();
    setPage(0);
    load();
  }

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <form className={styles.searchForm} onSubmit={handleSearch}>
          <input
            className={styles.input}
            type="text"
            placeholder="Search facilities…"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <select
            className={styles.select}
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value); setPage(0); }}
          >
            <option value="">All types</option>
            {FACILITY_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <button className={styles.btn} type="submit">Search</button>
        </form>
        <span className={styles.count}>{total.toLocaleString()} facilities</span>
      </div>

      {loading && <p className={styles.loading}>Loading…</p>}

      <div className={styles.grid}>
        {facilities.map((f) => (
          <div
            key={f.id}
            className={`${styles.cardWrapper} ${selected?.id === f.id ? styles.active : ""}`}
            onClick={() => setSelected(selected?.id === f.id ? null : f)}
          >
            <FacilityCard facility={f} />
          </div>
        ))}
      </div>

      {!typeFilter && !searchQuery && (
        <div className={styles.pagination}>
          <button
            className={styles.pageBtn}
            disabled={page === 0}
            onClick={() => setPage((p) => p - 1)}
          >
            ← Previous
          </button>
          <span className={styles.pageInfo}>
            Page {page + 1} of {Math.ceil(total / LIMIT)}
          </span>
          <button
            className={styles.pageBtn}
            disabled={(page + 1) * LIMIT >= total}
            onClick={() => setPage((p) => p + 1)}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
