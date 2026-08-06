import { useState } from "react";
import Dashboard  from "./pages/Dashboard/Dashboard";
import Facilities from "./pages/Facilities/Facilities";
import Routing    from "./pages/Routing/Routing";
import styles     from "./App.module.css";

const PAGES = [
  { id: "dashboard",  label: "Dashboard"  },
  { id: "facilities", label: "Facilities" },
  { id: "routing",    label: "Routing"    },
];

export default function App() {
  const [page, setPage] = useState("dashboard");

  return (
    <div className={styles.app}>
      <nav className={styles.nav}>
        <span className={styles.brand}>KHAP</span>
        {PAGES.map((p) => (
          <button
            key={p.id}
            className={`${styles.navBtn} ${page === p.id ? styles.active : ""}`}
            onClick={() => setPage(p.id)}
          >
            {p.label}
          </button>
        ))}
      </nav>

      <main className={styles.main}>
        {page === "dashboard"  && <Dashboard  />}
        {page === "facilities" && <Facilities />}
        {page === "routing"    && <Routing    />}
      </main>
    </div>
  );
}
