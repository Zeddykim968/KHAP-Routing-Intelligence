"use client";

import { useEffect, useRef, useState } from "react";
import { Crosshair, MapPin, Moon, Search, Sun, X } from "lucide-react";
import { searchFacilities } from "@/lib/api";
import { formatDistance } from "@/lib/format";
import { TYPE_LABELS } from "@/lib/labels";
import styles from "./SearchBar.module.css";

export default function SearchBar({
  origin,
  theme,
  onToggleTheme,
  onSelect,
  onLocate,
  locating,
}) {
  const [text, setText] = useState("");
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const tokenRef = useRef(0);
  const rootRef = useRef(null);

  // Debounced typeahead against /api/search/.
  useEffect(() => {
    const q = text.trim();
    if (q.length < 2) {
      setItems([]);
      return;
    }
    const id = setTimeout(async () => {
      const token = ++tokenRef.current;
      try {
        const res = await searchFacilities(q, origin?.lat, origin?.lon);
        if (token !== tokenRef.current) return;
        const list = Array.isArray(res) ? res : res?.results || [];
        setItems(list);
        setOpen(true);
      } catch {
        if (token === tokenRef.current) {
          setItems([]);
          setOpen(true);
        }
      }
    }, 250);
    return () => clearTimeout(id);
  }, [text, origin]);

  // Close suggestions on outside click.
  useEffect(() => {
    const onDoc = (e) => {
      if (!rootRef.current?.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const pick = (f) => {
    setText(f.name);
    setOpen(false);
    setItems([]);
    onSelect?.(f);
  };

  const clear = () => {
    setText("");
    setItems([]);
    setOpen(false);
  };

  const onKeyDown = (e) => {
    if (e.key === "Escape") setOpen(false);
    if (e.key === "Enter" && items.length > 0) pick(items[0]);
  };

  return (
    <div className={styles.root} ref={rootRef}>
      <div
        className={styles.pill}
        style={open && items.length ? { borderRadius: "22px 22px 0 0" } : undefined}
      >
        <Search size={20} className={styles.leadIcon} aria-hidden="true" />
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onFocus={() => items.length && setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Search facilities in Kenya"
          aria-label="Search health facilities"
          autoComplete="off"
        />
        {text && (
          <button className={styles.iconBtn} onClick={clear} aria-label="Clear search">
            <X size={18} />
          </button>
        )}
        <span className={styles.divider} aria-hidden="true" />
        <button
          className={`${styles.iconBtn} ${locating ? styles.spinning : ""}`}
          onClick={onLocate}
          aria-label="Use my location"
          title="Use my location"
        >
          <Crosshair size={19} />
        </button>
        <button
          className={styles.iconBtn}
          onClick={onToggleTheme}
          aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          title={theme === "dark" ? "Light mode" : "Dark mode"}
        >
          {theme === "dark" ? <Sun size={19} /> : <Moon size={19} />}
        </button>
      </div>

      {open && items.length > 0 && (
        <ul className={styles.suggest} role="listbox" aria-label="Search suggestions">
          {items.map((f) => (
            <li
              key={f.id}
              role="option"
              onMouseDown={(e) => {
                e.preventDefault();
                pick(f);
              }}
            >
              <span className={styles.sugIcon}>
                <MapPin size={16} />
              </span>
              <span className={styles.sugText}>
                <span className={styles.sugName}>{f.name}</span>
                <span className={styles.sugMeta}>
                  {TYPE_LABELS[f.facility_type] || f.facility_type}
                  {f.distance_m != null ? ` · ${formatDistance(f.distance_m)}` : ""}
                </span>
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
