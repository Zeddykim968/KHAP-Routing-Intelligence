"use client";

import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "khap-theme";

export function useTheme() {
  const [theme, setTheme] = useState("light");

  // Adopt the stored (or system) preference after mount — matches the
  // inline script in the layout so there is no flash of the wrong theme.
  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    const system = window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
    setTheme(stored || system);

    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (e) => {
      if (!window.localStorage.getItem(STORAGE_KEY)) {
        setTheme(e.matches ? "dark" : "light");
      }
    };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const toggle = useCallback(() => {
    setTheme((prev) => {
      const next = prev === "dark" ? "light" : "dark";
      try {
        window.localStorage.setItem(STORAGE_KEY, next);
      } catch {
        /* storage unavailable */
      }
      return next;
    });
  }, []);

  return [theme, toggle];
}
